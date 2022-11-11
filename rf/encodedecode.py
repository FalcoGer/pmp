#!/bin/python3

import argparse


def main():
    args = parse_args()
    result = '';
    
    for c in args.data:
        if not c in ['0', '1']:
            print(f'Bad data: \'{args.data=}\'')
            exit(1)

    if args.proto == 'came':
        result = came(args.data, args.direction, args.repeat, args.syncbit)
    elif args.proto == 'nice':
        result = nice(args.data, args.direction, args.repeat, args.syncbit)
    else:
        result = f'Protocol {args.proto} not implemented.'
    
    print(f'{result}')
    
    exit(0)

# format starts with 1, then 0X1 where X is the bit to be transmitted, but inverted.
def came(data: str, direction: str, repeat: int, syncbit: bool) -> str:
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

        if syncbit:
            result += '1' + pause

        for _ in range(0, repeat):
            result += '1' # start bit
            for c in data:
                result += '011' if c == '0' else '001'
            result += pause
        result = result.rstrip('0')
    return result

# format starts with 11, then 00X11 where Xx is the bit to be transmitted twice, but inverted.
def nice(data: str, direction: str, repeat: int, syncbit: bool) -> str:
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

        if syncbit:
            result = '1' + pause
        for _ in range(0, repeat):
            result += '11' # start bit
            for c in data:
                result += '001111' if c == '0' else '000011'
            result += pause
        result = result.rstrip('0')
    return result

def parse_args():
    parser = argparse.ArgumentParser(description='Decode and encode radio protocols for URH')

    parser.add_argument('--proto', dest='proto', help='Protocol to decode or encode', choices=['came', 'nice'], required=True)
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
