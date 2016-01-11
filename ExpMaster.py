'''
Created on 2010-9-8

@author: amraam
'''

import sys
import threading, socket, time
import yaml

usage = '''
python ExpMaster.py [cfg_file]
'''

# worker thread
class MachineDealer(threading.Thread):
    def __init__(self, name, job, cmd):
        threading.Thread.__init__(self, name = name)
        self.job = job
        self.cmd = cmd
        pass
    
    def run(self):
        # do your job
        self.CMD_TABLE = {
        'start':self.run_exp,
        'stop':self.end_exp,
        'shutdown':self.shutdownn_daemon
        }
        print "%s: my job: %s\n" % (self.name,self.job)
        self.host,self.port = self.job['target'].split(':')
        self.port = int(self.port)
        print self.host,self.port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host,self.port))
        self.CMD_TABLE[self.cmd]()
        self.sock.close()
        
    def shutdownn_daemon(self):
        print 'sending Shutdown'
        self.sock.send('Shutdown')
        print self.sock.recv(1024)
        
    def run_exp(self):
        self.sock.send('Run')
        self.sock.recv(1024)
        for name,cmd in self.job['exec'].items():
            self.sock.send(name)
            print 'sending ',name
            self.sock.recv(1024)
            self.sock.send(cmd)
            print 'sending ',cmd
            self.sock.recv(1024)
        self.sock.send('EOF')
        print 'sending EOF'
        
    def end_exp(self):
        self.sock.send('End')
    
class ExpMaster():
    def __init__(self, cfgFile, cmd):
        self.config = ExpCfg(cfgFile)
        self.cmd = cmd
        self.dealers = {}
        
    def start(self):
        # create dealers
        for name,job in self.config.getJobs().items():
            newDealer = MachineDealer(name,job,self.cmd)
            self.dealers[name] = newDealer
        
        # start working
        for dealer in self.dealers.values():
            dealer.start()

# config class
class ExpCfg():
    def __init__(self, cfgFile):
        self.cfgFile = cfgFile
        self.jobs = {}
        self.__parseCfg()
    
    def __parseCfg(self):
        # parse exp config and generate jobs
        config = yaml.load(file(cfgFile,'r'))
        #print 'config: %s' % config
        for machine_name,job in config['machines'].items():
            #print 'this job: %s' % job
            self.jobs[machine_name] = {"name":"default","target":"default","exec":{}}
            newJob = self.jobs[machine_name]
            newJob['name'] = machine_name
            newJob['target'] = job['info']['address']
            print newJob['target']
            for exec_name,exec_item in job['exec'].items():
                newJob['exec'][exec_name] = exec_item
        print 'jobs: %s' % self.jobs
    
    def getJobs(self):
        return self.jobs
    
def __runExp(cfgFile,cmd):
    expMaster = ExpMaster(cfgFile,cmd)
    expMaster.start()

if __name__ == "__main__":
    try:
        argc = len(sys.argv)
        if argc == 2:
            cfgFile = sys.argv[1]
        elif argc == 1:   # just for test
            cfgFile = 'ExpCfg.sample.yaml'
        else:
            raise 'parameter number error'
        
        CMD_TABLE = ('start','stop','shutdown')
        
        print 'what to do?'
        for i in range(len(CMD_TABLE)):
            print '%d\t%s'%(i+1,CMD_TABLE[i])
        select = int(raw_input('enter a number:'))
        cmd = CMD_TABLE[select-1]
        
        #print cmd
        
        __runExp(cfgFile,cmd)
    except Exception, e:
        print e
        print usage
