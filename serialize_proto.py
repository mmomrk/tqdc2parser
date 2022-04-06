#!/usr/bin/env python3
import argparse
import numass_proto_pb2
import struct as st
import sys

oflenam = None
ifle = None
debug = False
events = [{'secs': 1630672787, 'nanosecs': 133085416, 'TDC_TS': 305, 'EvNum': 0, 'TDCdata': 88516, 'RCdata': 0, 'TDC-ADC_Chan': 0, 'TDC_WC': 2, 'DataPayLen': 24, 'channel': 4, 'rlen': 10, 'ts': 259, 'DataBlockDtype': 1, 'data': [-52, -44, -52, 4, 768, 2712, 4920, 6188, 6244, 5732]},
          {'secs': 1630672788, 'nanosecs': 770896824, 'TDC_TS': 3087, 'EvNum': 1, 'TDCdata': 89144, 'RCdata': 0, 'TDC-ADC_Chan': 0, 'TDC_WC': 2,
              'DataPayLen': 24, 'channel': 4, 'rlen': 10, 'ts': 261, 'DataBlockDtype': 1, 'data': [-56, -52, -40, 84, 1016, 3076, 5192, 6264, 6176, 5660]},
          {'secs': 1630672790, 'nanosecs': 409120048, 'TDC_TS': 2548, 'EvNum': 2, 'TDCdata': 89060, 'RCdata': 0, 'TDC-ADC_Chan': 0, 'TDC_WC': 2, 'DataPayLen': 24, 'channel': 4, 'rlen': 10, 'ts': 261, 'DataBlockDtype': 1, 'data': [-48, -52, -52, 200, 1480, 3672, 5600, 6324, 6040, 5540]}]


# bibnary will return total events count in order to put it to metadata, debug will spam, total will work with binary only. binary but not total will return serialized data only, unsigned will pack data as if it is unsigned (magic half max is added in parser)
def data_to_proto(events, binary=True, debug=False, total=False, unsigned=False):
    report = numass_proto_pb2.Point()
    totalEvents = 0
    for chan in range(8):
        firstFlag = True  # introduced to avoid checking whole data for a given channel presence
        ch = None
        for eve in filter(lambda x: x['channel'] == chan, events):
            if firstFlag:
                ch = report.channels.add()
                ch.id = chan
                blolock = ch.blocks.add()
                # 30 is something I wish for to be true
                blolock.time = (eve['secs'] << 30) + eve['nanosecs']
                firstFlag = False
            if eve['rlen'] == 0:
                # I refuse to believe:
                continue
            # 30 is something I wish for to be true
            eventArrivalTime = (eve['secs'] << 30) + eve['nanosecs']
            frontTime = eventArrivalTime + 8*eve['ts']
            frame = blolock.frames.add()
            frame.time = frontTime - blolock.time
            # Legacy numass requires unsigned two byte values. Hence it is parsed to unsigned
            if unsigned:
                formatStr = str(len(eve['data']))+'H'
            else:
                formatStr = str(len(eve['data']))+'h'
            frame.data = st.pack(formatStr, *eve['data'])
            # I guess it's nanoseconds per time step of ADC. However naming it "bin" is confusing: might have been ADC bin size in mV. But comment in proto says otherwise
            blolock.bin_size = 8

            amp = max(eve['data'])
            ind = eve['data'].index(amp)
            peakTime = frontTime + 8*ind
            if amp - 0x8000 < 0:
                ampModerated = 0  # moderation is needed to show nicer charts that are close to zero. Don't ask. This is a workaround around a workaround in the parser.py
            # And this breaks self-test's "amplitudes" field too. Bravo
            else:
                ampModerated = amp - 0x8000
            # don't bother trying to understand why variable time is assigned here. It is pointless
            time = blolock.events.times.append(peakTime - blolock.time)
            time = blolock.events.amplitudes.append(ampModerated)
            totalEvents += 1

            if debug:
                #print ("RAW_DEBUG_", [(t) for t in eve['data']], [x - 0x8000 for x in eve['data'] if x > 0x7fff  ])
                #print("Unpacking to :", st.unpack(formatStr, frame.data))
                print(eve)
        if debug and ch:
            print(ch)
    if binary:
        if total:
            return totalEvents, report.SerializeToString()
        else:
            return report.SerializeToString()
    else:
        return report


def parseArgs():
    global debug, oflenam, ifle, filt
    parser = argparse.ArgumentParser(
        description="A tool to serialize parsed data from binary of TQDC2 to the protobuf")
    parser.add_argument("-f", "--filename",
                        help="Output filename. Stdout if not specified")
    parser.add_argument(
        "-i", "--input", help="Input file source. Default stdin. Does not workk for now. Requires parsing string dictionaries")
    parser.add_argument(
        "-t", "--selftest", help="Perform self-test on small hardcoded data piece", action="store_true")
    parser.add_argument(
        "-d", "--debug", help="Add deserialized output at the end", action="store_true")
    arrrgs = parser.parse_args()
    debug = arrrgs.debug
    oflenam = arrrgs.filename
    ifle = arrrgs.input
    if debug:
        print("Shiver me timbers", arrrgs)
    return arrrgs


if __name__ == "__main__":
    arrrgs = parseArgs()
    if oflenam == None:
        ofle = sys.stdout
    else:
        ofle = open(oflenam, 'w')

    if arrrgs.selftest:
        data = events
        report = data_to_proto(data, binary=True, total=False, debug=debug)
        ofle.write(str(report))
        sys.exit()

    if arrrgs.input == None:
        dataArr = []
        for line in sys.stdin:
            data.append(line)
        data = "".join(dataArr)
    else:
        with open(arrrgs.filneame, 'r') as ifle:
            data = ifle.read()  # not tested
    # todo data to events and process according to the flags
