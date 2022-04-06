# TQDC2Parser

This is a tool for parsing AFI-TQDC2 binary file data that is stored in the MPD Raw format.

Specs and test file could be found on these pages:
- Event block, Device Event block, MStream block
https://afi.jinr.ru/MpdDeviceRawDataFormat
- TQDC - realted specs
https://afi.jinr.ru/DataFormatTQDC16VSE

Other specs have been reverse-engineered

# Usage: 

parser.py [-h] [-f {numass,numassDebug,debug,txt,dictionary}] [-o OUTPUT] [-g GATE] [-c] filename

positional arguments:

  filename

optional arguments:

  -h, --help            show this help message and exit

  -f {numass,numassDebug,debug,txt,dictionary}, --format {numass,numassDebug,debug,txt,dictionary} output format. Default debug. txt might have bigger output.You are welcome to commit. 'dictionary' would print a line with a dictionary for each event found; uses json-friendly double quotes. Numass and numassDebug will serialize with serializer.py

  -o OUTPUT, --output OUTPUT output file. Will throw everything to stdout if not specified

  -g GATE, --gate GATE  argument to be passed to --gate in serializer. Will filter events with waveforms PP smaller than gate. No pun intended

  -c, --config          parse configuration file
 
# Comments

- 'Gate' argument is put here for basic noise alimination in case experiment has been conducted with 'Zero Suppression' flag turned off
- Format 'numass' is the most used version of output format
- Debug formats will throw addresses alongside with all the information that has been restored from the file. This may contain unwanted information (SWF though)
- 'dictionary' format is there to help integrate into json-related pipeline
- Format 'txt' is most likely the best one to begin with. It offers minimalistic ASCII lines as output inspired by the text mode in the TQDC2 GUI app
- This package ships with serialize_proto.py and numass-proto.proto that are used specifically in the nu-mass experiment. This might seem like bloat because it is. I just don't know how to properly organise packages. But you may find it useful to use protobuf and dataforge format and do the same serialisation because there are benefits to having human-readable metadata stored alongside with tightly-packed binary data. Also contains workarounds and workarounds around workarounds because legacy.
- 'config' flag is used to parse and store additional TQDC GUI app configuration into datafiles in the numass format in order to help investigations later


# TODO:

- Check bug with reading length shift 17 bits instead of documented(?) 16 bits. AND with corresponding timestamp that fits the other bits of the word
	- sent report to devs
- Watch out for all the "Watch it" comments
- Write readme.md properly so that it gives an impression of me being a good programmer
	- wip
- Add stdin suport so that piping is possible
- Test with more data files

# Tests

	This repo contains couple .dat files that could be fed into the parser to see that it may return no errors

# Licence

This code is published under MIT licence. Don't blame me if your PC is on fire
