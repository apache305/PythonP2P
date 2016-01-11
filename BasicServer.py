import SocketServer,time
import threading

# SimpleServer extends the TCPServer, using the threading mix in
# to create a new thread for every request.
class RawServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):

    # This means the main server will not do the equivalent of a
    # pthread_join() on the new threads. With this set, Ctrl-C will
    # kill the server reliably.
    daemon_threads = True#if the main process terminate,the threading continue working

    # By setting this we allow the server to re-bind to the address by
    # setting SO_REUSEADDR, meaning you don't have to wait for
    # timeouts when you kill the server and the sockets don't get
    # closed down correctly.
    allow_reuse_address = False

    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass,bind_and_activate=False)
        self.threadList=[]#indicate the working threads
        self.server_bind()
        
    def startServer(self):#before this,the server do not start to listen for request
        time.sleep(1)
        self.server_activate()
        print 'Server start at:',time.ctime()
        self.serve_forever()  
        
    
    def shutdownServer(self):#
        self.shutdown()
        print 'Server close at:',time.ctime()
      
    def process_request(self,request,client_address):
        t = threading.Thread(target = self.process_request_thread,args = (request, client_address))
        if self.daemon_threads:
            t.setDaemon (1)
        t.start()
        
        self.threadList.append(t)
        
    def close_request(self,request):
        #self.threadList.#the threads auto finallize?
        request.close()
  
        
    def pollThreading(self):#for test
        while 1:
            ls=raw_input('')
            if ls=='ls':
                for each in self.threadList:
                    print each.isAlive()
    def poll(self):
        t=threading.Thread(target=self.pollThreading)
        t.setDaemon(1)
        t.start()
        
    

# The RequestHandler handles an incoming request. We have extended in
# the SimpleServer class to have a 'processor' argument which we can
# access via the passed in server argument, but we could have stuffed
# all the processing in here too.
class RawRequestHandler(SocketServer.BaseRequestHandler):

    def __init__(self, request, client_address, server):
        #print request.getpeername(), '--Connected--'
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
    def setup(self):
        pass   
    def handle(self):
        """ override here"""
        print 'you need override'
        #data=self.request.recv(4096)
        #print data
                 
    def finish(self):
        #print self.client_address, '--Disconnected--'
        pass

def __runSimpleServer(port = 57000):#only for test
    # Start up a server on localhost, port 7000; each time a new
    # request comes in it will be handled by a SimpleRequestHandler
    # class; we pass in a SimpleCommandProcessor class that will be
    # able to be accessed in request handlers via server.processor;
    # and a hello message.
    server = RawServer(('', port), RawRequestHandler)

    try:
        server.startServer()
    except KeyboardInterrupt:
        raise
    
    
    
#def simple_parse(self, str):
#   args = str.split(' ')
#   command = args[0].lower()
#   args = args[1:]
#   return command, args


if __name__ == '__main__':
    try:
        __runSimpleServer()
    except Exception,e:
        print e
        raw_input('..fail..')