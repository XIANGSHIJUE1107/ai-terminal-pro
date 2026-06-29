import http.server
import socket
import os
import sys

os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['NO_PROXY'] = '*'

PORT = 8080

with open('server_log.txt', 'w') as f:
    f.write('Starting server test...\n')
    f.flush()
    
    try:
        server = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), http.server.SimpleHTTPRequestHandler)
        server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        f.write(f'Server bound to port {PORT}\n')
        f.flush()
        f.write('Calling serve_forever()...\n')
        f.flush()
        server.serve_forever()
    except Exception as e:
        f.write(f'Error: {e}\n')
        f.flush()