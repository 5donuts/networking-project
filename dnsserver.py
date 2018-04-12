"""
Charles German & Gabe Lake
DNS Server
"""
from socket import *
from copy import deepcopy

# global variables
WEBSERVER_IP_ADDR = '127.0.0.1'

# set up UDP server
serverPort = 53
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))


# serverSocket.listen(1)


# turn an ugly bit string into a nicely formatted bit string (Jorn's code)
# from https://joernhees.de/blog/2010/09/21/how-to-convert-hex-strings-to-binary-ascii-strings-in-python-incl-8bit-space/
def binary(bitstr):
    return ' '.join(reversed(
        [i + j for i, j in zip(*[["{0:04b}".format(int(c, 16)) for c in reversed('0' + x)][n::2] for n in [1, 0]])]))


# turn hexadecimal data into a bit string
def hex2bitstr(hex_val):
    return bin(int(hex_val, 16))[2:].zfill(8)

# parse the DNS header and return a list containing all elements of it
# this method assumes that header_bitstr has been formatted using Jorn's code
def parseHeader(header_bitstr):
    # get the octets
    octets = header_bitstr.split(" ")
    ID = octets[0] + octets[1]

    # parse the flags
    flags = octets[2] + octets[3]
    QR = int(flags[:1], 2)
    Opcode = int(flags[1:4], 2)
    AA = int(flags[4:5], 2)
    TC = int(flags[5:6], 2)
    RD = int(flags[6:7], 2)
    RA = int(flags[7:8], 2)
    Z = int(flags[8:11], 2)
    RCODE = int(flags[11:], 2)

    # rest of the header
    QDCOUNT = int(octets[4], 2)
    ANCOUNT = int(octets[5], 2)
    NSCOUNT = int(octets[6], 2)
    ARCOUNT = int(octets[7], 2)

    # build & return the list
    return [ID, QR, Opcode, AA, TC, RD, RA, Z, RCODE, QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT]


# generate the DNS response header using the parsed header
def genResponseHeader(parsed_header):
    # copy the header for the response
    response_list = deepcopy(parsed_header)

    # set QR to '1'
    response_list[1] = '1'

    # set ANCOUNT to '0x01'
    response_list[10] = '0' * 15 + '1'

    # build the response
    return ''.join(response_list)

# parse the question section of the DNS packet and return a list containing elements
# this method assumes that quest_bitstr has been formatted using Jorn's code
def parseQuestion(quest_bitstr):
    # get the octets
    octets = quest_bitstr.split(" ")

    idx = 1
    questions = []
    lenOct = octets[0]

    # TODO since we don't actually need the questions,
    # need to modify this so it only finds out how long
    # QNAME is

    # read until the 0 octet (null label) is reached
    while lenOct != '0' * 8:
        length = int(lenOct, 2)
        question = ""
        for i in range(0, length):
            question += octets[idx]
            idx += 1
        questions.append(question)
        lenOct = octets[idx]
        idx += 1

    # assemble QNAME with labels
    QNAME_list = []
    for i in range(0, idx):
        QNAME_list.append(octets[i])
    QNAME = ''.join(QNAME_list)

    # get qtype
    QTYPE = octets[idx] + octets[idx + 1]
    idx += 2

    # get qclass
    QCLASS = octets[idx] + octets[idx + 1]

    # return questions, qtype, qclass
    return [QNAME, QTYPE, QCLASS]


# build the DNS answer
# all of the response values are going to be hard-coded
def genAnswer(parsed_question):
    # same as QNAME
    NAME = parsed_question[0]

    # set TYPE to 0x01
    TYPE = '0' * 15 + '1'

    # set CLASS to 0x01
    CLASS = '0' * 15 + '1'

    # set TTL to 600
    TTL = '0' * 22 + '1001011000'

    # the IP address to return
    octet_vals = WEBSERVER_IP_ADDR.split('.')
    octets = []
    for val in octet_vals:
        octets.append(int(val))
    RDATA = ''.join(octets)

    # combine values into a single bit string
    return NAME + TYPE + CLASS + TTL + RDATA


# Construct the final response packet
def genResponse(response_header, response_answer):
    return response_header + response_answer


# listen for connections until SIGTERM is received
print("DNS server started. Use ^C to exit")
while True:
    # get DNS request
    request, addr = serverSocket.recvfrom(4096)
    bin_val = hex2bitstr(request)
    formatted = binary(bin_val).split(" ")

    # build response header
    list = []
    for i in range(0, 8):
        list.append(formatted[i])
    header_bitstr = ' '.join(list)
    header = parseHeader(header_bitstr)
    response_header = genResponseHeader(header)

    # build answers
    list = []
    for i in range(8, len(formatted)):
        list.append(formatted[i])
    quest_bitstr = ' '.join(list)
    question = parseQuestion(quest_bitstr)
    answer = genAnswer(question)

    # build & send response
    response = genResponse(response_header, answer)
    serverSocket.sendto(response, addr)
