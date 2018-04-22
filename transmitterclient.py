#!/usr/bin/env python3

from socket import *


# connect to the sound server
def connect():
    server_name = '127.0.0.1'
    server_port = 4000
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((server_name, server_port))

    return sock


# TODO implement this
def encrypt(message, pad):
    return message


if __name__ == "__main__":
    # establish connection
    sock = connect()

    # encrypt message
    message = input("Message to send: ")
    encrypted_message = encrypt(message, '')

    # send message
    sock.send(bytes(encrypted_message, 'utf-8'))

    # close connection
    sock.close()
