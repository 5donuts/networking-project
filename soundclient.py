from socket import * 
serverName = '127.0.0.1'
serverPort = 4000
clientSocket = socket(AF_INET, SOCK_STREAM) 
clientSocket.connect((serverName,serverPort))
clientSocket.send(bytes("101001101001001010100101010101010010101001010100101010101001010010101010010100011"*1000,'utf-8'))
clientSocket.close()
