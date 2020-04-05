### INCREMENT

Some facts about the incremental counter being used to control the shutters

* The incremental usually starts at 0 (zero)
* The max value of the incremental is 0xFFFF or 65535 in decimal. After 0xFFFF is reached it IS SAFE to restart the increment from 0x0 (zero)
* The next incremental must always be higher then the current
* The next VALID increment must be in range of 50. So `nextIncrement = currentIncrement + 49` is valid while `nextIncrement = currentIncrement + 50` is not
* If you program a new sender, the sender determines the increment. E.g. the sender has the increment of "1000" and you TRAIN it the receiver will accept the value

Knowing that the increment will restart from 0 (zero) once the max value has been reached
confirms that the `./centronic-stick.py` script will continue to work (even if the counter is higher than 65535 due to its `hex4(number)` conversion)