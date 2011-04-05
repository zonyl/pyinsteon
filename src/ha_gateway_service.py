'''

File:
        ha_gateway_service.py

Description:
        Gateway service for Home Automation protocols
        - Support xPL
        - Support for XMPP? (http://xmpppy.sourceforge.net/ ?)


Author(s): 
         Jason Sharpee <jason@sharpee.com>  http://www.sharpee.com

License:
    This free software is licensed under the terms of the GNU public license, Version 1     

Usage:
    - Run it.  


Example: (see bottom of file) 


Notes:
    - Prototype that will largely not function currently.

Created on Apr 3, 2011

@author: jason
'''
import select
from ha_common import TCP,UDP
from pyinsteon import PyInsteon,Insteon_Commmand_Codes
from pyxpl import PyxPL
 
if __name__ == '__main__':
    print "Start"
    def insteon_received(*params):
        command = params[1]

        xpl.send('lighting.basic',"command='%s'" % (command))
    
    def xpl_received(*params):    
        print "Here"
        toAddress = '12.34.56'
        fromAddress = '78.9A.BC'
        group = False
        messageDirect= True
        messageBroadcast = False
        messageGroup = False
        messageAcknowledge = False
        extended = False
        hopsLeft = 3
        hopsMax = 3
        command1 = Insteon_Commmand_Codes['on']
        command2 = 0
        data = None
        insteon.sendInsteon(toAddress, fromAddress, group, messageDirect, messageBroadcast, messageGroup, messageAcknowledge, extended, hopsLeft, hopsMax, command1, command2, data)

    #Lets get this party started
    insteon = PyInsteon(TCP('192.168.13.146',9761))
    insteon.onReceivedInsteon(insteon_received)
    xpl = PyxPL(UDP('0.0.0.0',9763,'255.255.255.255',3865))
    xpl.onReceive(xpl_received)
    
    #sit and spin, let the magic happen
    select.select([],[],[])
    