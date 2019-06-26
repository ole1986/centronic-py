#!/usr/bin/python3

import sys, getopt, os, time
import serial # pyserial module required

# <STX> and <ETX> for every single code being send
STX = b'\x02'
ETX = b'\x03'

number_file = "centronic-stick.num"
code_prefix = "0000000002010B" # 0-23 (24 chars)
code_suffix = "000000"
code_device = "1737b0" # 24-32 (8 chars) / CentralControl number (https://forum.fhem.de/index.php/topic,53756.165.html)
code_21 = "21"
code_remote = "01" # centronic remote control used "02" while contralControl seem to use "01"

COMMAND_UP = 0x20
COMMAND_UP2 = 0x22 # intermediate position "up"
COMMAND_DOWN = 0x40
COMMAND_DOWN2 = 0x44 # intermediate position "down" (sun protection)
COMMAND_HALT = 0x10
COMMAND_PAIR = 0x80
COMMAND_PAIR2 = 0x81 # simulates the delay of 3 seconds
COMMAND_PAIR3 = 0x82 # simulates the delay of 6 seconds
COMMAND_PAIR4 = 0x83 # simulates the delay of 10 seconds (important for deletion)

def showhelp():
	print('%s [-hlit] [--checksum <code>] [--device <device>] [--send <UP|UP2|DOWN|DOWN2|HALT|PAIR> --channel <channel>]' % sys.argv[0])
	print('')
	print('This script is used send command codes to CC11/CC51 compatible receivers through the CentronicControl USB Stick')
	print('It is necessary to own such USB device and to PAIR it first, before using commands like UP and DOWN')
	print('')
	print("                 -h: shows this help")
	print("                 -l: listen on the centronic USB device to fetch the codes")
	print("                 -i: increment the number (possible workaround for already consumed numbers)")
	print("                 -t: test mode - no codes will be send and no numbers consumed / works only with '--send'")
	print("   --send <command>: submit a completely generated code for UP/UP2/DOWN/DOWN2/HALT/PAIR commands / requires '--channel'")
	print("                     While UP2 and DOWN2 are the intermediate position (E.g. sun protection)")
	print("  --device <device>: set the device if it differs from the default")
	print("--channel <channel>: define the channel (1-15) being used for '--send'")
	print("  --checksum <code>: add a checksum to the given 40 char code and output (without STX, ETX)")
	print('')
	print('Version 0.3 - Author: ole1986')

def listen(devname):
	if not devname:
		print("No device defined")

	print("Listening on %s" % devname)
	with serial.Serial(devname, 115200, timeout=1) as ser:
		while(True):
			if (ser.inWaiting()>0):
				data_str = ser.read(ser.inWaiting())
				print(data_str)

def increment_number():
	number = read_number()
	number += 1

	filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), number_file)
	file = open(filepath, "w") 
	file.write(str(number))

def read_number():
	filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), number_file)
	exists = os.path.isfile(filepath)
	number = "0"
	if exists:
		file = open(filepath, "r")
		number = file.read()
	return int(number)

def send(cmd, channel, devname, test = False):
	ch = int(channel)

	if ch < 1 or ch > 15:
		print("Channel must be in range 1-15 (15 = F)")
		return

	if not devname:
		print("No device defined")
		return

	codes = []

	with serial.Serial(devname, 115200, timeout=1) as ser:

		if cmd == "UP":
			codes.append(generatecode(ch, COMMAND_UP))
		elif cmd == "UP2":
			codes.append(generatecode(ch, COMMAND_UP2))
		elif cmd == "HALT":
			codes.append(generatecode(ch, COMMAND_HALT))
		elif cmd == "DOWN":
			codes.append(generatecode(ch, COMMAND_DOWN))
		elif cmd == "DOWN2":
			codes.append(generatecode(ch, COMMAND_DOWN2))
		elif cmd == "PAIR":
			codes.append(generatecode(ch, COMMAND_PAIR))
			if not test:
				increment_number()
			codes.append(generatecode(ch, COMMAND_PAIR2))

		if not test:
			increment_number()

		codes.append(generatecode(ch, 0)) # append the release button code

		if not test:
			increment_number()

		if test: 
			print("Running in TEST MODE (no codes will be sent / no numbers increased)")
		else:
			print("Running in LIVE MODE")
	
		for code in codes:
			if test:
				print("[TEST MODE] Sending code %s to device %s" % (finalizeCode(code), devname))
			else:
				print("Sending code %s to device %s" % (code, devname))

			if not test: 
				ser.write(finalizeCode(code))

			time.sleep(0.1)

def hex2(n):
    return "%02X"%(n&0xFF)

def hex4(n):
	return "%04X"%(n&0xFFFF)

def generatecode(channel, cmd, with_checksum = True):
	number = read_number()
	code = code_prefix + ("%s" % hex4(number)) + code_suffix  + code_device + code_21 + code_remote
	code += ("%s" % hex2(channel)) + "00" + ("%s" % hex2(cmd))

	if with_checksum:
		code = checksum(code)

	return code

def finalizeCode(code):
	return STX + code.encode() + ETX

def checksum(code):
	l = len(code)

	if l != 40:
		print("The code must be 40 characters long (without <STX>, <ETX> and checksum)")
		return

	sum = 0
	i = 0
	while i < l:
		hex = code[i] + code[i + 1]
		sum += int(hex, 16)
		i += 2

	return '%s%s' % (code.upper(), hex2(0x03 - sum))

def main(argv):
	try:
		test_only = False
		is_listen = False
		is_send = False
		device = '/dev/serial/by-id/usb-BECKER-ANTRIEBE_GmbH_CDC_RS232_v125_Centronic-if00'
		code = ""
		cmd = ""
		channel = "0"
		
		opts, args = getopt.getopt(argv,"hlit",["checksum=", "device=", "channel=","send="])

		if len(opts) < 1:
			showhelp()

		for(opt,arg) in opts:
			if opt == '-h':
				showhelp()
			elif opt in ('-i'):
				increment_number()
			elif opt in ('-t'):
				test_only = True
			elif opt in ('--device'):
				device = arg
			elif opt in ('-l'):
				is_listen = True
			elif opt in ('--channel'):
				channel = arg
			elif opt in ('--send'):
				cmd = arg
				is_send = True
			elif opt in ("--checksum"):
				code = arg

		if is_listen and not is_send:
			listen(device)
		elif is_send and not is_listen:
			send(cmd, channel, device, test_only)
		elif code:
			code = checksum(code)
			if code: 
				print(code)

	except getopt.GetoptError:
		sys.exit(2)
	except KeyboardInterrupt:
		sys.exit()

if __name__ == "__main__":
   main(sys.argv[1:])
