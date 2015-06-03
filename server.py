#!/usr/bin/python

import BaseHTTPServer
import json
import handlers
import os

defaultAddr = '127.0.0.1:8000'
defaultConfFile = './setup.json'

class HTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    server_version = "Impostor/1.0"

    def __init__(self, request, client_address, server):
        self.data = None
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def write(self, data):
        return self.wfile.write(data)

    def getData(self):
        if self.data == None:
            length = int(self.headers.getheader('Content-Length', 0))
            if length:
                self.data = self.rfile.read(length)
            else:
                self.data = ''
        return self.data

    def handler(self):
        # iterate path, get deepest usable handler
        pos = 0
        handler = None
        while pos >= 0:
            path = self.path[:pos]
            h = self.getHandler(path)
            if h != None:
                handler = h
            pos = self.path.find('/', pos+1)
        #endwhile
        if handler == None:
            self.send_error(501, "Not Implemented by Imposter")
            return
        # call the handler
        handler.run(self.server.rootDir +'/'+ self.path)

    def do_HEAD(self):
        self.handler()

    def do_GET(self):
        self.handler()

    def do_POST(self):
        self.handler()

    def do_PUT(self):
        self.handler()

    def do_DELETE(self):
        self.handler()

    def do_OPTIONS(self):
        self.handler()

    def do_TRACE(self):
        self.handler()

    def do_CONNECT(self):
        self.handler()

    def getHandler(self, pathToTry):
        method = self.command
        path = self.server.rootDir + pathToTry

        #self.log_message('Trying '+path);
        if not os.path.exists(path):
            self.log_message(path+' not found')
            return None
        confPath = path+'/'+'setup.json'
        conf = {}
        if not os.path.exists(confPath):
            self.log_message(confPath+' not found')
            return None
        confData = "{%s}"%open(confPath, 'r').read()
        try:
            conf = json.loads(confData)
        except:
            self.log_error('Unable to parse '+confPath)
            raise
        methodConf = None
        for m, mconf in conf.iteritems():
            parts = [p.strip() for p in m.split('|')]
            for mp in parts:
                if mp.startswith(method+' '):
                    if self.path[len(pathToTry)+1:].startswith(mp[mp.find(' ')+1:]):
                        methodConf = mconf
                        method = mp
                        break
                elif mp == method:
                    methodConf = mconf
                    break
        if methodConf == None:
            self.log_error('no "'+method+'" in '+confPath)
            return None
        if 'handler' not in methodConf:
            self.log_error('no handler for "'+method+'" set in '+confPath)
            return None
        # create handler
        handlerClass = getattr(handlers, methodConf['handler'])
        handler = handlerClass(methodConf, self)
        # check acceptance
        if handler.accepts(self.server.rootDir +'/'+ self.path):
            return handler
        return None
    #enddef

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

#endmain
