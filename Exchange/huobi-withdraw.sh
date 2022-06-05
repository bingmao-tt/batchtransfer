#!/bin/bash

UNAME=$(uname)
if [ "${UNAME:0:6}" == "Darwin" ] ; then
    DIR_PATH=$(cd "$(dirname "$0")"; pwd)
else
    DIR_PATH=$(dirname "$(readlink -f "${0}")")
fi
if [ -f "${DIR_PATH}/.env" ]; then
    source "${DIR_PATH}/.env"
fi
: "${WITHDRAW_FOLDER="${DIR_PATH}/huobi/huobi_withdraw"}"


cd "${DIR_PATH}" || exit
echo "Check python image"
# docker build -t huobi-runner ./huobi
docker build -t huobi-runner ./huobi 1>/dev/null 2>&1


docker run --rm -ti --name huobi-withdraw -v /etc/localtime:/etc/localtime:ro -v "${WITHDRAW_FOLDER}:/huobi_withdraw" -v "${DIR_PATH}/huobi:/huobi" huobi-runner /huobi/send.py -d "/huobi_withdraw"
