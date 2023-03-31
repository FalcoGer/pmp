#/bin/python3

# struct is used to decode bytes into primitive data types
# https://docs.python.org/3/library/struct.html
import struct
from proxy import Proxy, ESocketRole
from hexdump import hexdump
from enum import Enum, auto


###############################################################################
# Setting storage stuff goes here.

class ESettingKey(Enum):
    printhexdump = auto()

    def __eq__(self, other) -> bool:
        if other is int:
            return self.value == other
        if other is str:
            return self.name == other
        if repr(type(self)) == repr(type(other)):
            return self.value == other.value
        return False

    def __gt__(self, other) -> bool:
        if other is int:
            return self.value > other
        if other is str:
            return self.name > other
        if repr(type(self)) == repr(type(other)):
            return self.value > other.value
        raise ValueError("Can not compare.")

    def __hash__(self):
    	return int.__hash__(self.value)

    def fromName(name: str):
        for e in list(ESettingKey):
            if name == e.name:
                return e
        return None

# Use this to set sensible defaults for your stored variables.
def settingsDefaults(settingKey: ESettingKey) -> object:
    ret = None
    if settingKey == ESettingKey.printhexdump:
        return True
    return ret

###############################################################################
# Packet parsing stuff goes here.

# Define what should happen when a packet arrives here
def parse(data: bytes, src: (str, int), dest: (str, int), origin: ESocketRole, proxy: Proxy) -> None:
    if getSetting(ESettingKey.printhexdump, proxy):
        # Print out the data in a nice format.
        sh, sp = src
        dh, dp = dest
        srcStr = f"{sh}:{sp}"
        destStr = f"{dh}:{dp}"
        maxLen = len(srcStr) if len(srcStr) > len(destStr) else len(destStr)

        srcStr = srcStr.rjust(maxLen)
        destStr = destStr.ljust(maxLen)
        hd = "\n".join(hexdump(data, 24, 8))

        print(f"{srcStr}->{destStr} ({len(data)} Bytes)\n{hd}")

    # Do interesting stuff with the data here.
    #if data == b'ABCD\n' and origin == ESocketRole.client:
    #    data = b'DCBA\n'

    # A construct like this may be used to drop packets. 
    #if data.find(b'\xFF\xFF\xFF\xFF') >= 0:
    #    print("Dropped")
    #    return

    # By default, append the data as is to the queue to send it to the client/server.
    proxy.sendData(ESocketRole.server if origin == ESocketRole.client else ESocketRole.client, data)
    return

###############################################################################
# CLI stuff goes here.

# Define your custom commands here. Each command requires two arguments:
# 1. userInput: str
#      This is whatever string follows the command, only the space immediately following the command is stripped.
#      For example when executing "ss   hello   ", userInput would be "  hello   "
# 2. proxy: Proxy
#      This allows to make calls to the proxy API, for example to inject packets.
# The functions return bool. If they return false, the execution is terminated and everything is shut down.

# Define which commands are available here and which function is called when it is entered by the user.
# Return a dictionary with the command as the key and a tuple of (function, str) as the value.
# The function is called when the command is executed, the string is the help text for that command.
def buildCommandDict() -> dict:
    ret = {}
    ret['quit']         = (cmd_quit, 'Stop the proxy and quit.')
    ret['exit']         = ret['quit']
    ret['clhist']       = (cmd_clearhistory, 'Clear the command history.\nAdd an integer to only clear that particular entry.\nNote: The history file will instantly be overwritten.')
    ret['lshist']       = (cmd_showhistory, 'Show the command history.\nAdd an integer to only display that particular entry.')
    ret['lssettings']   = (cmd_lssettings, 'Show the current settings.')
    ret['disconnect']   = (cmd_disconnect, 'Disconnect from the client and server and wait for a new connection.')
    ret['help']         = (cmd_help, 'Print available commands.')
    ret['printhexdump'] = (cmd_printhexdump, 'Toggle the printing of packets when they are being parsed.')
    ret['sh']           = (cmd_sh, 'Send arbitrary hex values to the server.\nUsage: "sh" hexstring \nExample: sh 41424344')
    ret['ss']           = (cmd_ss, 'Send arbitrary strings to the server.\nUsage: "ss" string\nExample: ss hello!\nNote: Leading spaces in the string are sent\nexcept for the space between the command and\nthe first character of the string.')
    ret['sf']           = (cmd_sf, 'Send arbitrary files to the server.\nUsage: "sf" filename\nExample: sf /home/user/.bashrc')
    ret['ch']           = (cmd_ch, 'Send arbitrary hex values to the client.\nUsage: "ch" hexstring \nExample: ch 41424344')
    ret['cs']           = (cmd_cs, 'Send arbitrary strings to the client.\nUsage: "cs" string\nExample: cs hello!\nNote: Leading spaces in the string are sent\nexcept for the space between the command and\nthe first character of the string.')
    ret['cf']           = (cmd_cf, 'Send arbitrary files to the client.\nUsage: "cf" filename\nExample: cf /home/user/.bashrc')
    return ret

def cmd_help(userInput: str, proxy: Proxy) -> bool:
    commandDict = buildCommandDict()
    # find the longest key for neat formatting.
    maxLen = 0
    for key in commandDict.keys():
        if len(key) > maxLen:
            maxLen = len(key)

    for key in commandDict.keys():
        function, helptext = commandDict[key]
        helptext = helptext.replace("\n", "\n" + (" " * (maxLen + 8))).strip()
        print(f"{key.rjust(maxLen)} - {helptext}")
    return True

def cmd_quit(userInput: str, proxy: Proxy) -> bool:
    return False

def cmd_sh(userInput: str, proxy: Proxy) -> bool:
    pkt = bytes.fromhex(userInput)
    if proxy.running:
        proxy.sendToServer(pkt)
    return True

def cmd_ss(userInput: str, proxy: Proxy) -> bool:
    pkt = str.encode(userInput, 'utf-8')
    if proxy.running:
        proxy.sendToServer(pkt)
    return True

def cmd_sf(userInput: str, proxy: Proxy) -> bool:
    print("TBD")
    return True

def cmd_ch(userInput: str, proxy: Proxy) -> bool:
    pkt = bytes.fromhex(userInput)
    if proxy.running:
        proxy.sendToClient(pkt)
    return True

def cmd_cs(userInput: str, proxy: Proxy) -> bool:
    pkt = str.encode(userInput, 'utf-8')
    if proxy.running:
        proxy.sendToClient(pkt)
    return True

def cmd_cf(userInput: str, proxy: Proxy) -> bool:
    print("TBD")
    return True

def cmd_disconnect(userInput: str, proxy: Proxy) -> bool:
    if proxy.running:
        proxy.disconnect()
    return True

def cmd_showhistory(userInput: str, proxy: Proxy) -> bool:
    if userInput.strip() != "":
        idx = int(userInput)
    else:
        idx = -1
    proxy.application.cmd_showhistory(idx)
    return True

def cmd_clearhistory(userInput: str, proxy: Proxy) -> bool:
    if userInput.strip() != "":
        idx = int(userInput)
    else:
        idx = -1
    proxy.application.cmd_clearhistory(idx)
    return True

def cmd_lssettings(userInput: str, proxy: Proxy) -> bool:
    longestKeyName = 0
    for key in proxy.settings.keys():
        keyName = key.name
        lenKeyName = len(keyName)
        if lenKeyName > longestKeyName:
            longestKeyName = lenKeyName

    for key in proxy.settings.keys():
        keyName = key.name
        value = getSetting(key, proxy)
        keyStr = keyName.rjust(longestKeyName)
        print(f"{keyStr}: {value}")
    return True

def cmd_printhexdump(userInput: str, proxy: Proxy) -> bool:
    currentSetting = getSetting(ESettingKey.printhexdump, proxy)
    currentSetting = not currentSetting
    setSetting(ESettingKey.printhexdump, currentSetting, proxy)
    print(f"Printing of packets is now {'enabled' if currentSetting else 'disabled'}")
    return True    

###############################################################################
# No need to edit the functions below

# This function take the command line string and calls the relevant python function with the correct arguments.
def handleUserInput(userInput: str, proxy: Proxy) -> bool:
    userInput = userInput.lstrip()
    cmd = userInput.split(' ')[0].strip().lower()
    if userInput.find(' ') >= 0 and userInput.find(' ') != len(userInput):
        userInput = userInput[userInput.find(' ') + 1:]
    else:
        userInput = ''

    cmdList = buildCommandDict()
    if cmd == '':
        pass
        # Skip empty commands
    elif cmd in cmdList.keys():
        function, helptext = cmdList[cmd]
        return function(userInput, proxy)
    else:
        print(f"Undefined command: \"{cmd}\"")
    
    # Keep going.
    return True

# Wrapper for proxy.getSetting to handle default values. Use this function only in this file.
# Don't make calls to proxy.getSetting elsewhere.
def getSetting(settingKey: ESettingKey, proxy: Proxy) -> object:
    ret = proxy.getSetting(settingKey)
    if ret is None:
        ret = settingsDefaults(settingKey)
        if ret is None:
            print(f"No default value for settingKey {settingKey.name}.")
        else:
            setSetting(settingKey, ret, proxy)
    return ret

# Wrapper for proxy.setSetting. Use this function only in this file.
# Don't make calls to proxy.setSetting elsewhere.
def setSetting(settingKey: ESettingKey, settingValue: object, proxy: Proxy) -> None:
    proxy.setSetting(settingKey, settingValue)
    return

