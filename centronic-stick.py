#!/usr/bin/python3

import sys
import getopt
import os
import time
import sqlite3
import socket
import serial  # pyserial module required
import time
import re

# <STX> and <ETX> for every single code being send
STX = b'\x02'
ETX = b'\x03'

DEFAULT_DEVICE_NAME = '/dev/serial/by-id/usb-BECKER-ANTRIEBE_GmbH_CDC_RS232_v125_Centronic-if00'
NUMBER_FILE = "centronic-stick.num" # (deprecated) previously used to store increment counter
CODE_PREFIX = "0000000002010B"  # some code prefix 0-23 (24 chars) followed by the increment
CODE_SUFFIX = "000000" # some code suffix right after the increment
CODE_21 = "021" # some code "021" right after the unit ids
CODE_REMOTE = "01" # centronic remote control used "02" while contralControl seem to use "01"

COMMAND_HALT = 0x10 # stop 
COMMAND_UP = 0x20 # move up
COMMAND_UP2 = 0x21 # move up
COMMAND_UP3 = 0x22 # move up
COMMAND_UP4 = 0x23 # move up
COMMAND_UP5 = 0x24  # intermediate position "up"
COMMAND_DOWN = 0x40 # move down
COMMAND_DOWN2 = 0x41 # move down
COMMAND_DOWN3 = 0x42 # move down
COMMAND_DOWN4 = 0x43 # move down
COMMAND_DOWN5 = 0x44  # intermediate position "down" (sun protection)
COMMAND_PAIR = 0x80 # pair button press
COMMAND_PAIR2 = 0x81  # pair button pressed for 3 seconds (without releasing)
COMMAND_PAIR3 = 0x82  # pair button pressed for 6 seconds (without releasing)
COMMAND_PAIR4 = 0x83 # pair button pressed for 10 seconds (without releasing)

COMMAND_CLEARPOS = 0x90
COMMAND_CLEARPOS2 = 0x91
COMMAND_CLEARPOS3 = 0x92
COMMAND_CLEARPOS4 = 0x93

def showhelp():
    print('%s [-hlst] [--checksum <code>] [--device <device>] [--send <UP|UP2|DOWN|DOWN2|HALT|TRAIN|TRAINMASTER|REMOVE> --channel <[unit:]channel>]' % sys.argv[0])
    print('')
    print('This script is used send command codes to CC11/CC51 compatible receivers through the CentronicControl USB Stick')
    print('It is necessary to own such USB device and to PAIR it first, before using commands like UP and DOWN')
    print('')
    print("                 -h: shows this help")
    print("                 -l: listen on the centronic USB device to fetch the codes")
    print("                 -s: display the current db stats (incl. last run of a unit)")
    print("                 -t: test mode - no codes will be send and no numbers consumed / works only with '--send'")
    print("   --send <command>: submit a completely generated code for UP/UP2/DOWN/DOWN2/HALT/TRAIN/REMOVE commands / requires '--channel'")
    print("                     While UP2 and DOWN2 are the intermediate position (E.g. sun protection)")
    print("  --device <device>: set the device if it differs from the default, also host:port possible (ser2net)")
    print("--channel <[unit:]channel>: define the unit (1-5) and channel (1-7) being used for '--send'. Example: 2:15 will close shutter for unit 2 on all channels")
    print("  --checksum <code>: add a checksum to the given 40 char code and output (without STX, ETX)")
    print("   --mod <modifier>: used to manipulate the db entries - FOR VERY ADVANCED USERS")
    print('')
    print('Version 0.6 - Authors: ole1986, toolking')

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
        checkTable = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='unit'")
        if checkTable.fetchone() is None:
            self.create()
            
        self.migrate()

    def migrate(self):
        try:
            # migrate the previous *.num file into its sqllite database
            self.oldfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), NUMBER_FILE)
            if os.path.isfile(self.oldfile):
                print('Migrate previous *.num file...')
                with open(self.oldfile, "r") as file:
                    number = int(file.read())
                    c = self.conn.cursor()
                    c.execute("UPDATE unit SET increment = ?, configured = ? WHERE code = ?", (number, 1, '1737b',))
                    self.conn.commit()
                    os.remove(self.oldfile)

            # add additional units
            c = self.conn.cursor()
            count = c.execute("SELECT COUNT(*) FROM unit").fetchone()[0]
            if count <= 3:
                print('Migrate more units...')
                c.execute("INSERT INTO unit VALUES (?, ?, ?, ?)", ('1737e', 0, 0, 0,))
                c.execute("INSERT INTO unit VALUES (?, ?, ?, ?)", ('1737f', 0, 0, 0,))
                self.conn.commit()
            
        except:
            print('Migration failed')
            self.conn.rollback()
        
    def create(self):
        # create the database table

        print('Create database...')
        c = self.conn.cursor()
        c.execute('CREATE TABLE unit (code NVARCHAR(5), increment INTEGER(4), configured BIT, executed INTEGER, UNIQUE(code))')
        c.execute("INSERT INTO unit VALUES (?, ?, ?, ?)", ('1737b', 0, 0, 0,))
        c.execute("INSERT INTO unit VALUES (?, ?, ?, ?)", ('1737c', 0, 0, 0,))
        c.execute("INSERT INTO unit VALUES (?, ?, ?, ?)", ('1737d', 0, 0, 0,))

        self.conn.commit()

    def output(self):
        c = self.conn.cursor()
        res = c.execute('SELECT * FROM unit')
        print('%-10s%-10s%-12s%-15s' % ('code', 'increment', 'configured', 'last run'))
        for line in res.fetchall():
            lastrun='(unknown)'
            if line[3] > 0:
                lastrun = time.strftime('%Y-%m-%d %H:%M', time.localtime(line[3]))
            print('%-10s%-10s%-12s%-15s' % (line[0], line[1], line[2] ,lastrun))

    def get_unit(self, rowid):
        c = self.conn.cursor()
        res = c.execute("SELECT code, increment, configured FROM unit WHERE rowid = ?", (rowid,))
        result = res.fetchone()

        return list(result) if result is not None else result
        #if result is not None:
        #    return list(result)

    def get_all_units(self):
        c = self.conn.cursor()
        res = c.execute('SELECT code, increment, configured FROM unit WHERE configured = 1 ORDER BY code ASC')
        result = []

        for row in res.fetchall():
            result.append(list(row))
        
        return result

    def set_unit(self, unit, test=False):
        c = self.conn.cursor()
        last_run = int(time.time())

        c.execute('UPDATE unit SET increment = ?, configured = ?, executed = ? WHERE code = ?', (unit[1], unit[2], last_run, unit[0],))

        if test:
            self.conn.rollback()
            return
        
        self.conn.commit()
    
class USBStick:

    def __init__(self, conn, devname=DEFAULT_DEVICE_NAME):
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
                    (code, self.device))
            else:
                print("Sending code %s to device %s" %
                    (code, self.device))

            if not test:
                self.write_function(finalizeCode(code))
            time.sleep(0.1)

    def send(self, cmd, channel, test=False):
        b = channel.split(':')
        if len(b) > 1:
            ch = int(b[1])
            un = int(b[0])
        else:
            ch = int(channel)
            un = 1

        if not 1 <= ch <= 7 and ch != 15:
            print("Channel must be in range of 1-7 or 15")
            return

        if not self.device:
            print("No device defined")
            return

        if un > 0:
            unit = self.db.get_unit(un)
            if unit is None:
                print("No unit on index %s found" % (un))
                return
            self.runcodes(ch, unit, cmd, test)
        else:
            units = self.db.get_all_units()
            for unit in units:
                self.runcodes(ch, unit, cmd, test)

    def runcodes(self, channel, unit, cmd, test):
        if unit[2] == 0 and cmd != "TRAIN" and cmd != "TRAINMASTER":
            print("The unit %s is not configured" % (unit[0]))
            return

        # move up/down dependent on given time
        mt = re.match("(DOWN|UP):(\d+)", cmd)

        codes = []
        if cmd == "UP":
            codes.append(self.generatecode(channel, unit, COMMAND_UP))
        elif cmd == "UP2":
            codes.append(self.generatecode(channel, unit, COMMAND_UP5))
        elif cmd == "HALT":
            codes.append(self.generatecode(channel, unit, COMMAND_HALT))
        elif cmd == "DOWN":
            codes.append(self.generatecode(channel, unit, COMMAND_DOWN))
        elif cmd == "DOWN2":
            codes.append(self.generatecode(channel, unit, COMMAND_DOWN5))
        elif cmd == "CLEARPOS":
            codes.append(self.generatecode(channel, unit, COMMAND_PAIR))
            unit[1] += 1
            codes.append(self.generatecode(channel, unit, COMMAND_CLEARPOS))
            unit[1] += 1
            codes.append(self.generatecode(channel, unit, COMMAND_CLEARPOS2))
            unit[1] += 1
            codes.append(self.generatecode(channel, unit, COMMAND_CLEARPOS3))
            unit[1] += 1
            codes.append(self.generatecode(channel, unit, COMMAND_CLEARPOS4))
        elif cmd == "TRAIN":
            codes.append(self.generatecode(channel, unit, COMMAND_PAIR))
            unit[1] += 1
            codes.append(self.generatecode(channel, unit, COMMAND_PAIR2))
            unit[1] += 1
            codes.append(self.generatecode(channel, unit, COMMAND_PAIR))
            unit[1] += 1
            codes.append(self.generatecode(channel, unit, COMMAND_PAIR2))
            # set unit as configured
            unit[2] = 1
        elif cmd == "REMOVE":
            codes.append(self.generatecode(channel, unit, COMMAND_PAIR))
            unit[1] += 1
            codes.append(self.generatecode(channel, unit, COMMAND_PAIR2))
            unit[1] += 1
            codes.append(self.generatecode(channel, unit, COMMAND_PAIR))
            unit[1] += 1
            codes.append(self.generatecode(channel, unit, COMMAND_PAIR2))
            unit[1] += 1
            codes.append(self.generatecode(channel, unit, COMMAND_PAIR3))
            unit[1] += 1
            codes.append(self.generatecode(channel, unit, COMMAND_PAIR4))
        elif cmd == "TRAINMASTER":
            codes.append(self.generatecode(channel, unit, COMMAND_PAIR))
            unit[1] += 1
            codes.append(self.generatecode(channel, unit, COMMAND_PAIR2))
            unit[1] += 1
            codes.append(self.generatecode(channel, unit, COMMAND_PAIR3))
            unit[1] += 1
            codes.append(self.generatecode(channel, unit, COMMAND_PAIR4))
            # set unit as configured
            unit[2] = 1

        if mt:
            print("Moving %s for %s seconds..." % (mt.group(1), mt.group(2)))
            # move down/up for a specific time
            if mt.group(1) == "UP":
                code = self.generatecode(channel, unit, COMMAND_UP)
            elif mt.group(1) == "DOWN":
                code = self.generatecode(channel, unit, COMMAND_DOWN)

            unit[1] += 1
            self.write([code],test)
            time.sleep(int(mt.group(2)))
        else:
            unit[1] += 1

        # append the release button code
        codes.append(self.generatecode(channel, unit, 0))
        unit[1] += 1

        self.write(codes,test)
        self.db.set_unit(unit, test)

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

    def generatecode(self, channel, unit, cmd_code, with_checksum=True):
        unitId = unit[0] # contains the unit code in hex (5 chars)
        unitIncrement = unit[1] # contains the next increment (required to convert into hex4)

        code = CODE_PREFIX + hex4(unitIncrement) + CODE_SUFFIX + unitId + CODE_21 + CODE_REMOTE + hex2(channel) + '00' + hex2(cmd_code)
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
        mod = ""
        code = ""
        cmd = ""
        channel = "0"
        device = DEFAULT_DEVICE_NAME
        opts, _ = getopt.getopt(
            argv, "hlits", ["checksum=", "device=", "channel=", "send=", "mod="])

        if len(opts) < 1:
            showhelp()
            return

        for (opt, arg) in opts:
            if opt == '-h':
                showhelp()
                return
            elif opt in ['-s']:
                is_stats = True
            elif opt in ('-t'):
                test_only = True
            elif opt in ('--device'):
                device = arg
            elif opt in ('-l'):
                is_listen = True
            elif opt in ('--mod'):
                mod = arg
            elif opt in ('--channel'):
                channel = arg
            elif opt in ('--send'):
                cmd = arg
                is_send = True
            elif opt in ("--checksum"):
                code = arg

        with Database() as db:
            stick = USBStick(db, device)
            if mod:
                unit = mod.split(':')
                db.set_unit(unit)
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
