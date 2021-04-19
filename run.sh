#!/bin/bash
DIR_PATH=$(dirname "$(readlink -f "${0}")")
TO_FILE="${DIR_PATH}/BatchTransfer/to.csv"

if [ -f "${DIR_PATH}/BatchTransfer/.env" ]; then
    # shellcheck source=.env
    # shellcheck disable=SC1091
    source "${DIR_PATH}/BatchTransfer/.env"
else
    echo "${DIR_PATH}/BatchTransfer/.env not exist."
    echo "You should put .env to BatchTransfer/.env"
    echo ".env example:"
    echo "######################### START #########################"
    cat "${DIR_PATH}/.env.example"
    echo -e "\n########################## END ##########################"
    exit 1
fi

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

echo -e "\n"

JSONRPC=("{\"jsonrpc\":\"2.0\",\"method\":\"eth_getBalance\",\"params\":[\"${BOT_ADDRESS}\",\"latest\"],\"id\":1}")
BALANCE=$(curl -s -H "Content-Type: application/json" -X POST --data ${JSONRPC} ${RPC_URL} | sed "s/\"/ /g" | awk -F ' ' '{print $10}' | sed "s/0x//g" )
BALANCE=$(echo "ibase=16;obase=A;$(echo "${BALANCE}" | tr '[a-z]' '[A-Z]')" | bc)
if [ "${#BALANCE}" -lt 18 ]; then
    echo "Bot balance less than 18, exit."
    exit 1
else
    BALANCE=${BALANCE:0:-18}
fi

address_list=$(< "${TO_FILE}" tr -d '\r' | cut -d "," -f 1 | sort)
amount_lis=$(< "${TO_FILE}" tr -d '\r' | cut -d "," -f 2 | sort)
total_amount=0
unset repeat

for address in ${address_list}; do
    if [ "${address}" == "${pre_address}" ]; then
        echo "Repeat address: ${address}"
        repeat="True"
    fi
    pre_address="${address}"
done

for amount in ${amount_lis}; do
    total_amount=$(("${total_amount}" + "${amount}"))
done

if [ "${repeat}" == "True" ]; then
    echo "Exist!"
    exit 1
fi

echo "Bot balance: ${BALANCE}"
# echo "Total pay: ${total_amount}"
echo -e "Total address: $(wc "${TO_FILE}" | awk '{print $2}'), Pay amount: ${total_amount}"
if [ "${total_amount}" -gt "${BALANCE}" ]; then
    echo "Bot balance less than pay, please refill."
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