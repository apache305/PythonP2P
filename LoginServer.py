import socket
import threading
import cPickle
import time
import copy
import uuid
import yaml


import sys
import urllib




#port 20000:vp as a server
#port 10000:st
#port 20002:vp listen,mainly for st'sorder being a track
#port 10002:ls loging server

#from hashlib import sha1
from HeadCheck import *
from BasicServer import *
from threading import Thread









class LSServer(RawServer):#ST=SoftwareStore server
    def __init__(self, server_address, RequestHandlerClass,clubthreshold):
        RawServer.__init__(self, server_address, RequestHandlerClass)
        self.uuid=str(uuid.uuid1())

        self.clubs={}###{softid:[isClubFlag,stadd]}
        self.stServerAddr={}##[STserverAddress:freq]
        self.softFreq={}#{softid:freqs}
        self.conClubFlag={}##{softid:boolean}
        self.clubthreshold=clubthreshold
        self.access=0
        
        
        
        
    def outInterface(self,softList):
        """the out interface for the system initial"""
        for each in softList:
            self.clubs[each]=[False]
            self.conClubFlag[each]=False
            self.softFreq[each]=0
    def conClub(self):
        
        while 1:
            time.sleep(0.1)
            if self.clubthreshold==-1:
                break
            for softId,softFreqs in self.softFreq.items():
                if softFreqs > self.clubthreshold:
                    #print "over clubthreshold!"
                    if not self.conClubFlag[softId]:
                        
                        self.cmdConClub(softId)
                        self.conClubFlag[softId]=True
            #print "******club information******"
            #print self.clubs
            #print self.conClubFlag
            #print 
            
            
    def lsOutput(self): 
        filename="/p2pexp-output/LS-%s.csv"%self.uuid
        record=file(filename,'w')
        record.write("ST,frequence\n")
        oldAccess=0
        while 1:
            time.sleep(1)
            total=self.access
            newAccess=total-oldAccess
            writeSTR="%s,%s\n"%(newAccess,time.ctime()[:-5])
            record.write(writeSTR)
            record.flush()
            oldAccess=newAccess
        record.close()
    
        
                    
    def cmdConClub(self,softId):
        '''Login server notice ST to conclub for the software'''
        
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

        stAdd=self.findMinFreqST(self.stServerAddr)
        
        s.connect(stAdd)
        #[softId]
        cmd='LRC'
        data=cPickle.dumps(softId)
        lens=data.__len__()      
        #'BLD':0:
        sendMes='%s:%d:%s&E#'%(cmd,lens,data)        
        s.send(sendMes)
        #print "order ST to conClub"
        
        #self.clubs[softId][0]=True
        #self.clubs[softId][1]=stAdd
        
        s.close()

        
    def findMinFreqST(self,dict):
        minKey=min(dict,key=lambda x:dict[x])
        return minKey

class LSRH(RawRequestHandler):
    LSHeadCmd=['VLS',#VP->LS:Vp login  LS server[softid]&E#
               'SLS',#ST->LS:St login  LS server:[softid]&E#
               'SRC',#ST->LS:St Return softid which is constructed as a Club
               'VLO', #VP->LS:Vp LogOut 
               'TLS'
               
               ]
    def sendData(self,cmd,data):
        data=cPickle.dumps(data)
        lens=data.__len__()
        
        #'BLD':0:
        sendMes='%s:%d:%s&E#'%(cmd,lens,data)        
        self.request.send(sendMes)
        self.request.close()

    def handle(self):
        #self.request.send(self.server.message)
        data = self.request.recv(4096)
        cmd,length,data=headCheck(data)
        #print cmd,length,data#only for test
        if cmd not in self.LSHeadCmd:
            self.request.send('ERR:8:ErrorCmd')
            return
        if length>data.__len__():#still has data
            data=dataComeIn(self.request,length,data)
        if data[-3:]!='&E#':
            self.request.send('ERR:8:ErrorEnd')
            return
        data=data[:-3]
       
        if cmd=='VLS':
            #print cmd
            self.cmdVLS(data)
            #print self.server.software
        elif cmd=='SLS':
            self.cmdSLS(data)
            
        elif cmd=='SRC':
            self.cmdSRC(data)
        elif cmd=='VLO':
            self.cmdVLO(data)
        elif cmd=='TLS':
            self.cmdTLS(data)
            
        #self.request.send('DONE')#if not done,such as 'refu' etc..
        #print self.request.recv(100)
    def cmdVLS(self,data):
        
        
        reqSoftList=cPickle.loads(data)
        tempDict={}
        addr=self.request.getpeername()[0]
        #print "******************"
        #print "******VP %s login......******"%addr
        self.server.access+=1
        for each in reqSoftList:
            if self.server.clubs[each][0]:
                stAdd=self.server.clubs[each][1]
                tempDict[each]=stAdd
            else:
                stAdd=self.server.findMinFreqST(self.server.stServerAddr)
                tempDict[each]=stAdd
            self.server.softFreq[each]+=1##freq ++
            self.server.stServerAddr[stAdd]+=1 ##freq++???????????
        #print "ST:frequency-->",self.server.stServerAddr  
        cmd='RVL'
        self.sendData(cmd, tempDict)
        #print 
        return
    def cmdTLS(self,data):
        
        
        reqSoftList=cPickle.loads(data)
        #print 
        for each in self.server.stServerAddr.keys():
            
 
            reqSoftList.append(each)

        #print "******************"
        #print "******VP %s login......******"%addr
        self.server.access+=1

        #stAdd=self.server.findMinFreqST(self.server.stServerAddr)
        
        
        
        cmd='RTL'
        self.sendData(cmd,reqSoftList)

        return



        
 
    def cmdSLS(self,data):#St login  LS server:[softid]&E#reqSoftBeClubList
        loginLSAddr=cPickle.loads(data)[0]
        print loginLSAddr
        #addr=self.request.getpeername()[0]
        #print "******************"
        print '******ST %s login......******'%repr(loginLSAddr)
        self.server.access+=1
        
        self.server.stServerAddr[loginLSAddr]=0
        #print self.server.clubs
        #print 
        print "ST list-->",self.server.stServerAddr.keys()
        #print self.server.softFreq
        #print 
        return
    
    def cmdSRC(self,data):
        #print "receive ST club info\n"
   
        reqData=cPickle.loads(data)
        softId=reqData[0]
        addr=reqData[1]
        self.server.clubs[softId][0]=True
        self.server.clubs[softId].append(addr)
        
        print "-->>new club info<<--"
        print self.server.clubs
        
    def cmdVLO(self,data):
        pass
        


    def finish(self):
        self.request.close()
        
def getConfig(url="cn21.hp.act.buaa.edu.cn/expcfg/lscfg.yaml"):
    try:
        uuid1=str(uuid.uuid1())
        filename="/root/p2pexp/Server/cfg/lscfg-%s.yaml"%uuid1
        urllib.urlretrieve(url,filename)
        return filename
        
    except Exception,e:
        print "can't get config file",e
def analysisConfig(filename):
    config=yaml.load(file(filename,"r"))         
    softInfoConfig={}
    for softId,blockInfo in config['soft'].items():
        softInfoConfig[softId]=[]
        for i in range(blockInfo['blockNum']):
            blockId="B%s"%i
            softInfoConfig[softId].append(blockId)
    clubthreshold=config['clubthreshold']
    return softInfoConfig,clubthreshold


    
def __runServer(softInfoConfig,clubthreshold,port = 10002):

        
    
    
    
    
    
    server = LSServer(('', port), LSRH,clubthreshold)
    
    conClubThread=Thread(target=server.conClub)
    conClubThread.setDaemon(1)
    conClubThread.start()
    
    lsOutputThread=Thread(target=server.lsOutput)
    lsOutputThread.setDaemon(1)
    lsOutputThread.start()
    
    try:
        softList=softInfoConfig.keys()
        #server.isClub('S2','B1')
        server.outInterface(softList)
        server.startServer()
    except KeyboardInterrupt:
        print "LS exit......"


if __name__ == '__main__':
    try:
        url=sys.argv[1]

        filename=getConfig(url)
  
        
        softInfoConfig,clubthreshold=analysisConfig(filename)
        
                
        __runServer(softInfoConfig,clubthreshold)
    except Exception,e:
        print e
        raw_input("something may be wrong")
