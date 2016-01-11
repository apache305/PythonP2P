
#protocol={'SRQ':1,#ST->VP, St ReQuery:len:(VPTadd)&E#
#          'SRD':2,#ST->VP, St ReDiret:len:(STadd)&E#
#          'SAF':3,#ST->VP, St AFfirm:len:{softId:blockId}&E#
#          'VRB':4,#VP->VP, Vp Request Block:len:{softId:blockId}&E#
#          'LAS':5,#LS->VP, Loginserver AnSwer:len:(STadd)&E#
#          'VRP':6,#VP->VP, Vp Request Peerinfo:len:{softId:blockId}&E#
#          'BLD':7,#BLock Data:0:blockdata&E#
#          'DON':8,#block transport DONe
#          'ERR':-1,#ERRor message
#          }
          


def headCheck(data):#first layer analysis
    #print data
    cmd=data[:3]
    data=data[4:]
    pos=data.find(":")
    length=int(data[:pos])
    data=data[pos+1:]
    return [cmd,length,data]
    



def dataComeIn(sock,length,data):
    while length>data.__len__():
        temp=sock.recv(4096)
        data=data+temp#
    return data

