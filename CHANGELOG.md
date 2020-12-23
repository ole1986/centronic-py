**0.8**

- slightly improved the amount of codes being sent (since we do not need to simulate button release)
- allow using the `--mod 1:0:1` arguments with index numbers (starting at one) instead of the exact unit code (E.g. 1737b0)
- display the increment as hex code when using `-s` argument
- fixed delayed movements using `--send UP:<delay>` or `--send DOWN:<delay>` commands

**v0.7**

- command to move up/down for a specific delay `--send DOWN|UP:<delay>` until release button is simulated (UNTESTED)
- command to clear stop positions `--send CLEARPOS`
- provided `--add <modifier>` and `--remove <code>` option to add or remove units
- support for `--channel 0` (zero) allowing to master wall mounted senders (overrides CODE_REMOTE)

**v0.6**

- added two more units ("1737e" and "1737f") counting a total of 5 units (35 possible channels)

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