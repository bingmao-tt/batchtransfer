#!/usr/bin/python3
import os
import sys
import json
import math
import codecs
import ecdsa

from Crypto.Hash import keccak
from web3 import Web3
from decimal import Decimal


def sendtx(fromAddress, tokenAddress, toList):
    nonce = w3.eth.getTransactionCount(fromAddress)

    kwargs = {
        '_tokenAddr': Web3.toChecksumAddress(tokenAddress),
        '_users': toList,
    }

    abidata = airdrop.encodeABI('doAirdrop', kwargs)
    # print("abidata: " + str(abidata))

    estimateGas = w3.eth.estimateGas({
        'to': airdropContractAddress,
        'from': fromAddress,
        'data': abidata
    })
    # print("E {}".format(estimateGas))
    transaction = {'to': airdropContractAddress,
                   'from': fromAddress,
                   'gas': math.ceil(estimateGas * 1.2),
                   'gasPrice': w3.toWei('1', 'gwei'),
                   'data': abidata,
                   'nonce': nonce}
    # print(transaction)
    signed_txn = w3.eth.account.signTransaction(transaction, privateKey)

    while True:
        try:
            print("Send raw TX")
            txHash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
            print("Tx: {}".format(txHash.hex()))
        except:
            continue
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
    return address


RPC_URL = "https://mainnet-rpc.thundercore.com"
print("PRC URL: {}".format(RPC_URL))
w3 = Web3(Web3.HTTPProvider(RPC_URL,
                            request_kwargs={'timeout': 10}))

f = open("{0}/../BatchTransfer/tokenAirdrop/.private.key".format(
    os.path.dirname(os.path.realpath(__file__))), "r")
privateKey = f.readline()
f.close
f = open("{0}/../BatchTransfer/tokenAirdrop/tokenAddress.txt".format(
    os.path.dirname(os.path.realpath(__file__))), "r")
tokenAddress = f.readline().strip('\n').strip('\t')
f.close

fromAddress = Web3.toChecksumAddress(calculate_address(privateKey))
print("Address: {}".format(fromAddress))
airdropContractAddress = "0xc46c4D799828f6748491cdf4D10f52E991D4E3dc"
# nonce = w3.eth.getTransactionCount(fromAddress)

f = open("{0}/Airdrop.abi".format(os.path.dirname(os.path.realpath(__file__))), "r")
abi = json.dumps(json.loads(f.read()), indent=2)
f.close


w3.eth.defaultAccount = fromAddress
airdrop = w3.eth.contract(abi=abi, address=airdropContractAddress)
getOwner = airdrop.functions.owner().call()
print("Contract owner: {0}".format(getOwner))

tokenName = airdrop.functions.getTokenName(tokenAddress).call()
print("Token name: {0}".format(tokenName))

tokenSymbol = airdrop.functions.getTokenSymbol(tokenAddress).call()
print("Token symbol: {0}".format(tokenSymbol))

tokenDecimal = airdrop.functions.getTokenDecimal(tokenAddress).call()
print("Token decimal: {0}".format(tokenDecimal))


# ##########################
# ### For to.csv version ###
# ##########################
# toFile = open("{0}/../BatchTransfer/tokenAirdrop/to.csv".format(os.path.dirname(os.path.realpath(__file__))), "r")
# lines = toFile.readlines()
# toFile.close
# txSize = 100
# count = 0
# sentCount = 0
# toList = []
# toLog = []
# fo = open("{0}/../BatchTransfer/tokenAirdrop/txs.log".format(os.path.dirname(os.path.realpath(__file__))), "a+")

# for line in lines:
#     toAddress = line.strip('\n').strip('\t').split(',')[0]
#     toValues = int(line.strip('\n').strip('\t').split(',')[1])
#     toLog.append("{},{}".format(toAddress, toValues))
#     # print(line)
#     # print("#@@@@")
#     toArgs = {
#         'toAddress': line.strip('\n').strip('\t').split(',')[0],
#         'values': int(line.strip('\n').strip('\t').split(',')[1]) * 10 ** tokenDecimal,
#         # 'values': int(line.strip('\n').strip('\t').split(',')[1]),
#         # int(line.strip('\n').strip('\t').split(',')[1])
#     }
#     toList.append(toArgs)

#     count += 1
#     sentCount += 1
#     if count == txSize:
#         # print(toList)
#         print("Send {} ~ {}".format(sentCount-txSize, sentCount-1))
#         txHash = sendtx(fromAddress, tokenAddress, toList)
#         # print(",0x{}".format(binascii.hexlify(txHash)))
#         for i in toLog:
#             fo.write("{},{}\n".format(i, txHash))
#         count = 0
#         toList = []
#         toLog = []

# if toList != []:
#     print("Send {} ~ {}".format(sentCount-(sentCount % txSize), sentCount-1))
#     txHash = sendtx(fromAddress, tokenAddress, toList)
#     for i in toLog:
#         fo.write("{},{}\n".format(i, txHash))
# fo.close

##########################
### For to.json version ###
##########################
toFile = open("{0}/../BatchTransfer/tokenAirdrop/to.json".format(
    os.path.dirname(os.path.realpath(__file__))))
# lines = toFile.readlines()
toInfo = json.loads(toFile.read())
txSize = 100
count = 0
sentCount = 0
toList = []
toLog = []

# sys.exit()
fo = open("{0}/../BatchTransfer/tokenAirdrop/txs.log".format(
    os.path.dirname(os.path.realpath(__file__))), "a+")
totalAddrNum = 0
totalSendAmount = 0
print("")
for addressInfo in toInfo:
    totalAddrNum += 1
    totalSendAmount += float(addressInfo['amount'])
    print("{0}: {1}".format(addressInfo['userAddress'], addressInfo['amount']))
print("")
print("Total send address number: {}".format(totalAddrNum))
print("Total send {0} amount: {1}".format(tokenSymbol, totalSendAmount))

tokenBalance = airdrop.functions.getTokenBalance(tokenAddress).call()
print("Contract {0} balance: {1}".format(
    tokenSymbol, tokenBalance/(10**tokenDecimal)))
# tokenBalance = airdrop.functions.getTokenBalance(tokenAddress).call()
# print("Avaliable token balance: {0}".format(tokenBalance))

print("")
if tokenBalance < totalSendAmount:
    print("Token Balance not enough, please send {0} {1} to airdrop contract({2})".format(
        totalSendAmount - tokenBalance, tokenSymbol, airdropContractAddress))
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
        'toAddress': toAddress,
        'values': int(int(float(toAmount) * 10 ** tokenDecimal)/100000)*100000
    }
    toList.append(toArgs)

    count += 1
    sentCount += 1
    if count == txSize:
        print("Send {} ~ {}".format(sentCount-txSize, sentCount-1))
        txHash = sendtx(fromAddress, tokenAddress, toList)
        # print(",0x{}".format(binascii.hexlify(txHash)))
        for i in toLog:
            fo.write("{},{}\n".format(i, txHash))
            # print("done {}".format(i))
        count = 0
        toList = []
        toLog = []

if toList != []:
    print("Send {} ~ {}".format(sentCount-(sentCount % txSize), sentCount-1))
    txHash = sendtx(fromAddress, tokenAddress, toList)
    for i in toLog:
        fo.write("{},{}\n".format(i, txHash))
        # print("done {}".format(i))

# sys.exit()
tokenBalance = airdrop.functions.getTokenBalance(tokenAddress).call()
print("Contract remaining {0} balance: {1}".format(
    tokenSymbol, tokenBalance/(10**tokenDecimal)))
