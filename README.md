# Using Centronic USB Stick to control Becker Shutter CC31/CC51

This project is used to automate "Becker Antriebe" shutter also known as CC31 or CC51 using the Centronic Stick V2

```
./centronic-stick.py [-hlst] [--checksum <code>] [--device <device>] [--send <UP|UP2|DOWN|DOWN2|HALT|TRAIN|REMOVE> --channel <[unit:]channel>]

This script is used send command codes to CC11/CC51 compatible receivers through the CentronicControl USB Stick
It is necessary to own such USB device and to PAIR it first, before using commands like UP and DOWN

                 -h: shows this help
                 -l: listen on the centronic USB device to fetch the codes
                 -s: display the current db stats (incl. last run of a unit)
                 -t: test mode - no codes will be send and no numbers consumed / works only with '--send'
   --send <command>: submit a completely generated code for UP/UP2/DOWN/DOWN2/HALT/TRAIN/REMOVE commands / requires '--channel'
                     While UP2 and DOWN2 are the intermediate position (E.g. sun protection)
  --device <device>: set the device if it differs from the default, also host:port possible (ser2net)
--channel <[unit:]channel>: define the unit (1-3) and channel (1-7) being used for '--send'. Example: 2:15 will close shutter for unit 2 on all channels
  --checksum <code>: add a checksum to the given 40 char code and output (without STX, ETX)
   --mod <modifier>: used to manipulate the db entries - FOR VERY ADVANCED USERS

Version 0.5 - Authors: ole1986, toolking
```

### INSTALL

Run the `install.sh` script to install all necessary dependencies.
The installer will also configure sudo to allow FHEM the execution of `centronic-stick.py` as current user.

For those who are familar with the installation routine, the following steps are required

* Install python3 pip
* Install python3 module `pyserial` using python3 pip
* Install python3 module `sqlite3` using python3 pip
* Add `fhem` user into sudoers file to allow executing `centronic-stick.py` from the FHEM website

### PAIRING

Before the USB stick can be used, a pairing must be achieved.

To make the reciever listening to new senders, either the "receiver" itself or the "master sender" can be used. For the sake of simplicity the below steps are focused on the "master sender" (this can be a wall-mounted transmitter or a remote / BUT NEVER BOTH)

**1) Press and hold the programming button on the MASTER SANDER for 3 seconds**
The receiver should confirm with a single "Klack" noise

**2) Run the below commands to TRAIN the receiver**
The receiver should confirm with a single "Klack" noise followed by a "Klack - Klack" once the training succeeded

```
./centronic-stick.py --send TRAIN --channel 1
```

Repeat the steps for all the receivers.

To control each receiver individually it is neccessary to change the channel number. Otherwise all paired receivers will act on the same channel

*You have successfully paired the Centronic Stick with your shutter*

### MORE CHANNELS

By default the `--channel` argument relays on a single unit  for 1-7 channels. For more channels to be configured nd commands need to be executed for the `--channel` argument can be extended with two additional units.

Example:

```
# Train another (kind of virtual) unit on channel 1
./centronic-stick.py --send TRAIN --channel 2:1
```

```
# Train a third unit on channel 7
./centronic-stick.py --send TRAIN --channel 3:7
```

### CONTROL EXAMPLE

To move down the shutter, run the below command (amend the channel if neccessary)

```
./centronic-stick.py --send DOWN --channel 1
```

To move up the shutter on unit 2 and channel, run the below command

```
./centronic-stick.py --send UP --channel 2:1
```

To pause the movement on unit 3 and channel 1 (which is not the same as unit 1 and channel 1), run the command

```
./centronic-stick.py --send HALT --channel 3:1
```

To move down all shutters per explicit unit, run the below command

```
# --channel 15 and --channel 1:15 is the same
./centronic-stick.py --send HALT --channel 1:15
```

To move down all shutters for ALL configured units, run the below command (check `-s` argument to see which unit is configured)

```
./centronic-stick.py --send HALT --channel 0:15
```

### REMOVE SENDER

To unpair the centronic-stick.py the following steps can be achieved

**1) Press and hold the programming button on the MASTER SANDER for 3 seconds**
The receiver should confirm with a single "Klack" noise

**2) Run the below commands to REMOVE the sender from its receiver**
The receiver should confirm with a single "Klack" noise followed by a "Klack - Klack"

```
./centronic-stick.py --send REMOVE --channel 1
```

**Please note that this command is per channel*

Once all senders are removed from ALL RECEIVERS it is safe to reset the increment counter using `--mod` argument.

### DB OUTPUT

Below is an example output of the sqlite3 database

```
code      increment configured  last run       
1737b     825       1           2020-04-01 17:26
1737c     0         0           (unknown)      
1737d     0         0           (unknown)  
```

### TROUBLESHOOTING

Since this script requires to store the incremental numbers for any unit being configured, the database file `centronic-stick.db` is used

It might be necessary to manually increase the number to match with the receiver.

Use the argument (CAREFULLY) `--mod "<code>:<increment>:<configured>"` to set the unit properties

### CHANGELOG

**v0.5**

- save incremental numbers (per unit) into sqlite3 db
- support for up to 3 units (allowing to manage ~21 channels)
- corrected the channels being used (1-7 and 15)
- slightly amended `--channel <[unit:]channel>` parameter to take units into account
- added `-s` argument to output sqllite3 db content (containing last run for instance)
- removed `-i` to manually increment counter
- added `--mod` (for very advanced users) to modify database entry
- replaced `PAIR` command with `TRAIN` needed to train the shutter
- added `REMOVE` command to remove the sender from shutter

**v0.4**

- added ser2net support for device

**v0.3**

- added commands "DOWN2" and "UP2" for intermediate positions

**v0.2**

- always use "centronic.num" from its local directory

**v0.1**

- Initial version