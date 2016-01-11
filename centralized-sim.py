import random
import time
import sys
import threading
import Queue

intervals = []

class Server(threading.Thread):
    def __init__(self,capa,vpnum,wqueue,servetime):
        threading.Thread.__init__(self)
        self.capa = capa
        self.vpnum = vpnum
        self.wqueue = wqueue
        self.servetime = servetime
        self.semaphore = threading.BoundedSemaphore(capa)
        # can_stop == True means server can shutdown when queue is empty
        self.can_stop = False
        
        self.results = Queue.Queue()
        
    def run(self):
        while 1:
            # check wating queue and serve
            self.semaphore.acquire()
            if self.wqueue.empty() == False:
                # not empty, get and serve
                cur_client = self.wqueue.get()
                #print 'serving:',cur_client
                real_servetime = self.servetime + random.uniform(-1,1)
                cur_timer = threading.Timer(real_servetime,self.end_serving,(cur_client,))
                cur_timer.start()
            else:
                if self.can_stop == True:
                    #print 'server shutting down...'
                    break
                else:
                    self.semaphore.release()
                    time.sleep(0.001)
        
    def end_serving(self,client):
        end_time = time.time()
        self.semaphore.release()
        dl_time = end_time - client
        # do sth with dl_time
        #print 'time used:',dl_time
        self.results.put(dl_time)
        
    def queue_done(self):
        self.can_stop = True
        
class Generator(threading.Thread):
    def __init__(self,vpnum,server,wqueue):
        threading.Thread.__init__(self)
        self.vpnum = vpnum
        self.server = server
        self.wqueue = wqueue
        
    def run(self):
        global intervals
        
        for i in range(self.vpnum):
            # generate client
            # client has only one attribute: start time
            new_client = time.time()
            
            # put into queue
            self.wqueue.put(new_client)
            #print 'in queue:',new_client
            
            # sleep for an interval
            #interval = random.expovariate(self.lambd)
            interval = float(intervals[i])
            #print interval
            time.sleep(interval)
        
        # done generating clients
        #print 'done generating'
        self.server.queue_done()

def do_sim(vpnum=100,dlslot=10,servetime=1):
    global intervals
    
    wqueue = Queue.Queue()
    server = Server(dlslot,vpnum,wqueue,servetime)
    #server = 1
    generator = Generator(vpnum,server,wqueue)
    server.start()
    generator.start()
    
    server.join()
    generator.join()
    
    totaltime = 0.0
    count = 0
    while count < vpnum:
        cur_time = server.results.get()
        totaltime += cur_time
        count += 1
    
    meantime = totaltime / count
    #print 'count=',count
    #print 'meantime=',meantime
    return meantime
    
if __name__ == '__main__':
    vpnum = int(sys.argv[1])
    dlslot = int(sys.argv[2])
    #freq = float(sys.argv[3])
    servetime = float(sys.argv[3])
    round = int(sys.argv[4])
    seqfile = sys.argv[5]
    
    f = open(seqfile,'r')
    intervals = f.readlines()
    f.close()
    
    totaltime = 0.0
    for i in range(round):
        #print 'round',i+1
        cur_time = do_sim(vpnum,dlslot,servetime)
        totaltime += cur_time
    
    result = totaltime / round
    print 'vpnum:',vpnum,'|channel:',dlslot,'|dl_time:',servetime
    print 'finally:',result,'in %d rounds' % round