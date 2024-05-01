from utility import Caller_read_HTTPRequestHandler
from http.server import HTTPServer

def run_caller_read(port=6666):
    server_address = ('', port)
    httpd = HTTPServer(server_address, Caller_read_HTTPRequestHandler)
    print(f"Starting caller_read on port {port}")
    httpd.serve_forever()
    
if __name__ == "__main__":
    run_caller_read()