from BasicServer import *
from SyncType import *

class VProcess():
    def __init__(self, uuid):
        self.uuid = uuid
        
# a new VP is registered to either a ST or a Club
class VPContainer():
    def addVP(self):
        pass
    def removeVP(self):
        pass
    
class SwStore(VPContainer):
    def __init__(self, address, count = 0):
        self.address = address
        self.count = count
        
    def addVP(self, count = 1):
        self.count += count
        
    def removeVP(self, count = 1):
        self.count -= count
        
class Club(VPContainer):
    def __init__(self, sw, swStore, count = 0):
        self.sw = sw
        self.swStore =  swStore
        self.count = count
        self.address = self.swStore.address
        
    def addVP(self, count = 1):
        self.count += count
        self.swStore.addVP(count)
        
    def removeVP(self, count = 1):
        self.count -= count
        self.swStore.removeVP(count)

class OvermanServer(SimpleServer):
    def __init__(self, server_address, RequestHandlerClass, processor, message=''):
        SimpleServer.__init__(self, server_address, RequestHandlerClass, message)
        self.softwares = {}
        self.clubs = {}
        self.swStores = {}
    
class OvermanRequestHandler(SimpleRequestHandler):
    def handle(self):
        self.request.send(self.server.message)
        data = self.request.recv(1024)
        cmd, args = self.simple_parse(data)
        print self.client_address, cmd, args
        if cmd == 'vp_login':
            self.reg_VP(args[0])
        elif cmd == 'st_report':
            self.report_ST()
        
    def reg_VP(self, sw):
        # reg VP to ST/Club
        reg_to = 'none'
        if self.server.clubs.has_key(sw):
            reg_to = self.server.clubs[sw].swStore
        else:
            reg_to = 'random me from STs'
        reg_to.addVP()
        
        # TODO: tell VP to reg
        self.request.send('reg to XX')
        self.request.close()
        
        # print log
        print 'new vp:', self.client_address, 'reg to', reg_to.address
    
    def report_ST(self):
        address = self.client_address[1]
        
        # print this ST
        print 'ST report in:', address
        
        if not self.server.swStores.has_key(address):
            swStore = SwStore(address)
            # maybe we need sync here
            self.server.swStores[address] = swStore
            
        # end procedure
        self.request.send('done')
        self.request.close()
        
        # print ST table
        for k,v in self.server.swStores.items():
            print k, v.count
        pass
    
    def CreateClub(self, sw):
        # TODO:
        pass

def __runServer(port = 5227):
    server = OvermanServer(('', port), OvermanRequestHandler, 'overman')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        __runServer()
    else:
        __runServer(int(sys.argv[1]))