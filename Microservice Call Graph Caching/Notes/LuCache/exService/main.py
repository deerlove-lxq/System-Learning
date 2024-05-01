from flask import Flask, request, jsonify
from queue import Queue
from collections import deque
import threading
import json
import os
import requests
import shortuuid
import time
import hashlib
from menu import *
from utils import *

"""global variable"""
QueueSize = 10
WQ = Queue(maxsize=QueueSize)   # Work Queue
readsets = {}                   # map(CallId, set(DepKey | DepCall))
state = State()                 # Record State
cacheList = {
    'caller_read': "./data/caller_read.json",
    'frontend': "./data/frontend.json"
}

"""LuCache Protocol"""
class Cache:
    def __init__(self, path: str):
        self.cachePath = path
        with open(self.cachePath, "r") as f:
            self.info = json.load(f)
        
    def cacheGet(self, key: str):
        if key in self.info:
            content = self.info.get(key)
            value = content.get('value')
            visited = content.get('visited')
            if value:
                return value, visited
        return None, None
    
    def cacheSet(self, key: str, value: str, vs: list):
        content = {
            'value': value,
            'visited': vs
        }
        self.info[key] = content
        with open(self.cachePath, "w") as f:
            json.dump(self.info, f)    
    
    def cacheInvalidate(self, key: str):
        if key in self.info:
            del self.info[key]
            with open(self.cachePath, "w") as f:
                json.dump(self.info, f)     

class CacheManager:
    def __init__(self, service_name, upstream_name):
        self.service_name = service_name
        self.upstream_name = upstream_name
    
    def validCall(self, ca: str):
        valid = True
        for item in reversed(state.history):
            if item.dataType == 'call' and item.data == ca:
                return valid
            elif item.dataType == 'inv_ca' and item.data in state.callDeps:
                valid = False
            elif item.dataType == 'inv_key' and item.data in state.keyDeps:
                valid = False
            else:
                continue
        print("Could not find call in history")
        return False
    
    def start(self, ca: str):
        historyItem = HistoryItem('call', ca)
        state.history.append(historyItem)
        
    def end(self, rs: set, ca: str, vs: list, service_name: str, ret: str, cache: Cache):
        if self.validCall(ca):
            req = {
                'to_whom': self.service_name,
                'dataType': 'saveCallsRequest',
                'ca': ca,
                'ret': ret,
                'vs': vs,
                'cache': cache
            }
            WQ.put(req)
            state.storeDeps(ca, service_name, rs)
    
    def saveCalls(self, ca: str, ret: str, vs: list, cache: Cache):
        cache.cacheSet(ca, ret, vs)
        
    def invalidateKey(self, key: str):
        state.history.append(HistoryItem('inv_key', key))
        if key in state.keyDeps:
            affected = state.keyDeps[key]
            del state.keyDeps[key]
            for service_name in affected:
                req = {
                    'to_whom': service_name,
                    'dataType': 'invalidateCallsRequest',
                    'ca': affected[service_name]
                }
                WQ.put(req)
        
    def invalidateCalls(self, ca: str):
        state.history.append(HistoryItem('inv_ca', ca))
        if self.service_name in cacheList:
            cache = Cache(cacheList[self.service_name])
            cache.cacheInvalidate(ca)
        if ca in state.callDeps:
            affected = state.callDeps[ca]
            del state.callDeps[ca]
            for service_name in affected:
                req = {
                    'to_whom': service_name,
                    'dataType': 'invalidateCallsRequest',
                    'ca': affected[service_name]
                }
                WQ.put(req)
            
    def process(self):
        while True:
            if not WQ.empty() and WQ.queue[0]['to_whom'] == self.service_name:
                # Slow processing considering that multiple threads may change when checking for non-empty and getting queue headers
                time.sleep(0.5)
                request = WQ.get()
                print(f"{self.service_name} processing request: {request['dataType']}")
                if request['dataType'] == 'startRequest':
                    self.start(request['ca'])
                elif request['dataType'] == 'endRequest':
                    self.end(request['rs'], request['ca'], request['vs'], request['service_name'] , request['ret'], request['cache'])
                elif request['dataType'] == 'saveCallsRequest':
                    self.saveCalls(request['ca'], request['ret'], request['vs'], request['cache'])
                elif request['dataType'] == 'invalidateKeyRequest':
                    self.invalidateKey(request['key'])
                elif request['dataType'] == 'invalidateCallsRequest':
                    self.invalidateCalls(request['ca'])
                else:
                    print("Unreachable")
                    
class Wrapper:
    def hash_call_args(self, service_name: str, endpoint: str, arg: str) -> str:
        h = hashlib.sha256()
        h.update(service_name.encode('utf-8'))
        h.update(endpoint.encode('utf-8'))
        h.update(arg.encode('utf-8'))
        input_hash = h.hexdigest()
        return input_hash
    
    def preReqStart(self, ctx: Context):
        if ctx.read_only:
            cid = ctx.call_id
            ca = ctx.ca
            readsets[cid] = set()
            req = {
                'to_whom': ctx.service_name,
                'dataType': 'startRequest',
                'ca': ca
            }
            WQ.put(req)
    
    def preReqEnd(self, ctx: Context, ret: str, cache: Cache):
        if ctx.read_only:
            cid = ctx.call_id
            ca = ctx.ca
            rs = readsets[cid]
            service_name = ctx.service_name
            vs = ctx.visited
            req = {
                'to_whom': ctx.service_name,
                'dataType': 'endRequest',
                'rs': rs,
                'ca': ca,
                'vs': vs,
                'service_name': service_name,
                'ret': ret,
                'cache': cache
            }
            WQ.put(req)
            
    def postWrite(self, ctx: Context, key: str):
        req = {
            'to_whom': ctx.service_name,
            'dataType': 'invalidateKeyRequest',
            'key': key,
        }
        WQ.put(req)
    
    def preRead(self, ctx: Context, key: str):
        if ctx.read_only:
            cid = ctx.call_id
            dep = Dep('key', key)
            readsets[cid].add(dep)
        
    def preCall(self, ctx: Context, ca: str, cache: Cache):
        if ctx.read_only:
            cid = ctx.call_id
            dep = Dep('ca', ca)
            readsets[cid].add(dep)
            # Determine if the intersection of two lists is empty
            val, visited = cache.cacheGet(ca)
            if val:                
                ctx_vs = set(ctx.visited)
                ca_vs = set(visited)
                if not (ctx_vs & ca_vs):
                    return val, visited
        return None, None

"""Flask"""
def run_callee():
    app = Flask("callee")
    @app.route('/read', methods=['GET'])
    def read():
        service_name = 'callee'
        key = request.args.get('key')
        print(f"Read request for key: {key}")
        if os.path.exists("./data/database.json"):
            with open("./data/database.json", "r") as f:
                db = json.load(f)
            value = db.get(key)
            if value:
                response = {
                    'visited': [service_name],
                    "data": value
                }
                return jsonify(response), 200
            else:
                return jsonify({"data": "Key not in database"}), 404
        else:
            return jsonify({"data": "Database file not found"}), 404
    @app.route('/write', methods=['GET'])
    def write():
        service_name = 'callee'
        key = request.args.get('key')
        value = request.args.get('value')
        data = {key: value}
        endpoint = "write"
        wrapper = Wrapper()
        call_id = shortuuid.uuid()
        ca = wrapper.hash_call_args(service_name, endpoint, key)
        ctx = Context(call_id, service_name, ca, [], False)
        print(f"Write request with data: {data}")
        with open("./data/database.json", "w") as f:
            json.dump(data, f)
        wrapper.postWrite(ctx, key)
        response = {
            'visited': [service_name],
            "data": "Write successful"
        }
        return jsonify(response), 200
    app.run(host='0.0.0.0', port=8888)

def run_caller_read():
    app = Flask("call_read")
    @app.route('/call_read', methods=['GET'])
    def caller_read():
        # initialize
        service_name = 'caller_read'
        endpoint = 'call_read'
        key = request.args.get('key')
        cache = Cache("./data/caller_read.json")
        wrapper = Wrapper()
        call_id = shortuuid.uuid()
        ca = wrapper.hash_call_args(service_name, endpoint, key)
        ctx = Context(call_id, service_name, ca, [], True)
        
        # process
        wrapper.preReqStart(ctx)
        wrapper.preRead(ctx, key)
        ret, ca_visited = wrapper.preCall(ctx, ca, cache)
        if ret:
            new_response = {
                'visited': ca_visited,
                "data": ret,
                "cache_hit": True
            }
            ctx.visited = ca_visited
        else:
            response = requests.get('http://localhost:8888/read', params={'key': key})
            response_content = response.json() if response.headers['Content-Type'] == 'application/json' else response.text
            if response.status_code == 200:
                ret = response_content['data']
                ctx.visited = response_content['visited']
                new_visited = ctx.visited.copy()
                new_visited.append(service_name)
                new_response = {
                    'visited': new_visited,
                    "data": ret,
                    "cache_hit": False
                }
            else:
                return jsonify(response_content), response.status_code
        wrapper.preReqEnd(ctx, ret, cache)
        return jsonify(new_response), 200
    app.run(host='0.0.0.0', port=6666)
    
def run_caller_write():
    app = Flask("call_write")
    @app.route('/call_write', methods=['GET'])
    def call_write():
        # initialize
        service_name = 'caller_write'
        key = request.args.get('key')
        value = request.args.get('value')
        endpoint = 'call_write'
        wrapper = Wrapper()
        call_id = shortuuid.uuid()
        ca = wrapper.hash_call_args(service_name, endpoint, key)
        ctx = Context(call_id, service_name, ca, [], False)
        
        # process
        response = requests.get(url='http://localhost:8888/write', params={'key': key, 'value': value})
        response_content = response.json() if response.headers['Content-Type'] == 'application/json' else response.text
        if response.status_code == 200:
            ctx.visited = response_content['visited']
            new_visited = ctx.visited.copy()
            new_visited.append(service_name)
            response_content['visited'] = new_visited
            wrapper.postWrite(ctx, key)
        return jsonify(response_content), response.status_code
    app.run(host='0.0.0.0', port=7777)

def run_frontend():
    app = Flask("frontend")
    @app.route('/read_from_caller', methods=['GET'])
    def read_from_caller():
        # initialize
        service_name = 'frontend'
        endpoint = 'read_from_caller'
        key = request.args.get('key')
        cache = Cache("./data/frontend.json")
        wrapper = Wrapper()
        call_id = shortuuid.uuid()
        ca = wrapper.hash_call_args(service_name, endpoint, key)
        ctx = Context(call_id, service_name, ca, [], True)
        
        # process
        wrapper.preReqStart(ctx)
        wrapper.preRead(ctx, key)
        ret, ca_visited = wrapper.preCall(ctx, ca, cache)
        if ret:
            new_response = {
                'visited': ca_visited,
                "data": ret,
                "cache_hit": True
            }
            ctx.visited = ca_visited
        else:
            response = requests.get(url='http://localhost:6666/call_read', params={'key': key})
            response_content = response.json() if response.headers['Content-Type'] == 'application/json' else response.text
            if response.status_code == 200:
                ret = response_content['data']
                ctx.visited = response_content['visited']
                new_visited = ctx.visited.copy()
                new_visited.append(service_name)
                new_response = {
                    'visited': new_visited,
                    "data": ret,
                    "cache_hit": False
                }
            else:
                return jsonify(response_content), response.status_code
        wrapper.preReqEnd(ctx, ret, cache)
        return jsonify(new_response), 200
    @app.route('/write_to_caller', methods=['GET'])
    def write_to_caller():
        # initialize
        service_name = 'frontend'
        key = request.args.get('key')
        value = request.args.get('value')
        endpoint = 'write_to_caller'
        wrapper = Wrapper()
        call_id = shortuuid.uuid()
        ca = wrapper.hash_call_args(service_name, endpoint, key)
        ctx = Context(call_id, service_name, ca, [], False)
        
        # process
        response = requests.get(url='http://localhost:7777/call_write', params={'key': key, 'value': value})
        response_content = response.json() if response.headers['Content-Type'] == 'application/json' else response.text
        if response.status_code == 200:
            ctx.visited = response_content['visited']
            new_visited = ctx.visited.copy()
            new_visited.append(service_name)
            response_content['visited'] = new_visited
            wrapper.postWrite(ctx, key)
        return jsonify(response_content), response.status_code

    app.run(host='0.0.0.0', port=5555)

"""Cache Manager"""
def run_cm_callee():
    print("Starting cache manager for callee...")
    cm = CacheManager("callee", "caller_read")
    cm.process()

def run_cm_caller_read():
    print("Starting cache manager for caller_read...")
    cm = CacheManager("caller_read", "frontend")
    cm.process()

def run_cm_caller_write():
    print("Starting cache manager for caller_write...")
    cm = CacheManager("caller_write", "frontend")
    cm.process()
    
def run_cm_frontend():
    print("Starting cache manager for frontend...")
    cm = CacheManager("frontend", "client")
    cm.process()

"""Main Function"""
def main():
    # Clean up the cache file
    with open("./data/frontend.json", "w") as f:
        json.dump({}, f)
    with open("./data/caller_read.json", "w") as f:
        json.dump({}, f)
    
    # Multi-threaded start-up services
    t1 = threading.Thread(target=run_callee, daemon=True)
    t2 = threading.Thread(target=run_caller_read, daemon=True)
    t3 = threading.Thread(target=run_caller_write, daemon=True)
    t4 = threading.Thread(target=run_frontend, daemon=True)
    t5 = threading.Thread(target=run_cm_callee, daemon=True)
    t6 = threading.Thread(target=run_cm_caller_read, daemon=True)
    t7 = threading.Thread(target=run_cm_caller_write, daemon=True)
    t8 = threading.Thread(target=run_cm_frontend, daemon=True)
    threads = [t1, t2, t3, t4, t5, t6, t7, t8]
    for t in threads:
        t.start()
        time.sleep(1)
        print("\n")
    print("All services have been started successfully!")
    print("You can now interact with the services.")
    
    show_menu()
    
    # Verify the characteristics of linear storage: compare the order of completion of READ and WRITE, and output the data returned by READ.
    # with open("./data/database.json", "w") as f:
    #     json.dump({"school": "pku"}, f)
    # rt = threading.Thread(target=caller_read, args=('school',))
    # wt = threading.Thread(target=caller_write, args=('school', 'hust'))
    # rt.start()
    # wt.start()
    # rt.join()
    # wt.join()
    
# Main function entry
if __name__ == "__main__":
    main()