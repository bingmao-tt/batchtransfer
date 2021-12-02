#!/bin/bash
DIR_PATH=$(dirname "$(readlink -f "${0}")")
ORIGIN_PAY_FILE="${DIR_PATH}/BatchTransfer/pay_list.csv"
TO_FILE="${DIR_PATH}/BatchTransfer/to.csv"
KEY_LIST="${DIR_PATH}/BatchTransfer/.private_list.csv"
PRIVATE_KEY="${DIR_PATH}/BatchTransfer/.private.key"

# set -ex

usage() {
    echo -e "\nUSAGE:"
    echo -e "  bash run.sh -n key_name_you_want_use"
    echo -e "\nOPTIONS:"
    echo -e "  -n key_name"
    echo -e "       Whitch private key name do you want to use?"
    echo -e "  -u version"
    echo -e "       Upgrade to which version"
    echo -e "  -v"
    echo -e "       Show version"
    echo -e "  -h"
    echo -e "       Help"
    echo -e "\nEXAMPLE:"
    echo -e "  bash run.sh -n airdrop(key name)"
    echo -e "  bash run.sh -u v0.1"
}

show_version(){
    echo -e "\033[32mVersion is $(git symbolic-ref -q --short HEAD || git describe --tags --exact-match)\033[0m"
}

upgrade_version(){
    set -e
    cd "${DIR_PATH}" || exit
    git fetch --all
    if ! git checkout "${VERSION}"; then
        echo -e "\033[31mChange version error, version still in $(git symbolic-ref -q --short HEAD || git describe --tags --exact-match).\033[0m"
        exit_clear 1
    fi
    echo -e "\033[32mVersion change to $(git symbolic-ref -q --short HEAD || git describe --tags --exact-match).\033[0m"
}

get_options() {
    while getopts "n:u:vh?" arg; do
        case $arg in
        n)
            KEY_NAME=$OPTARG
            ;;
        u)
            VERSION=$OPTARG
            upgrade_version
            exit_clear 0
            ;;
        v)
            show_version
            exit_clear 0
            ;;
        h)
            usage
            exit_clear 0
            ;;
        ?)
            echo "unkonw argument"
            usage
            exit_clear 1
            ;;
        esac
    done

    if [ -z "${KEY_NAME}" ]; then
        echo -e "\033[31mERROR, no -n parameter, exit.\033[0m"
        usage
        exit_clear 1
    fi
}

exit_clear(){
    rm "${TO_FILE}" 2>/dev/null || true
    rm "${PRIVATE_KEY}" 2>/dev/null || true
    exit "$@"
}

exec_pay(){
    rm "${PRIVATE_KEY}" 2>/dev/null || true
    if [ -f "${DIR_PATH}/BatchTransfer/.env" ]; then
        cp "${DIR_PATH}/BatchTransfer/.env" "${DIR_PATH}/BatchTransfer/.env.tmp"
        sed -i -e "s/\\r//g" "${DIR_PATH}/BatchTransfer/.env.tmp"
        # shellcheck source=.env
        # shellcheck disable=SC1091
        source "${DIR_PATH}/BatchTransfer/.env.tmp"
        rm "${DIR_PATH}/BatchTransfer/.env.tmp"
    else
        echo "${DIR_PATH}/BatchTransfer/.env not exist."
        echo -e "\033[31mYou should put .env to BatchTransfer/.env\033[0m"
        echo ".env example:"
        echo "######################### START #########################"
        cat "${DIR_PATH}/.env.example"
        echo -e "\n########################## END ##########################"
        exit_clear 1
    fi

    # Check pay_list.csv
    echo -e "\n### pay_list.csv ###"
    if ! cat "${ORIGIN_PAY_FILE}" 1>/dev/null 2>&1; then
        echo -e "\033[31mpay_list.csv don't exist.\033[0m"
        exit_clear 1
    fi

    # Generate to.csv
    n=0
    cat /dev/null > "${TO_FILE}"
    while IFS= read -r line || [ -n "${line}" ]; do
        # reading each line
        line=$(echo "${line}" | tr -d '\r')
        printf "%04d" ${n}
        echo ",${line}"
        if [ $n -ne 0 ]; then
            to_address=$(echo "${line}" | cut -d "," -f 1)
            to_amount=$(echo "${line}" | cut -d "," -f 2)
            echo "${to_address},${to_amount}" >> "${TO_FILE}"
            # echo "Line No. $n : $name"
        else
            row0=$(echo "${line}" | cut -d "," -f 1)
            if [ "${row0}" != "Address" ]; then
                echo -e "\033[31mThe (0,0) of pay_list.csv should be Address\033[0m"
                exit_clear 1
            fi
            row1=$(echo "${line}" | cut -d "," -f 2)
            if [ "${row1}" != "PayAmount" ]; then
                echo -e "\033[31mThe (0,1) of pay_list.csv should be PayAmount\033[0m"
                exit_clear 1
            fi
        fi
        n=$((n+1))
    done < "${ORIGIN_PAY_FILE}"

    # Check private key list file
    if [ ! -f "${KEY_LIST}" ]; then
        echo -e "\033[31m.private_list.csv don't exist.\033[0m"
        exit_clear 1
    fi

    # Get private key
    n=0
    while IFS= read -r line || [ -n "${line}" ]; do
        # reading each line
        line=$(echo "${line}" | tr -d '\r')
        if [ $n -ne 0 ]; then
            # echo "${line}"
            name=$(echo "${line}" | cut -d "," -f 1)
            if [[ "${name}" == "${KEY_NAME}" ]]; then
                private_key=$(echo "${line}" | cut -d "," -f 2)
                double_check_key=$(echo "${line}" | cut -d "," -f 3)
                # echo "Key No. $n : ${private_key}"
                echo "${private_key}" > "${PRIVATE_KEY}"
            fi
            # echo "Line No. $n : $name"
        else
            row0=$(echo "${line}" | cut -d "," -f 1)
            if [ "${row0}" != "Name" ]; then
                echo -e "\033[31mThe (0,0) of private_list.csv should be Name\033[0m"
                exit_clear 1
            fi
            row1=$(echo "${line}" | cut -d "," -f 2)
            if [ "${row1}" != "Key" ]; then
                echo -e "\033[31mThe (0,1) of private_list.csv should be Key\033[0m"
                exit_clear 1
            fi
        fi
        n=$((n+1))
    done < "${KEY_LIST}"
    if [ -z "${private_key}" ]; then
        echo -e "\033[31m${KEY_NAME}\033[0m key name not exist, exit."
        exit_clear 1
    fi

    # Check to.csv
    echo -e "\n### to.csv ###"
    if ! cat "${TO_FILE}" 1>/dev/null 2>&1; then
        echo -e "\033[31mto.csv don't exist.\033[0m"
        exit_clear 1
    fi

    if ! BOT_ADDRESS=$(python3 "${DIR_PATH}/address.py"); then
        echo -e "\n\033[31mCovert private key to address failed.\033[0m It seems to be \033[31m${KEY_NAME}\033[0m private key format error."
        exit_clear 1
    fi

    echo -e "\n"

    JSONRPC=("{\"jsonrpc\":\"2.0\",\"method\":\"eth_getBalance\",\"params\":[\"${BOT_ADDRESS}\",\"latest\"],\"id\":1}")
    BALANCE=$(curl -s -H "Content-Type: application/json" -X POST --data ${JSONRPC} ${RPC_URL} | sed "s/\"/ /g" | awk -F ' ' '{print $10}' | sed "s/0x//g" )
    BALANCE=$(echo "ibase=16;obase=A;$(echo "${BALANCE}" | tr '[a-z]' '[A-Z]')" | bc)
    BALANCE=$(bash -c "python3 -c 'print(${BALANCE} / 10 ** 18)'")

    address_list=$(< "${TO_FILE}" tr -d '\r' | cut -d "," -f 1 | sort)
    amount_list=$(< "${TO_FILE}" tr -d '\r' | cut -d "," -f 2)
    total_amount=0
    unset repeat

    for address in ${address_list}; do
        if [ "${address}" == "${pre_address}" ]; then
            echo "Repeat address: ${address}"
            repeat="True"
        fi
        pre_address="${address}"
    done

    for address in ${address_list}; do
        if [ "${#address}" -ne 42 ]; then
            echo -e "\033[31m${address} not address format.(without 0x or length not equal 42?)\033[0m"
            exit_clear 1
        fi
        if [ "$(echo "${address}" | sed 's/^0x//' | grep -o -a -m 1 "^[0-9A-Fa-f]*" | head -1 | wc -L)" -ne 40 ]; then
            echo -e "\033[31m${address} address format error.(0-9A-Fa-f))\033[0m"
            exit_clear 1
        fi
    done

    for amount in ${amount_list}; do
        total_amount=$(bash -c "python3 -c 'print(${total_amount} + ${amount})'")
    done

    if [ "${repeat}" == "True" ]; then
        echo -e "\033[31mExist!\033[0m"
        exit_clear 1
    fi

    echo -e "RPC: \033[33m${RPC_URL}\033[0m\n"
    echo -e "Bot Name: \033[33m${KEY_NAME}\033[0m"
    echo -e "Bot address: \033[33m${BOT_ADDRESS}\033[0m"
    echo -e "Bot balance: \033[33m${BALANCE}\033[0m\n"
    # echo "Total pay: ${total_amount}"
    echo -e "Total pay address number: \033[33m$(wc "${TO_FILE}" | awk '{print $2}')\033[0m"
    echo -e "Total pay amount: \033[33m${total_amount}\033[0m\n"
    if [ "$(echo "${total_amount} > ${BALANCE}" | bc)" == "1" ]; then
        echo -e "\033[31mBot balance less than pay, please refill $(bash -c "python3 -c 'print(${total_amount} - ${BALANCE})'") to address: ${BOT_ADDRESS}.\033[0m"
        exit_clear 1
    fi

    # echo -e "\n"

    read -r -s -p "Does send information current?: " current ; echo ""
    if [ -n "${double_check_key}" ]; then
        if [ "${double_check_key}" != "${current}" ]; then
            echo -e "\033[31mDouble check key\033[0m not match, exit."
            exit_clear 1
        fi
    elif [ "${current}" != "yes" ]; then
        echo -e "Error, please enter \033[31myes\033[0m, exit."
        exit_clear 1
    fi

    # Start execute batchtransfer
    echo -e "Start transfer"
    if docker run --rm -ti --name transfer --workdir="/BatchTransfer" -v "${DIR_PATH}/BatchTransfer:/BatchTransfer" -v "${DIR_PATH}/transfer.sh:/BatchTransfer/transfer.sh" thundercoretw/batchtransfer:b5c7d4c /BatchTransfer/transfer.sh; then
        echo -e "\033[32mTransfer done.\033[0m"
    else
        echo -e "\n\033[31mTransfer failed.\033[0m"
        exit_clear 1
    fi
}

main() {

    get_options "$@"
    exec_pay
}

main "$@"
