#!/usr/bin/python3

import sys
import getopt
import os
import time
import sqlite3
import socket
import serial  # pyserial module required

# <STX> and <ETX> for every single code being send
STX = b'\x02'
ETX = b'\x03'

default_device_name = '/dev/serial/by-id/usb-BECKER-ANTRIEBE_GmbH_CDC_RS232_v125_Centronic-if00'
number_file = "centronic-stick.num"
code_prefix = "0000000002010B"  # 0-23 (24 chars)
code_suffix = "000000"
# 24-32 (8 chars) / CentralControl number (https://forum.fhem.de/index.php/topic,53756.165.html)
code_device = "1737b0"
code_21 = "21"
# centronic remote control used "02" while contralControl seem to use "01"
code_remote = "01"

COMMAND_HALT = 0x10
COMMAND_UP = 0x20
COMMAND_UP2 = 0x24  # intermediate position "up"
COMMAND_DOWN = 0x40
COMMAND_DOWN2 = 0x44  # intermediate position "down" (sun protection)
COMMAND_PAIR = 0x80
COMMAND_PAIR2 = 0x81  # simulates the delay of 3 seconds
COMMAND_PAIR3 = 0x82  # simulates the delay of 6 seconds
# simulates the delay of 10 seconds (important for deletion)
COMMAND_PAIR4 = 0x83


def showhelp():
    print('%s [-hlit] [--checksum <code>] [--device <device>] [--send <UP|UP2|DOWN|DOWN2|HALT|PAIR|PAIRMASTER> --channel <channel>]' % sys.argv[0])
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
    print("  --device <device>: set the device if it differs from the default, also host:port possible (ser2net)")
    print("--channel <channel>: define the channel (1-15) being used for '--send'")
    print("  --checksum <code>: add a checksum to the given 40 char code and output (without STX, ETX)")
    print('')
    print('Version 0.4 - Authors: ole1986, toolking')

class NumberFile:

    def __init__(self, filename=number_file, value=0):
        self.value = value
        self.filename = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), filename)
        if not os.path.isfile(self.filename):
            with open(self.filename, "w") as file:
                file.write(str(self.value))

    def inc(self, test=False):
        if test:
            return
        number = self.get() + 1
        with open(self.filename, "w") as file:
            file.write(str(number))

    def get(self):
        number = str(self.value)
        with open(self.filename, "r") as file:
            number = file.read()
        return int(number)

class Database:

    def __init__(self):
        self.filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'centronic-stick.db')
        self.conn = sqlite3.connect(self.filename)
        self.check()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()
        
    def check(self):
        # check if table already exist
        c = self.conn.cursor()
        checkTable = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='channel'")
        if checkTable.fetchone() is None:
            self.create()
            self.migrate()

    def migrate(self):
        # migrate the previous *.num file into its sqllite database
        self.oldfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), number_file)

        if not os.path.isfile(self.oldfile):
            return

        try:
            print('Migrate previous *.num file...')
            with open(self.oldfile, "r") as file:
                number = int(file.read())

            c = self.conn.cursor()
            c.execute("UPDATE channel SET increment = ?", (number,))
            self.conn.commit()
            os.remove(self.oldfile)
        except:
            print('Migration failed')
            self.conn.rollback()

    def create(self):
        # create the database table

        print('Create database...')
        c = self.conn.cursor()
        c.execute('CREATE TABLE channel (number INTEGER(1), increment INTEGER(4), executed INTEGER, UNIQUE(number))')
        for i in range(1, 15):
            c.execute("INSERT INTO channel VALUES (?, ?, ?)", (i, 0, 0,))

        self.conn.commit()

    def output(self):
        c = self.conn.cursor()
        res = c.execute('SELECT * FROM channel')
        print('%-10s%-10s%-15s' % ('channel', 'increment', 'last run'))
        for line in res.fetchall():
            lastrun='(unknown)'
            if line[2] > 0:
                lastrun = time.strftime('%Y-%m-%d %H:%m', time.localtime(line[2]))
            print('%-10s%-10s%-15s' % (line[0], line[1], lastrun))

    def inc(self, channel, test=False):
        c = self.conn.cursor()
        last_run = int(time.time())

        if channel == 15:
            # update all channels when broadcast is called
            c.execute('UPDATE channel SET increment = (SELECT MAX(increment) FROM channel) + 1, executed = ?', (last_run,))
        else:
            # update only the related
            c.execute('UPDATE channel SET increment = increment + 1, executed = ? WHERE number = ?', (last_run, channel,))
        
        if test:
            self.conn.rollback()
            return

        self.conn.commit()
    def get(self, channel):
        c = self.conn.cursor()

        if channel == 15:
            result = c.execute('SELECT MAX(increment) FROM channel')
        else:
            result = c.execute('SELECT increment FROM channel WHERE number = ?', (channel,))
        return int(result.fetchone()[0])

class USBStick:

    def __init__(self, conn, devname=default_device_name):
        self.is_serial = "/" in devname
        if self.is_serial and not os.path.exists(devname):
            raise FileExistsError(devname + " don't exists")
        self.device = devname
        self.db = conn
        if self.is_serial:
            self.s = serial.Serial(self.device, 115200, timeout=1)
            self.write_function = self.s.write
        else:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if ':' in devname:
                host,port = self.device.split(':')
            else:
                host = devname
                port = '5000'
            self.s.connect((host,int(port)))
            self.write_function = self.s.sendall

    def write(self,codes,test):
        for code in codes:
            if test:
                print("[TEST MODE] Sending code %s to device %s" %
                    (finalizeCode(code), self.device))
            else:
                print("Sending code %s to device %s" %
                    (code, self.device))

            if not test:
                self.write_function(finalizeCode(code))
            time.sleep(0.1)

    def send(self, cmd, channel, test=False):
        ch = int(channel)

        if not 1 <= ch <= 15:
            print("Channel must be in range 1-15 (15 = F)")
            return

        if not self.device:
            print("No device defined")
            return

        codes = []
        if cmd == "UP":
            codes.append(self.generatecode(ch, COMMAND_UP))
        elif cmd == "UP2":
            codes.append(self.generatecode(ch, COMMAND_UP2))
        elif cmd == "HALT":
            codes.append(self.generatecode(ch, COMMAND_HALT))
        elif cmd == "DOWN":
            codes.append(self.generatecode(ch, COMMAND_DOWN))
        elif cmd == "DOWN2":
            codes.append(self.generatecode(ch, COMMAND_DOWN2))
        elif cmd == "PAIR":
            codes.append(self.generatecode(ch, COMMAND_PAIR))
            self.db.inc(ch, test)
            codes.append(self.generatecode(ch, COMMAND_PAIR2))
        elif cmd == "PAIRMASTER":
            codes.append(self.generatecode(ch, COMMAND_PAIR))
            self.db.inc(ch, test)
            codes.append(self.generatecode(ch, COMMAND_PAIR4))

        self.db.inc(ch, test)

        # append the release button code
        codes.append(self.generatecode(ch, 0))

        self.db.inc(ch, test)

        if test:
            print("Running in TEST MODE")
        else:
            print("Running in LIVE MODE")

        self.write(codes,test)

    def listen(self):
        if self.is_serial:
            print("Listening on %s" % self.device)
            while(True):
                if (self.s.inWaiting() > 0):
                    data_str = self.s.read(self.s.inWaiting())
                    print(data_str)
        else:
            while(True):
                data = self.s.recv(48)
                print ('Received', repr(data))

    def generatecode(self, channel, cmd_code, with_checksum=True):
        number = self.db.get(channel)
        code = "".join([
            code_prefix,
            hex4(number),
            code_suffix,
            code_device,
            code_21,
            code_remote,
            hex2(channel),
            '00',
            hex2(cmd_code)
        ])
        return checksum(code) if with_checksum else code


def hex2(n):
    return '%02X' % (n & 0xFF)


def hex4(n):
    return '%04X' % (n & 0xFFFF)


def finalizeCode(code):
    return b"".join([STX,code.encode(),ETX])


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
        is_stats = False
        code = ""
        cmd = ""
        channel = "0"
        device = default_device_name
        opts, _ = getopt.getopt(
            argv, "hlits", ["checksum=", "device=", "channel=", "send="])

        if len(opts) < 1:
            showhelp()
            return

        for (opt, arg) in opts:
            if opt == '-h':
                showhelp()
                return
            elif opt in ['-s']:
                is_stats = True
            elif opt in ('-i'):
                NumberFile().inc()
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

        with Database() as db:
            stick = USBStick(db, device)
            if is_stats:
                db.output()
            if is_listen and not is_send:
                stick.listen()
            elif is_send and not is_listen:
                stick.send(cmd, channel, test_only)
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
