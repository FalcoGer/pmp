#!/bin/python3

import argparse


def main():
    args = parse_args()
    result = '';
    
    if len(args.data) == 0:
        print("No data.")

    for c in args.data:
        if not c in ['0', '1']:
            print(f'Bad data: \'{args.data=}\'')
            exit(1)

    if args.proto == 'came':
        result = came(args.data, args.direction, args.repeat, args.wakeupbit)
    elif args.proto == 'nice':
        result = nice(args.data, args.direction, args.repeat, args.wakeupbit)
    elif args.proto == 'chamberlain':
        result = chamberlain(args.data, args.direction, args.repeat, args.wakeupbit)
    elif args.proto == 'linear':
        result = linear(args.data, args.direction, args.repeat, args.wakeupbit)
    else:
        result = f'Protocol {args.proto} not implemented.'
    
    print(f'{result}')
    
    exit(0)

# format starts with 1, then 0X1 where X is the bit to be transmitted, but inverted. (700 samples / symbol @ 2M samples/s)
def came(data: str, direction: str, repeat: int, wakeupbit: bool) -> str:
    result = ''
    if direction == 'decode':
        idx = 0
        bytesCount = 0
        for c in data:
            b = int(c)
            # first bit is startbit
            if idx == 0:
                if b == 0:
                    print(f'Bad Format, start bit must be 1, but found {b} at index {idx}.')
                    return result;
            elif (idx % 3 == 1 and b == 1) or (idx % 3 == 0 and b == 0):
                    print(f'Bad Format, carrier must be 0X1, but found {b} at index {idx}.')
                    return result;
            elif (idx % 3 == 2):
                result += '1' if b == 0 else '0'
            
            idx += 1
    elif direction == 'encode':
        result = ''
        pause = '0'*36

        if wakeupbit:
            result += '1' + pause

        for _ in range(0, repeat):
            result += '1' # start bit
            for c in data:
                result += '011' if c == '0' else '001'
            result += pause
        result = result.rstrip('0')
    return result

# format starts with 1, then 0X11 where X is the bit to be transmitted, but inverted. Special marker is 0001. (2000 samples / symbol @ 2M samples/s)
# if less than 9 bits are transmitted, then the signal is encoded as such
# 9bit:   S D8 D7 D6 D5 D4 D3 D2 D1 D0  S
# 8bit:   S D7 D6 D5 D4 D3  S D1 D0  S
# 7bit:   S D6 D5 D4 D3 D2 D1  S  S D0  S
# idx        0  1  2  3  4  5  6  7  8  9
# 
# Bit 3 (D2) is dropped for 8 bit codes
# See: https://github.com/flipperdevices/flipperzero-firmware/issues/2006
def chamberlain(data: str, direction: str, repeat: int, wakeupbit: bool) -> str:
    result = ''
    if direction == 'decode':
        idx = 0
        bytesCount = 0
        if data[0] == 0:
            print(f'Bad Format, start bit must be 1, but found {b} at index {idx}.')
            return result;

        data = data[1:] # cut off start bit
        if len(data) % 4 != 0:
            print(f'Bad Format, data length needs to be divisible by 4, but it\'s {len(data)}.')
            return result
        
        # loop over data in blocks of 4
        eightBit = False
        sevenBit = False
        
        one = '0011'
        zero = '0111'
        mark = '0001'

        for idx in range(0, int(len(data) / 4)):
            block = data[idx*4:idx*4+4]
            if block == one:
                result += '1'
            elif block == zero:
                result += '0'
            elif block == mark:
                if (idx == 5):
                    eightBit = True
                    result += '0' # 3rd bit is dropped, but still considered 8 bit code for some reason
                elif (idx == 6):
                    if eightBit:
                        print("Bad Format, found special marker at index 5 (8Bit), can't have special marker at index 6(7Bit).")
                        return result
                    sevenBit = True
                elif (idx == 7):
                    if not sevenBit:
                        print("Bad Format, symbol at bit 7 indicates a 7 bit code, but index 6 wasn't set to 0001.")
                        return result
            else:
                print(f"Bad Format, data block invalid at index {idx*4}. Expected '0011', '0111' or '0001', but found {data[idx*4:idx*4+4]}.")
                return result
            if idx == 8 and eightBit:
                if not block == 1:
                    print("Bad Format, 8 Bit codes must end with marker symbol at index 8.")
                    return result
            if idx == 9:
                if not block == 1 and not eightBit:
                    print("Bad Format, symbol at index 9 must be 0001.")
                    return result
                elif eightBit:
                    print("Bad Format, max synbols for 8 bits is 10.")
                    return result
            elif idx == 10:
                print("Bad Format, max symbols is 11.")
    elif direction == 'encode':
        result = ''
        pause = '0'*39 # 39ms

        if len(data) < 7 or len(data) > 9:
            print("Data must be 7, 8 or 9 bits.")
            return result

        if wakeupbit:
            result += '1' + pause
        
        for _ in range(0, repeat):
            result += '1' # start bit
            idx = 0
            for c in data:
                # this is what flipper zero accepts as 8 bit chamberlain
                # dropping 3rd bit
                if idx == 5 and len(data) == 8:
                    idx += 1
                    result += '0001'
                    continue
                
                # append data
                result += '0111' if c == '0' else '0011'

                if idx == 5:
                    if len(data) < 9:
                        result += '0001'
                    if len(data) < 8:
                        result += '0001'
                idx += 1
            result += '0001'
            result += pause
        result = result.rstrip('0')
    return result

# format starts with 11, then 00XX11 where XX is the bit to be transmitted twice, but inverted. (700 samples/symbol @ 2M samples/s)
def nice(data: str, direction: str, repeat: int, wakeupbit: bool) -> str:
    result = ''
    if direction == 'decode':
        idx = 0
        bytesCount = 0
        for c in data:
            b = int(c)
            # first bit is startbit
            if idx == 0 or idx == 1:
                if b == 0:
                    print(f'Bad Format, start bit must be 11, but found {b} at index {idx}.')
                    return result;
            # 11 00 xx 11   00 xx 11
            # 01 23 45 67   89
            elif (idx % 6 == 2 and b == 1 or idx % 6 == 3 and b == 1) or (idx % 6 == 0 and b == 0 or idx % 6 == 1 and b == 0):
                print(f'Bad Format, carrier must be 00XX11, but found {b} at index {idx}.')
                return result;
            elif (idx % 6 == 4):
                result += '1' if b == 0 else '0'
            elif (idx % 6 == 5):
                expected = 0 if result[-1] == '1' else 1
                if b != expected:
                    print(f'Bad Format, both data bits in one block must be the same, but found {b} at index {idx}.')
                    return result
            idx += 1
    elif direction == 'encode':
        result = ''
        pause = '0'*72

        if wakeupbit:
            result = '1' + pause
        for _ in range(0, repeat):
            result += '11' # start bit
            for c in data:
                result += '001111' if c == '0' else '000011'
            result += pause
        result = result.rstrip('0')
    return result

# dumb format. 1000 for 0, 1110 for 1. (2000 Samples/symbol @ 2M Samples/s)
def linear(data: str, direction: str, repeat: int, wakeupbit: bool) -> str:
    result = ''
    if direction == 'decode':
        # pad right with 0 to make it divisible by 4
        if len(data) % 4 != 0:
            data = data + ("0" * (4 - (len(data) % 4)))

        for idx in range(0, int(len(data) / 4)):
            block = data[idx*4:idx*4+4]
            if block == '1000':
                result += '0'
            elif block == '1110':
                result += '1'
            else:
                print(f"Bad Format, block at {idx} expected '1000' or '1110', but got '{block}'.")
                return result
    elif direction == 'encode':
        result = ''
        pause = '0'*40

        for _ in range(0, repeat):
            for c in data:
                result += '1000' if c == '0' else '1110'
            result += pause
        result = result.rstrip('0')
    return result

def parse_args():
    parser = argparse.ArgumentParser(description='Decode and encode radio protocols for URH')

    parser.add_argument('--proto', dest='proto', help='Protocol to decode or encode', choices=['came', 'nice', 'chamberlain', 'linear'], required=True)
    parser.add_argument('--dir', dest='direction', help='Decode or Encode', choices=['encode', 'decode'], required=True)
    parser.add_argument('--wakeupbit', dest='wakeupbit', help='On encoding, send wakeup bit up front', choices=['yes', 'no'], default='no', required=False)
    parser.add_argument('--repeat', dest='repeat', help='How often to repeat', type=int, default=1, required=False)
    parser.add_argument('data', help='Data to work on.')

    args = parser.parse_args()

    args.wakeupbit = (args.wakeupbit == 'yes')

    # print(args)

    return args

if __name__ == '__main__':
    main()
