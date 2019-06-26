# Using Centronic USB Stick to control Becker Shutter CC11/CC51

This project is used to automate "Becker Antriebe" shutter also known as CC11 or CC51 using the Centronic Stick V2

```
./centronic-py/centronic-stick.py [-hlit] [--checksum <code>] [--device <device>] [--send <UP|UP2|DOWN|DOWN2|HALT|PAIR> --channel <channel>]

This script is used send command codes to CC11/CC51 compatible receivers through the CentronicControl USB Stick
It is necessary to own such USB device and to PAIR it first, before using commands like UP and DOWN

                 -h: shows this help
                 -l: listen on the centronic USB device to fetch the codes
                 -i: increment the number (possible workaround for already consumed numbers)
                 -t: test mode - no codes will be send and no numbers consumed / works only with '--send'
   --send <command>: submit a completely generated code for UP/UP2/DOWN/DOWN2/HALT/PAIR commands / requires '--channel'
                     While UP2 and DOWN2 are the intermediate position (E.g. sun protection)
  --device <device>: set the device if it differs from the default
--channel <channel>: define the channel (1-15) being used for '--send'
  --checksum <code>: add a checksum to the given 40 char code and output (without STX, ETX)

Version 0.2 - Author: ole1986
```

### PAIRING

Before the USB stick can be used, a pairing must be achieved.

To make the reciever listening to new senders, either the "receiver" itself or the "master sender" can be used. For the sake of simplicity the below steps are focused on the "master sender" (this can be a wall-mounted transmitter or a remote / BUT NEVER BOTH)

**1) Press and hold the programming button on the master sender for 3 seconds**
The receiver should confirm with a single "Klack" noise

**2) Run the below commands to simulate the programming button two time**
The receiver should confirm with a single "Klack" noise followed by a "Klack - Klack" once the pairing succeeded

```
./centronic-stick.py --send PAIR --channel 1
./centronic-stick.py --send PAIR --channel 1
```

Repeat the steps for all receivers.
To control each receiver individually it is neccessary to change the channel number. Otherwise all paired receivers will act on the same channel

*You have successfully paired the Centronic Stick with your shutter*

### CONTROL

To move down the shutter, run the below command (amend the channel if neccessary)

```
./centronic-stick.py --send DOWN --channel 1
```

To move up the shutter, run the below command

```
./centronic-stick.py --send UP --channel 1
```

To pause the movement, run the command

```
./centronic-stick.py --send HALT --channel 1
```

### TROUBLESHOOTING

Since the script requires to increase a sequential number a file is created into the same directory `centronic-stick.num`

This number can be increased carefully, when the shutter does not respond. 

Entering a number lower then the actual will definitely stop the shutter from working.


### CHANGELOG

**v0.3**

- added commands "DOWN2" and "UP2" for intermediate positions

**v0.2**

- always use "centronic.num" from its local directory

**v0.1**

- Initial version