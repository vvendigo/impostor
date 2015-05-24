import os
import time

class method: # iface
    def __init__(self, cfg):
        self.status = cfg.get('status', 200)
        self.statusMessage = cfg.get('statusMessage', '')
        self.delay = cfg.get('delay', 0)
        self.headers = []
        for k, v in cfg.iteritems():
            if k.startswith('header:'):
                self.headers.append((k[7:], v))

    def run(self, path, rqHandler):
        if self.delay > 0:
            time.sleep(self.delay)
        if self.statusMessage != '':
            rqHandler.send_response(self.status, self.statusMessage)
        else:
            rqHandler.send_response(self.status)
        for n, v in self.headers():
            rqHandler.send_header(n, v)
#endclass


class serveFiles(method):
    def __init__(self, cfg, section):
        method.__init__(self, cfg, section)
        self.serveFile = cfg.get('serveFile', '')

    def run(self, path, rqHandler):
        method.run(self, path, rqHandler)
        rqHandler.end_headers()
        if self.serveFile != '':
            rqHandler.write(open(os.path.join(path, self.serveFile)).read())
        else:
            rqHandler.write(open(os.path.join(path, rqHandler.path[len(path):]),'r').read())
#endclass

'''
class post(method):
    def run(self, rqHandler):
        length = int(rqHandler.headers.getheader('content-length'))
        data = rqHandler.rfile.read(length)
        rqHandler.send_response(200, "OK")
        rqHandler.send_header('Content-Type', 'text/html')
        rqHandler.end_headers()
        rqHandler.write('<html><body><h1>Post!</h1>postdata:<br>'+data+'</body></html>')
#endclass 
'''
