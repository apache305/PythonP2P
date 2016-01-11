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
#import yaml

import uuid
import urllib

#import VPCluster
#import GetSeq


from HeadCheck import *
from BasicServer import *
from threading import Thread


#from VPCluster import PortManager

class VPServer(RawServer):#ST=SoftwareStore server
    def __init__(self, server_address, RequestHandlerClass,portMgr):
        
        flag=False
        
        while not flag:
            port=portMgr.getPort()
            #print "======",port
            bind_address=('',port)
            try:
                RawServer.__init__(self, bind_address, RequestHandlerClass)
                flag=True
            except Exception,e:
                print e

            
            
        self.softId=None# a VP represent a software
        self.blockPeers={}###{blockid:[peers]}#as a tracker provide blocks peer info
        #self.software={}##softid:[blockid]
        self.hasBlockInfo={} #{softId:{blockid:blockaddr} } #has blocks
        self.vpAsTrack=False
        self.ipAddr=socket.gethostbyname(socket.gethostname())#server port as 10000
        self.address=(self.ipAddr,self.socket.getsockname()[1])
        self.trackLoad=0
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

         
          

    
class VPRH(RawRequestHandler):
    VPHeadCmd=['VRP',#VP->VP:Vp Request block peers info:[softid,[blockid]]&E#
               'REB',#VP->VP:Vp Re Block:[softid,[blockid]]&E#
               'RPB',#VP->VP:vp RePort Blocks:[softid,blockid]&E#
               'CAT', #ST->VP:Cancel As a Track 
               'RCC' #st request peers info to ReConClub
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
        if cmd not in self.VPHeadCmd:
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
            self.server.trackLoad+=1
            self.cmdVRP(data)
            #print self.server.software
        elif cmd=='REB':
            self.cmdREB(data)
        elif cmd=='RPB':
            
            self.cmdRPB(data)
        elif cmd=='CAT':
            self.cmdCAT(data)
        elif cmd=='RCC':
            self.cmdRCC(data)
            
        #self.request.send('DONE')#if not done,such as 'refu' etc..
  
        
        
    def cmdVRP(self,data):#VP->VP:Vp Request block peers info:[softid,[blockid]]&E#
        #[softid,{blockid:[]}

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
    def cmdREB(self,data):#if the tracker give the staddress to other vp requeser
        #[softid,{blockid:[]}]

        reqSoft=data
        reqSoft=cPickle.loads(reqSoft)       
        #[softid,{blockid:[]}]
        #ipAddr=self.request.getpeername()[0]
        #reqAddr=(ipAddr,10000)
        #reqAddr=self.request.getpeername()

        #print reqSoft#only for test

        
        
        softId=reqSoft[0]

        reqBlocks=reqSoft[1]####{block1:[],block2:[]}dict
        for blockId in reqBlocks:
            if not self.server.validSoftReq(softId,blockId):
                print '%s,%s,invalid'%(softId,blockId)
                reqSoft[1][blockId].append('E')
                continue
  
            blockAddr=copy.deepcopy(self.server.hasBlockInfo[softId][blockId])#SYN
            #[blockAddr
            reqSoft[1][blockId].append('B')
            reqSoft[1][blockId].append(blockAddr) #return all
        
        #print "*********return block addr information for REB***************"
        #print reqSoft
        #print "*************************************************************"
        cmd='BLD'#Re Vp request Peers
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
    def cmdCAT(self,data):#Cancel As a Track 

        self.server.vpAsTrack=False
        self.server.blockPeers.clear()
        self.request.send("DONE")
        #print "******VP As Track Terminated******"
        return
    def cmdRCC(self,data):#st request peers info to ReConClub
        reqInfo=[]
        reqInfo.append(self.server.softId)
        blockList=[]
        
        
        blockPeers=copy.copy(self.server.blockPeers)
        for v in blockPeers.values():#[block pees]
            for l in v:
                blockList.append(l)
        if len(blockList)>10:
            blockList=blockList[:10]
        reqInfo.append(blockList)
        self.sendData('RRC',reqInfo)  # Re ReConclub
        #[softid,[blockpeers]]
            
            
        

        
        
        
        
        
  

    def finish(self):
        self.request.close()
        



class  VProcessNode(Thread):
    '''VP main body'''
    def __init__(self,portMgr,lifeTime,LSAddr,recordFile,VPReqList):
        Thread.__init__(self)
        self.uuid=None
        self.lifeTime=lifeTime
        self.portMgr=portMgr
        self.trackServer=VPServer(('',0),VPRH,portMgr)
        self.reqSoft=None
        self.reqSoftSTDict={}##used for recording the ST server address  need syn
        self.reqBlocks=None
        self.nodeHasBlocks={}#{softId:{blockId:addr}}
        self.reportFlag=False
        
        self.TrackSoftId=None
        self.TrackTable=None
        self.hasTrackTable=False
    
        self.hasReport=False
        
        
        #self.loginServerAddr=loginServerAddrConfig
        self.loginServerAddr=LSAddr
        self.requestRunFlag=True
        self.recordFile=recordFile
        self.VPReqList=VPReqList
        
        self.centerBlocks=0
        self.layerBlocks=0
        self.VPretryST=0
        self.VPretryTR=0
        self.VPretryLS=0
        self.VPretryReportVP=0
        
    def getReq(self,reqList):#out interface for the test
        """get request software"""
        self.reqSoft=reqList[0]
        i=1
        try:
            while reqList[i]!='EOF':
               blockId="B%s"%reqList[i]
               time.sleep(reqList[i+1])
               self.reqBlocks=[blockId]
               #print reqList[i]
               #print self.reqBlocks
               i+=2
        except Exception,e:
            print "reqList format wrong!",e
        
    def run(self):#execute reqSoft as a thread,then start the server as the main process
        
        
        
        
        #print self.VPReqList
        t=Thread(target=self.reportTrack)
        t.setDaemon(1)
        t.start()
        
        
        
        self.trackServer.vpAsTrack=False
        #print "here run"
        #self.trackServer.startServer()
        self.reqThread()
        #tR.setDaemon(1)
        
        


        #if self.lifeTime:
            #time.sleep(self.lifeTime)
            
            #self.requestRunFlag=False
            ##print "=======!!!!!",self.trackServer.vpAsTrack
            #if not self.trackServer.vpAsTrack:
                #self.trackServer.shutdown()
            
            

        print 'VP--exit'
        

        
        
        


    def reqThread(self):
        print "VP Address-->:%s\n"%repr(self.trackServer.address)
        #record=file(self.recordFileName,"a")
    
        totalList=self.VPReqList
        #random choice a reqlist
        totallength=len(self.VPReqList)
        choice=random.randint(0,totallength-1)
        testList=totalList[choice]
        
        
        
        #print testList
        
        self.reqSoft=testList[0]
        j=0
        i=1
        totalTime=0.0
        totalConnectStTime=0.0
        totalConnectTrTime=0.0
        
        # don't sleep, for we run each VP at designate time
        #time.sleep(random.uniform(0,10))       
        while self.requestRunFlag and testList[i]!='EOF':
            blockId="B%s"%testList[i]
            time.sleep(testList[i+1])
            self.reqBlocks=[blockId]
            i+=2

            
            # self.getReq(testList)
            if not self.reqSoftSTDict.has_key(self.reqSoft):
                self.loginLS([self.reqSoft])
            
                #print "******VP Login LS Successfully******"
            
    
            reqs=self.reqSoftBlocks(self.reqSoft, self.reqBlocks)
            #print "******VP Request %s,%s******"%(reqs[0],reqs[1].keys())
            #reqs=[softId,{blockid:[],blockid:[]}]
            #trackTable=#groupid:[[blocks],track]
            if reqs[0]==self.TrackSoftId and self.hasTrackTable:
                blockList=reqs[1].keys()
                for eachList in self.TrackTable.values():
                    if blockList[0] in eachList[0]:
                        getPeerAddr=eachList[1]
                        break  
                t3start=time.time()
                self.reDirectForPeers(reqs,getPeerAddr)
                t3end=time.time()
                
                connectStTime=0.0
                connectTrTime=t3end-t3start
            else:
  
                startTime=time.time()
                returnDic=self.reqSTForSoft(reqs, self.reqSoftSTDict[self.reqSoft])
                midTime=time.time()   
                self.dataAnalysis(returnDic)
                endTime=time.time()
                
                connectStTime=midTime-startTime
                connectTrTime=endTime-midTime
            
            
            
            
            
            duringTime=connectStTime+connectTrTime
            totalTime+=duringTime
            totalConnectStTime+=connectStTime
            totalConnectTrTime+=connectTrTime
            
            #recordTimeFmt="NO%s:duringTime:%s\n"%(j,duringTime)
            #record.write(recordTimeFmt)
            j+=1
            
        #print "exit"
        avgTime=totalTime/j
        avgConnectStTime=totalConnectStTime/j
        avgConnectTrTime=totalConnectTrTime/j
        
        
        recordTimeFmt="%s,%s,%s,VP-LS=%d,VP-ST=%d,VP-TR=%d,VP-R-VP=%d,Center=%d,Layer=%d\n"%(avgTime,avgConnectStTime,avgConnectTrTime,self.VPretryLS,self.VPretryST,self.VPretryTR,self.VPretryReportVP,self.centerBlocks,self.layerBlocks)
        self.recordFile.write(recordTimeFmt)

        self.recordFile.flush()
        self.portMgr.vpExit()
        
        
 


        
    def reqSoftBlocks(self,softId,blockList):
        ####req Thread call this method
        reqS=[]
        reqS.append(softId)
        tempDict={}
        for each in blockList:
            tempDict[each]=[]
        reqS.append(tempDict)
        reqS.append(self.trackServer.address)
        return reqS
    #return format :[softId,{blockid:[],blockid:[]}]
    #def reqSoft(self):
        #return ['S1','S2']
    def reqSTForSoft(self,reqs,addr):
        

        conflag=False
        while not conflag:
            try:

                s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                s.connect(addr)
                conflag=True
            except Exception,e:
                print e,'ST',addr
                self.VPretryST+=1
                time.sleep(random.uniform(0,2))
            
        reqs=cPickle.dumps(reqs)
        dat='%s&E#'%reqs
        lent=dat.__len__()
        if self.trackServer.vpAsTrack:
            mes='RWT:%d:%s'%(lent,dat)#################################
        else:
            mes='RWT:%d:%s'%(lent,dat)#################################
        s.send(mes)
    
        data=s.recv(4096)
        
        #print data
        cmd,length,data=headCheck(data)
        #print cmd,length,data#only for test
        if cmd !='ERR' and length>data.__len__():#still has data
            data=dataComeIn(s,length,data)
        if data[-3:]!='&E#':
            self.request.send('ERR:8:ErrorEnd')
            return
        data=data[:-3]
        
        if cmd=='BLD':
            dic=cPickle.loads(data)
        #print "--->>>VP Received From ST:<<<---"
        #[softid,{blockid:[]}]
        return dic
        
        #self.dataAnalysis(dic)
        
        #if s.recv(4096)=='DONE':
            #print 'done'
    def dataAnalysis(self,data):
        softId=data[0]
        if len(data)==3:#has all track table           
            trackTable=data[2]
            #print "\n--->>>GroupTable<<<---"
            #print trackTable
            #print 
            #report thread.
            if not self.hasReport:
                self.TrackTable=trackTable
                self.TrackSoftId=softId
                self.reportFlag=True
                self.hasReport=True
                self.hasTrackTable=True
            
            


            #only report when request happens
        blockDict=data[1]
        #print "\n--->>>BlockDict Received From ST<<<---"
        #print blockDict
        #print 

        ###{blockid:['B',add],blockid:['T',tadd],blockid:['BT',badd]}
    
        
        for blockId,blockInfo in blockDict.items():
            if blockInfo[0]=='B':
                #print "RECEIVED:%s-%s-address:%s"%(data[0],blockId,blockInfo[1])
                self.centerBlocks+=1

                    
                if not self.trackServer.hasBlockInfo.has_key(softId):
                    self.trackServer.hasBlockInfo[softId]={}
                tempBlockD=self.trackServer.hasBlockInfo[softId]
                tempBlockD[blockId]=blockInfo[1]
                
            elif blockInfo[0]=='BT':
                #blockInfo:['BT','addr',['S1',[blocks]],stadd]
                #print "RECEIVED:%s-%s-address:%s"%(data[0],blockId,blockInfo[1])
                self.centerBlocks+=1
                
                if not self.trackServer.hasBlockInfo.has_key(softId):
                    self.trackServer.hasBlockInfo[softId]={}
                tempBlockD=self.trackServer.hasBlockInfo[softId]
                tempBlockD[blockId]=blockInfo[1]
                
                #print "\nThis VP Need To Be Track"
                self.trackServer.softId=blockInfo[2][0]
                for eachBlock in blockInfo[2][1]:
                    self.trackServer.blockPeers[eachBlock]=[blockInfo[3]]


                #self.trackServer.vpAsTrack=True
                
                #t=Thread(target=self.statFreq)##start to statistic the trackload
                #t.start()
                

                
                
                
            elif blockInfo[0]=='T':
                #print "%s-%s-Redirect to%s"%(data[0],blockId,blockInfo[1])
                #print "here Track"
                reqs=[data[0],{blockId:[]}]
                addr=blockInfo[1]
                #print "--->>>VP ReDirected to TRACKER %s<<<---"%str(addr)
                self.reDirectForPeers(reqs,addr)
            elif blockInfo[0]=='E':
                print "%s-%s-Error Request"%(data[0],blockId)
            
            #print "\n--->>>This Server Has Block :<<<---"
            #print self.trackServer.hasBlockInfo
            #print 
                

          

                

    def reDirectForPeers(self,reqs,addr):
        
        reDirectForPeerRetryCount=0
        conflag=False
        while not conflag:
            try:
                reDirectForPeerRetryCount+=1
                s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                s.connect(addr)
                conflag=True
            except Exception,e:
                print e,'Tracker',addr
                self.VPretryTR+=1
                time.sleep(random.uniform(0,2))
                 
        reqs=cPickle.dumps(reqs)
        dat='%s&E#'%reqs
        lent=dat.__len__()
        #print "before VPR conn TR%s"%str(addr)
        mes='VRP:%d:%s'%(lent,dat)#################################
        
           
        s.send(mes)
    
        data=s.recv(4096)
        #print "**recv from TRACK"
        #print data
        cmd,length,data=headCheck(data)
        #print cmd,length,data#only for tes
        if cmd !='ERR' and length>data.__len__():#still has data
            data=dataComeIn(s,length,data)
            
        if data[-3:]!='&E#':
            s.send('ERR:8:ErrorEnd')
            return
        data=data[:-3]

        if cmd=='RVP':
            dic=cPickle.loads(data)
        if cmd=='ERR':
            print data


        #print "\n--->>>VP Received Peers From Track:<<<---"
        softId=dic[0]
        blockDict=dic[1]
        #print blockDict
        
        for blockId,blockInfo in blockDict.items():# 
            #if blockInfo[0]=='P':
                #print  "receive _________ Peer"
                #print "%s-%s-peers:%s"%(softId,blockId,blockInfo[1])
            if blockInfo[0]=='E':
                print "%s-%s-error request"%(softId,blockId)
        #print 
                
            

        
        reqs=[softId,{blockId:[]}]
        
        length=len(blockInfo[1])
        length-=1
        returnFlag=False
        addr=blockInfo[1][length]#choose the last one which means the latest peer
        
        self.layerBlocks+=1
        newSoftId=reqs[0]
        blockList=reqs[1].keys()
        
        
        for each in blockList: #only one item{softId:{blockid:blockaddr} } #has blocks
            
                #print "RECEIVED:%s-%s-address:%s"%(softId,blockId,blockInfo[1])
                #self.layerBlocks+=1
                
                if not self.trackServer.hasBlockInfo.has_key(newSoftId):
                    self.trackServer.hasBlockInfo[softId]={}
                tempBlockD=self.trackServer.hasBlockInfo[softId]
                tempBlockD[each]="%s%sADDR"%(softId,each)
                #print 
                
            
           
        
        
        
        
        
        '''
        while 1:
            #print "--->>>ReDirect For BlockAddr<<<---"
            #print addr
            #print 
            returnFlag=self.reDirectForAddr(reqs, addr)
            if returnFlag:
                break
            else:
                length-=1
                addr=blockInfo[1][length]
                if length ==-1:
                    break
        '''

        
    def reDirectForAddr(self,reqs,addr):
        

        #print "\n--->>>request soft,and the redirect Addr<<<---"
        #print reqs
        #print addr
        #print 

        try:

            s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.connect(addr)
        except Exception,e:
            print e,'VP',addr
            err="VP->VP retry!" + str(addr)
            self.recordFile.write(err)
            self.recordFile.flush()
            
            return False
        
        reqs=cPickle.dumps(reqs)
        dat='%s'%reqs
        lent=dat.__len__()
        mes='REB:%d:%s&E#'%(lent,dat)#################################
           
        s.send(mes)
    
        data=s.recv(4096)
        #print data
        cmd,length,data=headCheck(data)
        #print cmd,length,data#only for tes
        if cmd !='ERR' and length>data.__len__():#still has data
            data=dataComeIn(s,length,data)
            
        if data[-3:]!='&E#':
            s.send('ERR:8:ErrorEnd')
            return
        data=data[:-3]

            
        if cmd=='BLD':
            dic=cPickle.loads(data)
        if cmd=='ERR':
            print data

        #print "\n--->>>vp Received Address From Peers:<<<---"
        softId=dic[0]
        blockDict=dic[1]
        #print blockDict
        
        for blockId,blockInfo in blockDict.items(): #only one item
            if blockInfo[0]=='B':
                #print "RECEIVED:%s-%s-address:%s"%(softId,blockId,blockInfo[1])
                #self.layerBlocks+=1
                
                if not self.trackServer.hasBlockInfo.has_key(softId):
                    self.trackServer.hasBlockInfo[softId]={}
                tempBlockD=self.trackServer.hasBlockInfo[softId]
                tempBlockD[blockId]=blockInfo[1]
                #print 
                
                return True
                
                
            elif blockInfo[0]=='E':
                print "%s-%s-error request"%(softId,blockId)
                s.close()
                #print 
                return False
        
        
            


        
                

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
        
 
            
    def loginLS(self,data=[]):
        '''loging LoginServer for ST add'''
        
        
        
        loginLSRetryCount=0
        conflag=False
        while not conflag:
            try:
                loginLSRetryCount+=1
                s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                #print self.loginServerAddr
                s.connect((self.loginServerAddr,10002))
                conflag=True
            except Exception,e:
                print e,'LS',self.loginServerAddr
                self.VPretryLS+=1
                time.sleep(random.uniform(0,1))
        
        #[softId]
        #data=['S1','S2']
        cmd='VLS'#Vp login ls Server
        data=cPickle.dumps(data)
        lens=data.__len__()      
        #'BLD':0:
        sendMes='%s:%d:%s&E#'%(cmd,lens,data)        
        s.send(sendMes)
        data=s.recv(4096)
        rcmd,length,data=headCheck(data)
        if length>data.__len__():#still has data
            data=dataComeIn(self.request,length,data)          
        if data[-3:]!='&E#':
            self.request.send('ERR:8:ErrorEnd')
            s.close()
            return
        data=data[:-3]
        if rcmd=='RVL':###Re  Vp Login ls server
            self.reqSoftSTDict=cPickle.loads(data)
            #{softid:stserveradd,softid:stserveradd}
            #print "******Receive From LS:******"
        #for eachk,eachv in self.reqSoftSTDict.items():
            
            #print "******Software:%s Redirect to ST:%s******"%(eachk,eachv)
            
        s.close()
        
        
    def statFreq(self):
            oldSecTotal=0
            uuidstr=str(uuid.uuid1())
            filename="/p2pexp-output/TR-%s.csv"%uuidstr

            record=file(filename,'w')
            record.write("%s,%s\n"%(self.trackServer.softId,self.trackServer.blockPeers.keys()))
            while 1:
                time.sleep(1)
                total=self.trackServer.trackLoad
                newSecTotal=total-oldSecTotal
                writeSTR="%s,%s\n"%(newSecTotal,time.ctime()[:-5])
                #print writeSTR       
                record.write(writeSTR)
                record.flush()
                oldSecTotal=total
            record.close()

        
        

    def reportTrack(self):
        #trackTable:{groupId:[  [blocks],(tranke IP tuple)],groupid:[  [b],(t)}
        '''report track with the info of block have'''
        oldCount={}
        
        while 1:
             time.sleep(random.uniform(5,10))
             print self.reportFlag
             
             if  self.reportFlag:
                   
                softId=self.TrackSoftId
                trackTable=self.TrackTable
                #print "report"
                
                #print 
                if not self.trackServer.hasBlockInfo.has_key(softId):
                    continue
                
                reportMes=[]
                reportMes.append(softId)
                reportMes.append([])
                #print "=============*TKTABALDSJLAKFJSL;AKDFJSL;ADKFJ\n"
                #print trackTable
                #print "========================"
                #time.sleep(2)
                
        
                for trackInfo in trackTable.values():
                    reportMes[1]=[]
                    blocks=trackInfo[0]
                    trackIp=trackInfo[1]###{groupId:[  [blocks],(tranke IP tuple)],groupid:[  [b],(t)}
                    reportIp = trackIp
                    
                      
                    for blockId in blocks: 
                        if self.trackServer.hasBlockInfo[softId].has_key(blockId):
                                #print self.nodeHasBlocks[softId][blockId]
                            reportMes[1].append(blockId)
                    if not oldCount.has_key(trackIp):
                        oldCount[trackIp]=0 
                    
                    #oldMessage[]
                    
        
                    if  len(reportMes[1]) == 0 :
                        continue
                    elif oldCount[trackIp] == len(reportMes[1]):
                        continue
                        
                    else :
                        oldCount[trackIp]=len(reportMes[1])
                        #print reportMes
                        #print "====",reportIp
                        reportRetryCount=0
                        conflag=False
                        while not conflag:
                            try:
                                reportRetryCount+=1
                                s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                                s.connect(reportIp)  
                                conflag=True
                            except Exception,e:
                                print e,'Report',reportIp
                                self.VPretryReportVP+=1
                                time.sleep(random.uniform(0,2))
               
                        cmd='RPB'#VP->VP:vp RePort blocks:[softid,{blockid:[]}]&E#
                        print "***************************RPB CMD"
                        print reportMes
                        reportMes.append(self.trackServer.address)
                        data=cPickle.dumps(reportMes)
                        lens=data.__len__()      
                        sendMes='%s:%d:%s&E#'%(cmd,lens,data)        
                        s.send(sendMes)
                        print "******************report :%s",time.time()
                        #print "Report DONE\n"
          
                        s.close()
                    time.sleep(random.uniform(0,1))
            
                        
                        

    #def 
    def waitForAsTrack(self):#may need running as a threading
        '''wait for message to be a track,when st reconclub'''
        add=('',20002)
        s=socket(socket.AF_INET,socket.SOCK_STREAM)
        s.bind(add)
        s.listen(5)
        cmds=['SAT']
        while 1:
            conn,addr=s.accept()
            data=conn.recv(4096)
            cmd,length,data=headCheck(data)
            #print cmd,length,data#only for test
            if cmd not in cmds:
                self.request.send('ERR:8:ErrorCmd')
                conn.close()
                continue
            if cmd=='SAT' and self.vpAsTrack:
                self.request.send('ERR:8:ErrorCmd')
                conn.close()
                continue
                
            if length>data.__len__():#still has data
                data=dataComeIn(self.request,length,data)
                
            if data[-3:]!='&E#':
                self.request.send('ERR:8:ErrorEnd')
                conn.close()
                continue
            data=data[:-3]
            trackInfo=cPickle.loads(data)
            self.trackServer.softId =trackInfo[0]
            for each in trackInfo[1]:
                self.trackServer.blockPeers[each]=[(addr[0],10000)]
            #print self.trackServer.blockPeers
            self.trackServer.vpAsTrack=True

            conn.close()
            #print '******VP as Server start at %s******'%time.ctime()
            self.trackServer.startServer()
            
#def getConfig(url="cn21.hp.act.buaa.edu.cn/expcfg/cfg.yaml"):
##    try:
##       uuid=str(uuid.uuid1())
#        filename="/root/p2pexp/Server/cfg/vpcfg-%s.yaml"%uuid
#        urllib.urlretrieve(url,filename)
#        return filename
        
#     except Exception,e:
#        print "can't get config file",e   


        
        
          
def __runServer(portMgr):
    #server = VPServer(('', port), VPRH)
    vpserver=VProcessNode(portMgr,'192.168.1.169')

    try:
    

        #vpserver.run()
        vpserver.start()
        #raw_input('...')
        vpserver.join()
        print "exit"

            
        #server.initSoftInfo()
        #server.crazyTest()
        #server.isClub('S2','B1')
        #vpserver.trackServer.startServer()
        #raw_input("......")
    except KeyboardInterrupt:
        raise

if __name__ == '__main__':
    try:
#       portMgr = VPCluster.PortManager(30000)
        #__runServer(portMgr)
        #print VPServer.__doc__()
        test=[]
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
