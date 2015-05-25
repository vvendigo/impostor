import os
import time

# handlers:

class handler:
    ''' interface '''
    def __init__(self, cfg):
        self.disabled = cfg.get('disable', 0)
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
        for h, v in self.headers:
            rqHandler.send_header(h, v)
#endclass


class serveDir(handler):
    ''' directory serving handler '''
    def run(self, path, rqHandler):
        handler.run(self, path, rqHandler)
        rqHandler.end_headers()
        rqHandler.write(open(path, 'r').read())
#endclass

class serveFile(handler):
    ''' one file serving handler '''
    def __init__(self, cfg):
        handler.__init__(self, cfg)
        self.serveFile = cfg.get('serve', '')

    def run(self, path, rqHandler):
        handler.run(self, path, rqHandler)
        rqHandler.end_headers()
        rqHandler.write(open(os.path.join(path, self.serveFile)).read())
#endclass

class serveString(handler):
    ''' one file serving handler '''
    def __init__(self, cfg):
        handler.__init__(self, cfg)
        self.serve = cfg.get('serve', '')
        
    def run(self, path, rqHandler):
        handler.run(self, path, rqHandler)
        rqHandler.end_headers()
        rqHandler.write(self.serve)
#endclass



class headers(handler):
    ''' headers only handler '''
    def run(self, path, rqHandler):
        handler.run(self, path, rqHandler)
        rqHandler.end_headers()
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

