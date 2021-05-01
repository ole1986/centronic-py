[![Donations Badge](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=TDSRUDJ9EL98J&source=url)

This project automates "Becker Antriebe" shutter also known as CC31/CC51 using the Centronic USB Stick V2

```
./centronic-stick.py [-hlst] [--checksum <code>] [--device <device>] [--add <modifier>] [--mod <modifier>] [--remove <code>] [--send <UP|UP2|DOWN|DOWN2|HALT|DOWN:<delay>|UP:<delay>|CLEARPOS|TRAIN|TRAINMASTER|REMOVE> --channel <[unit:]channel>]

This script is used send command codes to CC11/CC51 compatible receivers through the CentronicControl USB Stick
It is necessary to own such USB device and to PAIR it first, before using commands like UP and DOWN

                 -h: shows this help
                 -l: listen on the centronic USB device to fetch the codes
                 -s: display the current db stats (incl. last run of a unit)
                 -t: test mode - no codes will be send and no numbers consumed / works only with '--send'
   --send <command>: submit a completely generated code for UP/UP2/DOWN/DOWN2/HALT/DOWN:<delay>/UP:<DELAY>/CLEARPOS/TRAIN/REMOVE commands / requires '--channel'
                     While UP2 and DOWN2 are the intermediate position (E.g. sun protection)
  --device <device>: set the device if it differs from the default, also host:port possible (ser2net)
--channel <[unit:]channel>: define the unit (1-5) and channel (1-7) being used for '--send'. Example: 2:15 will close shutter for unit 2 on all channels
  --checksum <code>: add a checksum to the given 40 char code and output (without STX, ETX)
   --mod <modifier>: used to manipulate the db entries
   --add <modifier>: used to add a db entry
    --remove <code>: used to remove an entry from db

Version 0.8 - Authors: ole1986, toolking
```

### INSTALLATION

Run the `install.sh` script to install all necessary dependencies.
The installer will also configure sudo to allow FHEM the execution of `centronic-stick.py`.

For those who are familar with the installation routine, the following steps are required

* Install python3 pip
* Install python3 module `pyserial` using python3 pip
* Add `fhem` user into sudoers file to allow executing `centronic-stick.py` from the FHEM website

### PROGRAM RECEIVER

To make recievers listening to the Centronic USB Stick, the "master sender" is required to add additional senders. The "master sender" can either be the wall-mounted transmitter or a remote.

To program another sender, please follow the beliw instruction

**1) Press and hold the programming button on the MASTER SENDER for ~3 seconds**
The receiver should confirm with a single "Klack" noise

**2) Run the below command to TRAIN the receiver**
The receiver should confirm with a single "Klack" noise followed by a "Klack - Klack" once the training succeeded

```
./centronic-stick.py --send TRAIN --channel 1
```

Repeat the steps for all the receivers using different channels (E.g. `--channel 2`, `--channel 3`, [...])

*You have successfully paired the Centronic Stick with your shutter(s)*

### ADD MORE CHANNELS

By default the `--channel` argument uses the first known unit (registered in the database file) for a maximum of **7 channels**.

If more channels are required, the `--channel` argument can be used to choose different units (maximum 5)

Example:

```
# program another unit on channel 1
./centronic-stick.py --send TRAIN --channel 2:1
```

```
# program a third unit on channel 7
./centronic-stick.py --send TRAIN --channel 3:7
```

### EXAMPLE USAGE

To move down the shutter, run the below command (amend the channel if neccessary)

```
# move down the shutter programmed on channel 1 for unit 1
./centronic-stick.py --send DOWN --channel 1
```

To move up the shutter on unit 2 and channel, run the below command

```
# move up the shutter programmed on channel 1 for unit 2
./centronic-stick.py --send UP --channel 2:1
```

To pause the movement on unit 3 and channel 1 (which is not the same as unit 1 and channel 1), run the command

```
# stop shutter on unit 3 channel 1
./centronic-stick.py --send HALT --channel 3:1
```

To move down all shutters per explicit unit, run the below command

```
# --channel 15 and --channel 1:15 is the same
./centronic-stick.py --send HALT --channel 1:15
```

To move down all shutters on ALL configured units, run the below command (check `-s` argument to see which unit is configured)

```
# move down shutter on all configured units and all channels (15 = broadcast)
./centronic-stick.py --send DOWN --channel 0:15
```

### REMOVE SENDER

To unpair the centronic-stick.py the following steps can be achieved

**1) Press and hold the programming button on the MASTER SENDER for 3 seconds**
The receiver should confirm with a single "Klack" noise

**2) Run the below commands to REMOVE the sender from its receiver**
The receiver should confirm with a single "Klack" noise followed by a "Klack - Klack"

```
# remove unit 1 with channel 1 from the shutter
./centronic-stick.py --send REMOVE --channel 1
```

**Please note that this command is per channel*

Once ALL SENDERS for a specific unit are removed from ALL RECEIVERS it is safe to reset the increment counter using `--mod` argument.

### DATABASE OUTPUT

Below is an example output of the sqlite3 database

```
code      increment configured  last run       
1737b     825       1           2020-04-01 17:26
1737c     0         0           (unknown)
1737d     0         0           (unknown)
1737e     0         0           (unknown)
1737f     0         0           (unknown)
```

### TROUBLESHOOTING

Since this script requires to store the incremental numbers for any unit being configured, the database file `centronic-stick.db` is used.
It might be necessary to manually change or increase the number to match with the receiver.

Use the argument `--mod "<unit>:<increment>:<configured>"` (CAREFULLY) to set the unit properties

Further technical details can be found in the [TECHNICAL.md](TECHNICAL.md) document
