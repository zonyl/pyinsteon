'''
File:
        pyinsteon.py

Description:
        Insteon Home Automation Protocol library for Python (Smarthome 2412N, 2412S, 2412U)
        
        For more information regarding the technical details of the PLM:
                http://www.smarthome.com/manuals/2412sdevguide.pdf

Author(s): 
         Pyjamasam@github <>
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

Example: (see bottom of file) 

    def x10_received(houseCode, unitCode, commandCode):
        print 'X10 Received: %s%s->%s' % (houseCode, unitCode, commandCode)

    def insteon_received(*params):
        print 'Insteon REceived:', params

    pyI = PyInsteon(TCP('192.168.0.1', 9671)) #2412N
    -- or --
    pyI = PyInsteon(Serial('/dev/ttyUSB0')) #2412S
#    pyI.onReceived(insteon_received)
#    pyI.onReceivedX10(x10_received)
    pyI.start()
    
    pyI.turnOn('ff.dd.ee') #insteon
    pyI.turnOn('m1') # Speaks X10 to
    select.select([],[],[])   

Notes:
    - Supports both 2412N and 2412S right now
    - 
    - Todo: Read Style Guide @: http://www.python.org/dev/peps/pep-0008/

Created on Mar 26, 2011
'''
import select
import traceback
import threading
import time
import binascii
import struct
import sys
import string
import hashlib
from collections import deque
import ha_common
import serial

def _byteIdToStringId(idHigh, idMid, idLow):
    return '%02X.%02X.%02X' % (idHigh, idMid, idLow)
    
def _cleanStringId(stringId):
    return stringId[0:2] + stringId[3:5] + stringId[6:8]

def _stringIdToByteIds(stringId):
    return binascii.unhexlify(_cleanStringId(stringId))
    
def _buildFlags():
    #todo: impliment this
    return '\x0f'
    
def hashPacket(packetData):
    return hashlib.md5(packetData).hexdigest()

def simpleMap(value, in_min, in_max, out_min, out_max):
    #stolen from the arduino implimentation.  I am sure there is a nice python way to do it, but I have yet to stublem across it                
    return (float(value) - float(in_min)) * (float(out_max) - float(out_min)) / (float(in_max) - float(in_min)) + float(out_min);

class PyInsteon(ha_common.HAProtocol):
    
    def __init__(self, interface):
        super(PyInsteon, self).__init__(interface)
        
        self.__modemCommands = {'60': {
                                    'responseSize':7,
                                    'callBack':self.__process_PLMInfo
                                  },
                                '62': {
                                    'responseSize':7,
                                    'callBack':self.__process_StandardInsteonMessagePLMEcho
                                  },
                                  
                                '50': {
                                    'responseSize':9,
                                    'callBack':self.__process_InboundStandardInsteonMessage
                                  },
                                '51': {
                                    'responseSize':23,
                                    'callBack':self.__process_InboundExtendedInsteonMessage
                                  },                                
                                '63': {
                                    'responseSize':4,
                                    'callBack':self.__process_InboundX10Message
                                  },
                                '52': {
                                    'responseSize':4,
                                    'callBack':self.__process_InboundX10Message
                                 },
                            }
        
        self.__insteonCommands = {
                                    #Direct Messages/Responses
                                    'SD03': {        #Product Data Request (generally an Ack)                            
                                        'callBack' : self.__handle_StandardDirect_IgnoreAck
                                    },
                                    'SD0D': {        #Get Insteon Engine                            
                                        'callBack' : self.__handle_StandardDirect_EngineResponse,
                                        'validResponseCommands' : ['SD0D']
                                    },
                                    'SD0F': {        #Ping Device                        
                                        'callBack' : self.__handle_StandardDirect_AckCompletesCommand,
                                        'validResponseCommands' : ['SD0F']
                                    },
                                    'SD10': {        #ID Request    (generally an Ack)                        
                                        'callBack' : self.__handle_StandardDirect_IgnoreAck,
                                        'validResponseCommands' : ['SD10', 'SB01']
                                    },    
                                    'SD11': {        #Devce On                                
                                        'callBack' : self.__handle_StandardDirect_AckCompletesCommand,
                                        'validResponseCommands' : ['SD11']
                                    },                                    
                                    'SD12': {        #Devce On Fast                                
                                        'callBack' : self.__handle_StandardDirect_AckCompletesCommand,
                                        'validResponseCommands' : ['SD12']
                                    },                                    
                                    'SD13': {        #Devce Off                                
                                        'callBack' : self.__handle_StandardDirect_AckCompletesCommand,
                                        'validResponseCommands' : ['SD13']
                                    },                                    
                                    'SD14': {        #Devce Off Fast                                
                                        'callBack' : self.__handle_StandardDirect_AckCompletesCommand,
                                        'validResponseCommands' : ['SD14']                                    
                                    },
                                    'SD15': {        #Brighten one step
                                        'callBack' : self.__handle_StandardDirect_AckCompletesCommand,
                                        'validResponseCommands' : ['SD15']                                    
                                    },    
                                    'SD16': {        #Dim one step
                                        'callBack' : self.__handle_StandardDirect_AckCompletesCommand,
                                        'validResponseCommands' : ['SD16']                                    
                                    },                                
                                    'SD19': {        #Light Status Response                                
                                        'callBack' : self.__handle_StandardDirect_LightStatusResponse,
                                        'validResponseCommands' : ['SD19']
                                    },    
                                    
                                    #Broadcast Messages/Responses                                
                                    'SB01': {    
                                                    #Set button pushed                                
                                        'callBack' : self.__handle_StandardBroadcast_SetButtonPressed
                                    },                                   
                                }
        
        self.__x10HouseCodes = ha_common.Lookup(zip((
                            'm',
                            'e',
                            'c',
                            'k',
                            'o',
                            'g',
                            'a',
                            'i',
                            'n',
                            'f',
                            'd',
                            'l',
                            'p',
                            'h',
                            'n',
                            'j' ),xrange(0x0, 0xF)))
        
        self.__x10UnitCodes = ha_common.Lookup(zip((
                             '13',
                             '5',
                             '3',
                             '11',
                             '15',
                             '7',
                             '1',
                             '9',
                             '14',
                             '6',
                             '4',
                             '12',
                             '16',
                             '8',
                             '2',
                             '10'
                             ),xrange(0x0,0xF)))
        
        self._allLinkDatabase = dict()
        
        self.__shutdownEvent = threading.Event()
        self.__interfaceRunningEvent = threading.Event()
        
        self.__commandLock = threading.Lock()
        self.__outboundQueue = deque()
        self.__outboundCommandDetails = dict()
        self.__retryCount = dict()        
        
        self.__pendingCommandDetails = dict()        
        
        self.__commandReturnData = dict()
        
        self.__intersend_delay = 0.15 #150 ms between network sends
        self.__lastSendTime = 0

#        print "Using %s for PLM communication" % serialDevicePath
#       self.__serialDevice = serial.Serial(serialDevicePath, 19200, timeout = 0.1)     
        self.__interface = interface       
    
    def shutdown(self):
        if self.__interfaceRunningEvent.isSet():
            self.__shutdownEvent.set()

            #wait 2 seconds for the interface to shut down
            self.__interfaceRunningEvent.wait(2000)
            
    def run(self):
        self.__interfaceRunningEvent.set();
        
        #for checking for duplicate messages received in a row
        lastPacketHash = None
        
        while not self.__shutdownEvent.isSet():
            
            #check to see if there are any outbound messages to deal with
            self.__commandLock.acquire()
            if (len(self.__outboundQueue) > 0) and (time.time() - self.__lastSendTime > self.__intersend_delay):
                commandHash = self.__outboundQueue.popleft()
                
                commandExecutionDetails = self.__outboundCommandDetails[commandHash]
                
                bytesToSend = commandExecutionDetails['bytesToSend']
                print "> ", ha_common.hex_dump(bytesToSend, len(bytesToSend)),

                self.__interface.write(bytesToSend)                    
                
                self.__pendingCommandDetails[commandHash] = commandExecutionDetails                
                del self.__outboundCommandDetails[commandHash]
                
                self.__lastSendTime = time.time()
                                
            self.__commandLock.release()    
            
            #check to see if there is anyting we need to read            
            firstByte = self.__interface.read(1)            
            if len(firstByte) == 1:
                #got at least one byte.  Check to see what kind of byte it is (helps us sort out how many bytes we need to read now)
                                    
                if firstByte[0] == '\x02':
                    #modem command (could be an echo or a response)
                    #read another byte to sort that out
                    secondByte = self.__interface.read(1)
                                        
                    responseSize = -1
                    callBack = None
                    
                    modemCommand = binascii.hexlify(secondByte).upper()
                    if self.__modemCommands.has_key(modemCommand):
                        if self.__modemCommands[modemCommand].has_key('responseSize'):                                                                    
                            responseSize = self.__modemCommands[modemCommand]['responseSize']                            
                        if self.__modemCommands[modemCommand].has_key('callBack'):                                                                    
                            callBack = self.__modemCommands[modemCommand]['callBack']                            
                            
                    if responseSize != -1:                        
                        remainingBytes = self.__interface.read(responseSize)
                        
                        print "< ",
                        print ha_common.hex_dump(firstByte + secondByte + remainingBytes, len(firstByte + secondByte + remainingBytes)),
                        
                        currentPacketHash = hashPacket(firstByte + secondByte + remainingBytes)
                        if lastPacketHash and lastPacketHash == currentPacketHash:
                            #duplicate packet.  Ignore
                            pass
                        else:                        
                            if callBack:
                                callBack(firstByte + secondByte + remainingBytes)    
                            else:
                                print "No callBack defined for for modem command %s" % modemCommand        
                        
                        lastPacketHash = currentPacketHash            
                        
                    else:
                        print "No responseSize defined for modem command %s" % modemCommand                        
                elif firstByte[0] == '\x15':
                    print "Received a Modem NAK!"
                else:
                    print "Unknown first byte %s" % binascii.hexlify(firstByte[0])
            else:
                #print "Sleeping"
                time.sleep(0.1)
            

            
        self.__interfaceRunningEvent.clear()
                                
    def __sendModemCommand(self, modemCommand, commandDataString = None, extraCommandDetails = None):        
        
        returnValue = False
        
        try:                
            bytesToSend = '\x02' + binascii.unhexlify(modemCommand)            
            if commandDataString != None:
                bytesToSend += commandDataString                            
            commandHash = hashPacket(bytesToSend)
                        
            self.__commandLock.acquire()
            if self.__outboundCommandDetails.has_key(commandHash):
                #duplicate command.  Ignore
                pass
                
            else:                
                waitEvent = threading.Event()
                
                basicCommandDetails = { 'bytesToSend': bytesToSend, 'waitEvent': waitEvent, 'modemCommand': modemCommand }                                                                                                                        
                
                if extraCommandDetails != None:
                    basicCommandDetails = dict(basicCommandDetails.items() + extraCommandDetails.items())                        
                
                self.__outboundCommandDetails[commandHash] = basicCommandDetails
                
                self.__outboundQueue.append(commandHash)
                self.__retryCount[commandHash] = 0
                
                print "Queued %s" % commandHash
                
                returnValue = {'commandHash': commandHash, 'waitEvent': waitEvent}
                
            self.__commandLock.release()                        
                    
        except Exception, ex:
            print traceback.format_exc()
            
        finally:
            
            #ensure that we unlock the thread lock
            #the code below will ensure that we have a valid lock before we call release
            self.__commandLock.acquire(False)
            self.__commandLock.release()
                    
        return returnValue    
        
        
        
    def __sendStandardP2PInsteonCommand(self, destinationDevice, commandId1, commandId2):                
        return self.__sendModemCommand('62', _stringIdToByteIds(destinationDevice) + _buildFlags() + binascii.unhexlify(commandId1) + binascii.unhexlify(commandId2), extraCommandDetails = { 'destinationDevice': destinationDevice, 'commandId1': 'SD' + commandId1, 'commandId2': commandId2})

    def __getX10UnitCommand(self,deviceId):
        "Send just an X10 unit code message"
        deviceId = deviceId.lower()
        return "%02x00" % ((self.__x10HouseCodes[deviceId[0:1]] << 4) | self.__x10UnitCodes[deviceId[1:2]])

    def __getX10CommandCommand(self,deviceId,commandCode):
        "Send just an X10 command code message"
        deviceId = deviceId.lower()
        return "%02x80" % ((self.__x10HouseCodes[deviceId[0:1]] << 4) | int(commandCode,16))
    
    def __sendStandardP2PX10Command(self,deviceId,commandId1, commandId2 = None):
        # X10 sends 1 complete message in two commands
        self.__sendModemCommand('63', binascii.unhexlify(self.__getX10UnitCommand(deviceId)))
        
        return self.__sendModemCommand('63', binascii.unhexlify(self.__getX10CommandCommand(deviceId, commandId1)))
            
    def __waitForCommandToFinish(self, commandExecutionDetails, timeout = None):
                
        if type(commandExecutionDetails) != type(dict()):
            print "Unable to wait without a valid commandExecutionDetails parameter"
            return False
            
        waitEvent = commandExecutionDetails['waitEvent']
        commandHash = commandExecutionDetails['commandHash']
        
        realTimeout = 2 #default timeout of 2 seconds
        if timeout:
            realTimeout = timeout
            
        timeoutOccured = False
        
        if sys.version_info[:2] > (2,6):
            #python 2.7 and above waits correctly on events
            timeoutOccured = not waitEvent.wait(realTimeout)
        else:
            #< then python 2.7 and we need to do the waiting manually
            while not waitEvent.isSet() and realTimeout > 0:
                time.sleep(0.1)
                realTimeout -= 0.1
                
            if realTimeout == 0:
                timeoutOccured = True
                    
        if not timeoutOccured:    
            if self.__commandReturnData.has_key(commandHash):
                return self.__commandReturnData[commandHash]
            else:
                return True
        else:            
            #re-queue the command to try again
            self.__commandLock.acquire()
            
            if self.__retryCount[commandHash] >= 5:
                #too many retries.  Bail out
                self.__commandLock.release()
                return False
                
            print "Timed out for %s - Requeueing (already had %d retries)" % (commandHash, self.__retryCount[commandHash])
            
            requiresRetry = True
            if self.__pendingCommandDetails.has_key(commandHash):
                
                self.__outboundCommandDetails[commandHash] = self.__pendingCommandDetails[commandHash]
                del self.__pendingCommandDetails[commandHash]
            
                self.__outboundQueue.append(commandHash)
                self.__retryCount[commandHash] += 1
            else:
                print "Interesting.  timed out for %s, but there is no pending command details" % commandHash
                #to prevent a huge loop here we bail out
                requiresRetry = False
            
            self.__commandLock.release()
            
            if requiresRetry:
                return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)
            else:
                return False
        
            




    #low level processing methods
    def __process_PLMInfo(self, responseBytes):                
        (modemCommand, idHigh, idMid, idLow, deviceCat, deviceSubCat, firmwareVer, acknak) = struct.unpack('xBBBBBBBB', responseBytes)        
        
        foundCommandHash = None        
        #find our pending command in the list so we can say that we're done (if we are running in syncronous mode - if not well then the caller didn't care)
        for (commandHash, commandDetails) in self.__pendingCommandDetails.items():                        
            if binascii.unhexlify(commandDetails['modemCommand']) == chr(modemCommand):
                #Looks like this is our command.  Lets deal with it.                
                self.__commandReturnData[commandHash] = { 'id': _byteIdToStringId(idHigh,idMid,idLow), 'deviceCategory': '%02X' % deviceCat, 'deviceSubCategory': '%02X' % deviceSubCat, 'firmwareVersion': '%02X' % firmwareVer }    
                
                waitEvent = commandDetails['waitEvent']
                waitEvent.set()
                
                foundCommandHash = commandHash
                break
                
        if foundCommandHash:
            del self.__pendingCommandDetails[foundCommandHash]
        else:
            print "Unable to find pending command details for the following packet:"
            print ha_common.hex_dump(responseBytes, len(responseBytes))
            
    def __process_StandardInsteonMessagePLMEcho(self, responseBytes):                
        #print utilities.hex_dump(responseBytes, len(responseBytes))
        #we don't do anything here.  Just eat the echoed bytes
        pass
            
        
    def __validResponseMessagesForCommandId(self, commandId):
        if self.__insteonCommands.has_key(commandId):
            commandInfo = self.__insteonCommands[commandId]
            if commandInfo.has_key('validResponseCommands'):
                return commandInfo['validResponseCommands']
        
        return False
        
    def __process_InboundStandardInsteonMessage(self, responseBytes):
        (insteonCommand, fromIdHigh, fromIdMid, fromIdLow, toIdHigh, toIdMid, toIdLow, messageFlags, command1, command2) = struct.unpack('xBBBBBBBBBB', responseBytes)        
        
        foundCommandHash = None            
        waitEvent = None
        
        #check to see what kind of message this was (based on message flags)
        isBroadcast = messageFlags & (1 << 7) == (1 << 7)
        isDirect = not isBroadcast
        isAck = messageFlags & (1 << 5) == (1 << 5)
        isNak = isAck and isBroadcast
        
        insteonCommandCode = "%02X" % command1
        if isBroadcast:
            #standard broadcast
            insteonCommandCode = 'SB' + insteonCommandCode
        else:
            #standard direct
            insteonCommandCode = 'SD' + insteonCommandCode
            
        if insteonCommandCode == 'SD00':
            #this is a strange special case...
            #lightStatusRequest returns a standard message and overwrites the cmd1 and cmd2 bytes with "data"
            #cmd1 (that we use here to sort out what kind of incoming message we got) contains an 
            #"ALL-Link Database Delta number that increments every time there is a change in the addressee's ALL-Link Database"
            #which makes is super hard to deal with this response (cause cmd1 can likley change)
            #for now my testing has show that its 0 (at least with my dimmer switch - my guess is cause I haven't linked it with anything)
            #so we treat the SD00 message special and pretend its really a SD19 message (and that works fine for now cause we only really
            #care about cmd2 - as it has our light status in it)
            insteonCommandCode = 'SD19'
        
        #print insteonCommandCode                    
        
        #find our pending command in the list so we can say that we're done (if we are running in syncronous mode - if not well then the caller didn't care)
        for (commandHash, commandDetails) in self.__pendingCommandDetails.items():
            
            #since this was a standard insteon message the modem command used to send it was a 0x62 so we check for that
            if binascii.unhexlify(commandDetails['modemCommand']) == '\x62':                                                                        
                originatingCommandId1 = None
                if commandDetails.has_key('commandId1'):
                    originatingCommandId1 = commandDetails['commandId1']    
                    
                validResponseMessages = self.__validResponseMessagesForCommandId(originatingCommandId1)
                if validResponseMessages and len(validResponseMessages):
                    #Check to see if this received command is one that this pending command is waiting for
                    if validResponseMessages.count(insteonCommandCode) == 0:
                        #this pending command isn't waiting for a response with this command code...  Move along
                        continue
                else:
                    print "Unable to find a list of valid response messages for command %s" % originatingCommandId1
                    continue
                        
                    
                #since there could be multiple insteon messages flying out over the wire, check to see if this one is from the device we send this command to
                destDeviceId = None
                if commandDetails.has_key('destinationDevice'):
                    destDeviceId = commandDetails['destinationDevice']
                        
                if destDeviceId:
                    if destDeviceId == _byteIdToStringId(fromIdHigh, fromIdMid, fromIdLow):
                                                                        
                        returnData = {} #{'isBroadcast': isBroadcast, 'isDirect': isDirect, 'isAck': isAck}
                        
                        #try and look up a handler for this command code
                        if self.__insteonCommands.has_key(insteonCommandCode):
                            if self.__insteonCommands[insteonCommandCode].has_key('callBack'):
                                (requestCycleDone, extraReturnData) = self.__insteonCommands[insteonCommandCode]['callBack'](responseBytes)
                                                        
                                if extraReturnData:
                                    returnData = dict(returnData.items() + extraReturnData.items())
                                
                                if requestCycleDone:                                    
                                    waitEvent = commandDetails['waitEvent']                                    
                            else:
                                print "No callBack for insteon command code %s" % insteonCommandCode    
                        else:
                            print "No insteonCommand lookup defined for insteon command code %s" % insteonCommandCode    
                                
                        if len(returnData):
                            self.__commandReturnData[commandHash] = returnData
                                                                                                                
                        foundCommandHash = commandHash
                        break
            
        if foundCommandHash == None:
            print "Unhandled packet (couldn't find any pending command to deal with it)"
            print "This could be an unsolocicited broadcast message"
                        
        if waitEvent and foundCommandHash:
            waitEvent.set()            
            del self.__pendingCommandDetails[foundCommandHash]
            
            print "Command %s completed" % foundCommandHash
    
    def __process_InboundExtendedInsteonMessage(self, responseBytes):
        #51 
        #17 C4 4A     from
        #18 BA 62     to
        #50         flags
        #FF         cmd1
        #C0         cmd2
        #02 90 00 00 00 00 00 00 00 00 00 00 00 00    data
        (insteonCommand, fromIdHigh, fromIdMid, fromIdLow, toIdHigh, toIdMid, toIdLow, messageFlags, command1, command2, data) = struct.unpack('xBBBBBBBBBB14s', responseBytes)        
        
        pass
        
    def __process_InboundX10Message(self, responseBytes):        
        "Receive Handler for X10 Data"
        #X10 sends commands fully in two separate messages. Not sure how to handle this yet
        #TODO not implemented
        unitCode = None
        commandCode = None
 #       (insteonCommand, fromIdHigh, fromIdMid, fromIdLow, toIdHigh, toIdMid, toIdLow, messageFlags, command1, command2) = struct.unpack('xBBBBBBBBBB', responseBytes)        
#        houseCode =     (int(responseBytes[4:6],16) & 0b11110000) >> 4 
 #       houseCodeDec = X10_House_Codes.get_key(houseCode)
#        keyCode =       (int(responseBytes[4:6],16) & 0b00001111)
#        flag =          int(responseBytes[6:8],16)
        
        
                
    #insteon message handlers
    def __handle_StandardDirect_IgnoreAck(self, messageBytes):
        #just ignore the ack for what ever command triggered us
        #there is most likley more data coming for what ever command we are handling
        return (False, None)
        
    def __handle_StandardDirect_AckCompletesCommand(self, messageBytes):
        #the ack for our command completes things.  So let the system know so
        return (True, None)                            
                                                    
    def __handle_StandardBroadcast_SetButtonPressed(self, messageBytes):        
        #02 50 17 C4 4A 01 19 38 8B 01 00
        (idHigh, idMid, idLow, deviceCat, deviceSubCat, deviceRevision) = struct.unpack('xxBBBBBBxxx', messageBytes)
        return (True, {'deviceType': '%02X%02X' % (deviceCat, deviceSubCat), 'deviceRevision':'%02X' % deviceRevision})
            
    def __handle_StandardDirect_EngineResponse(self, messageBytes):        
        #02 50 17 C4 4A 18 BA 62 2B 0D 01        
        engineVersionIdentifier = messageBytes[10]            
        return (True, {'engineVersion': engineVersionIdentifier == '\x01' and 'i2' or 'i1'})
            
    def __handle_StandardDirect_LightStatusResponse(self, messageBytes):
        #02 50 17 C4 4A 18 BA 62 2B 00 00
        lightLevelRaw = messageBytes[10]    
        
        #map the lightLevelRaw value to a sane value between 0 and 1
        normalizedLightLevel = simpleMap(ord(lightLevelRaw), 0, 255, 0, 1)
                    
        return (True, {'lightStatus': round(normalizedLightLevel, 2) })
        
        
        
        
        
    #public methods        
    def getPLMInfo(self, timeout = None):        
        commandExecutionDetails = self.__sendModemCommand('60')
            
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)                            
            
    def pingDevice(self, deviceId, timeout = None):        
        startTime = time.time()
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '0F', '00')                

        #Wait for ping result
        commandReturnCode = self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)    
        endTime = time.time()
        
        if commandReturnCode:
            return endTime - startTime
        else:
            return False
            
    def idRequest(self, deviceId, timeout = None):                
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '10', '00')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)    
        
    def getInsteonEngineVersion(self, deviceId, timeout = None):                
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '0D', '00')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)    
    
    def getProductData(self, deviceId, timeout = None):                
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '03', '00')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)    
            
    def lightStatusRequest(self, deviceId, timeout = None):                
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '19', '00')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)        
                    
    def turnOn(self, deviceId, timeout = None):        
        if len(deviceId) != 2: #insteon device address
            commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '11', 'ff')                        
        else: #X10 device address
            commandExecutionDetails = self.__sendStandardP2PX10Command(deviceId,'02')
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)            

    def turnOff(self, deviceId, timeout = None):
        if len(deviceId) != 2: #insteon device address
            commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '13', '00')
        else: #X10 device address
            commandExecutionDetails = self.__sendStandardP2PX10Command(deviceId,'03')
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)
    
    def turnOnFast(self, deviceId, timeout = None):        
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '12', 'ff')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)            

    def turnOffFast(self, deviceId, timeout = None):
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '14', '00')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)    
            
    def dimTo(self, deviceId, level, timeout = None):
        
        #organize what dim level we are heading to (figgure out the byte we need to send)
        lightLevelByte = simpleMap(level, 0, 1, 0, 255)
        
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '11', '%02x' % lightLevelByte)                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)        
            
    def brightenOneStep(self, deviceId, timeout = None):
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '15', '00')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)
    
    def dimOneStep(self, deviceId, timeout = None):
        commandExecutionDetails = self.__sendStandardP2PInsteonCommand(deviceId, '16', '00')                        
        return self.__waitForCommandToFinish(commandExecutionDetails, timeout = timeout)

'''

import select
import time
import binascii
import threading






#PLM Serial Commands
PLM_Commands = Lookup(zip(
                          ('insteon_received',
                        'insteon_ext_received',
                        'x10_received',
                        'all_link_complete',
                        'plm_button_event',
                        'user_user_reset',
                        'all_link_clean_failed',
                        'all_link_record',
                        'all_link_clean_status',
                        '',
                        '',
                        '',
                        '',
                        '',
                        '',
                        '',
                        'plm_info',
                        'all_link_send',
                        'insteon_send',
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
                        'plm_get_config'
                        ),xrange(0x250, 0x273)))
#pprint.pprint(PLM_commands)
PLM_Commands['unknown']=0x219 #odd little undocumented command
PLM_Commands['unknown1']=0x2b2 # ?

Insteon_Commmand_Codes = Lookup({
                                 'on':0x11,
                                 'fast_on':0x12,
                                 'off':0x19,
                                 'fast_off':0x20
                                 })
    
### Possibly error in Insteon Documentation regarding command mapping of preset dim and off
X10_Command_Codes = Lookup(zip((
        'all_lights_off',
        'status_off',
        'on',
#        'preset_dim',
        'off',
        'all_lights_on',
        'hail_acknowledge',
        'bright',
        'status_on',
        'extended_code',
        'status_request',
#        'off',
        'present_dim'
        'preset_dim2',
        'all_units_off',
        'hail_request',
        'dim',
        'extended_data'
        ),xrange(0,15)))

X10_Types = Lookup({
                    'unit_code': 0x0, 
                    'command_code': 0x80
                    })

X10_House_Codes = Lookup(zip((
                            'm',
                            'e',
                            'c',
                            'k',
                            'o',
                            'g',
                            'a',
                            'i',
                            'n',
                            'f',
                            'd',
                            'l',
                            'p',
                            'h',
                            'n',
                            'j' ),xrange(0x0, 0xF)))

        
X10_Unit_Codes = Lookup(zip((
        '13',
        '5',
        '3',
        '11',
        '15',
        '7',
        '1',
        '9',
        '14',
        '6',
        '4',
        '12',
        '16',
        '8',
        '2',
        '10'
        ),xrange(0x0,0xF)))


    



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
        self.__x10UnitCode = None
        self.__version = None
        return None

    def _handle_received(self,data):
        dataHex = binascii.hexlify(data)
        print "Data Received=>" + dataHex
        plm_command = int(dataHex[0:4],16)
        print "Command->%d %s '%s'" % (plm_command,plm_command,PLM_Commands.get_key(plm_command))
        callback = { 
                        'plm_info': self._recvInfo,
                        'insteon_received': self._recvInsteon,
                        'insteon_ext_received': self._recvInsteon,
                        'x10_received': self._recvX10
                    }.get(PLM_Commands.get_key(plm_command))
        if callback:
            callback(dataHex)

        #Let other threads know data has been received and processed
        self.__dataReceived.set()

    def _recvInfo(self,dataHex):
        "Receive Handler for PLM Info"
        self.__version=dataHex[14:16]

    def _recvInsteon(self,dataHex):
        "Receive Handler for Insteon Data"
        group=None
        userData=None

        fromAddress =       dataHex[4:6] + "." + dataHex[6:8] + "." +  dataHex[8:10] 
        toAddress =         dataHex[10:12] + "." + dataHex[12:14] + "." +  dataHex[14:16]
        messageDirect =     ((int(dataHex[16:18],16) & 0b11100000) >> 5)==0
        messageAcknowledge =((int(dataHex[16:18],16) & 0b00100000) >> 5)>0
        messageGroup =      ((int(dataHex[16:18],16) & 0b01000000) >> 6)>0
        if messageGroup:
            group =             dataHex[14:16] # overlapped into toAddress if a group call is made
        messageBroadcast =  ((int(dataHex[16:18],16) & 0b10000000) >> 7)>0
        extended =          ((int(dataHex[16:18],16) & 0b00010000) >> 4)>0 #4th MSB
        hopsLeft =          (int(dataHex[16:18],16) & 0b00001100) >> 2 #3-2nd MSB
        hopsMax =           (int(dataHex[16:18],16) & 0b00000011)  #0-1 MSB
        # could have also used ord(binascii.unhexlify(dataHex[16:17])) & 0b11100000
        command1=       dataHex[18:20]
        command2=       dataHex[20:22]
        if extended:
            userData =      dataHex[22:36]
        
        print "Insteon=>From=>%s To=>%s Group=> %s MessageD=>%s MB=>%s MG=>%s MA=>%s Extended=>%s HopsLeft=>%s HopsMax=>%s Command1=>%s Command2=>%s UD=>%s" % \
            (fromAddress, toAddress, group, messageDirect, messageBroadcast, messageGroup, messageAcknowledge, extended, hopsLeft, hopsMax, command1, command2, userData)
        if self.__callback_insteon != None:
            self.__callback_insteon(fromAddress, toAddress, group, messageDirect, messageBroadcast, messageGroup, messageAcknowledge, extended, hopsLeft, hopsMax, command1, command2, userData)
    
    def _recvX10(self,dataHex):
        "Receive Handler for X10 Data"
        #X10 sends commands fully in two separate messages"
        unitCode = None
        commandCode = None
        houseCode =     (int(dataHex[4:6],16) & 0b11110000) >> 4 
        houseCodeDec = X10_House_Codes.get_key(houseCode)
        keyCode =       (int(dataHex[4:6],16) & 0b00001111)
        flag =          int(dataHex[6:8],16)
#        print "X10=>House=>%s Unit=>%s Command=>%s Flag=%s" % (houseCode, unitCode, commandCode, flag)
        if flag == X10_Types['unit_code']:
            unitCode = keyCode
            unitCodeDec = X10_Unit_Codes.get_key(unitCode)
            #print "X10: Beginning transmission X10=>House=>%s Unit=>%s" % (houseCodeDec, unitCodeDec)
            self.__x10UnitCode = unitCodeDec
        elif flag == X10_Types['command_code']:
            commandCode = keyCode
            commandCodeDec = X10_Command_Codes.get_key(commandCode)
            #print "Fully formed X10=>House=>%s Unit=>%s Command=>%s" % (houseCodeDec, self.__x10UnitCode, commandCodeDec)
            #Only send fully formed messages
            if self.__callback_x10 != None:
                self.__callback_x10(houseCodeDec, self.__x10UnitCode, commandCodeDec)
            self.__x10UnitCode = None
            
    def getVersion(self):
        "Get PLM firmware version #"
#        self.__i.send(PLM_COMMANDS.plm_info)
        
        self.__i.send("%04x" %PLM_Commands['plm_info'])
        self.__dataReceived.wait(1000)
        return self.__version

    def _send(self,dataHex):
        "Send raw data"
        #We are starting a new transmission, clear any blocks on receive
        self.__dataReceived.clear()
        self.__i.send(dataHex)
        #Slow down the interface when sending.  Takes a while and can overrun easily
        #todo make this adaptable based on Ack / Nak rates
        # Of interest is that the controller will return an Ack before it is finished sending, so overrun wont be seen until next send
        time.sleep(.5)

    def sendInsteon(self, toAddress, messageBroadcast, messageGroup, messageAcknowledge, extended, hopsLeft, hopsMax, command1, command2, data):
        "Send raw Insteon message"
        messageType=0
        if extended==False:
            dataString  = "%04x" % PLM_Commands['insteon_send']
        else:
            dataString = "%04x" % PLM_Commands['insteon_ext_send']
        #better comprehension here?
        high, mid, low = toAddress.split('.')
        dataString += high
        dataString += mid
        dataString += low
        if messageAcknowledge:
            messageType=messageType | 0b00100000
        if messageGroup:
            messageType=messageType | 0b01000000
        if messageBroadcast:
            messageType=messageType | 0b10000000
        if extended:
            messageType=messageType | 0b00010000
        messageType = messageType | (hopsLeft  << 2)
        messageType = messageType | hopsMax
        dataString += "%02x" % messageType
        dataString += "%02x" % command1
        dataString += "%02x" % command2
        if extended:
            dataString += data
        print "InsteonSend=>%s" % (dataString)
        self._send(dataString)
        print dataString
            
        
    def sendX10(self, houseCode, unitCode, commandCode):
        "Send Fully formed X10 Unit / Command"
        self.sendX10Unit(houseCode, unitCode)

        #wait for acknowledge.
        self.__dataReceived.wait(1000)
                
        self.sendX10Command(houseCode, commandCode)

    def sendX10Unit(self,houseCode,unitCode):
        "Send just an X10 unit code message"
        
        houseCode=houseCode.lower()
        unitCodeEnc = X10_Unit_Codes[unitCode]
        houseCodeEnc = X10_House_Codes[houseCode]
        dataString = "%04x" % PLM_Commands['x10_send']
        firstByte = houseCodeEnc << 4
        firstByte = firstByte | unitCodeEnc
        dataString+= "%02x" % (firstByte)
        dataString+=  "%02x" % X10_Types['unit_code']
        self._send(dataString)

    def sendX10Command(self,houseCode,commandCode):
        "Send just an X10 command code message"

        houseCode=houseCode.lower()
        commandCode = commandCode.lower()
        commandCodeEnc= X10_Command_Codes[commandCode]
        houseCodeEnc = X10_House_Codes[houseCode]
        dataString = "%04x" % PLM_Commands['x10_send']
        firstByte = houseCodeEnc << 4
        firstByte = firstByte | commandCodeEnc
        dataString+= "%02x" % (firstByte)
        dataString+= "%02x" % X10_Types['command_code']
        self._send(dataString)
        
    def onReceivedX10(self, callback):
        "Set callback for reception of an X10 message"
        self.__callback_x10=callback
        return
    
    def onReceivedInsteon(self, callback):
        "Set callback for reception of an Insteon message"
        self.__callback_insteon=callback
        return
'''
######################
# EXAMPLE            #
######################


def x10_received(houseCode, unitCode, commandCode):
    print 'X10 Received: %s%s->%s' % (houseCode, unitCode, commandCode)

def insteon_received(*params):
    print 'Insteon Received:', params
    
if __name__ == "__main__":
    HOST='192.168.13.146'
    PORT=9761
    print 'shouldnt be here'
    pyI = PyInsteon(TCP(HOST, PORT))
#    pyI.onReceivedX10(x10_received)
#    pyI.onReceivedInsteon(insteon_received)
#    pyI.getVersion()
#    pyI.sendX10('m', '2', 'on')
#    pyI.sendX10('m', '1', 'on')
#    pyI.sendX10('m', '1', 'off')
    pyI.turnOn('ff.dd.cc')
    select.select([],[],[])


