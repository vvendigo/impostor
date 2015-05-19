#!/usr/bin/python

import BaseHTTPServer

server_address = ('127.0.0.1', 8000)

class HTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200, "HEAD")

    def do_GET(self):
        #self.send_header("status", 200)
        #self.end_headers()
        self.send_response(200, "OK")
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        #self.wfile.write('\n')
        self.wfile.write('<html><body><h1>It works!</h1>Path:'+self.path+'</body></html>')

    def do_POST(self):
        self.send_response(200, "POST")
        self.wfile.write('\n')

#endclass


if __name__ == "__main__":
    print "Running at %s:%d"%server_address
    httpd = BaseHTTPServer.HTTPServer(server_address, HTTPRequestHandler)
    httpd.serve_forever()

