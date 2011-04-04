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

from ha_common import HAProtocol

class PyxPL(HAProtocol):
    def __init__(self,interface):
        super(PyxPL,self).__init__(interface)
        self.__i = interface
        self.onReceive(self._handle_receive)
        
    def send(self,schema,data):
        self.__i.send(data)
        pass
    
    def _handle_receive(self,data):
        pass
    
    def onReceive(self,callback):
        self.c = callback
        
if __name__ == '__main__':
    pass