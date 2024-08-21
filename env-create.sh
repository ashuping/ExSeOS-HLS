#!/bin/bash

echo 'This program will create a new virtual environment for this project.'
read -p "Continue? [Y/n] >" RESP
if [ $RESP != "Y" ]; then
    echo "Cancelled by user. Have a nice day!"
    exit 1
fi

echo -n "Checking python version..."
PVER=$(python3 --version)

if [ $? -ne 0 ]; then
    echo "Couldn't find your python installation. Is it on PATH?"
    exit 11
fi

PVER_MA=$(echo $PVER | sed -n 's/Python \([0-9]\+\).*/\1/p')
PVER_MI=$(echo $PVER | sed -n 's/Python [0-9]\+\.\([0-9]\+\).*/\1/p')

if [ $PVER_MA -gt 3 ]; then
    echo "It looks like your python version ($PVER) has a major revision number greater than 3. This program was designed for versions 3.12 and up, but it may not work on versions 4.0 or greater."
    read -p "Try to continue anyway? [Y/n] >" RESP
    if [ $RESP != "Y" ]; then
        echo "Cancelled by user. Have a nice day!"
        exit 13
    fi
elif [ $PVER_MI -lt 12 ]; then
    echo "It looks like your python version ($PVER) is lower than 3.12. This program won't work with python versions older than 3.12. Please install a newer version, or use miniconda to manage this for you!"
    exit 12
else
    echo "$PVER"
fi

exit 0

if [ -e './venv' ]; then
    echo "It looks like the 'venv' directory already exists! Do you want to delete and re-create the virtual environment?"
    read -p "Delete and re-create venv? [Y/n] >" RESP
    if [ $RESP != "Y" ]; then
        echo "Cancelled by user. Have a nice day!"
        exit 2
    fi

    rm -rf ./venv
    if [ $? -ne 0 ]; then
        echo "Failed to delete existing directory. Aborting."
        exit 3
    fi
fi

echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "Creating virtual environment failed. Check whether your python installation has venv support!"
    exit 4
fi

echo "Activating virtual environment..."
source ./venv/bin/activate

if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment! Aborting."
    exit 5
fi

echo "Installing packages..."
python -m pip install -r ./requirements.txt

if [ $? -ne 0 ]; then
    echo "Something went wrong while installing packages! Aborting."
    exit 6
fi

echo "Done! To activate your new virtual environment, run the following command:"
echo "    source ./venv/bin/activate"
echo "Have a nice day!"