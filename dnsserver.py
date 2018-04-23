#!/usr/bin/env python3

from socket import *
from shared import *

TTL = 3600  # arbitrary value for ttl field


# setup udp server
def setup():
    addr = '127.0.0.1'
    port = 53
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind((addr, port))

    return sock


# get the flags from the DNS request for the response
def getflags(flag_bytes):
    byte1 = bytes(flag_bytes[:1])
    # byte2 = bytes(flag_bytes[1:])

    qr = '1'  # this is a response

    opcode = ''
    for bit in range(1, 5):
        opcode += str(ord(byte1) & (1 << bit))

    aa = '1'  # this is an authoritative answer
    tc = '0'  # this is not truncated
    rd = '0'  # recursion is not supported
    ra = '0'  # recursion is not supported
    z = '000'  # reserved
    rcode = '0000'  # assume all queries are successful

    # build response bytes
    rbyte1 = int(qr + opcode + aa + tc + rd, 2).to_bytes(1, byteorder='big')
    rbyte2 = int(ra + z + rcode, 2).to_bytes(1, byteorder='big')

    return rbyte1 + rbyte2


# get the domain name for the request
def get_domain_name(domain_name_bytes):
    expected_length = 0
    part = ''
    domain = []
    length_mode = True

    for byte in domain_name_bytes:
        if length_mode:
            expected_length = byte
            length_mode = False
        else:
            if byte == 0:
                domain.append(part)
                break

            part += chr(byte)
            if len(part) == expected_length:
                domain.append(part + '.')
                part = ''
                length_mode = True

    return ''.join(domain)


# turn HTTP_ADDR into a byte string
def get_rdata():
    return bytes_from_ip(HTTP_ADDR)


# build the body of the response
def build_body(record_type, record_class):
    offset = b'\xc0\x0c'  # offset of 12
    record_ttl = TTL.to_bytes(4, byteorder='big')  # arbitrary value
    rdlength = b'\x00\x04'  # 4 bytes in the record
    rdata = get_rdata()

    return offset + record_type + record_class + record_ttl + rdlength + rdata


# build the question for the response
def build_question(domain_name_str):
    domain_bytes = b''

    # build bytes for the domain name
    for part in domain_name_str.split('.'):
        domain_bytes += bytes([len(part)])

        for char in part:
            domain_bytes += ord(char).to_bytes(1, byteorder='big')

    # record type information
    record_type = b'\x00\x01'  # for A record type
    class_type = b'\x00\x01'  # for IN class type

    return domain_bytes + record_type + class_type


# build the response header
def build_header(header_data):
    # transaction id
    transaction_id = header_data[:2]  # first 2 bytes

    # flags
    flags = getflags(header_data[2:4])

    # question count
    qdcount = b'\x00\x01'

    # answer count
    ancount = b'\x00\x01'

    # nameserver count
    nscount = b'\x00\x00'

    # additional records
    arcount = b'\x00\x00'

    return transaction_id + flags + qdcount + ancount + nscount + arcount


# build the response
def build_response(request):
    name = get_domain_name(request[12:-4])
    print("Processing request for: " + name)

    header = build_header(request[:12])
    question = build_question(name)
    body = build_body(question[-4:-2], question[-2:])

    return header + question + body


if __name__ == "__main__":
    sock = setup()

    # listen for connections until SIGTERM is received
    print("DNS server started. Use ^C to exit")

    while True:
        # get DNS request, 512 byte packets use UDP
        request, addr = sock.recvfrom(512)

        # build & send response
        response = build_response(request)
        sock.sendto(response, addr)
