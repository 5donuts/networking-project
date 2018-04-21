#!/usr/bin/env python3

import pyaudio
import numpy as np
from socket import *
import hashlib
from time import sleep

# global variables
TONE_DURATION = 1
TONE_FREQUENCY = 5000
TRANSMITTER_ADDR = '192.168.0.1'  # TODO find a way to programmatically determine this


# setup TCP server
def setup():
    port = 4000
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(('127.0.0.1', port))
    sock.listen(1)

    return sock


# modulate & transmit the given data (an array of bits) using the given frequency
# each bit is represented by a tone with the given duration (in seconds)
def transmit_data(bit_array, tone_duration, frequency):
    # setup audio stream
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=44100, output=True)

    # modulate & transmit data
    for bit in bit_array:
        if bit == 1:
            play_tone(tone_duration, frequency, stream)
        else:
            play_tone(tone_duration, 0, stream)

    # cleanup audio stream
    stream.stop_stream()
    stream.close()
    p.terminate()


# generate & play a tone of the given duration (in seconds) at the given frequency using the given audio stream
def play_tone(tone_duration, frequency, audio_stream):
    # generate tone
    sampling_rate = 44100  # in Hz
    duration = tone_duration * 3  # this makes the duration approx. 1 second
    samples = (np.sin(2 * np.pi * np.arange(sampling_rate * duration) * frequency / sampling_rate)).astype(np.float32)

    # play tone
    audio_stream.write(samples)


# calculate the md5 hash of the given message
# returns string representing hash
def get_hash(message):
    h = hashlib.md5()
    h.update(message)
    return h.hexdigest()


# get a byte representation of a given ip address
def get_ip_addr_bytes(ip_addr):
    addr_bytes = b''

    for part in ip_addr.split('.'):
        addr_bytes += bytes([int(part)])

    return addr_bytes


# build a packet containing the message
# for more information, see ./docs/packet-structure/info.pdf
def build_packet(source_ip, transmitter_ip, sequence_number, checksum, data):
    packet = b''

    # source ip
    packet += get_ip_addr_bytes(source_ip)

    # transmitter_ip
    packet += get_ip_addr_bytes(transmitter_ip)

    # sequence number
    packet += bytes([int(sequence_number)])

    # length
    packet += bytes([len(data)])

    # reserved
    packet += b'\x00' * 12

    # checksum
    checksum_bytes = b''
    for digit in checksum:
        checksum_bytes += ord(digit).to_bytes(1, byteorder='big')
    packet += checksum_bytes

    # data (comes in as bytes)
    packet += data

    return packet


if __name__ == "__main__":
    sock = setup()

    # listen for connections until SIGTERM is received
    print("Sound server started. Use ^C to exit")

    while True:
        # establish connection with client
        connection, source_addr = sock.accept()

        # get the message
        message = connection.recv(4096)

        # build base packet from data
        packet = build_packet(source_addr, TRANSMITTER_ADDR, 1, get_hash(message), message)

        # transmit each packet 30 times with 10 second pauses between transmissions
        for i in range(0, 30):
            if i == 0:
                # transmit the packet
                transmit_data(packet, TONE_DURATION, TONE_FREQUENCY)
            else:
                # update the sequence number
                packet = packet[:64] + bytes([i]) + packet[69:]
                # transmit the packet
                transmit_data(packet, TONE_DURATION, TONE_FREQUENCY)
            # wait 10 seconds, unless last packet was transmitted
            if i != 29:
                sleep(10)

        # close the connection
        connection.close()

