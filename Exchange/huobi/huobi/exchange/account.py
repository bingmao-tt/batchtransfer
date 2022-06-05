#!/usr/bin/env python3
import logging
from huobi.utils import *
from huobi.constant import *


class AccountAsset:
    """
    The account information for spot account, margin account etc.

    :member
        id: The unique account id.
        account_type: The type of this account, possible value: spot, margin, otc, point.
        account_state: The account state, possible value: working, lock.
        assets: The balance list of the specified currency. The content is Balance class

    """

    def __init__(self):
        self.id = 0
        self.type = AccountType.INVALID
        self.state = AccountState.INVALID
        self.subtype = ""
        self.assets = []
        self.withdrawInfo = []

    # @staticmethod
    # def add_asset(assets, asset):
    #     assets.append(asset)
    #     return assets

    # def set_asset(self, account_balance_list):
    #     assets = []
    #     for account_balance in account_balance_list:
    #         logging.info("type:{}".format(account_balance.type))
    #         for asset in account_balance.list:
    #             if float(asset.balance) > 0:
    #                 assets.append(asset)
    #     self.assets = assets
    #     return "Set asset success", True

    def set_asset(self, account_balance_list):
        assets = []
        try:
            for account_balance in account_balance_list:
                if account_balance.type == "spot" and account_balance.state == "working":
                    for asset in account_balance.list:
                        if float(asset.balance) > 0:
                            assets.append(asset)
            self.assets = assets
            return "Set asset success", True
        except:
            return "Set asset faile", False

    # def add_asset(self, asset):
    #     try:
    #         self.assets.append(asset)
    #         return "Add asset success", True
    #     except:
    #         return "Add asset faile", False

    def show_account(self):
        logging.info("Account:")
        logging.info("  id = " + str(self.id))
        logging.info("  type = " + str(self.type))
        logging.info("  state = " + str(self.state))
        logging.info("  subtype = " + str(self.subtype))
        # logging.info("  assets = " + str(self.args.ignore_thunder_role))
        for asset in self.assets:
            asset.print_object()

    def get_balance(self, currency):
        for asset in self.assets:
            if currency == asset.currency:
                return float(asset.balance), True
        return 0, False

    def get_max_withdraw_quota(self, currency, chain) -> tuple:
        for info in self.withdrawInfo:
            if info.currency == currency:
                for quota in info.quotas:
                    if quota.chain == chain:
                        return float(quota.maxWithdrawAmt), True
        return 0, False

    def get_remain_withdraw_quota(self, currency, chain):
        for info in self.withdrawInfo:
            if info.currency == currency:
                for quota in info.quotas:
                    if quota.chain == chain:
                        return float(quota.remainWithdrawQuotaPerDay), True
        return 0, False

    def check_currency_chain_exit(self, currency, chain) -> bool:
        for withdraw in self.withdrawInfo:
            if withdraw.currency == currency:
                for quota in withdraw.quotas:
                    if quota.chain == chain:
                        return True
        return False


class WithdrawInfo:
    """
    The withdraw list information.

    :member
        currency: The currency name.
        chains: The withdraw chain list of this currency.
    """

    def __init__(self, currency=""):
        self.currency = currency
        self.quotas = []

    def set_quota(self, quota_list):
        try:
            quotas = []
            for quota in quota_list:
                quotas.append(WithdrawQuotaInfo(chain=quota.chain, maxWithdrawAmt=quota.maxWithdrawAmt, withdrawQuotaPerDay=quota.withdrawQuotaPerDay, remainWithdrawQuotaPerDay=quota.remainWithdrawQuotaPerDay,
                                                withdrawQuotaPerYear=quota.withdrawQuotaPerYear, remainWithdrawQuotaPerYear=quota.remainWithdrawQuotaPerYear, withdrawQuotaTotal=quota.withdrawQuotaTotal, remainWithdrawQuotaTotal=quota.remainWithdrawQuotaTotal))
            # self.quotas.append(quota)
            self.quotas = quotas
            return "Add quota success", True
        except:
            return "Add quota faile", False

    def add_quota(self, quota):
        try:
            self.quotas.append(quota)
            return "Add quota success", True
        except:
            return "Add quota faile", False

    def show_quota(self):
        logging.info(
            "#########{} Withdraw quota information:".format(self.currency))
        # logging.info("  currency = " + str(self.currency))
        # logging.info("  type = " + str(self.type))
        # logging.info("  state = " + str(self.state))
        # logging.info("  subtype = " + str(self.subtype))
        # logging.info("  assets = " + str(self.args.ignore_thunder_role))
        for quota in self.quotas:
            quota.show_withdraw_information()


class WithdrawQuotaInfo:
    """
    Withdraw Quota info.
    :member
        chain: Block chain name.
        maxWithdrawAmt: Maximum withdraw amount in each request.
        withdrawQuotaPerDay: Maximum withdraw amount in a day
        remainWithdrawQuotaPerDay: Remaining withdraw quota in the day
        withdrawQuotaPerYear: Maximum withdraw amount in a year
        remainWithdrawQuotaPerYear: Remaining withdraw quota in the year
        withdrawQuotaTotal: Maximum withdraw amount in total
        remainWithdrawQuotaTotal: Remaining withdraw quota in total
    """

    def __init__(self, chain="", maxWithdrawAmt: 'float' = 0, withdrawQuotaPerDay: 'float' = 0, remainWithdrawQuotaPerDay: 'float' = 0, withdrawQuotaPerYear: 'float' = 0, remainWithdrawQuotaPerYear: 'float' = 0, withdrawQuotaTotal: 'float' = 0, remainWithdrawQuotaTotal: 'float' = 0):
        self.chain = chain
        self.maxWithdrawAmt = maxWithdrawAmt
        self.withdrawQuotaPerDay = withdrawQuotaPerDay
        self.remainWithdrawQuotaPerDay = remainWithdrawQuotaPerDay
        self.withdrawQuotaPerYear = withdrawQuotaPerYear
        self.remainWithdrawQuotaPerYear = remainWithdrawQuotaPerYear
        self.withdrawQuotaTotal = withdrawQuotaTotal
        self.remainWithdrawQuotaTotal = remainWithdrawQuotaTotal

    def add_chain(self, chain):
        try:
            self.chains.append(chain)
            return "Add chain success", True
        except:
            return "Add chain faile", False

    def show_withdraw_information(self):
        logging.info("Withdraw quota information:")
        logging.info("  chain = " + str(self.chain))
        logging.info("  maxWithdrawAmt = " + str(self.maxWithdrawAmt))
        logging.info("  withdrawQuotaPerDay = " +
                     str(self.withdrawQuotaPerDay))
        logging.info("  remainWithdrawQuotaPerDay = " +
                     str(self.remainWithdrawQuotaPerDay))
        # for chain in self.chains:
        #     chain.print_object()


class Balance:
    """
    The balance of specified account.

    :member
        currency: The currency of this balance.
        balance_type: The balance type, trade or frozen.
        balance: The balance in the main currency unit.
    """

    def __init__(self, currency="", type=AccountBalanceUpdateType.INVALID, balance=0.0):
        self.currency = currency
        self.type = type
        self.balance = balance

    def print_object(self, format_data=""):
        from huobi.utils.print_mix_object import PrintBasic
        PrintBasic.print_basic(self.currency, format_data + "Currency")
        PrintBasic.print_basic(self.type, format_data + "Balance Type")
        PrintBasic.print_basic(self.balance, format_data + "Balance")
