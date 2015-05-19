import ConfigParser

class method: # iface
    def __init__(self, cfg, section):
        self.path = cfg.get(section,'path')
    def accepts(self, path):
        return path.startswith(self.path)
    def run(self, rqHandler):
        rqHandler.send_response(200, "OK")
#endclass

class get(method):
    def __init__(self, cfg, section):
        method.__init__(self, cfg, section)
        self.contentType = ''
        try: self.contentType = cfg.get(section,'contentType')
        except: pass
        self.servePath = ''
        try: self.servePath = cfg.get(section,'servePath')
        except: pass
        self.status = 200
        try: self.status = cfg.getint(section,'status');
        except: pass
    def run(self, rqHandler):
        rqHandler.send_response(self.status)
        if self.contentType != '':
            rqHandler.send_header('Content-Type', self.contentType)
        rqHandler.end_headers()
        if self.servePath != '':
            rqHandler.write(open(self.servePath+rqHandler.path[len(self.path):],'r').read())
#endclass

class post(method):
    def run(self, rqHandler):
        length = int(rqHandler.headers.getheader('content-length'))
        data = rqHandler.rfile.read(length)
        rqHandler.send_response(200, "OK")
        rqHandler.send_header('Content-Type', 'text/html')
        rqHandler.end_headers()
        rqHandler.write('<html><body><h1>Post!</h1>postdata:<br>'+data+'</body></html>')
#endclass 
