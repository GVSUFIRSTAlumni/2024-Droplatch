import socket
import sys

# droplatch server
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(('localhost', 9999))
serversocket.listen(2)

while True:
    connection, address = serversocket.accept()
    while True:
        buf = connection.recv(64)
        print(f"read in a buffer of size {len(buf)}")
        if len(buf) > 0:
            print(buf)
            if buf == "quit":
                sys.exit(0)

