"""
Charles German & Gabe Lake
Webserver
"""
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
def get_page(page_code, ip_addr):
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
               "you shouldn't be seeing this page</br>" \
               "Your IP address is " + str(ip_addr) + "\n</body>\n"


# determine the request type (HTTP GET, HTTP POST, etc.) from the request string
def get_request_type(request):
    return request.split('\n', 1)[0].split(' ', 1)[0]


# determine the page requested (/, /index.html, etc.) from the request string
def get_request_page(request):
    return request.split('\n', 1)[0].split(' ', 2)[1]


# get the ip address of the client from the connection object
def get_addr(connection):
    return str(connection.getpeername()[0])


if __name__ == "__main__":
    sock = setup()

    # listen for connections until SIGTERM is received
    print("Webserver started. Use ^C to exit")

    while True:
        # establish connection with client
        connection = sock.accept()[0]

        # declaring variables for HTTP response
        responseBody = ''
        responseHeader = ''
        responseStatus = ''
        responseStatusText = ''
        responseProto = 'HTTP/1.1'

        # receive HTTP request
        request = connection.recv(4096)

        # determine request type & form response status/text
        pageCode = -1
        if get_request_type(request) == 'GET':
            if get_request_page(request) == '/':
                pageCode = PAGE_NORMAL
                responseStatus = '200'
                responseStatusText = 'OK'
            else:
                pageCode = PAGE_404
                responseStatus = '404'
                responseStatusText = 'NOT FOUND'
        else:
            pageCode = PAGE_501
            responseStatus = '501'
            responseStatusText = 'NOT IMPLEMENTED'

        # form response body & header
        responseBody = get_page(pageCode, get_addr(connection))
        responseHeader = "Content-Type: text/html; encoding=utf8\n" \
                         "Content-Length: " + str(len(responseBody)) + "\nConnection: close\n\n"

        # send the HTTP response
        connection.send('%s %s %s' % (responseProto, responseStatus, responseStatusText))
        connection.send(responseHeader)
        connection.send(responseBody)

        # close the connection
        connection.close()
