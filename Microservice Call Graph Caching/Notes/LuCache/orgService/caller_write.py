from utility import Caller_write_HTTPRequestHandler
from http.server import HTTPServer

def run_caller_write(port=7777):
    server_address = ('', port)
    httpd = HTTPServer(server_address, Caller_write_HTTPRequestHandler)
    print(f"Starting caller_write on port {port}")
    httpd.serve_forever()
    
if __name__ == "__main__":
    run_caller_write()