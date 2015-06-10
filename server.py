#!/usr/bin/python

import BaseHTTPServer
import json
import handlers
import os
import importlib

defaultAddr = '127.0.0.1:8000'
defaultConfFile = './setup.json'

def delComments(t):
    ignore = False
    qCnt = 0
    bsCnt = 0
    sCnt = 0
    out = ''
    for ch in t:
        if ignore:
            if ch == '\n':
                out += ch
                ignore = False
        else:
            if ch == '"' and bsCnt%2==0:
                qCnt += 1
                sCnt = 0
                bsCnt = 0
            elif ch == '/':
                bsCnt = 0
                if sCnt > 0 and qCnt%2==0:
                    out = out[:-sCnt]
                    ignore = True
                    sCnt = 0
                    bsCnt = 0
                    continue
                sCnt += 1
            elif ch == '\\':
                bsCnt += 1
                sCnt = 0
            elif ch == '\n':
                bsCnt = 0
                sCnt = 0
            else:
                bsCnt = 0
                sCnt = 0
            out += ch
    return out
#enddef


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
        pos = len(self.path)
        while pos >= 0:
            path = self.path[:pos]
            handler = self.getHandler(path)
            if handler != None:
                break
            pos = self.path.rfind('/', 0, pos-1)
        #endwhile
        if handler == None:
            self.send_error(501, "Not Implemented by Imposter")
            return
        # call the handler
        handler.run(path)

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

        if self.server.verbose: self.log_message('Searching '+path);
        if not os.path.exists(path):
            if self.server.verbose: self.log_message(path+' not found')
            return None
        confPath = os.path.join(path, 'setup.json')
        conf = {}
        if not os.path.exists(confPath):
            if self.server.verbose: self.log_message(confPath+' not found')
            return None
        confData = "{%s}"%delComments(open(confPath, 'r').read())
        try:
            conf = json.loads(confData)
        except ValueError as e:
            self.log_error('Unable to parse '+confPath+': '+str(e))
            return None
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
            if self.server.verbose: self.log_error('no "'+method+'" in '+confPath)
            return None
        if 'handler' not in methodConf:
            if self.server.verbose: self.log_error('no handler for "'+method+'" set in '+confPath)
            return None
        # create handler
        handlerName = methodConf['handler']
        # if handler name contains '.', use given module
        p = handlerName.find('.')
        if p < 1:
            handlerClass = getattr(handlers, handlerName)
        else:
            module = importlib.import_module(handlerName[:p])
            handlerClass = getattr(module, handlerName[p+1:])
        handler = handlerClass(methodConf, self)
        # check acceptance
        if handler.accepts(self.server.rootDir +'/'+ self.path):
            return handler
        return None
    #enddef

#endclass


class HTTPServer(BaseHTTPServer.HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, rootDir, verbose=False):
        self.rootDir = rootDir
        self.verbose = verbose
        BaseHTTPServer.HTTPServer.__init__(self, server_address, RequestHandlerClass)
#endclass



if __name__ == "__main__":

    import sys
    from optparse import OptionParser

    parser = OptionParser(usage="usage: %prog [options] [host][:port] [rootDir]", version=HTTPRequestHandler.server_version)
    parser.add_option("-f", "--config", dest="conf", default=defaultConfFile,
                  help="JSON server config file to use")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                  help="Log a lot")

    (options, args) = parser.parse_args()

    addr = defaultAddr
    rootDir = os.path.dirname(sys.argv[0])
    host = '127.0.0.1'
    port = 8000

    # load server conf
    confData = "{%s}"%delComments(open(options.conf, 'r').read())
    conf = json.loads(confData)
    scfg = conf.get('server', {})
    if 'host' in scfg:
        addr = ''
        host = scfg['host']
    if 'port' in scfg:
        addr = ''
        port = scfg['port']
    if 'rootDir' in scfg:
        rootDir = os.path.join(rootDir, scfg['rootDir'])
    if not options.verbose:
        verbose = scfg.get("verbose", False)
    else:
        verbose = options.verbose

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
    httpd = HTTPServer((host, port), HTTPRequestHandler, rootDir, verbose)
    httpd.serve_forever()

#endmain
