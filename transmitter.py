#!/usr/bin/env python3

import pyaudio
import numpy as np
from socket import *
import hashlib
from time import sleep
from bitstring import BitArray

# global variables
TONE_DURATION = 1  # seconds
TONE_HIGH = 5000  # Hz
TONE_LOW = 0  # Hz
SAMPLING_RATE = 44100  # Hz
INTER_TRANSMISSION_PAUSE = 10  # seconds
INTER_TONE_PAUSE = 1  # seconds
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
def build_transmission_data(packet):
    # initialize list
    transmission_data = []

    # get array of bits to transmit
    b = BitArray(packet)

    # modulate the packet data
    for bit in b.bin:
        if bit == 1:
            tranmission_data.append(gen_tone(TONE_DURATION, TONE_HIGH))
        else:
            transmission_data.append(gen_tone(TONE_DURATION, TONE_LOW))

    return transmission_data


# play the transmission data
def send_transmission(transmission_data):
    # setup audio stream
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=SAMPLING_RATE, output=True)

    # play all tones in the transmission
    for tone in transmission_data:
        if stream.is_stopped():
            stream.start_stream()
        stream.write(tone)
        while(stream.is_active()):
            sleep(0.1)
        stream.stop_stream()
        sleep(INTER_TONE_PAUSE)

    # cleanup audio stream
    stream.stop_stream()
    stream.close()
    p.terminate()


# send each packet the given number of times with a pause between transmissions
def transmit_packet(packet, repetitions):
    # build transmission data for all repetitions
    full_transmission_data = []
    for i in range(0, repetitions):
        # build data for single transmission
        full_transmission_data.append(build_transmission_data(packet))

        # update sequence number
        packet = packet[:64] + bytes([i]) + packet[69:]

    # send all transmissions with a pause between transmissions
    for i in range(0, repetitions):
        send_transmission(full_transmission_data[i])
        sleep(INTER_TRANSMISSION_PAUSE)


# play a tone using a given audio stream
def play_tone(tone, audio_stream):
    audio_stream.write(tone)


# generate a tone of the given duration (in seconds) at the given frequency using the given audio stream
def gen_tone(tone_duration, frequency):
    duration = tone_duration * 3  # this makes a duration of 1 approx. equal to 1 second
    tone = (np.sin(2 * np.pi * np.arange(SAMPLING_RATE * duration) * frequency / SAMPLING_RATE)).astype(np.float32)
    return tone


# calculate the md5 hash of the given message
# returns hex string representing hash
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

    # data length
    packet += len(data).to_bytes(2, byteorder='big')

    # reserved
    packet += b'\x00' * 8

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
        print("Processing message: ")
        print(message)

        # send the packet over the 'wire' 30 times
        transmit_packet(message, 30)

        # close the connection
        connection.close()

