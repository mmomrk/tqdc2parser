#!/usr/bin/env python3

#import argparse

import sys
import struct

if len(sys.argv) == 1:
    print("Enter filename as an argument")
    sys.exit(1)

fname = sys.argv[1]
print("DEBUG: working with", fname)

fle = open(fname, 'rb')

getNext = fle.read


def iuint(x):
    lx = len(x)
    assert lx <= 4, "Too long int leaked for struct unpack"
    if lx == 4:
        return struct.unpack('I', x)[0]
    else:
        return struct.unpack('I', x + b'\x00'*(4-lx))[0]


def iusint(x): return struct.unpack('H', x)[0]
def iubint(x): return struct.unpack('B', x)[0]


def parseEventBlock(get):
    sword = iuint(get(4))
    swordDef = 0x2A502A50
    if sword != swordDef:
        print("ERROR: Sync word does not match. Invalid format")
        # sys.exit(2)

    payloadLength = iuint(get(4))
    print("DEBUG: payload length is ", payloadLength)

    eventNumber = iuint(get(4))
    print("DEBUG: event number is ", eventNumber)
    return payloadLength


def parseDeviceEventBlock(get):
    serial = iuint(get(4))
    deviceID = iubint(get(1))
    payloadLength = iuint(get(3))
    print(
        f"DEBUG: reading Device Event Block from serial {serial}, ID:{deviceID}, of size {payloadLength} bytes")

    endFilePointer = fle.tell() + payloadLength*4
    while fle.tell() < endFilePointer:
        parseMStreamBlock(get)
    sys.exit(111)


def parseMStreamBlock(get):
    subtypeBits = iubint(get(1))
    dense3bytes = iuint(get(3))
    payloadLengthWords = dense3bytes >> 2
    mStreamSubtype = dense3bytes & 0b11
    dataBlock = get(4*payloadLengthWords)
    data = struct.unpack('i' * payloadLengthWords, dataBlock)
    print(
        f"DEBUG: subtype bits of MStream {bin(subtypeBits)}. Payload size {payloadLengthWords} words, MStream subtype {mStreamSubtype}. Data:\n{data}")


if __name__ == "__main__":
    plength = parseEventBlock(getNext)
    while fle.tell() < 4 + plength:
        parseDeviceEventBlock(getNext)
