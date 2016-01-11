'''
Created on 2010-7-16

@author: Apache
'''

import socket
import threading
import cPickle
import time
import copy
import random
import yaml
import sys

#import yaml

import uuid
import urllib

#import VPCluster
#import GetSeq


from HeadCheck import *
from BasicServer import *
from threading import Thread


#from VPCluster import PortManager

class TrackServer(RawServer):#ST=SoftwareStore server
    def __init__(self, server_address, RequestHandlerClass):

        RawServer.__init__(self, server_address, RequestHandlerClass)

            
        self.softId=None# a VP represent a software
        self.blockPeers={}###{blockid:[peers]}#as a tracker provide blocks peer info
        #self.software={}##softid:[blockid]
        self.ipAddr=socket.gethostbyname(socket.gethostname())#server port as 10000
        self.address=(self.ipAddr,self.socket.getsockname()[1])
        print "TR Addr--->>>%s"%repr(self.address)
        self.trackLoad=0
        self.reportLoad=0
        self.loginServerAddr=None
        self.STADD=None
        self.uuid=None
        self.filename=None
        
        self.testFilename="/endflag/%s.flag"%(uuid.uuid1())
        #print self.address

        #self.blockPeersLock=threading.Lock()
        #self.hasBlockInfoLock=threading.Lock()



    def validPeerReq(self,blockId):#check out if the peer info request is valid 
        if blockId not in self.blockPeers.keys():
            return False
        else:
            return True
        
    def validSoftReq(self,softId,blockId):#check out if the block request is valid
        if softId not in self.hasBlockInfo.keys():
            return False
        else:
            blockD=self.hasBlockInfo[softId]
            if blockId not in blockD.keys():
                return False
            else:  
                return True
    def loginLS(self,data=[]):
        '''loging LoginServer for ST add'''
        
        
        
        loginLSRetryCount=0
        conflag=False
        while not conflag:
            try:
                loginLSRetryCount+=1
                print 'login LS',self.loginServerAddr

                s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                #print self.loginServerAddr
                s.connect((self.loginServerAddr,10002))
                conflag=True

            except Exception,e:
                print e,'loginLS'
                loginLSRetryCount+=1
                time.sleep(random.uniform(0,1))
        

        cmd='TLS'#Vp login ls Server
        data=cPickle.dumps(data)
        lens=data.__len__()      
        #'BLD':0:
        sendMes='%s:%d:%s&E#'%(cmd,lens,data)        
        s.send(sendMes)
        data=s.recv(4096)
        #print "rece__",data
        
        rcmd,length,data=headCheck(data)
        if length>data.__len__():#still has data
            data=dataComeIn(s,length,data)          
        if data[-3:]!='&E#':
            s.send('ERR:8:ErrorEnd')
            s.close()
            return
        
        print "here"
        if rcmd=='RTL':###Re  Vp Login ls server
            stAddList=cPickle.loads(data)
            
            self.STADD=stAddList[0]

            
            
        s.close()
    def loginST(self,data=[]):
        '''loging LoginServer for ST add'''
        print self.address
        data.append(self.address)
        
        
        
        loginSTRetryCount=0
        conflag=False
        while not conflag:
            try:
                loginSTRetryCount+=1
                s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                #print self.loginServerAddr
                s.connect(self.STADD)
                conflag=True
            except Exception,e:
                print e
                loginSTRetryCount+=1
                time.sleep(random.uniform(0,1))
        

        cmd='TRS'#Track Report to ST
        print 'TR->ST',data
        data=cPickle.dumps(data)
        lens=data.__len__()      
        #'BLD':0:
        sendMes='%s:%d:%s&E#'%(cmd,lens,data) 
               
        s.send(sendMes)
        
        s.close()
        
    def statFreq(self):
            oldSecTotal=0
            oldReportTotal=0
            #uuidstr=str(uuid.uuid1())
            #filename="/p2pexp-output/TR-%s.csv"%uuidstr

            record=file(self.filename,'w')
            addr="%s\n"%str(self.address)
            record.write(addr)
            record.write("%s,%s\n"%(self.softId,self.blockPeers.keys()))
            record.write("ServerLoad,ReportLoad\n")
            while 1:
                time.sleep(1)
                total=self.trackLoad
                reportTotal=self.reportLoad
                newSecTotal=total-oldSecTotal
                newReportTotal=reportTotal-oldReportTotal
                
                peerNum=[]
                for blockId,peers in self.blockPeers.items():
                    peerNum.append(len(peers))
                    
                writeSTR="%s,%s,%s,%s\n"%(newSecTotal,newReportTotal,time.ctime()[:-5],peerNum)
                #print writeSTR       
                record.write(writeSTR)
                record.flush()
                oldSecTotal=total
                oldReportTotal=reportTotal
            record.close()


    
class TRRH(RawRequestHandler):
    THeadCmd=['VRP',#VP->VP:Vp Request block peers info:[softid,[blockid]]&E#
               'RPB',#VP->VP:vp RePort Blocks:[softid,blockid]&E#
               #'TRS',#TR->ST:Track Report St:[self.address]&E#
               'STT'
               ]
    def sendData(self,cmd,data):# all information in one list
        data=cPickle.dumps(data)
        lens=data.__len__()
        
        #'BLD':0:
        sendMes='%s:%d:%s&E#'%(cmd,lens,data)        
        self.request.send(sendMes)

    
    def handle(self):
        #self.request.send(self.server.message)
        data = self.request.recv(4096)
        cmd,length,data=headCheck(data)
        #print cmd,length,data#only for test
        if cmd not in self.THeadCmd:
            self.request.send('ERR:8:ErrorCmd')
            return
        if length>data.__len__():#still has data
            data=dataComeIn(self.request,length,data)
            
        if data[-3:]!='&E#':
            self.request.send('ERR:8:ErrorEnd')
            return
        data=data[:-3]
  
        if cmd=='VRP':
            #print cmd
            
            t1s=time.time()
            
            self.server.trackLoad+=1
            self.cmdVRP(data)
            
            t1e=time.time()
            
            t1p=t1e-t1s
            #record=

        elif cmd=='RPB':
            
            self.server.reportLoad+=1
            
            self.cmdRPB(data)
        elif cmd=='STT':
            self.cmdSTT(data)

  
        
        
    def cmdVRP(self,data):#VP->TR:Vp Request block peers info:[softid,[blockid]]&E#
        #[softid,{blockid:[]}
        #print "rece:",data
        

        reqSoft=data
        reqSoft=cPickle.loads(reqSoft)       
        #[softid,{blockid:[]}
        #ipAddr=self.request.getpeername()[0]
        #reqAddr=(ipAddr,10000)
        #reqAddr=self.request.getpeername()
        #print reqSoft#only for test
        
        softId=reqSoft[0]
        if softId != self.server.softId:
            self.request.send('ERR:9:ErrSoftId')
            return
        reqBlocks=reqSoft[1]####{block1:[],block2:[]}dict
        for blockId in reqBlocks.keys():
            if not self.server.validPeerReq(blockId):
                print '%s,%s,invalid'%(softId,blockId)
                reqSoft[1][blockId].append('E')
                continue
  
            blockPeers=copy.deepcopy(self.server.blockPeers[blockId])#SYN
            #[peerlist]
            reqSoft[1][blockId].append('P')
            reqSoft[1][blockId].append(blockPeers) #return all

        #print reqSoft
        cmd='RVP'#Re Vp request Peers
        self.sendData(cmd,reqSoft)

        return
   
    def cmdRPB(self,data):#VP->VP:vp RePort blocks:[softid,[blocks]]&E#
        

        reqSoft=data
        reqSoft=cPickle.loads(reqSoft)
        reqAddr=reqSoft[2]
        #print "******received from %s to be peers******" %repr(reqAddr)
        #print reqSoft
        #print "*****************************************"
        
        softId=reqSoft[0]
        
        if softId != self.server.softId:
            return
        reqBlocks=reqSoft[1]####[blockds]
        for blockId in reqBlocks:
            if not self.server.validPeerReq(blockId):
                continue
            addr=reqAddr

            if addr not in self.server.blockPeers[blockId]:
                
                self.server.blockPeers[blockId].append(addr)
        #print "*********server block peers infomation**************"
        #for blockId,peers in self.server.blockPeers.items():
            #print "%s:%s"%(blockId,peers)
        #print "****************************************************"
        

                
        return
    
    def cmdSTT(self,data):#ST->TR:St To Track :[softid,[blocks]]&E#
        #print "recv from ST ",data

        reqSoft=data
        reqSoft=cPickle.loads(reqSoft)
        #print reqSoft
        #reqAddr=reqSoft[2]
        #print "******received from %s to be peers******" %repr(reqAddr)
        #print reqSoft
        #print "*****************************************"
        
        softId=reqSoft[0]
        
        self.server.softId=softId
        reqBlocks=reqSoft[1]####[blockds]
        stadd=reqSoft[2]
        for each in reqBlocks:
            self.server.blockPeers[each]=[]
            self.server.blockPeers[each].append(stadd)
        
        #print "*******self.softid***",self.server.softId
        #print self.server.blockPeers
        t=Thread(target=self.server.statFreq)
        t.start()


                
        return
 

    def finish(self):
        self.request.close()
        


    def logoutLS(self,data=[]):
        '''loging LoginServer for ST add'''
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        #print self.loginServerAddr
        s.connect((self.loginServerAddr,10002))
        #[softId]
        #data=['S1','S2']
        cmd='VLO'#Vp login ls Server
        data=cPickle.dumps(data)
        lens=data.__len__()      
        #'BLD':0:
        sendMes='%s:%d:%s&E#'%(cmd,lens,data)        
        s.send(sendMes)

 
        
 
            

        
        

def getConfig(url="cn21.hp.act.buaa.edu.cn/expcfg/stcfg.yaml"):
        try:
            uuid1=str(uuid.uuid1())
            filename="/root/p2pexp/Server/cfg/trcfg-%s.yaml"%uuid1
            urllib.urlretrieve(url,filename)
            return filename
            
        except Exception,e:
            print "can't get config file",e    
    
def analysisConfig(filename):
    
            config=yaml.load(file(filename,"r"))
                
    
            loginServerAddrConfig=config['lsConfig']['lsAddr']
            
          
            return loginServerAddrConfig
            
            



class  TrackServerNode(Thread):
        def __init__(self,port):
            Thread.__init__(self)

            self.trackServer=TrackServer(('', port), TRRH)
            self.trackServer.uuid=str(uuid.uuid1())
            self.trackServer.filename="/p2pexp-output/TR-%s.csv"%self.trackServer.uuid
            self.trackServer.loginServerAddr=None
        
            
        def run(self):
            
            
            
            
            
            
            
            self.trackServer.loginLS()
            self.trackServer.loginST()
            self.trackServer.startServer()
        
          
def __runServer(num=10,url="cn21.hp.act.buaa.edu.cn/expcfg/stcfg.yaml",port=5005):
    #server = VPServer(('', port), VPRH)
    filename=getConfig(url)
    retv=analysisConfig(filename)
    #port=20050
    #trackList=[]
    try:
    
        for i in range(num):
            trackNode=TrackServerNode(port)
            trackNode.trackServer.loginServerAddr=retv
            trackNode.start()
            print "ok",i
            port+=1
            time.sleep(0.1)
    
    
   
   
        
        #print trackserver.loginServerAddr
        
        

        #print "ST connect"
    
        

    except KeyboardInterrupt:
        raise


    
        

if __name__ == '__main__':
    num=int(sys.argv[1])
    port=int(sys.argv[2])
    url=sys.argv[3]
    try:
        
            
#       portMgr = VPCluster.PortManager(30000)
        __runServer(num,url,port)
        #print VPServer.__doc__()
        
        #VPPort=40005
        #for i in range(30):
        ##    VPPort=VPPort+1
         #   TT=Thread(target=__runServer,args=[VPPort])
         #   TT.setDaemon(1)
         #   TT.start()
            #__runServer(VPPort)
            
          #  test.append(TT)

           # time.sleep(11)
           # print "next"
        #__runServer(20055)
        #raw_input("wait......")
    except Exception,e:
        print e
        raw_input("something may be wrong")
