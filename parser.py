#!/usr/bin/env python3

# import argparse

import sys
import struct

if len(sys.argv) == 1:
    print("Enter filename as an argument")
    sys.exit(1)

fname = sys.argv[1]
print("DEBUG: working with", fname)

fle = open(fname, 'rb')

getNext = fle.read

wNum = 0


def getNext(x):
    global wNum
    i = fle.read(x)
    stro = ''
    print(hex(wNum), ':', i.hex(" ", 1))
    wNum += len(i)
    return i


# int data types for unpack b,s,i,l. Upper for unsigned
def iuint(x):
    lx = len(x)
    assert lx <= 4, "Too long int leaked for struct unpack"
    if lx == 4:
        return struct.unpack('I', x)[0]
    else:
        return struct.unpack('I', x + b'\x00'*(4-lx))[0]


def iusint(x): return struct.unpack('H', x)[0]
def issint(x): return struct.unpack('h', x)[0]
def iubint(x): return struct.unpack('B', x)[0]


def parseEventBlock(get):
    sword = iuint(get(4))
    swordDef = 0x2A502A50
    if sword != swordDef:
        print("ERROR: Sync word does not match. Invalid format", hex(sword))
        sys.exit(2)
    else:
        print("TRACE: Sync word ok")

    payloadLength = iuint(get(4))
    print("DEBUG: payload length is ", payloadLength)

    eventNumber = iuint(get(4))
    print("DEBUG: event number is ", eventNumber)
    return payloadLength


def parseDeviceEventBlock(get):
    print("TRACE: parsing device event block")
    serial = iuint(get(4))
    payloadLength = iuint(get(3))
    deviceID = iubint(get(1))
    print(
        f"DEBUG: reading Device Event Block from serial {hex(serial)}, ID:{hex(deviceID)}:{deviceID}, of size {hex(payloadLength)}:{payloadLength} bytes")

    endFilePointer = fle.tell() + payloadLength*4
    # while fle.tell() < endFilePointer:
    parseMStreamBlock(get)


def parseMStreamBlock_not(get):
    pass


def parseMStreamBlock(get):
    print("TRACE: parsing mstream block")
    dense3bytes = iuint(get(3))
    subtypeBits = iubint(get(1))
    payloadLengthWords = dense3bytes >> 2
    mStreamSubtype = dense3bytes & 0b11
    print(
        f"DEBUG: subtype bits of MStream {hex(subtypeBits)}:{bin(subtypeBits)}. Payload size  {hex(payloadLengthWords)}:{payloadLengthWords} words, MStream subtype {mStreamSubtype}. ")
    parseMStreamPayload(get)


def parseInputCountersLowBits(data):
    # 27 - 19 = 9 when you include both ends
    channel = (data >> 19) & 0b111111111
    bits31_16 = data & 0b1111111111111111  # 16 bits
    if data & (0b111 << 16):
        print(
            f"WARNING: data does not follow the protocol. Input counters low bits has non-zero bits 16..18 {hex(data)}")
    return ({"ICChanLow": channel, "b31-16": bits31_16})


def parseInputCountersHighBits(data):
    channel = (data >> 19) & 0b111111111  # from 27 to 19 included
    bits15_0 = data & 0b1111111111111111  # 16 bits
    if data & (0b111 << 16):
        print(
            f"WARNING: data does not follow the protocol. Input counters high bits has non-zero bits 16..18 {hex(data)}")
    return {"ICChanHigh": channel, "b0-15": bits15_0}


def parseTDCEventHeader(data):
    evHdrEvNumPlusTrash = data
    # 12 bits. # QM = question mark
    tdcTimestampQM = data & 0b111111111111
    evNum = (data >> 12) & 0b111111111111  # 12 more bits
    print(
        f"TDC event header ev num {evNum}, tstamp:{tdcTimestampQM}")
    if data & (0b11 << 26):
        print(
            f"WARNING: TDC event header word has non-zero bits 26..27: {hex(data)}")
    return({"TDC_TS": tdcTimestampQM, "EvNum": evNum})


def parseTDCEventTrailer(data):
    tdcWordCount = data & 0b111111111111  # 12 bits
    evNum = (data >> 12) & 0b111111111111  # 12 more bits
    if data & (0b11 << 26):
        print(
            f"WARNING: TDC event trailer word has non-zero bits 26..27: {hex(data)}")
    return ({"TDC_WC": tdcWordCount, "EvNum": evNum})


def parse4(data):
    mode = data >> 26 & 0b11
    ret = {}
    if (mode == 0):
        data = data & 0b111111111111111111  # 18 bits
        ret["TDCdata"] = data
        rcData = (data >> 24) & 0b11
        ret["RCdata"] = rcData
    else:
        wnum = data & (1 << 15)
        if wnum == 0:
            triggerTimestamp = data & 0b1111111111111111  # 16 bits
            ret["ADC_TrigTS"] = triggerTimestamp
        else:
            adcTimestamp = data & 0b1111111111111111  # 16 bits
            ret["ADC_TS"] = adcTimestamp
    channel = (data >> 19) & 0b11111  # 5 bits
    ret["TDC-ADC_Chan"] = channel
    # I really have little idea why I am doing this
    print(
        f"ADC timestamp mode {bin(mode)}, channel {channel}")
    # But it gives an impression of a working thing now
    return ret


def parseData(data):
    mode = (data >> 26) & 0b11
    channel = (data >> 19) & 0b11111  # 5 bits
    ret = {}
    ret["TADC_Chan"] = channel
    if mode == 0:
        stepCount = data & 0b1111111111111111111  # 19 bits. Not a mistake
        ret["BlockLen"] = stepCount
    elif mode == 1:
        adcSample = data & 0b11111111111111111  # 16 bits
        ret["TADC_CalibSample"] = adcSample
    elif mode == 2:
        adcSample = data & 0b11111111111111111  # 16 bits
        ret["TADC_Sample"] = adcSample
    elif mode == 3:
        sumADC = data & 0b1111111111111111111  # 19 bits. Not a mistake
        ret["TADC_Integ"] = sumADC
    return ret


def parseError(data):
    err = data & 0b111111111111111  # 14 bits
    return({"ERROR": err})


def parseUndocumentedWords(w1, w2):
    print("WARNING: adc block len and channel mask is likely a lie")
    # 16 bits according to DataFormatTQDC16VSE webpage 'Data Block Format' section
    dataPayloadLen = w1 & 0b1111111111111111
    # Watch it. This is to be additionally fuzzed
    channel = (w1 >> 24) & 0b1111  # see DataFormatTQDC16VSE
    dtype = w1 >> 28
    readingLen = w2 >> 17  # is this an error on the DataFormatTQDC16VSE webpage in the ADC data block section? it definitely fails with >> 16 on our data
    # "timestamp":
    shift = w2 & 0b1111111111111111  # Not too sure
    # an awful workaround??
    print("DEBUG: parsing undocumented ", hex(w1), hex(w2))
    res = {"DataPayLen": dataPayloadLen, "channel": channel,
           "rlen": readingLen, "ts": shift, "DataBlockDtype": dtype}
    return res


def getDataArray(get, length):
    data = []
    for t in range(length):
        data.append(issint(get(2)))
        # watch it: is likely to fail when rlen is odd
    return data


def parseMStreamPayload(get):
    print("TRACE: parse MStream Payload")
    timeSeconds = iuint(get(4))
    timeNanosecondsUndFlag = iuint(get(4))
    flag = timeNanosecondsUndFlag & 0b11
    timeNanoseconds = timeNanosecondsUndFlag >> 2  # could be >> 1. Watch it

    tdcBlockLen = iuint(get(4))
    print(f"TAI: {hex(timeSeconds)}_{timeSeconds}.{timeNanoseconds}, flag {flag}, TDC block len: {tdcBlockLen}")

    anotherOne = True
    event = {}
    i = 1
    while anotherOne:
        nxt = iuint(get(4))
        dtype = nxt >> 28
        res = {}
        if dtype == 0:
            res = parseInputCountersHighBits(nxt)
        elif dtype == 1:
            res = parseInputCountersLowBits(nxt)
        elif dtype == 2:
            res = parseTDCEventHeader(nxt)
        elif dtype == 3:
            res = parseTDCEventTrailer(nxt)
        elif dtype == 4:
            res = parse4(nxt)
        elif dtype == 5:
            res = parseData(nxt)
            # probably i will need another method call here. Watch it
            anotherOne = False
        elif dtype == 6:
            res = parseError(nxt)
        elif nxt == 0x70000000:
            print("TRACE: Found magic 0x70000000")
            (w1, w2) = (iuint(get(4)), iuint(get(4)))
            while w1 != 0x2a502a50:
                res = parseUndocumentedWords(w1, w2)
                if res['rlen'] > 0:
                    res['data'] = getDataArray(get, res['rlen'])
                print("ACHTUNG: ", res)
                (w1, w2) = (iuint(get(4)), iuint(get(4)))
                if w1 == w2 == 0x0:  # EOF dude
                    anotherOne = False
                    break
            else:
                # Rewind pointer back to magic to progress with its unexpected discovery later
                fle.seek(-8, 1)
                anotherOne = False
        else:
            print("ERROR: found incompatible data word type ", dtype)
        # This means we have unintentionally reached the next record:
        if nxt == 0x2a502a50:
            print(
                "WARNING: parser reached next data entry without finishing parsing of the previous one")
            anotherOne = False
            # rewind pointer to read 2a50 officially again further on route
            fle.seek(-4, 1)

        print(i, hex(nxt), dtype, res)
        i += 1
        event.update(res)
    print("Finished parsing this event", event)


def parseMStreamPayload_not(get):
    cStart = fle.tell()
    deviceID = iubint(get(1))
    flagsSubtype = iubint(get(1))
    flags = flagsSubtype >> 2
    subtype = flagsSubtype & 0b11
    fragmentLengthWords = iusint(get(2))
    fragmentID = iubint(get(1))
    fragmentOffsetBytes = iuint(get(3))
    # this line works incorrect for some reason:
    deviceSerial = iuint(get(4))
    print(
        f"DEBUG: MStream payload from device ID {hex(deviceID)}, with flags {bin(flags)} and subtype {bin(subtype)} that form {hex(flagsSubtype)} of length {hex(fragmentLengthWords)}:{fragmentLengthWords} words(?), fragment ID {hex(fragmentID)}, fragment offset {hex(fragmentOffsetBytes)} bytes, device serial {hex(deviceSerial)}")
    print("WARGNING: THIS LINE SHOULD CONTAIN VALID MATCH")
    if subtype:
        subtypeAndCustomBits = iubint(get(1))
        eventNumber = iuint(get(3))
        timestampS = iuint(get(4))
        timestampAndFlags = iuint(get(4))
        timestampNS = timestampAndFlags >> 2
        flagsTAI = timestampAndFlags & 0b11
        # +-1 is error is likely to happen here:
        dataLengthBytes = fragmentLengthWords*4 - 6
        print(
            f"DEBUG: mstream subtype 0 of event #{hex(eventNumber)} at time {timestampS}.{timestampNS} with flag TAI {bin(flagsTAI)}")
        dataBlock = get(dataLengthBytes)
        print("WARNING: This line has not been even tested on paper")
        sys.exit()
        data = struct.unpack("s"*dataLengthBytes/2, dataBlock)[0]
    elif subtype == 1:
        print("DEBUG: mstream subtype 1")
        # TODO
        pass


if __name__ == "__main__":
    plength = parseEventBlock(getNext)
    start = fle.tell()
    end = start + 12 + plength
    i = 1
    # while fle.tell() < end:
    while True:
        start = fle.tell()
        parseDeviceEventBlock(getNext)
        print("INFO: Event", i,
              f"pointer: {fle.tell()}, assert end: {end}\n++++++++++++++++++++++++++++")
        plength = parseEventBlock(getNext)
        end = start + 12 + plength
        i += 1
