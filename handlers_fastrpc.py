import handlers
import fastrpc
import os

class fastRpc(handlers.xmlRpc):
    ''' handling fastRPC requests '''
    def __init__(self, cfg, rq):
        handlers.xmlRpc.__init__(self, cfg, rq)
        if 'useBinary' not in self.dumpsParams:
            self.dumpsParams['useBinary'] = True
        self.xmlrpclib = fastrpc

    def run(self, path):
        data = self.rq.getData()
        params, methodname = self.xmlrpclib.loads(data)
        self.rq.log_message('FastRPC call: '+methodname)
        path = self.rq.server.rootDir + path
        cfg = self.methods[methodname]
        if "checkParams" in cfg and not self.checkMethodParams(cfg["checkParams"], params):
            f = self.xmlrpclib.Fault(400, "wrong arguments")
            self.rq.log_error("wrong arguments");
            self.dumpsParams['params'] = f
            self.dumpsParams['methodresponse'] = True
            data = self.xmlrpclib.dumps(**(self.dumpsParams))
        elif 'fault' in cfg:
            code, msg = cfg['fault']
            f = self.xmlrpclib.Fault(code, msg)
            self.rq.log_error("Fault %d: %s"%(code, msg));
            self.dumpsParams['params'] = f
            self.dumpsParams['methodresponse'] = True
            data = self.xmlrpclib.dumps(**(self.dumpsParams))
        elif 'serve' in cfg:
            data = self.processFile(os.path.join(path, cfg['serve']), cfg.get('verbatim', False))
        elif 'function' in cfg:
            self.dumpsParams['params'] = (cfg['function'](params),)
            self.dumpsParams['methodresponse'] = True
            data = self.xmlrpclib.dumps(**(self.dumpsParams))
        else:
            data = self.processFile(path+'/'+methodname+'.xmlrpc', cfg.get('verbatim', False))

        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = 'application/x-frpc'
        self.headers['Content-Length'] = len(data)
        handlers.handler.run(self, path)
        self.rq.end_headers()
        self.rq.write(data)
        #self.rq.log_message('Data: '+str(data))

    def processFile(self, fname, verbatim):
        data = open(fname, 'r').read()
        if verbatim:
            return data

        params, methodname = self.xmlrpclib.loads(data)
        self.dumpsParams['params'] = (params,)
        self.dumpsParams['methodresponse'] = True
        data = self.xmlrpclib.dumps(**(self.dumpsParams))
        return data
#endclass
