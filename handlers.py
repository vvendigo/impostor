import sys, os
import json
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


class serveFiles(handler):
    ''' file serving handler '''
    def __init__(self, cfg):
        handler.__init__(self, cfg)
        self.serveFile = cfg.get('serveFile', '')

    def run(self, path, rqHandler):
        handler.run(self, path, rqHandler)
        rqHandler.end_headers()
        if self.serveFile != '':
            rqHandler.write(open(os.path.join(path, self.serveFile)).read())
        else:
            rqHandler.write(open(path, 'r').read())
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


def getHandler(path, method, rq):
    if not os.path.exists(path):
        rq.log_message(path+' not found')
        return None
    confPath = path+'/'+'setup.json'
    conf = {}
    if not os.path.exists(confPath):
        rq.log_message(confPath+' not found')
        return None
    else:
        confData = "{%s}"%open(confPath, 'r').read()
        try:
            conf = json.loads(confData)
        except:
            rq.log_error('Unable to parse '+confPath)
            raise
    if method not in conf:
        rq.log_error('no "'+method+'" in '+confPath)
        return None
    if 'handler' not in conf[method]:
        rq.log_error('no handler for "'+method+'" set in '+confPath)
        return None
    handlerClass = getattr(sys.modules[__name__], conf[method]['handler'])
    return handlerClass(conf[method])
#enddef



