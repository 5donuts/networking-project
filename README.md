See `docs/Exam.pdf` for project instructions.

# Dependencies
This project is implemented in Python 3 with the following dependencies:

* `rtlsdr`
* `numpy`
* `sounddevice`
* `bitstring`
* `scipy`

Installing dependencies may vary between platforms, though 
`python3 -m pip install <module>` should work in most cases.

# Usage

### HTTP Server
The http server can be started via `./httpserver.py`.

The page hosted by the webserver can be seen by visiting `http://localhost/` in the browser.

### DNS server
The DNS server can be started via `./dnsserver.py`.

To be able to use the DNS server, you must instruct your system to use it.

To temporarily use `dnsserver.py` as your DNS server on a linux system, you can modify `/etc/resolv.conf` to contain `nameserver <address>` where `<address>` is the value of `DNS_ADDR` in `addresses.py`.
Note that this change will prevent your machine from accessing the internet.

Once your machine is using `dnsserver.py` as your DNS server, you can attempt to visit any site via
the browser and be redirected to `http://localhost/`.

### Transmitter
The transmitter can be started via `./transmitter.py`.

To send a message using the transmitter, use `sender.py`.
The transmitter will modulate this message and play it via the sound card.
If the machine running the transmitter has an FM transmitter hooked up to the sound card, then
the transmitter can be used to send an FM broadcast.

### Sender
The sender can be started via `./sender.py`.

The sender will prompt you for a text message which it will send to the transmitter.
Messages sent with the sender are encrypted using a one-time pad.

### Receiver
The receiver can be started via `./receiver.py`

The receiver will listen (by default) on the 87.7FM band for transmissions made by the transmitter.
It will demodulate the message and, assuming the receiver has access to the key used by the sender
to encrypt the message, it will decrypt the message and display it to the user.
