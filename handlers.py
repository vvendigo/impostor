import os
import time
import httplib
import urlparse

# handlers:

class handler:
    ''' interface '''
    def __init__(self, cfg, rqHandler):
        self.rq = rqHandler
        self.disabled = cfg.get('disable', False)
        self.status = cfg.get('status', 200)
        self.statusMessage = cfg.get('statusMessage', '')
        self.delay = cfg.get('delay', 0)
        self.headers = cfg.get('headers', {})
        self.checkParams = cfg.get('checkParams', None)

    def accepts(self, path):
        return not self.disabled

    def run(self, path):
        if self.delay > 0:
            time.sleep(self.delay)
        if self.checkParams != None:
            up = urlparse.parse_qs(urlparse.urlparse(self.rq.path).query)
            if not self.paramCheck(self.checkParams, up):
                self.rq.send_response(400, "Impostor says, Bad request!")
                return
        if self.statusMessage != '':
            self.rq.send_response(self.status, self.statusMessage)
        else:
            self.rq.send_response(self.status)
        for h, v in self.headers.iteritems():
            self.rq.send_header(h, v)

    def paramCheck(self, conf, params):
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
#eddef



#endclass


class serveDir(handler):
    ''' directory serving handler '''
    def __init__(self, cfg, rq):
        handler.__init__(self, cfg, rq)
        self.dropParams = cfg.get('dropParams', False)

    def run(self, path):
        handler.run(self, path)
        self.rq.end_headers()
        if self.dropParams:
            path = urlparse.urlparse(path).path
        self.rq.write(open(path, 'r').read())
#endclass

class serveFile(handler):
    ''' one file serving handler '''
    def __init__(self, cfg, rq):
        handler.__init__(self, cfg, rq)
        self.serveFile = cfg.get('serve', '')

    def run(self, path):
        handler.run(self, path)
        self.rq.end_headers()
        self.rq.write(open(os.path.join(path, self.serveFile)).read())
#endclass

class serveString(handler):
    ''' data serving handler '''
    def __init__(self, cfg, rq):
        handler.__init__(self, cfg, rq)
        self.serve = cfg.get('serve', '')
        
    def run(self, path):
        handler.run(self, path)
        self.rq.end_headers()
        self.rq.write(self.serve)
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
        body = None
        bodyLen = int(self.rq.headers.getheader('content-length', 0))
        if bodyLen:
            body = rqHandler.rfile.read(bodyLen)
        rqheaders = {}
        url = urlparse.urlparse(self.serve)
        for ln in rq.headers.headers:
            h,v = ln.split(':', 1)
            if h=="Host":
                v = url.netloc
            rqheaders[h] = v.strip()
            #rq.log_message(h+": "+v.strip())
        #rq.log_message(url.netloc+" "+url.path)

        conn = httplib.HTTPConnection(url.netloc)
        conn.request(self.rq.command, url.path, body, rqheaders)
        
        #rq.path
        #rq.request_version

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


'''
class returnPost(handler):
    def run(self, rqHandler):
        length = int(rqHandler.headers.getheader('content-length'))
        data = rqHandler.rfile.read(length)
        handler.run(self, path, rqHandler)
        TODO: rqHandler.send_header_if_not_set('Content-Type', 'text/html')
        rqHandler.end_headers()
        rqHandler.write('<html><body><h1>Post!</h1>postdata:<br>'+data+'</body></html>')
#endclass
'''

