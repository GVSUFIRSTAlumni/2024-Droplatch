#!/usr/bin/env python
import socket

# droplatch client
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 9999))

while True:
    user_in = input('enter a command >')
    if s.sendall(str.encode(user_in)) != None:
        print(f"failed to send all of {user_in}")
