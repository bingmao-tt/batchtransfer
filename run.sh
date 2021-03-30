#!/bin/bash
DIR_PATH=$(dirname "$(readlink -f "${0}")")

# Check private key file
if [ ! -f "${DIR_PATH}/BatchTransfer/.private.key" ]; then
    echo ".private.key don't exist."
    exit 1
fi

# Check to.csv
echo -e "\n### to.csv ###"
if ! cat "${DIR_PATH}/BatchTransfer/to.csv" 2>/dev/null; then
    echo "to.csv don't exist."
    exit 1
fi
echo -e "\n"

read -r -s -p "Does to.csv current?: " current ; echo ""
if [ "${current}" == "yes" ]; then
    echo "Start transfer"
    # Start execute batchtransfer
    docker run --rm -ti --name transfer --workdir="/BatchTransfer" -v "${DIR_PATH}/BatchTransfer:/BatchTransfer" -v "${DIR_PATH}/transfer.sh:/BatchTransfer/transfer.sh" thundercoretw/batchtransfer:b5c7d4c /BatchTransfer/transfer.sh

    echo -e "\nTransfer done."
else
    echo "exit!"
fi