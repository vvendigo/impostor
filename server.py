#!/usr/bin/python

import BaseHTTPServer
import json
import handlers
import os

defaultAddr = '127.0.0.1:8000'
defaultConfFile = './setup.json'

class HTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    server_version = "Impostor/1.0"

    def write(self, data):
        return self.wfile.write(data)

    def do(self, method):
        # iterate path, get deepest usable handler
        pos = 0
        handler = None
        while pos >= 0:
            path = self.server.rootDir +'/'+ self.path[:pos]
            h = handlers.getHandler(path, method, self)
            if h != None:
                handler = h
            pos = self.path.find('/', pos+1)
        #endwhile
        if handler == None:
            self.send_error(501, "Not Implemented by Imposter")
            return
        # call the handler
        handler.run(self.server.rootDir +'/'+ self.path, self)

    def do_HEAD(self):
        self.do('head')

    def do_GET(self):
        self.do('get')

    def do_POST(self):
        self.do('post')

    def do_PUT(self):
        self.do('put')

    def do_DELETE(self):
        self.do('delete')
#endclass


class HTTPServer(BaseHTTPServer.HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, rootDir):
        self.rootDir = rootDir
        BaseHTTPServer.HTTPServer.__init__(self, server_address, RequestHandlerClass)
#endclass



if __name__ == "__main__":

    import sys
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

    print "Running at %s:%d, serving %s/,"%(host, port, rootDir),
    print "Ctrl+C to stop"
    httpd = HTTPServer((host, port), HTTPRequestHandler, rootDir)
    httpd.serve_forever()

