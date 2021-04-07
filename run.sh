#!/bin/bash
DIR_PATH=$(dirname "$(readlink -f "${0}")")
TO_FILE="${DIR_PATH}/BatchTransfer/to.csv"

# Check private key file
if [ ! -f "${DIR_PATH}/BatchTransfer/.private.key" ]; then
    echo ".private.key don't exist."
    exit 1
fi

# Check to.csv
echo -e "\n### to.csv ###"
if ! cat "${TO_FILE}" 2>/dev/null; then
    echo "to.csv don't exist."
    exit 1
fi

address_list=$(< "${TO_FILE}" cut -d "," -f 1 | sort)
unset repeat

echo -e "\n"
for address in ${address_list}; do
    if [ "${address}" == "${preAddress}" ]; then
        echo "Repeat address: ${address}"
        repeat="True"
    fi
    preAddress="${address}"
done

if [ "${repeat}" == "True" ]; then
    echo "Exist!"
    exit 1
fi

echo -e "\n"
echo -e "Total $(wc "${TO_FILE}" | awk '{print $1}') address."
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