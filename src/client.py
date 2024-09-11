#!/usr/bin/env python
import socket

# droplatch client
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 9999))
s.send(str.encode('hello'))