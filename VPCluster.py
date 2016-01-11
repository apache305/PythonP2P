# sys import
import sys
import threading

import urllib
import yaml
import time,random

import uuid




# custom import
from VPServer import VProcessNode

usage = '''
usage: python2.6 VPCluster.py vpnum lifetime frequency minport cfg_url
'''

# a container holding many VPs
class VPCluster():
    def __init__(self,portMgr,VPnum,lifeTime,freq,LSaddr,VPReqList):
        self.uuid=portMgr.uuid1
        self.VPs = []
        self.portMgr = portMgr
        self.VPnum = VPnum
        self.LSaddr = LSaddr
        self.lifeTime=lifeTime
        self.freq = freq
        self.recordFileName="/p2pexp-output/VC-%s.csv"%self.uuid
        self.VPReqList=VPReqList
        self.recordFile=file(self.recordFileName,'w')

        
    def createVPs(self):

        for i in range(self.VPnum):
            newVP = VProcessNode(self.portMgr,self.lifeTime,self.LSaddr,self.recordFile,self.VPReqList)
            self.VPs.append(newVP)
    
    def run(self):
        self.createVPs()
        # arrive interval -> exponential distribution
        for vp in self.VPs:
            vp.start()
            time.sleep(random.expovariate(self.freq))

# provide ports for VPs. ports start from minPort
class PortManager():
    def __init__(self, minPort,vpNum):
        self.minPort = minPort
        self.lock = threading.RLock()
        self.curPort = minPort
        self.vpNum=vpNum
        self.vpNumLock=threading.RLock()
        self.uuid1=str(uuid.uuid1())
        self.filename="/endflag/%s.flag"%self.uuid1
        
    def getPort(self):
        self.lock.acquire()
        ret = self.curPort
        self.curPort += 1
        self.lock.release()
        return ret
    def vpExit(self):
        self.vpNumLock.acquire()
        self.vpNum-=1
        print 'still running: ',self.vpNum
        if self.vpNum==0:
            endFlag=file(self.filename,"w")
            endFlag.write("end......")
            endFlag.close()
        self.vpNumLock.release()
    
def getConfig(url="cn21.hp.act.buaa.edu.cn/expcfg/vpccfg.yaml"):
    try:
        uuid1=str(uuid.uuid1())
        filename="/root/p2pexp/Server/cfg/vpccfg-%s.yaml"%uuid1
        urllib.urlretrieve(url,filename)
        return filename
        
    except Exception,e:
        print "can't get config file",e  
def analysisConfig(filename):

        config=yaml.load(file(filename,"r"))
        loginServerAddrConfig=config['lsConfig']['lsAddr']
        VPReqList=config['seqList']
#        VPArriveSeq = config['arriveSeq']
        return loginServerAddrConfig,VPReqList
            
def __runVPCluster(VPnum, lifeTime,freq,minPort, LSaddr,VPReqList):
    portMgr = PortManager(minPort,VPnum)
    vpCluster = VPCluster(portMgr,VPnum,lifeTime,freq,LSaddr,VPReqList)
    vpCluster.run()

if __name__ == "__main__":
    try:
        VPnum = int(sys.argv[1])
        lifeTime= int(sys.argv[2])
        freq = float(sys.argv[3])
        minPort = int(sys.argv[4])
        #LSaddr = sys.argv[4]
        url=sys.argv[5]
        filename=getConfig(url)
        retv=analysisConfig(filename)
        LSaddr=retv[0]
        VPReqList=retv[1]
        
        
               
        __runVPCluster(VPnum,lifeTime,freq,minPort,LSaddr,VPReqList)
        
        
    except Exception, e:
        print e
        print usage
