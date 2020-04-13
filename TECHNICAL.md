### INCREMENT

Some facts about the incremental counter being used to control the shutters

* The incremental usually starts at 0 (zero)
* The max value of the incremental is 0xFFFF or 65535 in decimal. After 0xFFFF is reached it IS SAFE to restart the increment from 0x0 (zero)
* The next incremental must always be higher then the current
* The next VALID increment must be in range of 50. So `nextIncrement = currentIncrement + 49` is valid while `nextIncrement = currentIncrement + 50` is not
* If you program a new sender, the sender determines the increment. E.g. the sender has the increment of "1000" and you TRAIN it the receiver will accept the value

Knowing that the increment will restart from 0 (zero) once the max value has been reached
confirms that the `./centronic-stick.py` script will continue to work (even if the counter is higher than 65535 due to its `hex4(number)` conversion)

### USB Stick code revealed

The below illustrates the USB Stick code being submitted through serial connection in order to control the shutter.
While the complete code is required to send the radio frequency (RF) signal, several parts do not matter what the content is.

```
          Does not effect RF code (can be anything)
                       |
                    |----|
0000000002010B 0000 000000 FFFFF 021 0101 00 20 C4  => CA5E62AB5D0716BB8 (RF code)
|------------|                   |-|      |     |
      |                           |       |     Checksum is important for USB Stick to accept submission of the code
  Is required for USB Stick       |       |     
  Otherwise not signal sent       |       Does not effect RF code
                                  |       
                       Does not effect RF code
```

By knowing this, the below are the relevant parts for sending the RF signal

```
0000000002010B 0000 000000 FFFFF 021 0101 00 20 C4 => CA5E62AB5D0716BB8 (RF code)
               |--|        |---|     |--|    |  |
                |            |        |      |  Checksum (not confirmed)
                Increment    |        |      |
                            Unit      CODE_REMOTE (01) and channel (01)
                                             |
                                             Command (UP/DOWN/TRAIN 3sec/...)

Increment: MAX = 0xFFFF / MIN = 0x0000
Unit: MAX = 0xFFFFF / MIN = 0x00000
CODE_REMOTE: Only 02 / 01 / 00 is known
Channel: Range 0x00 to 0x0F is used (possible other options available)
```

### RECEIVE RAW SIGNAL USING FHEM

Without the USB Stick the signal can be received using SIGNALduino through FHEM and a nanoCUL.
More details on how to configure the SIGNALduino can be [found here](https://forum.fhem.de/index.php/topic,110043.msg1040546.html#msg1040546)

**Setup the CC1101 register**

The below configuration setup the nanoCUL to use 2-FSK on 868.283 Mhz

```
set SIGDUINO cc1101_reg 000D 012E 022D 0347 04D3 0591 063D 0704 0832 0900 0A00 0B06 0C00 0D21 0E65 0F3F 1057 11C4 1206 1323 14B9 1540 1607 1700 1818 1914 1A6C 1B00 1C00 1D92 1E87 1F6B 20F8 21B6 2211 23EF 242B 2514 261F 2741 2800 2959 2A7F 2B07 2C88 2D31 2E0B
```

**Enable Manchester message type**

Make sure the Manchester message type is enabled using

```
set SIGDUINO enableMessagetype manchesterMC
```

**Set SIGNALduino to verbose**

The signal being received by FHEM will be stored into the logs (/opt/fhem/log/fhem-*.log).
It is necessary to set the verbose attribute

**Result**

A possible result from the log file may look the following

```
2020.04.11 12:15:23 4: SIGDUINO/msg READ: MC;LL=-826;LH=846;SL=-403;SH=432;D=FFE9BC20B299FC858;C=417;L=65;R=242;
```

**Troubleshooting**

If no data is being show on the log files it may be helpful to reset the usb port

```
set SIGDUINO reset
```