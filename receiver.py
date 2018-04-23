#!/usr/bin/env python3

from transmitter import INTER_TRANSMISSION_PAUSE, TONE_DURATION, AUDIO_SAMPLE_RATE, AUDIO_SAMPLES_PER_TONE, get_hash
from rtlsdr import RtlSdr
import numpy as np
import scipy.signal as signal
from scipy.io.wavfile import read
from bitstring import BitArray
import hashlib
from math import ceil

# constants
STATION_FREQ = int(87.7e6)  # in Hz
OFFSET_FREQ = 250000  # offset to capture at, see https://witestlab.poly.edu/blog/capture-and-decode-fm-radio/
CENTER_FREQ = STATION_FREQ - OFFSET_FREQ
RADIO_SAMPLE_RATE = int(1140000)
TRANSMISSION_AUDIO_SAMPLE_RATE = AUDIO_SAMPLE_RATE


# TODO implement this
def decrypt(message):
    return message


# configure sdr device
def setup():
    sdr = RtlSdr()
    sdr.sample_rate = RADIO_SAMPLE_RATE
    sdr.center_freq = CENTER_FREQ
    sdr.gain = 'auto'

    return sdr


# mix the data down
def mix_data_down(samples):
    # generate a digital complex exponential with the same length as samples
    # and phase -OFFSET_FREQ / RADIO_SAMPLE_RATE
    cpl_exp = np.exp(-1.0j * 2.0 * np.pi * OFFSET_FREQ / RADIO_SAMPLE_RATE * np.arange(len(samples)))
    return samples * cpl_exp


# filter & downsample the signal to focus only the FM signal
def filter_and_downsample(samples):
    print("Focusing on FM signal...", end='', flush=True)
    fm_broadcast_width = 200000  # Hz
    dec_rate = int(RADIO_SAMPLE_RATE / fm_broadcast_width)
    output = signal.decimate(samples, dec_rate)
    new_sample_rate = RADIO_SAMPLE_RATE / dec_rate  # calculate new sampling rate
    print("done")

    return output, new_sample_rate  # return as tuple


# demodulate using a polar discriminator
def apply_polar_discriminator(samples):
    print("Applying polar discriminator...", end='', flush=True)
    y = samples[1:] * np.conj(samples[:-1])
    x = np.angle(y)
    print("done")
    return x


# apply de-emphasis filter
def apply_de_emphasis_filter(demodulated_samples, sample_rate):
    print("Applying de-emphasis filter...", end='', flush=True)
    d = sample_rate * 75e-6  # number of samples to hit -3dB point
    x = np.exp(-1 / d)  # decay between each sample

    # filter coefficients
    b = [1 - x]
    a = [1, -x]

    output = signal.lfilter(b, a, demodulated_samples)
    print("done")

    return output


# decimate again to focus on mono part of broadcast
def get_mono(demodulated_samples, sample_rate):
    print("Focusing on mono audio...", end='', flush=True)
    dec_audio = int(sample_rate / TRANSMISSION_AUDIO_SAMPLE_RATE)
    audio_sample_rate = sample_rate / dec_audio
    output = signal.decimate(demodulated_samples, dec_audio)
    output *= 10000 / np.max(np.abs(output))  # scale audio to adjust volume
    print("done")

    return output, audio_sample_rate


# read in the given number of radio samples
def get_radio_samples(n):
    # setup sdr
    sdr = setup()

    # get samples from radio
    print("Sampling radio...", end='', flush=True)
    read_size = 8192  # recommendation from https://github.com/roger-/pyrtlsdr/issues/56
    num_read = 0
    radio_samples = None
    while num_read <= n:
        sweep = sdr.read_samples(read_size)
        if radio_samples is None:
            radio_samples = sweep
        else:
            radio_samples = np.concatenate((radio_samples, sweep))
        num_read += read_size
        if radio_samples.size > n:
            radio_samples = radio_samples[:n]
    print("done")

    # cleanup sdr device
    sdr.close()
    del sdr

    return radio_samples


# read the given number of radio samples and produce the corresponding audio samples
def get_audio_samples(n):
    # get the radio samples
    radio_samples = get_radio_samples(n)

    # mix the data down
    samples = np.array(radio_samples).astype('complex64')
    samples = mix_data_down(samples)

    # filter & downsample the signal to focus only the FM signal
    samples, sample_rate = filter_and_downsample(samples)

    # demodulate using a polar discriminator
    demodulated_samples = apply_polar_discriminator(samples)

    # apply the de-emphasis filter
    demodulated_samples = apply_de_emphasis_filter(demodulated_samples, sample_rate)

    # decimate again to focus on mono part of audio
    mono_audio, mono_sample_rate = get_mono(demodulated_samples, sample_rate)

    # downsample the mono audio to match transmission sample rate
    print("Downsampling audio to " + str(TRANSMISSION_AUDIO_SAMPLE_RATE) + "Hz...", end='', flush=True)
    seconds = len(mono_audio) / mono_sample_rate
    num_samples = seconds * TRANSMISSION_AUDIO_SAMPLE_RATE
    mono_audio = signal.resample(mono_audio, int(num_samples))
    print("done")

    # return mono_audio, TRANSMISSION_AUDIO_SAMPLE_RATE
    return mono_audio, mono_sample_rate


# save mono audio to a file
def save_to_file(filename, mono_audio, sample_rate):
    mono_audio.astype('int16').tofile(filename)
    print("Sample rate for " + filename + ": " + str(sample_rate))


# load a wav file into a numpy.ndarray object
def load_wav(filename):
    rate, data = read(filename)
    if rate != AUDIO_SAMPLE_RATE:
        print("WARNING: " + filename + " does not have sample rate of " + str(AUDIO_SAMPLE_RATE) + "Hz")
    return data


# take audio data and build a list of tones
def get_tones_from_audio(audio_data):
    # TODO handle possibility of audio data left over at the end
    print("Building tone list...", end='', flush=True)

    # build list of tones
    tones = list(chunks(audio_data[1:], AUDIO_SAMPLES_PER_TONE))

    # pad last tone with extra 0s if necessary
    while len(tones[-1]) < 8:
        tones[-1].append(0)

    print("done")
    return tones


# see https://stackoverflow.com/a/312464
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


# determine the average value of a tone, only considering the absolute value of its components
def average_tone(tone):
    avg = 0
    for val in tone:
        avg += abs(val)
    avg /= len(tone)
    return avg


# demodulate tones
def demodulate(tones):
    data = []

    print("Demodulating audio data...", end='', flush=True)
    for tone in tones:
        avg = average_tone(tone)
        # TODO improve this using TONE_HIGH and TONE_LOW
        if avg < 1000:
            data.append(0)
        else:
            data.append(1)
    print("done")

    return data


# detect and separate transmissions
def separate_transmissions(demodulated_data):
    transmissions = []
    min_tones_between_transmissions = ceil(INTER_TRANSMISSION_PAUSE / TONE_DURATION)

    # TODO fix me
    print("Separating transmissions...", end='', flush=True)
    run_length = 0
    prev_start = 0
    idx = 0
    for bit in demodulated_data:
        idx += 1

        # find runs of zeroes
        if bit == 0:
            run_length += 1
        else:
            run_length = 0

        # separate transmissions
        if run_length == min_tones_between_transmissions:
            run_length = 0
            transmissions.append(demodulated_data[prev_start:idx - min_tones_between_transmissions])
            prev_start = idx - min_tones_between_transmissions
    print("done")

    return transmissions


# rebuild the packet from the data
def rebuild_packet(data):
    packet = b''

    # preamble
    packet += BitArray(data[:32]).bytes

    # source ip
    packet += BitArray(data[32:64]).bytes

    # transmitter ip
    packet += BitArray(data[64:96]).bytes

    # sequence number
    packet += BitArray(data[96:104]).bytes

    # data length
    packet += BitArray(data[104:120]).bytes

    # reserved
    packet += BitArray(data[120:128]).bytes

    # checksum
    packet += BitArray(data[128:160]).bytes

    # data
    packet += BitArray(data[160:]).bytes

    return packet


# get information from packet
def get_packet_info(packet):
    info = {}

    # preamble is 32 bits (4 bytes)
    # source ip (32 bits)
    source_ip_bytes = packet[4:8]
    ip = []
    for byte in source_ip_bytes:
        ip.append(int(byte))
    info['source_ip'] = '.'.join(ip)

    # transmitter ip (32 bits)
    transmitter_ip_bytes = packet[8:12]
    ip = []
    for byte in transmitter_ip_bytes:
        ip.append(int(byte))
    info['transmitter_ip'] = '.'.join(ip)

    # sequence number (8 bits)
    info['sn'] = int(packet[12:13])

    # data length (16 bits)
    info['data_length'] = BitArray(packet[13:15]).int

    # reserved is 8 bits (1 byte)
    # checksum (32 bits)
    checksum_bytes = packet[16:20]
    checksum = []
    for byte in checksum_bytes:
        int_val = BitArray(byte).int
        checksum.append(chr(int_val))
    info['checksum'] = ''.join(checksum)

    # data
    info['data'] = packet[20:]

    return info


# display packet information
# if data is not None, use data instead of info_dict['data']
def display_packet_info(info_dict, data=None):
    print("Received packet: ")
    print("Source: " + source_ip + "\tTransmitter: " + trans_ip)
    print("SN: " + str(sn) + "\tLength: " + str(length))
    print("Checksum: " + checksum)
    if data is not None:
        show_data = data
    else:
        show_data = info_dict['data']
    print("Message: " + show_data)


if __name__ == "__main__":
    # TODO implement getting audio from transmitter

    # for testing purposes, load audio data from a wav file
    audio_data = load_wav("sample_transmission_data.wav")

    # get tones from the audio data
    tones = get_tones_from_audio(audio_data)

    # demodulate data
    demodulated_data = demodulate(tones)

    # separate transmissions
    transmissions = separate_transmissions(demodulated_data)

    # display contents of each transmission
    i = 0
    for transmission in transmissions:
        i += 1
        print("Processing transmission " + str(i) + " of " + str(len(transmissions)))

        # build packet from demodulated data
        packet = rebuild_packet(demodulated_data)

        # get packet info
        info_dict = get_packet_info(packet)

        # validate message checksum
        checksum = get_hash(info_dict['data'])
        if checksum != info_dict['checksum']:
            print("WARNING: message checksum does not match calculated value; data is corrupted")
            # display the raw data
            display_packet_info(info_dict)
        else:
            # TODO decrypt the message
            message = decrypt(info_dict['data'])

            # display the decrypted message
            display_packet_info(info_dict, data=message)
