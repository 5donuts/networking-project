#!/usr/bin/env python3

from socket import *
from random import choice
import string
from shared import *


# TODO rework this
def encrypt(message):
    return message


# TODO rework this
def connect():
    server_name = TRANSMITTER_ADDR
    server_port = TRANSMITTER_PORT
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((server_name, server_port))

    return sock


if __name__ == "__main__":
    # establish connection
    sock = connect()

    # encrypt message
    message = input("Message to send: ")
    encrypted_message = encrypt(message)

    # send message
    sock.send(bytes(encrypted_message, 'utf-8'))

    # close connection
    sock.close()
