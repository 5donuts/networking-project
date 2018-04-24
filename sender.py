#!/usr/bin/env python3

from socket import *
from shared import *


# connect to the transmitter
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
    key = gen_key(message)
    save_key(key)
    encrypted_message = encrypt(message, key)

    # send message
    sock.send(bytes(encrypted_message, 'utf-8'))

    # close connection
    sock.close()
