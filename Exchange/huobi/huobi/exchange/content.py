#!/usr/bin/env python3
import os
import sys
import csv
import logging
from huobi.utils import *
from huobi.constant import *
from huobi.client.generic import GenericClient


class WithdrawContent:
    """
    The account information for spot account, margin account etc.

    :member
        id: The unique account id.
        account_type: The type of this account, possible value: spot, margin, otc, point.
        account_state: The account state, possible value: working, lock.
        assets: The balance list of the specified currency. The content is Balance class

    """

    def __init__(self):
        # self.path = "./to.csv"
        # self.output_path = "./result.csv"
        self.withdraw_list = []
        self.statistics = WithdrawStatistics()

    def init_statistics(self):
        self.statistics.init_currencies(self.withdraw_list)

    def update_withdraw_stat(self, id, stat):
        for withdraw in self.withdraw_list:
            if withdraw.id == id:
                withdraw.stat = stat

    def update_withdraw_hash(self, id, hash):
        for withdraw in self.withdraw_list:
            if withdraw.id == id:
                withdraw.hash = hash

    def show_withdraw_stats(self):
        for withdraw in self.withdraw_list:
            withdraw.show_withdraw()

    def show_specific_withdraw(self, currency="all", address="all", addressTag="all", note="all", chain="all", amount=-1, stat="all", hash="all", log_type="info"):
        for withdraw in self.withdraw_list:
            if currency != "all" and currency != withdraw.currency:
                continue
            if address != "all" and address != withdraw.address:
                continue
            if addressTag != "all" and addressTag != withdraw.addressTag:
                continue
            if note != "all" and note != withdraw.note:
                continue
            if chain != "all" and chain != withdraw.chain:
                continue
            if amount != -1 and amount != withdraw.amount:
                continue
            if stat != "all" and stat != withdraw.stat:
                continue
            if hash != "all" and hash != withdraw.hash:
                continue
            withdraw.show_withdraw(log_type=log_type)

    @staticmethod
    def load_list(path):
        withdraw_list = []
        if not os.path.isfile(path):
            logging.error("File {} not exist, exit.".format(path))
            sys.exit()
        generic_client = GenericClient()

        not_support = False
        with open(path, newline='') as csvfile:
            rows = csv.DictReader(csvfile)
            count = 0
            for row in rows:
                count += 1
                # logging.info("currency: {}".format(row['Currency']))
                reference_currencies = generic_client.get_reference_currencies(
                    currency=row['Currency'])
                chain_s = None
                for currency in reference_currencies:
                    for chain in currency.chains:
                        # print("#####{}".format(row['Currency']))
                        # print("#####{}".format(chain.displayName))
                        # chain.print_object()
                        if row['DisplayName'] == chain.displayName:
                            chain_s = chain.chain
                if chain_s == None:
                    logging.error("Currency {} not support displayName={}".format(
                        row['Currency'], row['DisplayName']))
                    not_support = True
                    # sys.exit()
                withdraw = Withdraw(id=count, currency=row['Currency'], address=row['Address'],
                                    addressTag=row['AddressTag'], note=row['Note'], chain=chain_s, displayName=row['DisplayName'], amount=row['Amount'])
                withdraw_list.append(withdraw)
        if not_support:
            logging.error("Load csv error.")
            sys.exit()
        return withdraw_list

    @staticmethod
    def dump_withdraw_info(path, withdraw_list):
        with open(path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            titles = []
            for attribute, _ in withdraw_list[0].__dict__.items():
                titles.append(attribute)
            writer.writerow(titles)
            for withdraw in withdraw_list:
                values = []
                for _, value in withdraw.__dict__.items():
                    values.append(value)
                writer.writerow(values)


class Withdraw:
    """
    The withdraw list information.

    :member
        id: The number of colume.
        currency: The crypto currency to deposit.
        address: Deposit address
        addressTag: Deposit address tag.
        note: Note of address
        chain: The chain you want withdraw.
        displayName: The displayName of withdraw cahin.
        amount: Amount you want withdraw.
        stat: Withdraw stat.
        transactionHash: The transaction hash.
    """

    def __init__(self, id, currency, address, addressTag, note, chain, displayName, amount):
        self.id = id
        self.currency = currency
        self.address = address
        self.addressTag = addressTag
        self.note = note
        self.chain = chain
        self.displayName = displayName
        self.amount = int(amount)

    withdraw_id = None
    stat = None
    transactionHash = None
    created_at = None
    updated_at = None
    fee = None

    def show_withdraw(self, log_type="info"):
        output = "Show withdraw info: "
        for attribute, value in self.__dict__.items():
            output += "{}={}, ".format(attribute, value)
        output = output[:-2]
        if log_type == "info":
            logging.info(output)
        else:
            logging.error(output)

    def update_stat(self, stat):
        self.stat = stat

    def update_transactionHash(self, hash):
        self.stat = hash


class WithdrawAddress:
    """
    The withdraw address.

    :member
        address: The list of currencies statistics.
    """

    def __init__(self):
        self.address_list = []

    def add_address_list(self, address_list):
        try:
            for address in address_list:
                # logging.info("@@@@@{},{},{},{},{}".format(address.currency,
                #                                    address.address, address.addressTag, address.chain, address.note))
                addr = AddressInfo(
                    address.currency, address.address, address.addressTag, address.chain, address.note)
                self.address_list.append(addr)
            return "Set address list succeeded", True
        except:
            return "Set address list failed", False

    def show_address_list(self):
        for address in self.address_list:
            address.show_address()

    def check_withdrawAddr_in_address_list(self, withdraw: Withdraw) -> bool:
        match = False
        match_address = False
        match_currency = False
        match_chain = False
        match_note = False
        for addr in self.address_list:
            if withdraw.currency == addr.currency:
                match_currency = True
            else:
                continue
            if withdraw.chain == addr.chain:
                match_chain = True
            else:
                continue
            if withdraw.address == addr.address:
                match_address = True
            else:
                continue
            if withdraw.note == addr.note:
                match_note = True
                match = True
                break
        if not match:
            logging.error(
                "Account's withdraw address list not support this withdraw.")
            if not match_currency:
                logging.error(
                    "This account can't withdraw currency {}".format(withdraw.currency))
            elif not match_chain:
                logging.error("This account can't withdraw currency {} in {}.".format(
                    withdraw.currency, withdraw.displayName))
            elif not match_address:
                logging.error("This account has no address {} can withdraw currency {} in {}.".format(
                    withdraw.address, withdraw.currency, withdraw.displayName))
            elif not match_note:
                logging.error("The note({}) of address {} withdraw {} in {} is not match.".format(
                    withdraw.note, withdraw.address, withdraw.currency, withdraw.displayName))
            else:
                pass
        return match


class AddressInfo:
    """
    The withdraw address informations.

    :member
        currency: The currencies.
        address: The address.
        addressTag: The addressTag.
        chain: The chain.
        note: The note.
    """

    def __init__(self, currency, address, addressTag, chain, note):
        self.currency = currency
        self.address = address
        self.addressTag = addressTag
        self.chain = chain
        self.note = note

    def show_address(self, log_type="info"):
        output = "Show address: "
        for attribute, value in self.__dict__.items():
            output += "{}={}, ".format(attribute, value)
        output = output[:-2]
        if log_type == "info":
            logging.info(output)
        else:
            logging.error(output)


class WithdrawStatistics:
    """
    The withdraw statistics.

    :member
        currencies: The list of currencies statistics.
    """

    def __init__(self):
        self.currencies = []

    def init_currencies(self, withdraw_list):
        for withdraw in withdraw_list:
            currencyExist = False
            for currency in self.currencies:
                if currency.currency == withdraw.currency:
                    currency.add_chain_info(withdraw)
                    currencyExist = True
                    break
            if currencyExist == False:
                newCurrency = CurrencyStatistics(withdraw.currency)
                newCurrency.add_chain_info(withdraw)
                self.currencies.append(newCurrency)

    def show_withdraw_statistics_by_chain(self, specific_chain="all", specific_currency="all"):
        for currency in self.currencies:
            if specific_currency == currency.currency or specific_currency == "all":
                currency.show_currency_statistics_by_chain(specific_chain)
        # logging.info("id={id}, currency={currency}, address={address}, addressTag={addressTag}, chain={chain}, amount={amount}, stat={stat}, hash={hash}".format(
        #     id=self.id, currency=self.currency, address=self.address, addressTag=self.addressTag,
        #     chain=self.chain, amount=self.amount, stat=self.stat, hash=self.transactionHash))
        # logging.info("Withdraw list:{},{},{},{},{},{},{}".format(self.id, self.currency, self.address,
        #                                                   self.addressTag, self.chain, self.amount, self.stat, self.transactionHash))

    def show_withdraw_statistics(self, specific_currency="all"):
        for currency in self.currencies:
            if specific_currency == currency.currency or specific_currency == "all":
                currency.show_currency_statistics()

    def show_withdraw_statistics_all(self):
        for currency in self.currencies:
            logging.info("Currency({}):".format(currency.currency))
            self.show_withdraw_statistics(specific_currency=currency.currency)
            logging.info(
                "Currency({}) by chain :".format(currency.currency))
            self.show_withdraw_statistics_by_chain(
                specific_currency=currency.currency, specific_chain="all")

    def get_attribute(self, specific_currency, specific_attribute, specific_chain="all"):
        """
        get withdraw statistics attribute
        :param specific_currency: currency
        :param specific_chain: chain(no asign is total of chains)
        :param specific_attribute: attribute, the value can be "amount", "count", "fee", "estimateFee", "succeedAmmount", "failedAmmount", "succeedCount" and "failedCount"
        """
        value = 0
        for currency in self.currencies:
            if specific_currency == currency.currency:
                for chain in currency.chains:
                    if specific_chain == chain.chain or specific_chain == "all":
                        value += getattr(chain, specific_attribute)
                        # logging.info("######{},{},{},{}".format(
                        #     currency.currency, chain.chain, specific_attribute, value))
        return value

    def update_withdraw_statistics_attr(self, specific_currency, specific_chain, specific_attribute, value):
        """
        update withdraw statistics attribute
        :param specific_currency: currency
        :param specific_chain: chain
        :param specific_attribute: attribute, the value can be "fee", "estimateFee", "succeedAmmount", "failedAmmount", "succeedCount" and "failedCount"
        :param value: value
        """
        if specific_attribute != "fee" and specific_attribute != "estimateFee" and specific_attribute != "succeedAmmount" and specific_attribute != "failedAmmount" and specific_attribute != "succeedCount" and specific_attribute != "failedCount":
            logging.error(
                "Error, can only upde: fee, estimateFee, succeedAmmount, failedAmmount, succeedCount, failedCount")
            sys.exit()

        for currency in self.currencies:
            if specific_currency == currency.currency:
                for chain in currency.chains:
                    if specific_chain == chain.chain:
                        if hasattr(chain, specific_attribute):
                            setattr(chain, specific_attribute, value)

    def update_transactionHash(self, hash):
        self.stat = hash


class CurrencyStatistics:
    def __init__(self, currency):
        self.currency = currency
        self.chains = []

    def add_chain_info(self, withdraw):
        for chain in self.chains:
            if chain.chain == withdraw.chain:
                chain.amount += withdraw.amount
                chain.count += 1
                return
        newChain = ChainStatistics(
            self.currency, withdraw.chain, withdraw.amount, 1, 0, 0)
        self.chains.append(newChain)

    def show_currency_statistics(self):
        amount = 0
        fee = 0
        estimateFee = 0
        count = 0
        succeedAmmount = 0
        failedAmmount = 0
        succeedCount = 0
        failedCount = 0
        for chain in self.chains:
            amount += chain.amount
            count += chain.count
            fee += chain.fee
            estimateFee += chain.estimateFee
            succeedAmmount += chain.succeedAmmount
            failedAmmount += chain.failedAmmount
            succeedCount += chain.succeedCount
            failedCount += chain.failedCount
        logging.info("currency={currency}, amount={amount}, count={count}, fee={fee}, estimateFee={estimateFee}, succeedAmmount={succeedAmmount}, failedAmmount={failedAmmount}, succeedCount={succeedCount}, failedCount={failedCount}".format(
            currency=self.currency, amount=amount, fee=fee, estimateFee=estimateFee,
            count=count, succeedAmmount=succeedAmmount, failedAmmount=failedAmmount, succeedCount=succeedCount, failedCount=failedCount))

    def show_currency_statistics_by_chain(self, specific_chain="all"):
        for chain in self.chains:
            if specific_chain == chain.chain or specific_chain == "all":
                chain.show_chain_statistics()


class ChainStatistics:
    def __init__(self, currency, chain, amount, count, fee, estimateFee, succeedAmmount=0, failedAmmount=0, succeedCount=0, failedCount=0):
        self.currency = currency
        self.chain = chain
        self.amount = amount
        self.count = count
        self.fee = fee
        self.estimateFee = estimateFee
        self.succeedAmmount = succeedAmmount
        self.failedAmmount = failedAmmount
        self.succeedCount = succeedCount
        self.failedCount = failedCount
        self.get_currency_stats(currency, chain)
    displayName = ""
    numOfConfirmations = 0
    withdrawStatus = ""
    minWithdrawAmt = 0
    withdrawPrecision = 0
    maxWithdrawAmt = 0
    transactFeeWithdraw = 0

    def get_currency_stats(self, specific_currency, specific_chain):
        generic_client = GenericClient()
        reference_currencies = generic_client.get_reference_currencies(
            currency=specific_currency)
        for currency in reference_currencies:
            for chain in currency.chains:
                if chain.chain == specific_chain:
                    self.displayName = chain.displayName
                    self.numOfConfirmations = chain.numOfConfirmations
                    self.withdrawStatus = chain.withdrawStatus
                    self.minWithdrawAmt = float(chain.minWithdrawAmt)
                    self.withdrawPrecision = chain.withdrawPrecision
                    self.maxWithdrawAmt = float(chain.maxWithdrawAmt)
                    self.transactFeeWithdraw = float(chain.transactFeeWithdraw)

    def show_chain_statistics(self, log_type="info"):
        # logging.info("currency={currency}, chain={chain}, amount={amount}, count={count}, fee={fee}, estimateFee={estimateFee}, succeedAmmount={succeedAmmount}, failedAmmount={failedAmmount}, succeedCount={succeedCount}, failedCount={failedCount}".format(
        #     currency=self.currency, chain=self.chain, amount=self.amount, count=self.count, fee=self.fee, estimateFee=self.estimateFee,
        #     succeedAmmount=self.succeedAmmount, failedAmmount=self.failedAmmount, succeedCount=self.succeedCount, failedCount=self.failedCount))
        output = "Show currency staticstics by chain: "
        for attribute, value in self.__dict__.items():
            output += "{}={}, ".format(attribute, value)
        output = output[:-2]
        if log_type == "info":
            logging.info(output)
        else:
            logging.error(output)
