#!/usr/bin/env python3
import logging
import re

import web3
from huobi.utils import *
from huobi.constant import *
from web3 import Web3


class SendWithdraw:
    """
    The account information for spot account, margin account etc.

    :member
        id: The unique account id.
        account_type: The type of this account, possible value: spot, margin, otc, point.
        account_state: The account state, possible value: working, lock.
        assets: The balance list of the specified currency. The content is Balance class

    """

    @staticmethod
    def get_withdraw_fee(generic_client, specific_currency, specific_chain):
        # generic_client = GenericClient()
        reference_currencies = generic_client.get_reference_currencies(
            currency=specific_currency)
        # LogInfo.output_list(reference_currencies)
        for currency in reference_currencies:
            if specific_currency != currency.currency:
                continue
            for chain in currency.chains:
                if specific_chain == chain.chain:
                    # print("fee:{}".format(chain.transactFeeWithdraw))
                    return float(chain.transactFeeWithdraw)

    @staticmethod
    def check_withdrawStatus(generic_client, specific_currency, specific_chain) -> bool:
        # generic_client = GenericClient()
        reference_currencies = generic_client.get_reference_currencies(
            currency=specific_currency)
        # LogInfo.output_list(reference_currencies)
        for currency in reference_currencies:
            for chain in currency.chains:
                if chain.chain == specific_chain:
                    if "allowed" != chain.withdrawStatus:
                        logging.error("Currency: {}, chain: {}, withdrawStatus: {}, not allowed to withdraw".format(
                            specific_currency, specific_chain, chain.withdrawStatus))
                        return False
        return True

    @staticmethod
    def check_withdraw_format(type, address) -> bool:
        # LogInfo.output_list(reference_currencies)
        if type == "eth":
            # regex = re.compile(r'0x[0-9a-fA-F]{40}')
            if Web3.isAddress(address):
                return True
            else:
                return False
        else:
            logging.error("Only support eth format.")
            return False
        # for currency in reference_currencies:
        #     for chain in currency.chains:
        #         if chain.chain == specific_chain:
        #             if "allowed" != chain.withdrawStatus:
        #                 logging.error("Currency: {}, chain: {}, withdrawStatus: {}, not allowed to withdraw".format(
        #                     specific_currency, specific_chain, chain.withdrawStatus))
        #                 return False
        # return True

    # @staticmethod
    # def send_withdraw(wallet_client, withdraw, fee):
    #     withdraw_id = wallet_client.post_create_withdraw(address=withdraw.address,
    #                                                      amount=withdraw.amount, currency=withdraw.currency, fee=fee,
    #                                                      chain=withdraw.chain, address_tag=withdraw.addressTag)
    #     return withdraw_id
