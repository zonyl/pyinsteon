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


class Interface(threading.Thread):
#class Interface:
    
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        
    def send(self,Data):
        return None

    def onReceive(self, callback):
        self.c = callback
        return None    
   
class TCP(Interface):
    def __init__(self, host, port):
 #       threading.Thread.__init__(self)
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
        self.__handle_receive()
        

        
    def __handle_receive(self):
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

class MessageTypes:
    #Message Types as integers
    broadcast=          1
    group=              2
    acknowledge=        3

class InsteonCommand:
    #Commands in Hex
    on=                '11'
    
class HAProtocol(object):
    "Base protocol interface"
    def __init__(self, interface):
        pass
    
class PyInsteon(HAProtocol):
    "The Main event"
    def __init__(self, interface):
        super(PyInsteon, self).__init__(interface)        
        self.__i = interface
        self.__i.onReceive(self.__handle_received)
        self.__dataReceived = threading.Event()
        self.__dataReceived.clear()
        return None
    
    def __handle_received(self,data):
        "Decode packet"
        print "Data Received=>" + binascii.hexlify(data)
        dataString = binascii.hexlify(data)
        plm_command = dataString[0:4]   
#        print "fffff:"  + plm_command + ":" + dataString
        #lambda here?  ahhh maybe next time ;)
        if PLM_COMMANDS.plm_info == plm_command:
            self.__version=dataString[14:16]
        elif PLM_COMMANDS.insteon_received == plm_command or PLM_COMMANDS.insteon_ext_received == plm_command:
            fromAddress =   dataString[4:5] + "." + dataString[6:7] + "." +  dataString[8:9] 
            toAddress =     dataString[10:11] + "." + dataString[12:13] + "." +  dataString[14:15]
            messageType =   (int(dataString[16:17],16) & 0b11100000) >> 5 #3 MSB
            extended =      (int(dataString[16:17],16) & 0b00010000) >> 4 #4th MSB
            hopsLeft =      (int(dataString[16:17],16) & 0b00001100) >> 2 #3-2nd MSB
            hopsMax =       (int(dataString[16:17],16) & 0b00000011)  #0-1 MSB
            # could have also used ord(binascii.unhexlify(dataString[16:17])) & 0b11100000
            command1=       dataString[17:17]
            command2=       dataString[18:18]
            print "Insteon=>From=>%s To=>%s MessageType=>%s Extended=>%s HopsLeft=>%s HopsMax=>%s Command1=>%s Command2=>%s" % \
                (fromAddress, toAddress, messageType, extended, hopsLeft, hopsMax, command1, command2)
            #self.__callback_insteon(fromAddress,toAddress,MessageType,extended,hopsLeft,hopsMax,command1,command2)
            pass
        elif PLM_COMMANDS.x10_received == plm_command:
            #self.__calback_x10()
            pass
            
        
        self.__dataReceived.set()
        

    def getVersion(self):
        self.__i.send(PLM_COMMANDS.plm_info)
        self.__dataReceived.wait(1000)
        return self.__version

    def send(self,data):
        self.__dataReceived.clear()
        self.__i.send(data)

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
    
    
    