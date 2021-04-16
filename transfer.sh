#!/bin/bash

if [ -f "/BatchTransfer/.env" ]; then
    # shellcheck source=.env
    # shellcheck disable=SC1091
    source "/BatchTransfer/.env"
else
    echo "/BatchTransfer/.env not exist. exit"
    exit 1
fi

# batch-transfer .private.key to.csv https://mainnet-rpc.thundercore.com
# batch-transfer .private.key to.csv https://testnet-rpc.thundercore.com

batch-transfer .private.key to.csv "${RPC_URL}"
