#!/usr/bin/python3
import os
import sys
import argparse
import json
import math
import codecs
import ecdsa
import csv
import traceback

from Crypto.Hash import keccak
from web3 import Web3
from decimal import Decimal


def parseArgs(action="get"):
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--chain', required=True,
                        help='Name of chain')
    parser.add_argument('-f', '--file', required=True,
                        help='File of send list.(ex: to.csv, to.json')
    parser.add_argument('-t', '--token', required=True,
                        help='Name of token')
    if action == "help":
        parser.print_help()
        return None
    else:
        args = parser.parse_args()
        return args


def sendtx(w3, csvArgs, contract, toList):
    nonce = w3.eth.getTransactionCount(csvArgs['Owner'])

    kwargs = {
        '_tokenAddr': Web3.toChecksumAddress(csvArgs['TokenAddress']),
        '_users': toList,
    }

    abidata = contract.encodeABI('doAirdrop', kwargs)
    # print("abidata: " + str(abidata))

    estimateGas = w3.eth.estimateGas({
        'to': csvArgs['AirdropContract'],
        'from': csvArgs['Owner'],
        'data': abidata
    })
    chainId = w3.eth.chain_id
    gasPrice = w3.eth.gas_price

    # print("E {}".format(estimateGas))
    #    'gasPrice': w3.toWei('11', 'gwei'),
    transaction = {'to': csvArgs['AirdropContract'],
                   'from': csvArgs['Owner'],
                   'gas': math.ceil(estimateGas * 1.2),
                   'gasPrice': gasPrice,
                   'data': abidata,
                   'chainId': chainId,
                   'nonce': nonce}
    # print(transaction)
    # sys.exit()
    signed_txn = w3.eth.account.signTransaction(transaction, csvArgs['Key'])

    while True:
        try:
            print("Send raw TX")
            txHash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
            print("Tx: {}".format(txHash.hex()))
        except Exception as e:
            error_class = e.__class__.__name__  # 取得錯誤類型
            detail = e.args[0]  # 取得詳細內容
            cl, exc, tb = sys.exc_info()  # 取得Call Stack
            lastCallStack = traceback.extract_tb(tb)[-1]  # 取得Call Stack的最後一筆資料
            fileName = lastCallStack[0]  # 取得發生的檔案名稱
            lineNum = lastCallStack[1]  # 取得發生的行號
            funcName = lastCallStack[2]  # 取得發生的函數名稱
            errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(
                fileName, lineNum, funcName, error_class, detail)
            print(errMsg)
            sys.exit()
        break
    while True:
        try:
            print("Get receipt")
            w3.eth.waitForTransactionReceipt(
                txHash, timeout=10, poll_latency=1)
        except:
            continue
        break
    return txHash.hex()


def calculate_address(privateKey):
    private_key_bytes = bytearray.fromhex('{0}'.format(privateKey[:64]))

    key = ecdsa.SigningKey.from_string(
        private_key_bytes, curve=ecdsa.SECP256k1).verifying_key

    key_bytes = key.to_string()

    private_key = codecs.encode(private_key_bytes, 'hex')
    public_key = codecs.encode(key_bytes, 'hex')

    public_key_bytes = codecs.decode(public_key, 'hex')

    hash = keccak.new(digest_bits=256)
    hash.update(public_key_bytes)
    keccak_digest = hash.hexdigest()

    address = '0x' + keccak_digest[-40:]
    return Web3.toChecksumAddress(address)


def main():
    args = parseArgs()

    # print("{0}/../BatchTransfer/tokenAirdrop/.private_list.csv".format(
    #     os.path.dirname(os.path.realpath(__file__))))
    # Chain,TokenSymbol,URL,AirdropContract,TokenAddress,Key,Owner
    with open("{0}/../BatchTransfer/tokenAirdrop/private_list.csv".format(
            os.path.dirname(os.path.realpath(__file__))), newline='') as csvfile:
        # fieldnames = ['Chain', 'TokenSymbol', 'URL', 'AirdropContract', 'TokenAddress', 'Key', 'Owner']
        dict_reader = csv.DictReader(csvfile)
        configs = []
        for row in dict_reader:
            configs.append(row)

        for row in configs:
            if row['Chain'] == args.chain and row['TokenSymbol'] == args.token:
                csvArgs = row

        try:
            csvArgs['Owner'] = Web3.toChecksumAddress(csvArgs['Owner'])
            csvArgs['AirdropContract'] = Web3.toChecksumAddress(
                csvArgs['AirdropContract'])
            csvArgs['TokenAddress'] = Web3.toChecksumAddress(
                csvArgs['TokenAddress'])
        except NameError:
            parseArgs("help")
            print("Chain     |Token     ")
            print("----------------------")
            for row in configs:
                print("{chain:10s}|{token:10s}".format(
                    chain=row['Chain'], token=row['TokenSymbol']))
            print("----------------------")
            print("Chain or Token not match")
            sys.exit()

        if calculate_address(csvArgs['Key']) != csvArgs['Owner']:
            print("Key of address({address}) not match. (chain: {chain}, token: {token})".format(
                address=csvArgs['Owner'], chain=csvArgs['Chain'], token=csvArgs['TokenSymbol']))
            sys.exit()

    print("PRC URL: {}".format(csvArgs['URL']))
    w3 = Web3(Web3.HTTPProvider(
        csvArgs['URL'], request_kwargs={'timeout': 10}))

    f = open(
        "{0}/Airdrop.abi".format(os.path.dirname(os.path.realpath(__file__))), "r")
    abi = json.dumps(json.loads(f.read()), indent=2)
    f.close
    w3.eth.defaultAccount = csvArgs['Owner']
    airdrop = w3.eth.contract(abi=abi, address=csvArgs['AirdropContract'])
    getOwner = airdrop.functions.owner().call()
    print("Contract owner: {0}".format(getOwner))

    tokenName = airdrop.functions.getTokenName(csvArgs['TokenAddress']).call()
    print("Token name: {0}".format(tokenName))

    tokenSymbol = airdrop.functions.getTokenSymbol(
        csvArgs['TokenAddress']).call()
    if tokenSymbol == csvArgs['TokenSymbol']:
        print("Token symbol: {0}".format(tokenSymbol))
    else:
        print("Token address: {0}".format(csvArgs['TokenAddress']))
        print("TokenSymbol not match TokenAddress")
        sys.exit()

    tokenDecimal = airdrop.functions.getTokenDecimal(
        csvArgs['TokenAddress']).call()
    print("Token decimal: {0}".format(tokenDecimal))

    txSize = 3
    count = 0
    sentCount = 0
    toList = []
    toLog = []

    if args.file.split('.')[-1] == "csv":
        ##########################
        ### For to.csv         ###
        ##########################
        toFile = open("{0}/../BatchTransfer/tokenAirdrop/to.csv".format(
            os.path.dirname(os.path.realpath(__file__))), "r")
        lines = toFile.readlines()
        toFile.close

        toInfo = []

        for line in lines:
            item = {}
            item["userAddress"] = line.strip('\n').strip('\t').split(',')[0]
            item["amount"] = int(line.strip('\n').strip('\t').split(',')[1])
            toInfo.append(item)
    elif args.file.split('.')[-1] == "json":
        ##########################
        ### For to.json        ###
        ##########################
        toFile = open("{0}/../BatchTransfer/tokenAirdrop/to.json".format(
            os.path.dirname(os.path.realpath(__file__))))
        toInfo = json.loads(toFile.read())
    else:
        print("File type not support. Only support csv and json.")
        sys.exit()

    ##########################
    ### Start transfer     ###
    ##########################
    fo = open("{0}/../BatchTransfer/tokenAirdrop/txs.log".format(
        os.path.dirname(os.path.realpath(__file__))), "a+")
    totalAddrNum = 0
    totalSendAmount = 0
    print("")
    for addressInfo in toInfo:
        totalAddrNum += 1
        totalSendAmount += float(addressInfo['amount'])
        print("{0}: {1}".format(
            addressInfo['userAddress'], addressInfo['amount']))
    print("")
    print("Total send address number: {}".format(totalAddrNum))
    print("Total send {0} amount: {1}".format(tokenSymbol, totalSendAmount))

    tokenBalance = airdrop.functions.getTokenBalance(
        csvArgs['TokenAddress']).call()
    print("Contract {0} balance: {1}".format(
        tokenSymbol, tokenBalance/(10**tokenDecimal)))

    print("")
    if tokenBalance/(10**tokenDecimal) < totalSendAmount:
        print("Token Balance not enough, please send {0} {1} to airdrop contract({2})".format(
            totalSendAmount - tokenBalance/(10**tokenDecimal), tokenSymbol, csvArgs['AirdropContract']))
        sys.exit()
    print("Start send transaction.")

    double_check = input("Do you want send {0} {1} to {2} addresses? (Yes/No): ".format(
        totalSendAmount, tokenSymbol, totalAddrNum))
    if double_check != "Yes":
        print("Exit.")
        sys.exit()

    for addressInfo in toInfo:
        toAddress = addressInfo['userAddress']
        toAmount = addressInfo['amount']
        toLog.append("{},{}".format(toAddress, toAmount))
        toArgs = {
            'toAddress': Web3.toChecksumAddress(toAddress),
            'values': int(int(float(toAmount) * 10 ** tokenDecimal)/100000)*100000
        }
        toList.append(toArgs)

        count += 1
        sentCount += 1
        if count == txSize:
            print("Send {} ~ {}".format(sentCount-txSize, sentCount-1))
            txHash = sendtx(w3, csvArgs, airdrop, toList)
            for i in toLog:
                fo.write("{},{}\n".format(i, txHash))
            count = 0
            toList = []
            toLog = []

    # Send remaining transaction
    if toList != []:
        print("Send {} ~ {}".format(sentCount-(sentCount % txSize), sentCount-1))
        txHash = sendtx(w3, csvArgs, airdrop, toList)
        for i in toLog:
            fo.write("{},{}\n".format(i, txHash))
    fo.close

    tokenBalance = airdrop.functions.getTokenBalance(
        csvArgs['TokenAddress']).call()
    print("Contract remaining {0} balance: {1}".format(
        tokenSymbol, tokenBalance/(10**tokenDecimal)))


if __name__ == "__main__":
    main()
