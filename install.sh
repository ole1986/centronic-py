#!/bin/bash

if ! [[ -f "/usr/bin/python3" ]]
then
    echo "No python3 found"
    exit
fi

echo "Checking for PIP..."

if ! [[ $(dpkg -l |grep "^ii  python3-pip ") ]]
then
    echo "Installing python3 pip..."
    sudo apt-get install python3-pip
fi

echo "Installing pip module 'pyserial'"
/usr/bin/python3 -m pip install pyserial

echo "Checking for FHEM installation..."
if [ -d "/opt/fhem" ]
then
    read -p "Allow FHEM to run 'centronic-stick.py' as $USER? " -n 1 -r
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        if ! sudo grep -E '^fhem.*centronic-stick.py' /etc/sudoers
        then
            sudo echo "# allow fhem user to execute centronic-stick.py as $USER" >> /etc/sudoers
            sudo echo "fhem ALL=($USER) NOPASSWD: $PWD/centronic-stick.py" >> /etc/sudoers
        fi
    fi
fi
echo "Installation completed"
