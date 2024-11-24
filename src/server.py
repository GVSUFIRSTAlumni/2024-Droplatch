#!/usr/bin/env python
# droplatch server

import socket
import selectors
from typing import Callable
try:
    import RPi.GPIO as GPIO
except:
    import Mock.GPIO as GPIO
import random
import time

# see https://pinout.xyz
GPIO.setmode(GPIO.BOARD)
GPIO.setup(36, GPIO.HIGH)

ADDR: str = 'localhost'
PORT: int = 9999
MAX_CONNECTIONS: int = 2

class Droplatch:
    def __init__(self, *pins):
        # save the pins
        self._pins: list[int] = list(pins)
        # Setup pins
        GPIO.setmode(GPIO.BOARD)
        pin: int
        for pin in self._pins:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
    
    def setPin(self, pinNum: int, state: bool):
        """ set a pin high (state == True) or low """
        GPIO.output(self._pins[pinNum], state)

    def setPinByValue(self, pinValue: int, state: bool):
        GPIO.output(pinValue, state)
    
    def readPin(self, pinNum: int) -> bool:
        """ read a pin's state (high == True) """
        return GPIO.input(self._pins[pinNum])

    def randSelect(self):
        pins =  []
        for x in range(len(self._pins)):
            pins.append(self._pins[x])

        while len(pins) > 0:
            time.sleep(random.randint(5, 15) / 10.0)
            randnum = random.randint(0, len(pins) - 1)
            self.setPinByValue(pins[randnum], False)
            time.sleep(1)
            self.setPinByValue(pins[randnum], True)
            del pins[randnum]
            
    def zero(self):
        for x in self._pins:
            self.setPinByValue(x, False)
        time.sleep(.5)
        for x in self._pins:
            self.setPinByValue(x, True)

selector: selectors.BaseSelector = selectors.DefaultSelector()
# droplatch: Droplatch = Droplatch(21, 23, 27, 29, 31, 33, 35, 37)
droplatch: Droplatch = Droplatch(21, 23, 29, 31, 33, 35, 37, 11)

def _numericCommand(conn: socket.socket, number: str, on_success: str, func: Callable[int, None]):
    """ helper func for commands in the form <verb> <n> """
    try:
        num_parsed: int = int(number) - 1
        if num_parsed >= 0:
            func(num_parsed)
            conn.sendall(on_success.format(number=num_parsed+1).encode("utf-8"))
        else:
            conn.sendall(f"invalid number \"{number}\"".encode("utf-8"))
    except ValueError:
        conn.sendall(f"cannot parse \"{number}\"".encode("utf-8"))

def handleCommand(conn: socket.socket, command: str):
    """ handle received data; largely just routes to setPin. """
    match command.split():
        case ["echo"]:
            conn.sendall(b"echo! echo! echo!")
        case ["toggle"]:
            print("toggle requires a numeric argument.")
        case ["toggle", num]:
            _numericCommand(conn, num, "toggled pin {number}", lambda n: droplatch.setPin(n, not droplatch.readPin(n)))
        case ["set"]:
            print("set requires a numeric argument")
        case ["set", num]:
            _numericCommand(conn, num, "set pin {number} high", lambda n: droplatch.setPin(n, True))
        case ["unset"]:
            print("unset requires a numeric argument")
        case ["unset", num]:
            _numericCommand(conn, num, "set pin {number} low", lambda n: droplatch.setPin(n, False))
        case ["random"]:
            droplatch.randSelect()
        case ["dropAll"]:
            droplatch.zero()

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
