from utility import Frontend_HTTPRequestHandler
from http.server import HTTPServer

def run_frontend(port=5555):
    server_address = ('', port)
    httpd = HTTPServer(server_address, Frontend_HTTPRequestHandler)
    print(f"Starting frontend on port {port}")
    httpd.serve_forever()
    
if __name__ == "__main__":
    run_frontend()