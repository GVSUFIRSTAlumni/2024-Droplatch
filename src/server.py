#!/usr/bin/env python
# droplatch server

import socket
import selectors
from typing import Callable
# import RPi.GPIO as GPIO

# see https://pinout.xyz
# GPIO.setmode(GPIO.BOARD)

ADDR: str = 'localhost'
PORT: int = 9999
MAX_CONNECTIONS: int = 2

selector: selectors.BaseSelector = selectors.DefaultSelector()

def setPin(pinNum: int, state: bool):
    """ set a pin high (state == True) or low """
    # TODO
    pass

def getPin(pinNum: int) -> bool:
    """ get the state of a pin (true == high) """
    # TODO
    return False

def _numericCommand(conn: socket.socket, number: str, on_success: str, func: Callable[int, None]):
    """ helper func for commands in the form <verb> <n> """
    try:
        num_parsed: int = int(number)
        func(num_parsed)
        conn.sendall(on_success.format(number=num_parsed).encode("utf-8"))
        # print(on_success.format(number=num_parsed))
    except ValueError:
        conn.sendall(f"cannot parse \"{number}\"".encode("utf-8"))
        # print(f"cannot parse \"{number}\"")

def handleCommand(conn: socket.socket, command: str):
    """ handle received data; largely just routes to setPin. """
    match command.split():
        case ["echo"]:
            conn.sendall(b"echo! echo! echo!")
        case ["toggle"]:
            print("toggle requires a numeric argument.")
        case ["toggle", num]:
            _numericCommand(conn, num, "toggled pin {number}", lambda n: setPin(n, not getPin(n)))
        case ["set"]:
            print("set requires a numeric argument")
        case ["set", num]:
            _numericCommand(conn, num, "set pin {number} high", lambda n: setPin(n, True))
        case ["unset"]:
            print("unset requires a numeric argument")
        case ["unset", num]:
            _numericCommand(conn, num, "set pin {number} low", lambda n: setPin(n, False))

def accept(sock: socket.socket, mask: int):
    """ handle incoming connections """
    # accept the incoming connection
    conn: socket.socket
    # addr is a private type
    conn, addr = sock.accept()
    # make it non-blocking - selectors are useless without this
    conn.setblocking(False)
    # register the accepted connection with the selector
    selector.register(conn, selectors.EVENT_READ, read)

def read(conn: socket.socket, mask: int):
    """ handle incoming data from existing connections """
    # read incoming data
    data: bytes = conn.recv(1000) # this buffer size is arbitrary, and probably does not need to be this high
    if data:
        # assuming data is a utf-8 encoded string; in reality I expect it to always
        # be ascii, but utf-8 is a superset of ascii anyways.
        data_str: str = data.decode("utf-8")
        print(f"received data \"{data_str}\" from {conn}")

        # handle received data
        handleCommand(conn, data_str)
    else:
        print(f"closing connection {conn}")
        selector.unregister(conn)
        conn.close()

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind((ADDR, PORT))
serversocket.listen(MAX_CONNECTIONS)
serversocket.setblocking(False)
selector.register(serversocket, selectors.EVENT_READ, accept)

while True:
    events = selector.select()
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
