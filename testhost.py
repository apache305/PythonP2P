from HeadCheck import headCheck,dataComeIn
from socket import *
import time
import cPickle

HOST = '192.168.1.202'    # The remote host
PORT = 10000            # The same port as used by the server
s = socket(AF_INET,SOCK_STREAM)
try:
    s.connect((HOST,PORT))
    print "****************req data format***************************"
    req=['S1',{'B1':[],'B7':[]}]
    req=cPickle.dumps(req)
    dat='%s&E#'%req
    #print dat
    lent=dat.__len__()
    #print lent
    print "**********cmd=VRS  VP->ST vp request soft*****************"
    mes='VRS:%d:%s'%(lent,dat)#################################
    s.send(mes)
    
    data=s.recv(4096)
    #print data
    cmd,length,data=headCheck(data)
    #print cmd,length,data#only for test
    print cmd
    if cmd !='ERR' and length>data.__len__():#still has data
        data=dataComeIn(s,length,data)
    if cmd=='BLD':
        dic=cPickle.loads(data)
        print dic
        print len(dic)
        
    if s.recv(4096)=='DONE':
        print 'done'
     
    s.send('DONE')    
    print 'end'
    time.sleep(1)
    s.close()
    str=raw_input('next string:')
    
    
    
    
    s = socket(AF_INET,SOCK_STREAM)
   
    s.connect((HOST,PORT))

    
    req=['S1',{'B1':[],'B7':[]}]
    req=cPickle.dumps(req)

    lent=req.__len__()
    print lent
    
    print "**********cmd=REB VP->ST Request block Add*****************"
    mes='REB:%d:%s&E#'%(lent,req)
    s.send(mes)
    
    data=s.recv(4096)
    #print data
    cmd,length,data=headCheck(data)
    #print cmd,length,data#only for test
    if cmd !='ERR' and length>data.__len__():#still has data
        data=dataComeIn(s,length,data)
    if cmd=='BLD':
        dic=cPickle.loads(data)
        print dic
        print len(dic)
    if cmd=='RVP':
        dic=cPickle.loads(data)
        print dic
        print len(dic)
    
    
    
    
    
    if s.recv(4096)=='DONE':
        print 'done'
    
            
        
    s.send('DONE')    
    print 'end'
    time.sleep(1)
    s.close()
    str=raw_input('next string:')
    
    
    s = socket(AF_INET,SOCK_STREAM)
   
    s.connect((HOST,20000))

    
    req=['S1',{'B1':[],'B7':[]}]
    req=cPickle.dumps(req)

    lent=req.__len__()
    print lent
    
    print "**********cmd=REB VP->VP Request block Add *****************"
    mes='REB:%d:%s&E#'%(lent,req)
    s.send(mes)
    
    data=s.recv(4096)
    #print data
    cmd,length,data=headCheck(data)
    #print cmd,length,data#only for test
    if cmd !='ERR' and length>data.__len__():#still has data
        data=dataComeIn(s,length,data)
    if cmd=='BLD':
        dic=cPickle.loads(data)
        print dic
        print len(dic)
    if cmd=='RVP':
        dic=cPickle.loads(data)
        print dic
        print len(dic)
    
    
    
    
    
    if s.recv(4096)=='DONE':
        print 'done'
    
            
        
    s.send('DONE')    
    print 'end'
    time.sleep(1)
    s.close()
    
    str=raw_input('next string:')
    
    
    
    
    s = socket(AF_INET,SOCK_STREAM)
   
    s.connect((HOST,20000))

    
    req=['S1',{'B1':[],'B7':[]}]
    req=cPickle.dumps(req)

    lent=req.__len__()
    print lent
    
    print "**********cmd=VRP:VP->VPTrack*****************"
    mes='VRP:%d:%s&E#'%(lent,req)
    s.send(mes)
    
    data=s.recv(4096)
    #print data
    cmd,length,data=headCheck(data)
    #print cmd,length,data#only for test
    if cmd !='ERR' and length>data.__len__():#still has data
        data=dataComeIn(s,length,data)
    if cmd=='BLD':
        dic=cPickle.loads(data)
        print dic
        print len(dic)
    if cmd=='RVP':
        dic=cPickle.loads(data)
        print dic
        print len(dic)
    
    
    
    
    
    if s.recv(4096)=='DONE':
        print 'done'
    
            
        
    s.send('DONE')    
    print 'end'
    time.sleep(1)
    s.close()
    str=raw_input('next string:')
    
    
    
    s = socket(AF_INET,SOCK_STREAM)
   
    s.connect((HOST,20000))

    
    
    print "**********cmd=RCC:VP->ST*****************"
    mes='RRC:3:RRC&E#'
    s.send(mes)
    
    data=s.recv(4096)
    #print data
    cmd,length,data=headCheck(data)
    #print cmd,length,data#only for test
    if cmd !='ERR' and length>data.__len__():#still has data
        data=dataComeIn(s,length,data)
    if cmd=='BLD':
        dic=cPickle.loads(data)
        print dic
        print len(dic)
    if cmd=='RVP':
        dic=cPickle.loads(data)
        print dic
        print len(dic)
    
    
    
    
    
    if s.recv(4096)=='DONE':
        print 'done'
    
            
        
    s.send('DONE')    
    print 'end'
    time.sleep(1)
    s.close()
    
    
    
    
    
except Exception,e:
    print e
    raw_input('..')


