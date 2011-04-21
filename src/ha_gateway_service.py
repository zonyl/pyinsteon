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
from ha_common import *
from pyinsteon import InsteonPLM
from pyxpl import PyxPL
import time

if __name__ == '__main__':
    print "Start"
    def insteon_received(*params):
        command = params[1]

        #xpl.send('lighting.basic',"command='%s'" % (command))
    
    def xpl_received(*params):    
        print "Here", params
 #       jlight.set('on')
 #       jlight.set('off')

    #Lets get this party started
    insteonPLM = InsteonPLM(TCP('192.168.13.146',9761))
#    insteonPLM = InsteonPLM(Serial('/dev/ttyMI0'))

    jlight = InsteonDevice('19.05.7b',insteonPLM)
    jRelay = X10Device('m1',insteonPLM)

    insteonPLM.start()

    jlight.set('on')
    jlight.set('off')
    jRelay.set('on')
    jRelay.set('off')
    
    # Need to get a callback implemented
    #    insteon.onReceivedInsteon(insteon_received)

    xpl = PyxPL(UDP('0.0.0.0',9763,'255.255.255.255',3865))
    #xpl.onReceive(xpl_received)

    #sit and spin, let the magic happen
    select.select([],[],[])
    