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
    
class HAProtocol:
    "Base protocol interface"
    
class PyInsteon(HAProtocol):
    "The Main event"
    def __init__(self, Interface):
        self.__i = Interface
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
            
        
        self.__dataReceived.set()
        

    def getVersion(self):
        self.__i.send(PLM_COMMANDS.plm_info)
        self.__dataReceived.wait(1000)
        return self.__version

    def send(self,data):
        self.__dataReceived.clear()
        self.__i.send(PLM_COMMANDS.plm_info)


if __name__ == "__main__":
    pyI = PyInsteon(TCP(HOST, PORT))
    pyI.getVersion()
    select.select([],[],[])
    
    
    