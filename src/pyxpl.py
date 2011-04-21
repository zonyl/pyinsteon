'''
File:
        pyxpl.py

Description:
        xPL Protocol library for Python
        
        For more information regarding the technical details:
            http://xplproject.org.uk/


Author(s): 
         Jason Sharpee <jason@sharpee.com>  http://www.sharpee.com

License:
    This free software is licensed under the terms of the GNU public license, Version 1     

Usage:
    - Instantiate PyxPL by passing in an interface
    - Call its methods


Example: (see bottom of file) 


Notes:


Created on Mar 26, 2011
'''

from ha_common import HAInterface

class PyxPL(HAInterface):
    def __init__(self,interface):
        super(PyxPL,self).__init__(interface)
        self.__i = interface
        self.c = None
        self.__i.onReceive(self._handle_receive)
        self.sendHeartBeat()
        
    def sendHeartBeat(self):
        data = "xpl-stat\n"
        data+= "{\n"
        data+= "hop=1\n"
        data+= "source=zonyl-2412.gateway\n"
        data+= "target=*\n"
        data+= "}\n"
        data+= "hbeat.app\n"
        data+= "{\n"
        data+= "interval=5\n"
        data+= "port=%s\n" % (self.__i.port)
        data+= "remote-ip=192.168.13.5\n" 
        data+= "}\n"
        self.send(data)
        
    def send(self,data):
        self.__i.send(data)
        pass
    
    def _handle_receive(self,data):
        if self.c != None:
            self.c(data)
        
    def onReceive(self,callback):
        self.c = callback
        
if __name__ == '__main__':
    pass