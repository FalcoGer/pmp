#!/bin/python3

import argparse
import requests
import json


def main():
    args = parse_args()
    # get the json, however provided
    j = {}
    if args.infile:
        j = json.load(args.infile)
        args.infile.close()
    elif args.msgid and args.apikey:
        host = args.apihost
        apikey = args.apikey
        msgid = args.msgid
        j = requests.get(url=f"{host}/JSON/core/view/message/?apikey={apikey}&id={msgid}")
        j = j.json()
    
    j = j['message']
    # build request file
    if not args.outfile:
        print(j['requestHeader'])
        print(j['requestBody'])        
    else:
        args.outfile.write(j['requestHeader'])
        args.outfile.write(j['requestBody'])        

def parse_args():
    parser = argparse.ArgumentParser(description='Turn ZAP messages into request files for sqlmap.')
    parser.add_argument('--msgid', dest='msgid', help='Message ID from ZAProxy', type=int)
    parser.add_argument('--apikey', dest='apikey', help='API Key for ZAProxy')
    parser.add_argument('--in', dest='infile', help='JSON formatted file from API', type=argparse.FileType('r'))
    parser.add_argument('--out', dest='outfile', help='RAW text file with HTTP request', type=argparse.FileType('w'))
    parser.add_argument('--apihost', dest='apihost', help='Host to request the data from.\nDefaults to http://localhost:8080', default='http://localhost:8080')
    
    # process command line
    args = parser.parse_args()
    
    # check validity
    if not args.infile and not (args.msgid and args.apikey):
        print("Needs Message ID and API Key or input file.")
        exit(-1)
    if args.msgid < 0:
        print(f"Bad MsgID: {args.msgid}")
        exit(-1)
    
    return args

if __name__ == '__main__':
    main()
