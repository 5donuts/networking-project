"""
Charles German & Gabe Lake
Webserver
"""
from socket import *

# set up TCP server
serverPort = 14000
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(1)

# page codes
PAGE_NORMAL = 0
PAGE_404 = 1
PAGE_501 = 2

"""
generate the response page based on the page code
and the client's ip address
"""
def getPage(pageCode, ipAddr):
	if pageCode == PAGE_NORMAL:
		return "<!DOCTYPE html>\n" \
			   "<head>\n" \
			   "\t<title>BC Black Site</title>\n" \
			   "</head>\n" \
			   "<body>\n" \
			   "\tBridgewater Black Site</br>\n" \
			   "\tYour IP address is " + str(ipAddr) + "\n" \
			   "</body>\n"
	elif pageCode == PAGE_404:
		return "<!DOCTYPE html>\n" \
			   "<head>\n" \
			   "\t<title>404 Not Found</title>\n" \
			   "</head>\n" \
			   "<body>\n" \
			   "\tError 404: Page Not Found</br>\n" \
			   "\tYour IP address is " + str(ipAddr) + "\n" \
			   "</body>\n"
	elif pageCode == PAGE_501:
		return "<!DOCTYPE html>\n" \
			   "<head>\n" \
			   "\t<title>501 Not Implemented</title>\n" \
			   "</head>\n" \
			   "<body>\n" \
			   "\tError 501: Request Not Implemented</br>\n" \
			   "\tYour IP address is " + str(ipAddr) + "\n" \
			   "</body>\n"
	else:
		return "<!DOCTYPE html>\n" \
			   "<head>\n" \
			   "\t<title>ERROR</title>\n" \
			   "</head>\n" \
			   "<body>\n" \
			   "\tSomething REALLY went wrong," \
			   "you shouldn't be seeing this page</br>" \
			   "Your IP address is " + str(ipAddr) + "\n" \
			   "</body>\n"

"""
determine the request type (HTTP GET, HTTP POST, etc.)
from the request string
"""
def getRequestType(request):
	return request.split('\n', 1)[0].split(' ', 1)[0]

"""
determine the page requested (/, /index.html, etc.)
from the request string
"""
def getRequestPage(request):
	return request.split('\n', 1)[0].split(' ', 2)[1]

"""
get the ip address of the client
from the connection object
"""	
def getIPAddr(connection):
	return str(connection.getpeername()[0])

# listen for connections until SIGTERM is received
print("Webserver started. Use ^C to exit")
while True:
	# establish connection with client
	connection = serverSocket.accept()[0]

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
	if getRequestType(request) == 'GET':
		if getRequestPage(request) == '/':
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
	responseBody = getPage(pageCode, getIPAddr(connection))
	responseHeader = "Content-Type: text/html; encoding=utf8\n" \
					 "Content-Length: " + str(len(responseBody)) + "\n" \
					 "Connection: close\n\n"

	# send the HTTP response
	connection.send('%s %s %s' % (responseProto, responseStatus, responseStatusText))
	connection.send(responseHeader)
	connection.send(responseBody)

	# close the connection
	connection.close()