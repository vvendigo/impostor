#!/usr/bin/python

import BaseHTTPServer
import json
import method

defaultAddr = '127.0.0.1:8000'
defaultConfFile = './setup.json'

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

    import sys, os
    from optparse import OptionParser

    parser = OptionParser(usage="usage: %prog [options] [host][:port] [rootDir]", version=HTTPRequestHandler.server_version)
    parser.add_option("-f", "--config", dest="conf", default=defaultConfFile,
                  help="JSON server config file to use")

    (options, args) = parser.parse_args()

    
    addr = defaultAddr
    rootDir = os.path.dirname(sys.argv[0])
    host = '127.0.0.1'
    port = 8000

    # load server conf
    confData = "{%s}"%open(options.conf, 'r').read()
    conf = json.loads(confData)
    if 'server' in conf:
        if 'host' in conf['server']:
            addr = ''
            host = conf['server']['host']
        if 'port' in conf['server']:
            addr = ''
            port = conf['server']['port']
        if 'rootDir' in conf['server']:
            rootDir = os.path.join(rootDir, conf['server']['rootDir'])

    if len(args) > 2:
        parser.error("Incorrect number of arguments")
    if len(args) > 0: addr = args[0]
    if len(args) > 1: rootDir = os.path.join(rootDir, args[1])

    pos = addr.rfind(':')
    if pos >= 0: 
        hostS = addr[:pos]
        portS = addr[pos+1:]
        if hostS != '': host = hostS
        if portS != '': port = int(portS)
    elif addr != '': # given host only
        host = addr

    print "Running at %s:%d, serving %s/"%(host, port, rootDir)
    httpd = HTTPServer((host, port), HTTPRequestHandler)
    #loadInterfaces(confFile, httpd)
    httpd.serve_forever()

