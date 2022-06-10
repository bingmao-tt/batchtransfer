#!/usr/bin/env python3
import logging
import sys
import argparse
import os.path
import time
import requests
import json
import random
import argparse
from tabnanny import check
from xml.dom.expatbuilder import Rejecter
from huobi.utils import *
from datetime import datetime, timezone, timedelta

from huobi.client.account import AccountClient
from huobi.client.wallet import WalletClient
from huobi.client.generic import GenericClient
# from huobi.constant import *
from huobi.exchange.account import *
from huobi.exchange.content import *
from huobi.exchange.send_withdraw import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', default='/Exchange/huobi/huobi_withdraw',
                        help='The directory of config, output and log file')
    args = parser.parse_args()
    return args


exec_dir = os.path.dirname(os.path.realpath(__file__))
args = parse_args()

now = datetime.now().astimezone(timezone(timedelta(hours=8)))
start_time = now.strftime("%Y%m%d_%H%M%S")
data_folder = args.directory
config_path = "{}/config.json".format(data_folder)
output_file = "{folder}/{time}_output.csv".format(
    folder=data_folder, time=start_time)
output_tmp_file = "{folder}/{time}_output_tmp.csv".format(
    folder=data_folder, time=start_time)
log_file = "{folder}/{time}.log".format(
    folder=data_folder, time=start_time)

with open(config_path) as config_file:
    configs = json.load(config_file)

# Setting logging
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
fileHandler = logging.FileHandler(log_file)
fileHandler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)-5.5s] %(message)s"))
logging.getLogger().addHandler(fileHandler)

# get account
account_client = AccountClient(api_key=configs['access_key'],
                               secret_key=configs['secret_key'])
account = AccountAsset()
wallet_client = WalletClient(
    api_key=configs['access_key'], secret_key=configs['secret_key'])
generic_client = GenericClient()
send_withdraw = SendWithdraw()
withdraw_info = WithdrawContent()
withdraw_address = WithdrawAddress()
# list_obj = account_client.get_balance(account_id=g_account_id)
# LogInfo.output_list(list_obj)

# Get account info
logging.info("Get Huobi account information")
try:
    account_balance_list = account_client.get_account_balance()
except:
    ip = requests.get(configs['public_ip_url']).text.strip()
    # print(ip)
    logging.error(
        "Failed to connect huobi. Check your key/ip. Your ip address: {}".format(ip))
    sys.exit()
# LogInfo.output_list(account_balance_list)
account.set_asset(account_balance_list)
# account.show_account()


# Get withdraw information of the specific account
for asset in account.assets:
    wi = WithdrawInfo(currency=asset.currency)
    wq = wallet_client.get_account_withdraw_quota(
        currency=asset.currency)
    wi.set_quota(wq)
    # wi.show_quota()
    account.withdrawInfo.append(wi)

# # Test: get withdraw info
# tt_balance, _ = account.get_balance("tt")
# tt_max_withdraw_quota, _ = account.get_max_withdraw_quota("tt", "hrc20tt")
# tt_remain_withdraw_quota, _ = account.get_remain_withdraw_quota(
#     "tt", "hrc20tt")
# # logging.info("{}, {}, {}".format(tt_balance, tt_max_withdraw_quota, tt_remain_withdraw_quota))


# Get Withdraw information
logging.info("Get withdraw information from csv")
withdraw_info.withdraw_list = withdraw_info.load_list(
    "{folder}/withdraw.csv".format(folder=data_folder))

# withdraw_info.update_withdraw_stat(1, "aaaaa")
# withdraw_info.show_specific_withdraw(currency="usdt")
withdraw_info.show_specific_withdraw()

# withdraw_info.dump_withdraw_info("/Exchange/huobi/huobi_withdraw", withdraw_info.withdraw_list)


# WithdrawStatistics
logging.info("Init account withdraw statistics")
withdraw_info.init_statistics()
# withdraw_info.statistics.show_withdraw_statistics_all()

# withdraw_info.statistics.show_withdraw_statistics()
# withdraw_info.statistics.show_withdraw_statistics("tt")
# withdraw_info.statistics.show_withdraw_statistics_by_chain(specific_chain="tt")
# withdraw_info.statistics.show_withdraw_statistics_by_chain("hrc20tt")
# withdraw_info.statistics.show_withdraw_statistics_by_chain(
#     specific_chain="hrc20tt", specific_currency="tt")

# withdraw_info.statistics.update_withdraw_statistics_attr(specific_currency="tt", specific_chain="tt",
#                                                          specific_attribute="succeedAmmount", value=10000)

# withdraw_info.statistics.show_withdraw_statistics("tt")
# withdraw_info.statistics.show_withdraw_statistics_by_chain(specific_currency="tt")


# amount = withdraw_info.statistics.get_attribute(specific_currency="tt", specific_chain="hrc20tt",
#                                                 specific_attribute="amount")
# logging.info("aaaaa:{}".format(amount))


# Get account withdraw address
logging.info("Get account withdraw address")
for currency in withdraw_info.statistics.currencies:
    list_obj = wallet_client.get_account_withdraw_address(
        currency=currency.currency)
    withdraw_address.add_address_list(list_obj)
withdraw_address.show_address_list()

reject = False

# Check withdraw info: currency <-> chain
logging.info(
    "Check withdraw information: address list has pair currency <-> chain")
for currency in withdraw_info.statistics.currencies:
    for chain in currency.chains:
        if not account.check_currency_chain_exit(chain.currency, chain.chain):
            logging.error("Not support: currency={}, chain={}".format(
                currency.currency, chain.chain))
            withdraw_info.show_specific_withdraw(
                currency=chain.currency, chain=chain.chain, log_type="error")

# Check currency chain withdrawStatus
logging.info("Check the withdrawStatus of currency chain is allowed")
for currency in withdraw_info.statistics.currencies:
    for chain in currency.chains:
        if not send_withdraw.check_withdrawStatus(generic_client, chain.currency, chain.chain):
            reject = True

# Check withdraw address in account's address list
logging.info("Check the withdraw address in account's address list")
for withdraw in withdraw_info.withdraw_list:
    if not withdraw_address.check_withdrawAddr_in_address_list(withdraw):
        reject = True
        withdraw.show_withdraw(log_type="error")

# Check withdraw address format
currency_list = ["tt", "usdc", "usdt", "busd", "husd", "bnb", "ht"]
logging.info(
    "Check the withdraw address's format, only check currency={}".format(currency_list))
for withdraw in withdraw_info.withdraw_list:
    for currency in currency_list:
        if withdraw.currency == currency:
            if withdraw.displayName == "TRC20":
                continue
            if not send_withdraw.check_withdraw_format(type="eth", address=withdraw.address):
                logging.error("Address format error: id={}, address={}".format(
                    withdraw.id, withdraw.address))
                reject = True
                withdraw.show_withdraw(log_type="error")

# Check withdraw amount
logging.info("Check per withdraw amount")
for withdraw in withdraw_info.withdraw_list:
    mwq, ms = account.get_max_withdraw_quota(withdraw.currency, withdraw.chain)
    min_withdraw_amount = withdraw_info.statistics.get_attribute(
        specific_currency=withdraw.currency, specific_chain=withdraw.chain, specific_attribute="minWithdrawAmt")
    withdraw_fee = withdraw_info.statistics.get_attribute(
        specific_currency=withdraw.currency, specific_chain=withdraw.chain, specific_attribute="transactFeeWithdraw")
    if not ms:
        logging.error("Can't get max_withdraw_quota, currency={currency}, chain={chain} can't get max_withdraw_quota".format(
            currency=withdraw.currency, chain=withdraw.chain))
        reject = True
        continue
    if withdraw.amount > mwq:
        logging.error("Amount to large, currency={currency}, chain={chain}, max_withdraw_quota:{max_withdraw_quota}, but total send amount:{send_amount}".format(
            currency=withdraw.currency, chain=withdraw.chain, max_withdraw_quota=mwq, send_amount=withdraw.amount))
        withdraw.show_withdraw(log_type="error")
        reject = True
        continue
    if withdraw.amount < min_withdraw_amount:
        logging.error("Amount to small, currency={currency}, chain={chain}, mim_withdraw_amoount:{mim_withdraw_amoount}, but total send amount:{send_amount}".format(
            currency=withdraw.currency, chain=withdraw.chain, mim_withdraw_amoount=min_withdraw_amount, send_amount=withdraw.amount))
        withdraw.show_withdraw(log_type="error")
        reject = True
        continue

# Check withdraw total amount
logging.info("Check withdraw total amount")
for currency in withdraw_info.statistics.currencies:
    currecny_withdraw_total_amount = withdraw_info.statistics.get_attribute(
        specific_currency=currency.currency, specific_attribute="amount")
    account_balance, _ = account.get_balance(currency=currency.currency)
    if account_balance < currecny_withdraw_total_amount:
        logging.error("Account not enough, need refill. currency={currency}, balance:{balance}, total_withdraw:{total_withdraw}".format(
            currency=currency.currency, balance=account_balance, total_withdraw=currecny_withdraw_total_amount))
        reject = True
        continue
    for chain in currency.chains:
        rwq, rs = account.get_remain_withdraw_quota(
            chain.currency, chain.chain)
        if not rs:
            logging.error("currency={currency}, chain={chain}: can't get remain_withdraw_quota".format(
                currency=chain.currency, chain=chain.chain))
            reject = True
            continue
        if chain.amount > rwq:
            logging.error("currency={currency}, chain={chain}, remain_withdraw_quota:{remain_withdraw_quota}, but total send amount:{send_amount}".format(
                currency=chain.currency, chain=chain.chain, remain_withdraw_quota=rwq, send_amount=chain.amount))
            reject = True
            continue

if reject == True:
    logging.error("Something error. Exit!")
    sys.exit(1)

logging.info("Check pass")

# Show calculate
for currency in withdraw_info.statistics.currencies:
    amount = withdraw_info.statistics.get_attribute(
        specific_currency=currency.currency, specific_attribute="amount")
    count = withdraw_info.statistics.get_attribute(
        specific_currency=currency.currency, specific_attribute="count")
    logging.info("Send {count} withdraws, and total {amount} {currency}".format(
        count=count, amount=amount, currency=currency.currency))
# Start send
value = input('Are your sure to withdraw? ')
if value.lower() != "yes":
    logging.error("Input = {}. Exit!".format(value))
    sys.exit()

logging.info("Start send withdraw request")

try:
    for withdraw in withdraw_info.withdraw_list:
        # Send withdraw request
        if configs['ignore_zero_amount'] == True:
            if withdraw.amount == 0:
                logging.info("Ignore 0 amount withdraw.")
                withdraw.show_withdraw()
                continue
        if configs['withdraw'] == True:
            try:
                fee = 0
                withdraw_id = wallet_client.post_create_withdraw(address=withdraw.address,
                                                                 amount=withdraw.amount, currency=withdraw.currency, fee=fee,
                                                                 chain=withdraw.chain)
            except:
                fee = send_withdraw.get_withdraw_fee(
                    generic_client, withdraw.currency, withdraw.chain)
                try:
                    withdraw_id = wallet_client.post_create_withdraw(address=withdraw.address,
                                                                     amount=withdraw.amount, currency=withdraw.currency, fee=fee,
                                                                     chain=withdraw.chain)
                except:
                    withdraw_info.statistics.update_withdraw_statistics_attr(specific_currency=withdraw.currency, specific_chain=withdraw.chain, specific_attribute="failedAmmount",
                                                                             value=withdraw.amount+withdraw_info.statistics.get_attribute(specific_currency=withdraw.currency, specific_chain=withdraw.chain, specific_attribute="failedAmmount"))

                    withdraw_info.statistics.update_withdraw_statistics_attr(specific_currency=withdraw.currency, specific_chain=withdraw.chain, specific_attribute="failedCount",
                                                                             value=withdraw.amount+withdraw_info.statistics.get_attribute(specific_currency=withdraw.currency, specific_chain=withdraw.chain, specific_attribute="failedCount"))
                    logging.error("Send withdraw failed")
                    withdraw.show_withdraw(log_type="error")
                    sys.exit()

            logging.info("Send withdraw. id:{}, currency:{}, chain:{}, fee:{}, amount:{}".format(
                withdraw.id, withdraw.currency, withdraw.chain, fee, withdraw.amount))
            LogInfo.output("Create Withdraw ID {id}".format(id=withdraw_id))
        else:
            logging.info("Get latest withdraw id.")
            list_obj = wallet_client.get_deposit_withdraw(
                op_type=DepositWithdraw.WITHDRAW, currency=None, size=1, direct=QueryDirection.NEXT)
            withdraw_id = list_obj[0].id
            fee = float(list_obj[0].fee)
            logging.info("The latest withdraw id is {}.".format(withdraw_id))

        # Check withdraw request stats
        old_state = None
        while withdraw.stat != "confirmed":
            try:
                list_obj = wallet_client.get_deposit_withdraw(
                    op_type=DepositWithdraw.WITHDRAW, currency=None, from_id=withdraw_id, size=1, direct=QueryDirection.NEXT)
            except:
                time.sleep(configs['check_withdraw_reuqest_interval'])
                continue
            # LogInfo.output_list(list_obj)
            for w_obj in list_obj:
                if w_obj.id == withdraw_id:
                    withdraw.withdraw_id = withdraw_id
                    withdraw.stat = w_obj.state
                    withdraw.transactionHash = w_obj.tx_hash
                    withdraw.created_at = datetime.utcfromtimestamp(
                        int(w_obj.created_at)/1000).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
                    withdraw.updated_at = datetime.utcfromtimestamp(
                        int(w_obj.updated_at)/1000).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
                    withdraw.fee = fee

            if withdraw.stat == "confirmed":
                logging.info("Withdraw {wid}({id},{note}) done.".format(
                    wid=withdraw_id, id=withdraw.id, note=withdraw.note))
                withdraw_info.statistics.update_withdraw_statistics_attr(specific_currency=withdraw.currency, specific_chain=withdraw.chain, specific_attribute="fee",
                                                                         value=fee+withdraw_info.statistics.get_attribute(specific_currency=withdraw.currency, specific_chain=withdraw.chain, specific_attribute="fee"))

                withdraw_info.statistics.update_withdraw_statistics_attr(specific_currency=withdraw.currency, specific_chain=withdraw.chain, specific_attribute="succeedAmmount",
                                                                         value=withdraw.amount+withdraw_info.statistics.get_attribute(specific_currency=withdraw.currency, specific_chain=withdraw.chain, specific_attribute="succeedAmmount"))

                withdraw_info.statistics.update_withdraw_statistics_attr(specific_currency=withdraw.currency, specific_chain=withdraw.chain, specific_attribute="succeedCount",
                                                                         value=1+withdraw_info.statistics.get_attribute(specific_currency=withdraw.currency, specific_chain=withdraw.chain, specific_attribute="succeedCount"))
                withdraw.show_withdraw()
                withdraw_info.dump_withdraw_info(
                    output_tmp_file, withdraw_info.withdraw_list)

                # zero-fee withdraw pass blank time when configs['withdraw_blank_time_zero_fee'] = false

                if configs['withdraw_blank_time'] == True and withdraw.id != len(withdraw_info.withdraw_list):
                    if withdraw.fee == 0 and "withdraw_blank_time_zero_fee" in configs:
                        if not configs['withdraw_blank_time_zero_fee']:
                            logging.info("0 fee don't need sleep time")
                            break
                    sleep_time = random.randint(
                        configs['withdraw_blank_min_time'], configs['withdraw_blank_max_time'])
                    logging.info("Sleep {} seconds. Will start next withdraw at {}".format(sleep_time, datetime.utcfromtimestamp(datetime.timestamp(
                        datetime.now())+sleep_time).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')))
                    time.sleep(sleep_time)
            else:
                if withdraw.stat != old_state:
                    old_state = withdraw.stat
                    logging.info("The stat of withdraw {id} is {stat}. Update time: {time}".format(
                        id=withdraw_id, stat=withdraw.stat, time=withdraw.updated_at))
                    withdraw_info.dump_withdraw_info(
                        output_tmp_file, withdraw_info.withdraw_list)
                    time.sleep(configs['check_withdraw_reuqest_interval'])

    # Write log
    withdraw_info.statistics.show_withdraw_statistics_all()
    logging.info("Write log back to csv")
    withdraw_info.dump_withdraw_info(output_file, withdraw_info.withdraw_list)
    if os.path.exists(output_tmp_file):
        os.remove(output_tmp_file)
except:
    list_obj = wallet_client.get_deposit_withdraw(
        op_type=DepositWithdraw.WITHDRAW, currency=None, size=1, direct=QueryDirection.NEXT)
    withdraw_id = list_obj[0].id
    try:
        withdraw_id_ret = wallet_client.post_cancel_withdraw(
            withdraw_id=withdraw_id)
        logging.info("Cancle withdraw id {}".format(withdraw_id))
        LogInfo.output_list(list_obj)
        withdraw_info.dump_withdraw_info(
            output_file, withdraw_info.withdraw_list)
        if os.path.exists(output_tmp_file):
            os.remove(output_tmp_file)
        logging.info("Close withdraw process")
    except:
        logging.error("Cancle withdraw id {} failed".format(withdraw_id))
        withdraw_info.dump_withdraw_info(
            output_tmp_file, withdraw_info.withdraw_list)
        logging.error("Withdraw process failed")


logging.info("Done.")
