'''

File:
        ha_common.py

Description:
        Library of Home Automation code for Python


Author(s): 
         Jason Sharpee <jason@sharpee.com>  http://www.sharpee.com

License:
    This free software is licensed under the terms of the GNU public license, Version 1     

Usage:
    - 


Example: (see bottom of file) 


Notes:
    - Common functionality between all of the classes I am implementing currently.

Created on Apr 3, 2011

@author: jason
'''

import threading
import socket
import binascii

class Lookup(dict):
    """
    a dictionary which can lookup value by key, or keys by value
    # tested with Python25 by Ene Uran 01/19/2008    http://www.daniweb.com/software-development/python/code/217019
    """
    def __init__(self, items=[]):
        """items can be a list of pair_lists or a dictionary"""
        dict.__init__(self, items)
    def get_key(self, value):
        """find the key as a list given a value"""
        items = [item[0] for item in self.items() if item[1] == value]
        return items[0]   
     
    def get_keys(self, value):
        """find the key(s) as a list given a value"""
        return [item[0] for item in self.items() if item[1] == value]
    def get_value(self, key):
        """find the value given a key"""
        return self[key]
    
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
        "Send raw HEX encoded String"
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
        
class UDP(Interface):
    def __init__(self, host, port):
        super(TCP, self).__init__(host,port)   
        
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