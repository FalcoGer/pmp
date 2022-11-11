#!/bin/python3

import argparse


def main():
    args = parse_args()
    result = "";
    
    for c in args.data:
        if not c in ['0', '1']:
            print(f"Bad data: '{args.data=}'")
            exit(1)

    if args.proto == 'came':
        result = came(args.data, args.direction, args.repeat, args.syncbit)
    
    print(f"{result}")
    
    exit(0)

# format starts with 1, then 0X1 where X is the bit to be transmitted, but inverted.
def came(data: str, direction: str, repeat: int, syncbit: bool) -> str:
    result = ""
    if direction == 'decode':
        idx = 0
        bytesCount = 0
        for c in data:
            b = int(c)
            # first bit is startbit
            if idx == 0:
                if b == 0:
                    print(f"Bad Format, start bit must be 1, but found {b} at index {idx}.")
                    return result;
            if (idx % 3 == 1 and b == 1) or (idx % 3 == 0 and b == 0):
                    print(f"Bad Format, carrier must be 0X1, but found {b} at index {idx}.")
                    return result;
            if (idx % 3 == 2):
                result += "1" if b == 0 else "0"
            
            idx += 1
    elif direction == 'encode':
        result = '1'
        pause = '0'*36

        if syncbit:
            result += pause + '1'

        for _ in range(0, repeat):
            for c in data:
                result += '011' if c == '0' else '001'
            result += pause
    result = result.strip('0')
    return result

def parse_args():
    parser = argparse.ArgumentParser(description='Decode and encode radio protocols for URH')

    parser.add_argument('--proto', dest='proto', help='Protocol to decode or encode', choices=['came'], required=True)
    parser.add_argument('--dir', dest='direction', help='Decode or Encode', choices=['encode', 'decode'], required=True)
    parser.add_argument('--syncbit', dest='syncbit', help='On encoding, send sync bit up front', choices=['yes', 'no'], default='no', required=False)
    parser.add_argument('--repeat', dest='repeat', help='How often to repeat', type=int, default=1, required=False)
    parser.add_argument('data', help='Data to work on.')

    args = parser.parse_args()

    args.syncbit = (args.syncbit == 'yes')

    # print(args)

    return args

if __name__ == '__main__':
    main()
