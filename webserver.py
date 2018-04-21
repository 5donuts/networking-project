#!/bin/python3

from socket import *

# page codes
PAGE_NORMAL = 0
PAGE_404 = 1
PAGE_501 = 2


# set up TCP server
def setup():
    port = 80
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(('127.0.0.1', port))
    sock.listen(1)

    return sock


# generate the response page based on the page code and the client's ip address
def build_page(page_code, ip_addr):
    if page_code == PAGE_NORMAL:
        return "<!DOCTYPE html>\n" \
               "<head>\n" \
               "\t<title>BC Black Site</title>\n" \
               "</head>\n" \
               "<body>\n" \
               "\tBridgewater Black Site</br>\n" \
               "\tYour IP address is " + str(ip_addr) + "\n</body>\n"
    elif page_code == PAGE_404:
        return "<!DOCTYPE html>\n" \
               "<head>\n" \
               "\t<title>404 Not Found</title>\n" \
               "</head>\n" \
               "<body>\n" \
               "\tError 404: Page Not Found</br>\n" \
               "\tYour IP address is " + str(ip_addr) + "\n</body>\n"
    elif page_code == PAGE_501:
        return "<!DOCTYPE html>\n" \
               "<head>\n" \
               "\t<title>501 Not Implemented</title>\n" \
               "</head>\n" \
               "<body>\n" \
               "\tError 501: Request Not Implemented</br>\n" \
               "\tYour IP address is " + str(ip_addr) + "\n</body>\n"
    else:
        return "<!DOCTYPE html>\n" \
               "<head>\n" \
               "\t<title>ERROR</title>\n" \
               "</head>\n" \
               "<body>\n" \
               "\tSomething REALLY went wrong," \
               "you shouldn't be seeing this page</br>\n" \
               "\tYour IP address is " + str(ip_addr) + "\n</body>\n"


# determine the request method (HTTP GET, HTTP POST, etc.) from the request string
def get_request_method(request_str):
    return request_str.split('\n', 1)[0].split(' ', 1)[0]


# determine the page requested (/, /index.html, etc.) from the request string
def get_request_uri(request_str):
    return request_str.split('\n', 1)[0].split(' ', 2)[1]


# get the ip address of the client from the connection object
def get_ip_addr(connection):
    return str(connection.getpeername()[0])


if __name__ == "__main__":
    sock = setup()

    # listen for connections until SIGTERM is received
    print("Webserver started. Use ^C to exit")

    while True:
        # establish connection with client
        connection = sock.accept()[0]

        # declaring variables for HTTP response
        response_body = ''
        response_header = ''
        response_status = ''
        response_status_text = ''
        response_protocol = 'HTTP/1.1'

        # receive HTTP request
        request = connection.recv(4096)
        request_str = str(request, 'utf-8')

        # determine request type & form response status/text
        page_code = -1
        if get_request_method(request_str) == 'GET':
            if get_request_uri(request_str) == '/':
                page_code = PAGE_NORMAL
                response_status = '200'
                response_status_text = 'OK'
            else:
                page_code = PAGE_404
                response_status = '404'
                response_status_text = 'NOT FOUND'
        else:
            page_code = PAGE_501
            response_status = '501'
            response_status_text = 'NOT IMPLEMENTED'

        # form response body & header
        response_body = build_page(page_code, get_ip_addr(connection))
        response_header = "Content-Type: text/html; encoding=utf8\n" \
                          "Content-Length: " + str(len(response_body)) + "\nConnection: close\n\n"

        # send the HTTP response
        response_proto_status_line = '%s %s %s' % (response_protocol, response_status, response_status_text)
        connection.send(bytes(response_proto_status_line, 'utf-8'))
        connection.send(bytes(response_header, 'utf-8'))
        connection.send(bytes(response_body, 'utf-8'))

        # close the connection
        connection.close()
