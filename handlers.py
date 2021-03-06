import os
import time
import httplib
import urlparse
import mimetypes
import importlib
from inspect import getmembers, isfunction
import xmlrpclib

class handler:
    ''' interface '''
    def __init__(self, cfg, rqHandler):
        self.rq = rqHandler
        self.disabled = cfg.get('disable', False)
        self.status = cfg.get('status', None)
        self.statusForced = True
        if self.status == None:
            self.status = 200
            self.statusForced = False
        self.statusMessage = cfg.get('statusMessage', '')
        self.delay = cfg.get('delay', 0)
        self.headers = cfg.get('headers', {})
        self.checkParams = cfg.get('checkParams', None)
        self.dumpRequest = cfg.get('dumpRequest', False)
        self.template = cfg.get('template', None)

    def accepts(self, path):
        return not self.disabled

    def run(self, path):
        if self.dumpRequest:
            client, command, headers, data = self.requestDump()
            self.rq.log_message('--- DUMPING REQUEST FROM '+client+' ---\n'
                + command + '\n'
                + headers + '\n'
                + data)
        if self.delay > 0:
            time.sleep(self.delay)
        if self.checkParams != None:
            up = self.getParamDict()
            if not self.paramCheck(self.checkParams, up):
                self.rq.send_response(400, "Impostor says, Bad request!")
                return
        if self.statusMessage != '':
            self.rq.send_response(self.status, self.statusMessage)
        else:
            self.rq.send_response(self.status)
        for h, v in self.headers.iteritems():
            self.rq.send_header(h, v)

    def getParamDict(self, get=True, post=True):
        up = {}
        if get:
            up = urlparse.parse_qs(urlparse.urlparse(self.rq.path).query)
        if post and self.rq.command == 'POST':
            data = self.rq.getData()
            up.update(urlparse.parse_qs(data))
        return up

    def paramCheck(self, conf, params):
        if type(conf) != dict:
            return True
        for k, d in conf.iteritems():
            settings = set([v.strip() for v in d.lower().split(',')])
            if not k in params:
                if 'required' in settings:
                    return False
                continue
            val = params[k][0]
            if 'int' in settings:
                try: int(val)
                except: return False
            if 'float' in settings:
                try: float(val)
                except: return False
        return True

    def requestDump(self):
        client = self.rq.client_address[0]+':'+str(self.rq.client_address[1])
        command = self.rq.command+' '+self.rq.path+' '+self.rq.request_version
        headers = ''
        for ln in self.rq.headers.headers:
            headers += ln
        length = int(self.rq.headers.getheader('Content-Length', 0))
        data = self.rq.getData()
        return client, command, headers, data

    def templateData(self, src):
        if self.template == None:
            return src
        args = self.template
        args.update(self.getParamDict())
        tArgs = {}
        for k, v in args.items():
            if type(v)==list:
                tArgs[k] = v[0]
            else:
                tArgs[k] = v
        try:
            return src % tArgs
        except KeyError as e:
            self.rq.log_error("Unable to template '%s': KeyError %s"%(fpath, str(e)))
        except ValueError as e:
            self.rq.log_error("Unable to template '%s': ValueError %s"%(fpath, str(e)))
        return src

    def getFile(self, fpath, template=True):
        try:
            src = open(fpath, 'r').read()
            if template:
                return self.templateData(src)
            return src
        except IOError as e:
            self.rq.log_error(str(e))
            if not self.statusForced:
                self.status = 404
                self.statusMesssage = 'Not found'
        return ''

#endclass


class serveDir(handler):
    ''' directory serving handler '''
    def __init__(self, cfg, rq):
        handler.__init__(self, cfg, rq)
        self.dropParams = cfg.get('dropParams', False)

    def run(self, path):
        if self.dropParams:
            parts = urlparse.urlparse(self.rq.path)
            path = self.rq.server.rootDir + '/' + parts.path
        else:
            path = self.rq.server.rootDir + '/' + self.rq.path
        data = self.getFile(path)
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = mimetypes.guess_type(path)[0]
        handler.run(self, path)
        self.rq.end_headers()
        self.rq.write(data)
#endclass

class serveFile(handler):
    ''' one file serving handler '''
    def __init__(self, cfg, rq):
        handler.__init__(self, cfg, rq)
        self.serveFile = cfg.get('serve', '')

    def run(self, path):
        path = self.rq.server.rootDir + '/' + path
        data = self.getFile(os.path.join(path, self.serveFile))
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = mimetypes.guess_type(self.serveFile)[0]
        handler.run(self, path)
        self.rq.end_headers()
        self.rq.write(data)
#endclass

class serveString(handler):
    ''' data serving handler '''
    def __init__(self, cfg, rq):
        handler.__init__(self, cfg, rq)
        self.serve = cfg.get('serve', '')

    def run(self, path):
        handler.run(self, path)
        self.rq.end_headers()
        self.rq.write(self.templateData(self.serve))
#endclass

class headers(handler):
    ''' headers only handler '''
    def run(self, path):
        handler.run(self, path)
        self.rq.end_headers()
#endclass

class proxy(handler):
    ''' proxy requests '''
    def __init__(self, cfg, rq):
        handler.__init__(self, cfg, rq)
        self.status = cfg.get('status', 0)
        self.serve = cfg.get('URL', '')

    def run(self, path):
        body = self.rq.getData()
        rqheaders = {}
        url = urlparse.urlparse(self.serve)
        for ln in self.rq.headers.headers:
            h,v = ln.split(':', 1)
            if h=="Host":
                v = url.netloc
            rqheaders[h] = v.strip()
            #rq.log_message(h+": "+v.strip())
        #rq.log_message(url.netloc+" "+url.path)

        conn = httplib.HTTPConnection(url.netloc)
        conn.request(self.rq.command, url.path, body, rqheaders)
        res = conn.getresponse()

        if self.status == 0:
            self.status = res.status
        if self.statusMessage == '':
            self.statusMessage = res.reason
        for h, v in res.getheaders():
            if h not in self.headers:
                self.headers[h] = v
        handler.run(self, path)
        self.rq.end_headers()
        self.rq.write(res.read())
        conn.close()
#endclass

class dump(handler):
    def run(self, path):
        client, command, headers, data = self.requestDump()

        self.headers = {'Content-Type': 'text/html'}
        self.status = 200
        self.statusMessage = 'Dump - forced OK'
        handler.run(self, path)
        self.rq.end_headers()

        self.rq.write('<html><head><title>Dump request from '+client+'</title><style>pre{background-color:f0f0ff}</style></head><body>')
        self.rq.write('<h1>'+command+'</h1>\n')
        self.rq.write('<h2>Headers</h2>\n')
        self.rq.write('<pre>\n'+headers+'</pre>\n')
       
        self.rq.write('<h2>Data</h2>\n')
        self.rq.write('<pre>\n')
        self.rq.write(data)
        self.rq.write('</pre>\n')
        self.rq.write('</body></html>')
#endclass

class xmlRpc(handler):
    ''' handling XML-RPC requests '''
    def __init__(self, cfg, rq):
        handler.__init__(self, cfg, rq)
        self.xmlrpclib = xmlrpclib # set xmlrpc lib
        self.dumpsParams = cfg.get('dumpsParams', {})
        self.methods = cfg.get('methods', {})
        # load methods from module
        mName = cfg.get('module')
        if mName != None:
            try:
                module = importlib.import_module(mName)
            except ImportError as e:
                self.rq.log_error("Unable to import XMLRPC functions: "+str(e))
                return
            for n, f in getmembers(module, isfunction):
                if n not in self.methods:
                    self.methods[n] = {'function':f}

    def accepts(self, path):
        data = self.rq.getData()
        params, methodname = self.xmlrpclib.loads(data)
        return handler.accepts(self, path) and methodname in self.methods

    def run(self, path):
        data = self.rq.getData()
        params, methodname = self.xmlrpclib.loads(data)
        self.rq.log_message('RPC call: '+methodname)
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
            data = self.getFile(os.path.join(path, cfg['serve']))
        elif 'function' in cfg:
            self.dumpsParams['params'] = (cfg['function'](params),)
            self.dumpsParams['methodresponse'] = True
            data = self.xmlrpclib.dumps(**(self.dumpsParams))
        else:
            data = self.getFile(path+'/'+methodname+'.xmlrpc', 'r')

        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = 'text/xml'
        self.headers['Content-Length'] = len(data)
        handler.run(self, path)
        self.rq.end_headers()
        self.rq.write(data)

    def checkMethodParams(self, cfg, params):
        for i, t in enumerate(cfg):
            tp = set([p.strip() for p in t.split(',')])
            if i >= len(params):
                if not 'optional' in tp:
                    return False
                continue
            #self.rq.log_message(str(type(params[i])))
            if "int" in tp and type(params[i]) != int:
                return False
            elif "float" in tp and type(params[i]) != float:
                return False
            elif "bool" in tp and type(params[i]) != bool:
                return False
            elif "string" in tp and type(params[i]) != str:
                return False
            elif "array" in tp and type(params[i]) != list:
                return False
            elif "dict" in tp and type(params[i]) != dict:
                return False
        return True
#endclass

