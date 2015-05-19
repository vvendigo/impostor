#!/usr/bin/python

import BaseHTTPServer
import ConfigParser
import method

server_address = ('127.0.0.1', 8000)
confFile = './setup.conf'

class HTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    server_version = "Impostor/1.0"

    def write(self, data):
        return self.wfile.write(data)

    def do_HEAD(self):
        self.send_response(200, "HEAD")

    def do_GET(self):
        iface = self.server.getInterface(self.path)
        if iface == None:
            self.send_error(501, "Not Implemented by Imposter")
            return
        iface.run(self)

    def do_POST(self):
        iface = self.server.getInterface(self.path)
        if iface == None:
            self.send_error(501, "Not Implemented by Imposter")
            return
        iface.run(self)

#endclass


class HTTPServer(BaseHTTPServer.HTTPServer):
    def __init__(self, server_address, RequestHandlerClass):
        BaseHTTPServer.HTTPServer.__init__(self, server_address, RequestHandlerClass)
        self.interfaces = []

    def addInterface(self, iface):
        self.interfaces.append(iface)

    def getInterface(self, path):
        for i in self.interfaces:
            if i.accepts(path):
                return i
        return None
#endclass


def loadInterfaces(confFile, httpd):
    cfg = ConfigParser.ConfigParser()
    cfg.read(confFile)
    for section in cfg.sections():
        meth = cfg.get(section, 'method')
        httpd.addInterface(eval('method.'+meth+'(cfg,"'+section+'")'))
#enddef


if __name__ == "__main__":
    print "Running at %s:%d"%server_address
    httpd = HTTPServer(server_address, HTTPRequestHandler)
    loadInterfaces(confFile, httpd)
    httpd.serve_forever()

