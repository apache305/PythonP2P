'''
Created on 2010-9-8

@author: amraam
'''

import sys
import thread
import subprocess
import shlex
import SocketServer

import BasicServer

usage = '''
nothing yet...
'''
DAEMON = None

class SafePopen(subprocess.Popen):
    def safe_kill(self):
        self.kill()
        self.wait()

class ExpHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        print 'handling: ',self.request.getpeername()
        global DAEMON
        self.daemon = DAEMON
        # cmd list
        self.CMD_TABLE = {
        'Run':self.run_exp,
        'End':self.end_exp,
        'Shutdown':self.shutdown_daemon
        }
        # handle request
        msg = self.request.recv(4096)
        print 'cmd: ',msg
        if msg in self.CMD_TABLE.keys():
            self.request.send('OK')
            self.CMD_TABLE[msg]()
        else:
            self.request.send('Err CMD')
            
    def shutdown_daemon(self):
        print 'daemon shutting down...'
        self.server.shutdown()
        
    def run_exp(self):
        print 'run an exp'
        self.processes = {}
        self.cmds = {}
        
        # receive cmds
        data = self.request.recv(4096)
        print data
        while not data == 'EOF':
            name = data
            print name
            self.request.send('OK')
            cmd = self.request.recv(4096)
            print cmd
            self.cmds[name] = cmd
            #self.exec_cmd(name,cmd)
            self.request.send('OK')
            data = self.request.recv(4096)
            
        # exec cmds
        for name,cmd in self.cmds.items():
            thread.start_new(self.exec_cmd,(name, cmd))
        
        print self.daemon.procs
        
    def end_exp(self):
        print 'end current exp'
        for name,proc in self.daemon.procs.items():
            try:
                # do not kill proc that named with 'VP'
                #if name[:2].upper() != 'VP':
                    proc.safe_kill()
                    
            except Exception, e:
                print e
            finally:
                del self.daemon.procs[name]
        print 'Proc:',self.daemon.procs
        
    def exec_cmd(self, name, cmd):
        try:
            print name,cmd
            # delay run
            import time
            type = name[:2].upper()
            if type == 'ST':
                time.sleep(2)
            elif type == 'VP':
                time.sleep(7)
            elif type == 'TR':
                time.sleep(5)
                
            new_proc = SafePopen(shlex.split(cmd),close_fds=True)
            self.daemon.procs[name] = new_proc
        except Exception, e:
            print e

# exp daemon class
class ExpDaemon(BasicServer.RawServer):
    def __init__(self, server_address):
        BasicServer.RawServer.__init__(self, server_address, ExpHandler)
        self.procs = {}
        
if __name__ == "__main__":
    try:
        if len(sys.argv) == 1:
            port = 12345
        else:
            port = int(sys.argv[1])
        
        DAEMON = expDaemon = ExpDaemon(('',port))
        expDaemon.startServer()
        
    except Exception, e:
        print e
        print usage