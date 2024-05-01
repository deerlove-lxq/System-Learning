import requests
import json
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler

# frontend handler
class Frontend_HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        key = parse_qs(urlparse(self.path).query).get('key', [None])[0]
        
        if path.startswith('/read_from_caller'):
            response = self.read_from_caller('http://localhost:6666/caller_read', key)
            self.send_response(response.status_code)
            self.end_headers()
            self.wfile.write(response.content)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Get: frontend method Not found")
            
    def do_POST(self):
        path = self.path
        length = int(self.headers.get('content-length'))
        data = json.loads(self.rfile.read(length))
        
        if path == '/write_to_caller':
            response = self.write_to_caller('http://localhost:7777/caller_write', data)
            self.send_response(response.status_code)
            self.end_headers()
            self.wfile.write(response.content)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Post: frontend method Not found")
            
    def read_from_caller(self, service_url, key):
        # 发送GET请求到指定的服务
        response = requests.get(url=service_url, params={'key': key})
        return response
    
    def write_to_caller(self, service_url, data):
        # 发送POST请求到指定的服务
        response = requests.post(url=service_url, json=data)
        return response

# caller_read handler
class Caller_read_HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        key = parse_qs(urlparse(self.path).query).get('key', [None])[0]

        if path.startswith('/caller_read'):
            response = self.caller_read('http://localhost:8888/read', key)
            self.send_response(response.status_code)
            self.end_headers()
            self.wfile.write(response.content)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Get: caller_read method Not found")

    def caller_read(self, service_url, key):
        # 发送GET请求到指定的服务
        response = requests.get(url=service_url, params={'key': key})
        return response

class Caller_write_HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        path = self.path
        length = int(self.headers.get('content-length'))
        data = json.loads(self.rfile.read(length))
        
        if path == '/caller_write':
            response = self.caller_write('http://localhost:8888/write', data)
            self.send_response(response.status_code)
            self.end_headers()
            self.wfile.write(response.content)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Post: caller_write method Not found")

    def caller_write(self, service_url, data):
        # 发送POST请求到指定的服务
        response = requests.post(url=service_url, json=data)
        return response
    
# Callee handler
class CalleeHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        path = self.path
        length = int(self.headers.get('content-length'))
        data = json.loads(self.rfile.read(length))

        if path == '/write':
            print(f"\nWrite request with data: {data}")
            with open("./data/database.json", "w") as f:
                json.dump(data, f)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Write successful")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Post: callee method Not found")

    def do_GET(self):
        path = self.path
        key = parse_qs(urlparse(self.path).query).get('key', [None])[0]

        if path.startswith('/read'):
            print(f"\nRead request for key: {key}")
            with open("./data/database.json", "r") as f:
                db = json.load(f)
            value = db.get(key)
            if value:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(value).encode())
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps("Key not in database").encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Get: callee method Not found")
            
# Cache
# wrapper
# Cache manager