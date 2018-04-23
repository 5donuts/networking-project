
#!/usr/bin/env python3

from socket import *
from random import choice
import string

# TODO implement this
def encrypt(message):
    def xor(message, k):
    """Given strings m and k of characters 0 or 1,
    it returns the string representing the XOR
    between each character in the same position.
    This means that m and k should be of the same length.

    Use this function both for encrypting and decrypting!"""
    r = []
    for i, j in zip(message, key):
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
    for i in range(k.length):
        k[i]=int(k[i])
    return "".join(k)



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

    # encrypt message
    message = input("Message to send: ")
    encrypted_message = encrypt(message)

    # send message
    sock.send(bytes(encrypted_message, 'utf-8'))

    # close connection
    sock.close()
