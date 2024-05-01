class Context:
    def __init__(self, call_id: str, service_name: str, ca: str, visited: list, read_only: bool):
        self.call_id = call_id 
        self.service_name = service_name
        self.ca = ca
        self.visited = visited
        self.read_only = read_only

class Dep:
    def __init__(self, dataType: str, data: str):
        self.dataType = dataType    # [key | ca]
        self.data = data
        
class Request:
    def __init__(self, call_id, dataType: str, data: str):
        self.call_id = call_id
        self.dataType = dataType    # [start | end | saveCalls | invalidateKey | invalidateCalls]
        self.data = data
        
class HistoryItem:
    def __init__(self, dataType: str, data: str):
        self.dataType = dataType    # [call | inv_key | inv_ca]
        self.data = data
        
class State:
    def __init__(self):
        self.history = []   # list(Call(CallArgs) | Inv(Key) | Inv(CallArgs)): Contains a sequence of started calls and key writes
        self.keyDeps = {}   # map(Key, map(Service, CA))
        self.callDeps = {}  # map(CallArgs, map(Service, CA))
    
    def storeDeps(self, ca: str, service_name: str, rs: set):
        for item in rs:
            if item.dataType == 'key':
                key = item.data
                if key not in self.keyDeps:
                    self.keyDeps[key] = {}
                self.keyDeps[key][service_name] = ca
            elif item.dataType == 'call':
                callArgs = item.data
                if callArgs not in self.callDeps:
                    self.callDeps[callArgs] = {}
                self.callDeps[callArgs][service_name] = ca