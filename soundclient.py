#!/usr/bin/env python3

from socket import *


# connect to the sound server
def connect():
    server_name = '127.0.0.1'
    server_port = 4000
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((server_name, server_port))

    return sock


if __name__ == "__main__":
    # establish connection
    sock = connect()

    # send message
    message = input("Message to send: ")
    sock.send(bytes(message, 'utf-8'))

    # close connection
    sock.close()
