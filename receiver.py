#!/usr/bin/env python3

from transmitter import INTER_TRANSMISSION_PAUSE, AUDIO_SAMPLE_RATE
from rtlsdr import RtlSdr
import numpy as np
import scipy.signal as signal

# constants
STATION_FREQ = int(87.7e6)  # in Hz
OFFSET_FREQ = 250000  # offset to capture at (use offset to avoid DC spike)
CENTER_FREQ = STATION_FREQ - OFFSET_FREQ
RADIO_SAMPLE_RATE = int(1140000)
SAMPLES_PER_SECOND = 1131227  # approx. number of radio samples per 1 second of audio
TRANSMISSION_AUDIO_SAMPLE_RATE = AUDIO_SAMPLE_RATE


# TODO implement this
def decrypt(message, pad):
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
def demodulate(samples):
    print("Applying polar discriminator...", end='', flush=True)
    y = samples[1:] * np.conj(samples[:-1])
    x = np.angle(y)
    print("done")
    return x


# de-emphasis filter
def de_emphasis_filter(demodulated_samples, sample_rate):
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

    # read samples
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
    demodulated_samples = demodulate(samples)

    # apply the de-emphasis filter
    demodulated_samples = de_emphasis_filter(demodulated_samples, sample_rate)

    # decimate again to focus on mono part of audio
    mono_audio, mono_sample_rate = get_mono(demodulated_samples, sample_rate)

    # downsample the mono audio to match transmission sample rate
    print("Downsampling audio to " + str(TRANSMISSION_AUDIO_SAMPLE_RATE) + "Hz...", end='', flush=True)
    seconds = len(mono_audio) / mono_sample_rate
    num_samples = seconds * TRANSMISSION_AUDIO_SAMPLE_RATE
    mono_audio = signal.resample(mono_audio, int(num_samples))
    print("done")

    return mono_audio, TRANSMISSION_AUDIO_SAMPLE_RATE


# save mono audio to a file
def save_to_file(filename, mono_audio, sample_rate):
    mono_audio.astype('int16').tofile(filename)
    print("Sample rate for " + filename + ": " + str(sample_rate))


if __name__ == "__main__":
    audio, sample_rate = get_audio_samples(SAMPLES_PER_SECOND * 10)
    # save_to_file("output.raw", audio, sample_rate)
