'''
File:
        pyinsteon.py

Description:
        Insteon Home Automation Protocol library for Python (Smarthome 2412N, 2412S, 2412U)
        
        For more information regarding the technical details of the PLM:
                http://www.smarthome.com/manuals/2412sdevguide.pdf

Author(s): 
         Jason Sharpee <jason@sharpee.com>  http://www.sharpee.com

        Based loosely on the Insteon_PLM.pm code:
        -       Expanded by Gregg Liming <gregg@limings.net>

License:
    This free software is licensed under the terms of the GNU public license, Version 1     

Usage:
    - Instantiate PyInsteon by passing in an interface
    - Call its methods
    - ?
    - Profit

    example: 
    pyI = PyInsteon(TCP("192.168.1.1","9761"))
    pyI.getVersion()
    select.select([],[],[])   

Notes:
    - Integrate Mahmul dict's and event dispatch
    - Read Style Guide @: http://www.python.org/dev/peps/pep-0008/

Created on Mar 26, 2011
'''
import socket
import threading
import binascii
import select

HOST='192.168.13.146'
PORT=9761

#PLM Serial Commands
class PLM_COMMANDS:
    insteon_received        ='0250'
    insteon_ext_received    ='0251'
    x10_received            ='0252'
    all_link_complete       ='0253'
    plm_button_event        ='0254'
    user_user_reset         ='0255'
    all_link_clean_failed   ='0256'
    all_link_record         ='0257'
    all_link_clean_status   ='0258'
    plm_info                ='0260'
    all_link_send           ='0261'
    insteon_send            ='0262'
    insteon_ext_send        ='0262'
    x10_send                ='0263'
    all_link_start          ='0264'
    all_link_cancel         ='0265'
    plm_reset               ='0267'
    all_link_first_rec      ='0269'
    all_link_next_rec       ='026a'
    plm_set_config          ='026b'
    plm_led_on              ='026d'
    plm_led_off             ='026e'
    all_link_manage_rec     ='026f'
    insteon_nak             ='0270'
    insteon_ack             ='0271'
    rf_sleep                ='0272'
    plm_get_config          ='0273'

''' mahmul @ #python
import pprint
keys = ('insteon_received',
        'insteon_ext_received',
        'x10_received',
        'all_link_complete',
        'plm_button_event',
        'user_user_reset',
        'all_link_clean_failed',
        'all_link_record',
        'all_link_clean_status',
        'plm_info',
        'all_link_send',
        'insteon_send',
        'insteon_ext_send',
        'x10_send',
        'all_link_start',
        'all_link_cancel',
        'plm_reset',
        'all_link_first_rec',
        'all_link_next_rec',
        'plm_set_config',
        'plm_led_on',
        'plm_led_off',
        'all_link_manage_rec',
        'insteon_nak',
        'insteon_ack',
        'rf_sleep',
        'plm_get_config')

commands = dict(zip(xrange(0x250, 0x273), keys))
pprint.pprint(commands)

def rf_sleep(*args):
    print 'called rf_sleep with', args

def get_config(*args):
    print 'called get_config with', args
    print 'calling rf_sleep...'
    rf_sleep(args)

def dispatcher(datum):
    callback = {'plm_get_config': get_config,
                'rf_sleep': rf_sleep}.get(commands[datum])
    if callback:
        callback(1)

dispatcher(0x26a)
dispatcher(0x259)

'''
class InsteonCommand:
    #Commands in Hex
    on=                '11'

class Interface(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        
    def _send(self,Data):
        return None

    def onReceive(self, callback):
        self.c = callback
        return None    
   
class TCP(Interface):
    def __init__(self, host, port):
        super(TCP, self).__init__(host,port)        
        self.__s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print"connect"
        self.__s.connect((host, port))
        self.start()

        
    def send(self, dataString):
        print "Data Sent=>" + dataString
        data = binascii.unhexlify(dataString)
        self.__s.send(data) 
        return None
    
    def run(self):
        self._handle_receive()
        

        
    def _handle_receive(self):
        while 1:
            data = self.__s.recv(1024)
            self.c(data)
        self.__s.close()
        
class Serial(Interface):
    def __init__(self, port, speed):
        return None
    pass
    
class USB(Interface): 
    pass
    def __init__(self, device):
        return None

    
class HAProtocol(object):
    "Base protocol interface"
    def __init__(self, interface):
        pass
    
class PyInsteon(HAProtocol):
    "The Main event"
    def __init__(self, interface):
        super(PyInsteon, self).__init__(interface)        
        self.__i = interface
        self.__i.onReceive(self._handle_received)
        self.__dataReceived = threading.Event()
        self.__dataReceived.clear()
        self.__callback_x10 = None
        self.__callback_insteon = None
        return None
    
    def _handle_received(self,data):
        "Decode packet"
        dataHex = binascii.hexlify(data)
        print "Data Received=>" + dataHex
        #SwitchLinc 025019057b000001cb1100 025019057b16f9ec411101
        #X10 02520d00 02520380
        #Mystery packet from PLM -- Data Received=>024a00
        plm_command = dataHex[0:4]   
        #<mahmul> zonyl: you know, you could use a dispatch dict and functions instead those if clauses
        if PLM_COMMANDS.plm_info == plm_command:
            self.__version=dataHex[14:16]
        elif PLM_COMMANDS.insteon_received == plm_command or PLM_COMMANDS.insteon_ext_received == plm_command:
            fromAddress =       dataHex[4:6] + "." + dataHex[6:8] + "." +  dataHex[8:10] 
            toAddress =         dataHex[10:12] + "." + dataHex[12:14] + "." +  dataHex[14:16]
            group =             dataHex[14:16] # overlapped into toAddress if a group call is made
#            messageType =       (int(dataHex[16:18],16) & 0b11100000) >> 5 #3 MSB
            messageDirect =     ((int(dataHex[16:18],16) & 0b11100000) >> 5)==0
            messageAcknowledge =((int(dataHex[16:18],16) & 0b00100000) >> 5)>0
            messageGroup =      ((int(dataHex[16:18],16) & 0b01000000) >> 6)>0
            messageBroadcast =  ((int(dataHex[16:18],16) & 0b10000000) >> 7)>0
            extended =          ((int(dataHex[16:18],16) & 0b00010000) >> 4)>0 #4th MSB
            hopsLeft =          (int(dataHex[16:18],16) & 0b00001100) >> 2 #3-2nd MSB
            hopsMax =           (int(dataHex[16:18],16) & 0b00000011)  #0-1 MSB
            # could have also used ord(binascii.unhexlify(dataHex[16:17])) & 0b11100000
            command1=       dataHex[18:20]
            command2=       dataHex[20:22]
            print "Insteon=>From=>%s To=>%s Group=> %s MessageD=>%s MB=>%s MG=>%s MA=>%s Extended=>%s HopsLeft=>%s HopsMax=>%s Command1=>%s Command2=>%s" % \
                (fromAddress, toAddress, group, messageDirect, messageBroadcast, messageGroup, messageAcknowledge, extended, hopsLeft, hopsMax, command1, command2)
            if self.__callback_insteon != None:
                self.__callback_insteon(fromAddress, toAddress, group, messageDirect, messageBroadcast, messageGroup, messageAcknowledge, extended, hopsLeft, hopsMax, command1, command2)
            pass
        elif PLM_COMMANDS.x10_received == plm_command:
            houseCode =     (int(dataHex[4:6],16) & 0b11110000) >> 4 
            keyCode =       (int(dataHex[4:6],16) & 0b00001111)
            unitCode =      (int(dataHex[6:8],16) & 0b11110000) >> 4
            commandCode =   (int(dataHex[6:8],16) & 0b00001111)
            print "X10=>House=>%s Key=>%s Unit=>%s Command=>%s" % (houseCode, keyCode, unitCode, commandCode)
            if self.__callback_x10 != None:
                self.__calback_x10(houseCode, keyCode, unitCode, commandCode)
            pass
            
        
        self.__dataReceived.set()
        

    def getVersion(self):
        self.__i.send(PLM_COMMANDS.plm_info)
        self.__dataReceived.wait(1000)
        return self.__version

    def _send(self,data):
        self.__dataReceived.clear()
        self.__i.send(data)

    def sendInsteon(self, fromAddress, toAddress, group, messageDirect, messageBroadcast, messageGroup, messageAcknowledge, extended, hopsLeft, hopsMax, command1, command2, data):
        messageType=0
        #todo make this really work
        if extended==False:
            dataString  = PLM_COMMANDS.insteon_send
        else:
            dataString = PLM_COMMANDS.insteon_ext_send
        dataString += fromAddress[0:2] + fromAddress[3:5] + fromAddress[6:7]
        dataString += toAddress[0:2] + toAddress[3:5] + toAddress[6:7]
        if messageDirect:
            messageType=0
        if messageBroadcast:
            pass
        if messageAcknowledge:
            pass
        if messageGroup:
            pass
        if extended:
            pass
        dataString += hopsLeft
        dataString += hopsMax
        dataString += command1
        dataString += command2
        dataString += data
        #crc goes here
        self._send(dataString)
        
    def sendX10(self, houseCode, keyCode, unitCode, commandCode):
        dataString = PLM_COMMANDS.x10_send
        #todo bit wrangling
        dataString+= binascii.hexlify(int(houseCode,16))
        dataString+= binascii.hexlify(int(keyCode,16))
        dataString+= binascii.hexlify(int(unitCode,16))
        dataString+= binascii.hexlify(int(commandCode,16))
        self._send(dataString)
        
    def onReceivedX10(self, callback):
        self.__callback_x10=callback
        return
    
    def onReceivedInsteon(self, callback):
        self.__callback_insteon=callback
        return
    

if __name__ == "__main__":
    pyI = PyInsteon(TCP(HOST, PORT))
    pyI.getVersion()
    select.select([],[],[])
    
    
    