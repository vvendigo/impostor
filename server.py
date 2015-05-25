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
        handler.run(self.server.rootDir +'/'+ self.path, self)

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

    def getHandler(self, pathToTry):
        method = self.command
        path = self.server.rootDir + pathToTry

        self.log_message('Trying '+path);
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
        for m in conf.keys():
            if m.startswith(method+' '):
                self.log_message("'%s' '%s'"%(self.path[len(pathToTry)+1:], m[m.find(' ')+1:]))
                if self.path[len(pathToTry)+1:].startswith(m[m.find(' ')+1:]):
                    method = m
                    break
        if method not in conf:
            self.log_error('no "'+method+'" in '+confPath)
            return None
        if 'handler' not in conf[method]:
            self.log_error('no handler for "'+method+'" set in '+confPath)
            return None
        handlerClass = getattr(handlers, conf[method]['handler'])
        handler = handlerClass(conf[method])
        if handler.disabled:
            return None
        return handler
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
