#!/usr/bin/env python

# droplatch client

import socket
import selectors

ADDR: str = 'localhost'
PORT: int = 9999
MAX_CONNECTIONS: int = 2

def readSock(sock: socket.socket, mask: int):
    data: bytes = sock.recv(1000)
    if data:
        print(f"{data.decode('utf-8')}")

# setup socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ADDR, PORT))
s.setblocking(False)
# setup selector
selector: selectors.BaseSelector = selectors.DefaultSelector()
selector.register(s, selectors.EVENT_READ, readSock)

while True:
    # read in user command
    user_in = input('enter a command > ')
    # send command to server
    if s.sendall(str.encode(user_in)) != None:
        print(f"failed to send all of {user_in}")
    # handle "quit" command (could probably be done before sending)
    if (user_in == "quit"):
        break
    # check for server response (1s timeout)
    events = selector.select(timeout=1)
    key: selectors.SelectorKey
    # mask is a private type
    for key, mask in events:
        # we happen to store callbacks in the data, but it is an opaque type
        # that can be anything we want so I am not type hinting it.
        callback = key.data
        # the field is called fileobj because you can use selectors on any
        # kind of file descriptor, but it's really the socket here. Sockets
        # just happen to also be a type of file, albeit a virtual one.
        callback(key.fileobj, mask)
