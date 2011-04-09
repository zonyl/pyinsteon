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
from ha_common import TCP,UDP,Serial
from pyinsteon import PyInsteon
from pyxpl import PyxPL
import time

if __name__ == '__main__':
    print "Start"
    def insteon_received(*params):
        command = params[1]

        #xpl.send('lighting.basic',"command='%s'" % (command))
    
    def xpl_received(*params):    
        print "Here", params
#        fromAddress = '16.f9.ec'
        toAddress = '19.05.7b'
#        toAddress = '16.f9.ff' #Nothing when a broadcast command is sent
        group = 1
        messageDirect= False
        messageBroadcast = False
        messageGroup = False
        messageAcknowledge = False
        extended = False
        hopsLeft = 3
        hopsMax = 3
#        command1 = Insteon_Commmand_Codes['on']
        command2 = 0xff
        data = None
#        insteon.sendInsteon(toAddress,messageBroadcast, messageGroup, messageAcknowledge, extended, hopsLeft, hopsMax, command1, command2, data)
        insteon.turnOn(toAddress, 2)
        insteon.turnOff(toAddress, 2)

    #Lets get this party started
#    insteon = PyInsteon(TCP('192.168.13.146',9761))
    insteon = PyInsteon(Serial('/dev/ttyMI0'))
    insteon.start()
    # Need to get a callback implemented
    #    insteon.onReceivedInsteon(insteon_received)
    xpl = PyxPL(UDP('0.0.0.0',9763,'255.255.255.255',3865))
    #xpl.onReceive(xpl_received)
    insteon.turnOn('19.05.7b')
    insteon.turnOff('19.05.7b')
    insteon.turnOn('m1')
    insteon.turnOff('m1')
    #sit and spin, let the magic happen
    select.select([],[],[])
    