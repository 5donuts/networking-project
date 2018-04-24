#!/usr/bin/env python3

from random import choice
import string
import hashlib

# machine addresses
DNS_ADDR = '127.0.0.1'
HTTP_ADDR = '127.0.0.1'
TRANSMITTER_ADDR = '127.0.0.1'
TRANSMITTER_PORT = 4000
WAV_FILENAME = "transmission.wav"


# return a string of bytes representing the given ip address
def bytes_from_ip(ip_addr):
    addr_bytes = b''

    for octet in ip_addr.split('.'):
        addr_bytes += bytes([int(octet)])

    return addr_bytes


# return a string representing an ip address given a string of bytes
def ip_from_bytes(ip_bytes):
    ip = []

    for byte in ip_bytes:
        ip.append(str(int(byte)))

    return '.'.join(ip)


# encrypt the message (see https://codereview.stackexchange.com/a/116070)
def encrypt(message, key):
    return ''.join(chr(ord(i) ^ ord(j)) for (i, j) in zip(message, key))


# decrypt the message (see https://codereview.stackexchange.com/a/116070)
def decrypt(ciphertext, key):
    return encrypt(ciphertext, key)


# generate a one-time pad for the given message
# (see https://codereview.stackexchange.com/a/116070)
def gen_key(message):
    return ''.join(choice(string.printable) for _ in message)


# save the key file into 'key.txt'
def save_key(key):
    f = open('key.txt', 'w')
    f.write(key)
    f.close()


# load the key file from 'key.txt'
def load_key():
    f = open('key.txt', 'r')
    key = f.read()
    f.close()
    return key


# calculate the md5 hash of the given message
# returns byte string representing hash
def get_hash(message):
    h = hashlib.md5()
    h.update(message)
    return h.digest()
