#!/usr/bin/env python3

from transmitter import INTER_TRANSMISSION_PAUSE, TONE_DURATION, AUDIO_SAMPLE_RATE, AUDIO_SAMPLES_PER_TONE, get_hash
from rtlsdr import RtlSdr
import numpy as np
import scipy.signal as signal
from scipy.io.wavfile import read
from bitstring import BitArray
import hashlib
from math import ceil
import asyncio
from random import choice
import string

# constants
STATION_FREQ = int(87.7e6)  # in Hz
OFFSET_FREQ = 250000  # offset to capture at, see https://witestlab.poly.edu/blog/capture-and-decode-fm-radio/
CENTER_FREQ = STATION_FREQ - OFFSET_FREQ
RADIO_SAMPLE_RATE = int(1140000)
TRANSMISSION_AUDIO_SAMPLE_RATE = AUDIO_SAMPLE_RATE
THRESHOLD = 0.1


# TODO reformat this
def decrypt(message):
    def xor(message, k):
    """Given strings m and k of characters 0 or 1,
    it returns the string representing the XOR
    between each character in the same position.
    This means that m and k should be of the same length.

    Use this function both for encrypting and decrypting!"""
    r = []
    for i, j in zip(m, k):
        r.append(str(int(i) ^ int(j)))  # xor between bits i and j
    return "".join(r)

    if __name__ == "__main__":
    ls = []

    for i in range(100):
        for i in range(100):
            ls.append(choice(string.ascii_letters))

        s = "".join(ls)

        bits = convert_to_bits(s)
        key = gen_random_key(len(bits))
        cipher = xor(bits, key)
        original = xor(key, cipher)

        if original != bits:
            raise Exception("Something wrong with the implementation...")
    return message


def convert_to_bits(s):
    """Converts string s to a string containing only 0s or 1s,
    representing the original string."""
    return "".join(format(ord(x), 'b') for x in s)


def gen_random_key(n):
    """Generates a random key of bits (with 0s or 1s) of length n"""
    k =" 90  195  225  101   14  220  159  221  239   44  158  237  124   62  208  233  147  161  103   54  183  210   20  165   58   91    8   17   22   11  243   83   32  245   38  109  206  129  251   21   10   76  166  248  120   64   92  213  171  214  126  228  100  122  108   41   77  226  136  172   99  177  241   50   34    4   70  116  198  131  189   53  140   42  204  146   94  244  184   26  236  224  134  219  104   28  107   49  240  252   37    2    5  199   75   69  175  217  151  144   81   96  118  105   31  235  227  123  168  247  197  121  141  154   72   43  250   59  114   82  155   40  160  162  232  163  173  110  231    1   46  194  205  242   25   29  255  145   12   73   48   35  180  185   74   18  106  167  249  143  212   33  130   93   56  135   86   45  211   95  132   16  234   36  113  139  179  182  102   89   88  193  190   15  191  202  138   65  238   19  215  192  156   63   66   84  209   97  127   67  200  149  188  174  150  157  201   13  169  153  246  196  186   87   71   30   68  203  119  223    9  216  152  222  112  230  137  181    3  170    7   78   60  148  133  125  111  253  254   52  115  164    6  229   51  207  176   27   55   79   61   39   23  128   57   80  218  187   85  142   98   24   47  117  178  "
    k=k.split()
    unfinished_key=""
    for i in range(n):
        k[i]=convert_to_bits(k[i])
        unfinsihed_key.join(k[i])
    return unfinished_key


# configure sdr device
def setup():
    sdr = RtlSdr()
    sdr.sample_rate = RADIO_SAMPLE_RATE
    sdr.center_freq = CENTER_FREQ
    sdr.gain = 'auto'

    return sdr


audio_samples = []
async def streaming():
    sdr = setup()

    async for samples in sdr.stream():
        d = filter_and_downsample(samples)
        d2 = apply_polar_discriminator(d)
        audio_samples.append(d2)
        print(d2)

    # to stop streaming:
    await sdr.stop()

    # done
    sdr.close()


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
    print("Building tone list...", end='', flush=True)

    # build list of tones
    # TODO programmatically determine AUDIO_SAMPLES_PER_TONE?
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
        # TODO get this working properly
        if avg < 0.1:
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
    # preamble
    preamble = BitArray(data[:32]).bytes

    # source ip
    source_ip = BitArray(data[32:64]).bytes

    # transmitter ip
    trans_ip = BitArray(data[64:96]).bytes

    # sequence number
    sequence_number = BitArray(data[96:104]).bytes

    # data length
    b = BitArray(data[104:120])
    length = b.int
    data_length = b.bytes

    # reserved
    reserved = BitArray(data[120:128]).bytes

    # checksum
    checksum = BitArray(data[128:256]).bytes

    # data
    packet_data = BitArray(data[256:256 + (length * 8)]).bytes

    return preamble + source_ip + trans_ip + sequence_number + data_length + reserved + checksum + packet_data


# get information from packet
def get_packet_info(packet):
    info = {}

    # preamble is 32 bits (4 bytes)
    # source ip (32 bits)
    source_ip_bytes = packet[4:8]

    ip = []
    for byte in source_ip_bytes:
        ip.append(str(int(byte)))
    info['source_ip'] = '.'.join(ip)

    # transmitter ip (32 bits)
    transmitter_ip_bytes = packet[8:12]

    ip = []
    for byte in transmitter_ip_bytes:
        ip.append(str(int(byte)))
    info['transmitter_ip'] = '.'.join(ip)

    # sequence number (8 bits)
    info['sn'] = str(BitArray(packet[12:13]).int)

    # data length (16 bits)
    info['data_length'] = str(BitArray(packet[13:15]).int)

    # reserved is 8 bits (1 byte)
    # checksum (32 bits)
    checksum_bytes = packet[16:20]
    checksum = []
    for byte in checksum_bytes:
        int_val = BitArray(byte).int
        checksum.append(chr(int_val))
    info['checksum'] = str(''.join(checksum), 'utf-8')

    # data
    info['data'] = packet[20:]

    return info


# display packet information
# if data is not None, use data instead of info_dict['data']
def display_packet_info(info_dict, data=None):
    print("Received packet: ")
    print("Source: " + info_dict['source_ip'] + "\tTransmitter: " + info_dict['transmitter_ip'])
    print("SN: " + info_dict['sn'] + "\t\t\tLength: " + info_dict['data_length'])
    print("Checksum: " + info_dict['checksum'])
    if data is not None:
        show_data = str(data, 'utf-8')
    else:
        show_data = info_dict['data']
    print("Message: " + show_data)


if __name__ == "__main__":
    # for testing purposes, load audio data from a wav file
    audio_samples = load_wav("sample_transmission_data.wav")

    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(streaming())

    i = 0
    started = False
    while not started and i < len(audio_samples):
        if abs(audio_samples[i]) > THRESHOLD:
            started = True
        else:
            i += 1

    # get tones from the audio data
    tones = get_tones_from_audio(audio_samples[i:])

    # demodulate data
    demodulated_data = demodulate(tones)

    # display contents of each transmission
    # i = 0
    # for transmission in transmissions:
    #     i += 1
    #     print("Processing transmission " + str(i) + " of " + str(len(transmissions)))

    # build packet from demodulated data)
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

