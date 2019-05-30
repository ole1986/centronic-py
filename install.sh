#!/bin/bash

if ! [[ -f "/usr/bin/python3" ]]
then
    echo "No python3 found"
    exit
fi

echo "Checking for PIP..."

if ! [[ $(dpkg -l |grep "^ii  python3-pip ") ]]
then
    echo "Python 3 PIP is not installed"
    read -p "Do you want to install now? " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]] && sudo apt-get install python3-pip
fi

echo
read -p "Run PIP now to install the required modules? " -n 1 -r
[[ $REPLY =~ ^[Yy]$ ]] && /usr/bin/python3 -m pip install pyserial
echo
echo "Installation completed"