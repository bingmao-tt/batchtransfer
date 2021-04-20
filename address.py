#!/usr/bin/env python3

import codecs
import ecdsa
from Crypto.Hash import keccak
import os

f = open("{0}/BatchTransfer/.private.key".format(os.path.dirname(os.path.realpath(__file__))), "r")
private_key = f.readline()
f.close

private_key_bytes = bytearray.fromhex('{0}'.format(private_key[:64]))

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
print(address)
