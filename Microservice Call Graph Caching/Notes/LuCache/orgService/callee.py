from utility import CalleeHTTPRequestHandler
from http.server import HTTPServer

def run_callee(port=8888):
    server_address = ('', port)
    httpd = HTTPServer(server_address, CalleeHTTPRequestHandler)
    print(f"Starting callee on port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_callee()