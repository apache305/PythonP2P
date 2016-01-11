import socket
import threading
import cPickle
import time
import copy
import uuid
import sys
import urllib
import yaml


#port 20000:vp as a server
#port 10000:st
#port 20002:vp listen,mainly for st'sorder being a track
#port 10002:ls loging server

#from hashlib import sha1
from HeadCheck import *
from BasicServer import *
from threading import Thread





class STServer(RawServer):#ST=SoftwareStore server
    def __init__(self, server_address, RequestHandlerClass,loginServerAddrConfig,groupNum):
        RawServer.__init__(self, server_address, RequestHandlerClass)
        self.uuid=str(uuid.uuid1())       
        self.clubs={}###softid:groupid:[[blocks],track]
        self.software={}##softid:[blockid]
        self.blockInfo={}#{sofid:blockid:[freq,blockaddr]}
        self.conClubFlag={}#sotid:boolean
        self.isClubFlag={}#softId:boolean
        self.ipAddr=socket.gethostbyname(socket.gethostname())#server port as 10000
        self.address=(self.ipAddr,server_address[1])
        #print self.address
        self.loginServerAddr=loginServerAddrConfig
        self.filename="/p2pexp-output/ST-%s.csv"%self.uuid
        self.serverStopFlag=False
        self.creatClubDiv=groupNum
        self.trackAddr=[]
        
        self.softInfoLock=threading.Lock()
        self.clubsLock=threading.Lock()
        self.conClubFlagLock=threading.RLock()
        self.isClubFlagLock=threading.Lock()
        
    def getBlockTrack(self,softId,blockId):
        self.clubsLock.acquire()
        groups=copy.deepcopy(self.clubs[softId])
        self.clubsLock.release()
        #{groupid:[[blocks],traker]}
        for tracktable in groups.values():
            if blockId in tracktable[0]:
                return tracktable[1]
            
        return None
    
    def getSoftTrack(self,softId):
        self.clubsLock.acquire()
        groups=copy.deepcopy(self.clubs[softId])
        self.clubsLock.release()
        return groups
        
        
    def creatClub(self,softId):
        
        self.initFreq()

        
        tempDict={}
        div=self.creatClubDiv
        
        blocks=self.software[softId]
        groups=len(blocks)/div
        for i in range(groups):
            gid='G%d'%i
            tempDict[gid]={}
        
        tempDiv={}
        for blockId in blocks:
            #sha=self.getSoftHash(softId, blockId)
            #freq=self.softAttr[sha][0]
            freq=self.blockInfo[softId][blockId][0]
            tempDiv[blockId]=freq
            #{blockid:freq}
        #print "**********************************"
        #print tempDiv
        #print "**********************************"
        
        while len(tempDiv)>groups:
            
            minKey1=self.findMinFreq(tempDiv)
            minValue1=tempDiv.pop(minKey1)
            minKey2=self.findMinFreq(tempDiv)
            minValue2=tempDiv.pop(minKey2)
            #print "**********************************"
            #print tempDiv
            #print "**********************************"

            #print 'minkey1:%s,minvalue1:%s'%(minKey1,minValue1)
            #print 'minkey2:%s,minvalue2:%s'%(minKey2,minValue2)
            #print "**********************************"
            
            if minKey1[0]!='G' and minKey2[0]!='G':
                findFlag=False
                for tempk,tempv in tempDict.items():
                    if len(tempv)==0:
                        findFlag=True
                        break
                if findFlag: #still has empty group                             
                    tempDict[tempk][minKey1]=minValue1
                    tempDict[tempk][minKey2]=minValue2
                    tempDiv[tempk]=minValue1+minValue2
                else:#all groups full

                    tempDiv[minKey2]=minValue2###put back 1 item.

                    minGid='G0'
                    for  ming in tempDict.keys():#all has full
                        if tempDiv[ming]<tempDiv[minGid]:#curr min < indicate min  indicate=curr
                            minGid=ming

                    tempDict[minGid][minKey1]=minValue1
                    tempDiv[minGid]+=minValue1
                    
                    


                    #tempDict['G0'][minKey1]=minValue1
                    #tempDiv['G0']+=minValue1
                    #if tempDict.has_key('G1'):#case if there is only 1 groups
                    #    tempDict['G1'][minKey2]=minValue2
                    #    tempDiv['G1']+=minValue2
                    #else:
                    #    tempDict['G0'][minKey2]=minValue2
                    #    tempDict['G0']+=minValue2
                    
            elif minKey1[0]=='G' and minKey2[0]!='G':
                tempDict[minKey1][minKey2]=minValue2
                tempDiv[minKey1]=minValue1+minValue2
            elif minKey1[0]!='G' and minKey2[0]=='G':
                tempDict[minKey2][minKey1]=minValue1
                tempDiv[minKey2]=minValue1+minValue2
            elif minKey1[0]=='G' and minKey2[0]=='G':
                if minKey1[1]<minKey2[1]:
                    tempDict[minKey1].update(tempDict[minKey2])
                    tempDict[minKey2].clear()
                    tempDiv[minKey1]=minValue1+minValue2
                    
                else:
                    tempDict[minKey2].update(tempDict[minKey1])
                    tempDict[minKey1].clear()
                    tempDiv[minKey2]=minValue1+minValue2
                
            #print "**********************************"
            #print tempDict
            #print tempDiv
            #print "**********************************"
        #print tempDict
        #print tempDiv
        for kk,vv in tempDiv.items():##b1/g1:freq
            if kk[0]!='G':
                fFlag=False
                for tempk,tempv in tempDict.items():
                    if len(tempv)==0:
                        fFlag=True
                        break
                if fFlag:
                    tempDict[tempk][kk]=vv
                    tempDiv[tempk]=vv
                
            
        #print tempDict
        print "******groups******"
        for kkk,vvv in tempDict.items():
            print '%s:%s ===%s'%(kkk,vvv,tempDiv[kkk])
        print "******************"
        #{G1:{B1:fre,B2:fre},G2:{B3:fre,B4:fre,B5:fre}}
           
        for k,v in tempDict.items():
                tempDict[k]=[]
                tempDict[k].append(v.keys())
                
        #{G1:[[B1,B2]],G2:[B3,B4,B5]}
        #print tempDict
        #return tempDict
        #{G1:[[B1,B2],Tracers],G2:[[B3,B4,B5],trackes]}
        self.clubs[softId]=tempDict
        #{S1:{G1:[[B1,B2],Tracers],G2:[[B3,B4,B5],trackes]}}             
            
    def findMinFreq(self,dict):
        minKey=min(dict,key=lambda x:dict[x])
        return minKey
    
    def initSoftInfo(self,softAddrInfoConfig):
        #self.software=softInfoConfig
        #print self.software
        for softId in self.software.keys():
            blocks=self.software[softId]
            self.conClubFlag[softId]=False
            self.isClubFlag[softId]=False
            #print "****************"
            #print softId,blocks
            #print "****************"          
            blockdict={}
            for blockId in blocks:                    
                blockdict[blockId]=[0,softAddrInfoConfig[softId][blockId]]
            self.blockInfo[softId]=blockdict
            

        #print "\n******Software information******"
        #for sid,bks in self.blockInfo.items():
        #    print "%s : %s\n"%(sid,bks)
            #print 
        #print self.blockInfo
        #print "******************"
        #print self.conClubFlag
        #print self.isClubFlag


    def isClub(self,softId):

        return self.isClubFlag[softId]
    
    
    
 
        #
    def conClub(self,softId):
        #{S1:{G1:[[B1,B2],Tracers],G2:[[B3,B4,B5],trackes]}}
        if len(self.trackAddr)!=10:
            time.sleep(2)
        tmpDict=self.clubs[softId]
        #{G1:[[B1,B2],Tracers],G2:[[B3,B4,B5],trackes]}
        i=0
        
        for eachv in tmpDict.values():
            eachv.append(self.trackAddr[i])
            
            try:
                
                s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                s.connect(self.trackAddr[i])
            except Exception,e:
                print e
                print "conClubError"
            #[softId]
            cmd='STT'#St login ls Server
            data=[]
            data.append(softId)
            data.append(eachv[0])
            data.append(self.address)
            #print "\n STT ConClub",data
            data=cPickle.dumps(data)
            lens=data.__len__()      
            #'BLD':0:
            sendMes='%s:%d:%s&E#'%(cmd,lens,data)        
            s.send(sendMes)
        
            s.close()
            i+=1

        
        
        #flag=False
        
        #{G1:[[B1,B2],Tracers],G2:[[B3,B4,B5],trackes]}
        #self.conClubFlagLock.acquire()
        self.afterConClub(softId)
        self.isClubFlag[softId]=True####NEED SYNC
        print "***************"
        print self.clubs[softId]
        

    def afterConClub(self,softId):
        
        '''st return the softid to LS when the club is constructed successfully'''
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((self.loginServerAddr,10002))
        #[softId]
        cmd='SRC'#St Return softid which is constructed as a Club
        data=[]
        data.append(softId)
        data.append(self.address)
        data=cPickle.dumps(data)
        lens=data.__len__()      
        #'BLD':0:
        sendMes='%s:%d:%s&E#'%(cmd,lens,data)        
        s.send(sendMes)
        
        s.close()
        
        return
    def reConClub(self,softId):# only when the club has been canceled
        softInfo=self.clubs[softId]
        #groupid:[[blocks],track]
        for v in softInfo.values():
            v=v[1:]
            for trackAdd in v:
                self.reqPeerForReConClub(trackAdd,softId)
                
        self.creatClub(softId)
        for v in softInfo.values():
            v=v[1:]
            for trackAdd in v:
                self.cancelTrack(trackAdd,softId)
                
                
        softInfo=self.clubs[softId]
        for v in softInfo.values():#[[blocks],track]
            blockList=v[0]
            v=v[1:]
            for trackAdd in v:
                self.startTrack(trackAdd,blockList,softId)
        
        
        
        
    def cancelTrack(self,trackAdd,softId):#only when the club need to be canceled
        s = socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((trackAdd,20000))
        mes='CAT:3:CAT&E#'
        s.send(mes)
        rec=s.recv(100)
        if rec=='DONE':
            print "******%s stop as a track:******"%trackAdd
        s.close()
        
    def startTrack(self,trackAdd,blockList,softId):
        s = socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((trackAdd,20002))
        data=[]
        data.append(softId)
        data.append(blockList)
        
        
        data=cPickle.dumps(data)
        lens=data.__len__()
        cmd='SAT'        
        #'BLD':0:
        sendMes='%s:%d:%s&E#'%(cmd,lens,data)        
        self.request.send(sendMes)
        rec=s.recv(100)
        if rec=='DONE':
            print "******%s start as a track:******"%trackAdd
        s.close()
        
    def statFreq(self):
            oldSecTotal=0
        #try:
            record=file(self.filename,'w')
            while not self.serverStopFlag:
                time.sleep(1)
                total=0
                
                for eachv in self.blockInfo.values():
                    for blockInfoList in eachv.values():
                            total+=blockInfoList[0]
                newSecTotal=total-oldSecTotal
                writeSTR="%s,%s\n"%(newSecTotal,time.ctime()[:-5])
                #print writeSTR       
                record.write(writeSTR)
                record.flush()
                oldSecTotal=total
            record.close()
        #print
                
        #except KeyboardInterrupt:
            #print e
        #finally:
            #record.close()
                
            
                    
                
                
                
    def reqPeerForReConClub(self,trackAdd,softId):
        s = socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((trackAdd,20000))
        mes='RCC:3:RCC&E#'
        s.send(mes)
        data=s.recv(4096)
        cmd,length,data=headCheck(data)
        #print cmd,length,data#only for test
        if cmd !='ERR' and length>data.__len__():#still has data
            data=dataComeIn(s,length,data)

        if data[-3:]!='&E#':
            self.request.send('ERR:8:ErrorEnd')
            s.close()
            return
        data=data[:-3]    
        if cmd == 'RRC':
            reqInfo=cPickle.loads(data)
            if reqInfo[0]!=softId:
                return
            peers=reqInfo[1]
            #for each in peers:
                #print each
                
        s.close()        
        

    #def conGroup(self):
        #pass
    def validSoftReq(self,softId,blockId):#check out if the request is valid
        if softId not in self.software.keys():
            return False
        blocks=self.software[softId]
        if blockId not in blocks:
            return False
        else:
            return True
        
        
        
    def loginLSServer(self,data=[]):
        '''loging LoginServer for ST add'''
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.connect((self.loginServerAddr,10002))
        #[softId]
        cmd='SLS'#St login ls Server
        data.append(self.address)
        data=cPickle.dumps(data)
        lens=data.__len__()      
        #'BLD':0:
        sendMes='%s:%d:%s&E#'%(cmd,lens,data)        
        s.send(sendMes)
        
        s.close()

    
    def outInterface(self,softInfoConfig):
        #define={softid:[blockList]}    
        self.software=softInfoConfig
        print "ST Address-->",self.address
        
    def initFreq(self):
        
        #self.conClubFlag['S1']=True
        softId='S3'
        #print "******init S1 freq******"
        #self.blockInfo={sofid:blockid:[freq,blockaddr]}
        blockDict=self.blockInfo[softId]
        
        #{blockid:[ferq,blockaddr]
        for each in blockDict.values():
            each[0]=200
            
        reco=file(self.filename,"a")
        writemessage=str(self.blockInfo['S3'])
        reco.write(writemessage)
        reco.close()
        
        #self.blockInfo[softId]['B1'][0]=1        
        #self.blockInfo[softId]['B2'][0]=2
    
        #for k,v in self.blockInfo['S1'].items():
            #print '%s freq is %d'%(k,v[0])


        #print self.blockInfo
        
        #self.creatClub(softId)
                       

    
class STRH(RawRequestHandler):
    STHeadCmd=['VRS',#VP->ST:Vp Request Software:{softid:blockid}&E#(selfAsServerAdd)&E#
               'REB',#VP->ST:Vp Re Block:{softid,blockid)&E#
               'RWT', #VP->ST:vp Request software.Without be a Track
               'LRC',  #LS->ST:Login server Return construct Club info
               'TRS'
               ]
    def sendData(self,cmd,data):
        data=cPickle.dumps(data)
        lens=data.__len__()
        
        #'BLD':0:
        sendMes='%s:%d:%s&E#'%(cmd,lens,data)        
        self.request.send(sendMes)
        
    def afterConClub(self):
        pass
        
        
    def sendTracker(self,softId,blockId):
    
        pass
    
    def handle(self):
        #self.request.send(self.server.message)
        data = self.request.recv(4096)
        cmd,length,data=headCheck(data)
        #print cmd,length,data#only for test
        if cmd not in self.STHeadCmd:
            self.request.send('ERR:8:ErrorCmd')
            return
        if length>data.__len__():#still has data
            data=dataComeIn(self.request,length,data)
        if data[-3:]!='&E#':
            self.request.send('ERR:8:ErrorEnd')
            return
        data=data[:-3]
            
            
            
            
        if cmd=='VRS':
            #print cmd
            self.cmdVRS(data)
            #print self.server.software
        elif cmd=='REB':
            self.cmdREB(data)
        elif cmd=='RWT':
            self.cmdRWT(data)
        
        elif cmd=='LRC':#Login server Return Club info
            self.cmdLRC(data)
            
        elif cmd=='TRS':#Login server Return Club info
            self.cmdTRS(data)
        
            
        #self.request.send('DONE')#if not done,such as 'refu' etc..
        #print self.request.recv(100)
        #print "*********server block info*********"
        #print self.server.blockInfo
        #print "***********************************"
        
        
    def cmdVRS(self,data):
        ##[softid,{blockid:[]}]&E#

        reqSoft=data
        reqSoft=cPickle.loads(reqSoft)       
        #[softid,{blockid:[]}]
        #ipAddr=self.request.getpeername()[0]
        #reqAddr=(ipAddr,10000)
        #reqAddr=self.request.getpeername()
        reqAddr=reqSoft.pop()
        #print "!!!!!!!!",repr(reqAddr)
        #print "\n******Receive Request From %s******"%reqAddr[0]
        #print "\n******request software list******"
        #print reqSoft[0],reqSoft[1].keys()
        #print "*********************************\n"
        #unusedFlag=True
        softTFlag=False
        
        softId=reqSoft[0]
        #print softId
        reqBlocks=reqSoft[1]####{block1;[],block2:[]}dict
        for blockId in reqBlocks.keys():
            if not self.server.validSoftReq(softId,blockId):
                print '%s,%s,invalid'%(softId,blockId)
                reqSoft[1][blockId].append('E')
                continue
                
                
            self.server.blockInfo[softId][blockId][0] +=1#SYN
            blockAddr=copy.deepcopy(self.server.blockInfo[softId][blockId][1])#SYN
                
            if self.server.isClub(softId)==False:
                #self.server.conClubFlagLock.acquire()
                #if self.server.conClubFlag[softId]==True :
                    #groupD=self.server.conClub(softId,blockId,reqAddr)
                        #groupD=['sid',['bid','bid2']]
                        #self.afterConClub()
                    #if groupD != None:
                        #reqSoft[1][blockId].append('BT')
                            #blockAddr=self.server.blockInfo[softId][blockId][1]
                        #reqSoft[1][blockId].append(blockAddr)
                        #reqSoft[1][blockId].append(groupD)
                        #reqSoft[1][blockId].append(self.server.address)#the default address for VP as a track
                        #self.address is (selfIp,10000)
                        #unusedFlag=False
                    #else:
                        reqSoft[1][blockId].append('B')
                        #blockAddr=self.server.blockInfo[softId][blockId][1]#SYN
                        reqSoft[1][blockId].append(blockAddr)
                            
                            
                #else:
                    #reqSoft[1][blockId].append('B')
                        #blockAddr=self.server.blockInfo[softId][blockId][1]#SYN
                    #reqSoft[1][blockId].append(blockAddr)

            else:
                reqSoft[1][blockId].append('T')
                trackAddr=self.server.getBlockTrack(softId,blockId)
                reqSoft[1][blockId].append(trackAddr)
                softTFlag=True
                
                
        if softTFlag:
            reqSoft.append(self.server.getSoftTrack(softId))
        #print "--->>>Return Information<<<---"
        #print reqSoft
        #print "******Request Done******"
        #print 
        self.sendData('BLD',reqSoft)#Re Vp request Software

        return
    def cmdREB(self,data):#if the tracker give the staddress to other vp requeser
        ###[softid,{blockid:[]}]

        reqSoft=data
        reqSoft=cPickle.loads(reqSoft) 
        #reqAddr=reqSoft.pop()      
        #{'S1':[block1],'S2':[block2,block3]}
        #print reqSoft#only for test

        softId=reqSoft[0]
        reqBlocks=reqSoft[1]####{block1;[],block2:[]}dict
        for blockId in reqBlocks.keys():
            if not self.server.validSoftReq(softId,blockId):
                print '%s,%s,invalid'%(softId,blockId)
                reqSoft[1][blockId].append('E')
                continue
            self.server.blockInfo[softId][blockId][0] +=1#SYN
            blockAddr=copy.deepcopy(self.server.blockInfo[softId][blockId][1])#SYN

            reqSoft[1][blockId].append('B')
            reqSoft[1][blockId].append(blockAddr)
        self.sendData('BLD',reqSoft)   # 
        
        #print "--->>>Return Information<<<---"
        #print reqSoft
        #print "******Request Done******"
        #print 
       
        return
    
    
    def cmdRWT(self,data):
        ##{softid:[blockid]}&E#

        reqSoft=cPickle.loads(data) 
        reqAddr=reqSoft.pop()      
        
        #reqAddr=cPickle.loads(reqAddr)
        #print reqSoft,reqAddr#only for test
        softTFlag=False
        softId=reqSoft[0]
        reqBlocks=reqSoft[1]####{block1;[],block2:[]}dict
        for blockId in reqBlocks.keys():
            if not self.server.validSoftReq(softId,blockId):
                print '%s,%s,invalid'%(softId,blockId)
                reqSoft[1][blockId].append('E')
                continue
                
                #tempsha=self.server.getSoftHash(softId,blockId)
                #print tempsha             
                #self.server.softAttr[tempsha][0]+=1 ###need syn
                
            self.server.blockInfo[softId][blockId][0] +=1#SYN
            blockAddr=self.server.blockInfo[softId][blockId][1]#SYN
                
            if self.server.isClub(softId)==False:
                reqSoft[1][blockId].append('B')
                #blockAddr=self.server.blockInfo[softId][blockId][1]#SYN
                reqSoft[1][blockId].append(blockAddr)

            else:
                reqSoft[1][blockId].append('T')
                trackAddr=self.server.getBlockTrack(softId,blockId)
                reqSoft[1][blockId].append(trackAddr)
                softTFlag=True
                
        if softTFlag:
            reqSoft.append(self.server.getSoftTrack(softId))

        #print "--->>>Return Information<<<---"
        #print reqSoft
        #print "******Request Done******"
        #print 
        
        self.sendData('BLD',reqSoft)
        return
    
    
    
    def cmdLRC(self,data):
        
        
        conClubSoftId=cPickle.loads(data)
        
        
        
        self.server.conClubFlag[conClubSoftId]=True
        self.server.creatClub(conClubSoftId)
        
        self.server.conClub(conClubSoftId)
        
   
        return
        
    def cmdTRS(self,data):
        
        trackAddr=cPickle.loads(data)
        print trackAddr
        self.server.trackAddr.append(trackAddr.pop())
        #print self.server.trackAddr

    def finish(self):

        self.request.close()

def getConfig(url="cn21.hp.act.buaa.edu.cn/expcfg/stcfg.yaml"):
    try:
        uuid1=str(uuid.uuid1())
        filename="/root/p2pexp/Server/cfg/stcfg-%s.yaml"%uuid1
        urllib.urlretrieve(url,filename)
        return filename
        
    except Exception,e:
        print "can't get config file",e    

def analysisConfig(filename):

        config=yaml.load(file(filename,"r"))
            
        softInfoConfig={}
        softAddrInfoConfig={}

        loginServerAddrConfig=config['lsConfig']['lsAddr']
        
        for softId,blockInfo in config['soft'].items():
            softInfoConfig[softId]=[]

            softAddrInfoConfig[softId]={}
            #print range(blockInfo['blockNum'])

            for i in range(blockInfo['blockNum']):
                blockId="B%s"%i
                
                #print softInfoConfig[softId]
                softInfoConfig[softId].append(blockId)
                #print softInfoConfig[softId]
                addInfo="%sB%s%s"%(softId,i,blockInfo['blockAddr'])
                softAddrInfoConfig[softId][blockId]=addInfo
        gNum=config['groupNum']
        groupNum=int(gNum)
        #$stPort=config['']
        return softInfoConfig,softAddrInfoConfig,loginServerAddrConfig,groupNum
        
        
    
def __runServer(url,STPort=3000):
 

    filename=getConfig(url)
    
    
    retv=analysisConfig(filename)
    softInfoConfig=retv[0]
    softAddrInfoConfig=retv[1]
    loginServerAddrConfig=retv[2]
    groupNum=retv[3]
    #print softInfoConfig
    #print softAddrInfoConfig
        
    
    
    
    
    server = STServer(('', STPort), STRH,loginServerAddrConfig,groupNum)

    try:
        server.outInterface(softInfoConfig)

        try:
            server.loginLSServer()
        except Exception,e:
            print e

        server.initSoftInfo(softAddrInfoConfig)
        #server.crazyTest()
        
        t=Thread(target=server.statFreq)
        t.start()
        
        #server.isClub('S2','B1')
        server.startServer()
    except KeyboardInterrupt:
        print "ST exit......"
    finally:
        
        server.serverStopFlag=True
        
        
 
        


if __name__ == '__main__':
    STPort=int(sys.argv[1])
    url=sys.argv[2]
    
    try:
        #STPort=3000
        __runServer(url,STPort)
    except Exception,e:
        print e
        raw_input("something may be wrong")
