############################################
#this file is used to produce random request sequence.

import random
import time
import yaml
import sys



def mkSeq(softId,blockNum,seqLength,max):
    seq=[]
    seq.append(softId)
    while seqLength!= 0:
      seqLength-=1
      blockId=random.randint(0,blockNum-1)#blockNum=5,blockid only in [0,1,2,3,4] 
      blockInfo='B%s'%blockId
      waitTime=random.uniform(0,max)
      seq.append(blockId)
      seq.append(waitTime)
    seq.append('EOF')
    return seq

def getSeq(len):
    
    config=yaml.load(file("lscfg.yaml","r"))


    softBasicInfo={}
        
    for softId,blockInfo in config['soft'].items():
       
        softBasicInfo[softId]=blockInfo['blockNum']

    reqList=[]
    for softid,blocknum in softBasicInfo.items():
       req=mkSeq(softid,blocknum,len,10)
       reqList.append(req)
    return reqList

if __name__ =="__main__":
    len=int(sys.argv[1])
    
    l=getSeq(len)
    #for a in l:
        #print a
    a=file("vpccfg.yaml",'a')
    seq={"seqList":l[0]}
    yaml.dump(seq,a)
    a.close()

    
    



  
      
    
   
