import threading

class SyncDict():
    def __init__(self):
        self.__dict = {}
        self.mutex = threading.Lock()
        
    def __setitem__(self, key, item):
        self.mutex.acquire()
        self.__dict[key] = item
        self.mutex.release()
        
    def __getitem__(self, key):
        return self.__dict[key]
    
    def has_key(self, key):
        return self.__dict.has_key(key)
    
    def pop(self, key):
        self.mutex.acquire()
        ret = self.__dict.pop(key)
        self.mutex.release()
        return ret
    
    def count(self):
        return len(self.__dict)
    
    def copy(self):
        return self.__dict.items()
    #def __str__(self):
        

class SyncList():
    pass



if __name__=='__main__':
    syncdict=SyncDict()
    syncdict['S1']={}
    syncdict['S2']={}
    syncdict['S1']['B1']='b1'
    syncdict['S1']['B2']='b2'
    print syncdict
    