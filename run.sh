#!/bin/bash
DIR_PATH=$(dirname "$(readlink -f "${0}")")

cat "${DIR_PATH}/BatchTransfer/to.csv"
# docker-compose up -d
read -r -s -p "Does to.csv current?: " current ; echo ""
if [ "${current}" == "yes" ]; then
    echo "Start transfer"
    docker run --rm -ti --name transfer --workdir="/BatchTransfer" -v "${DIR_PATH}/BatchTransfer:/BatchTransfer" -v "${DIR_PATH}/transfer.sh:/BatchTransfer/transfer.sh" thundercoretw/batchtransfer:b5c7d4c /BatchTransfer/transfer.sh
else
    echo "exit!"
fi