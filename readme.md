This is a tool for parsing AFI-TQDC2 binary file data that is stored in the MPD Raw format.

Specs and test file could be found on these pages:
- Event block, Device Event block, MStream block
https://afi.jinr.ru/MpdDeviceRawDataFormat
- TQDC - realted specs
https://afi.jinr.ru/DataFormatTQDC16VSE

Other specs have been reverse-engineered

By the time this message is written the code may pose an impression of being executable and working

I promise I will write documentation later

TODO:
- Format the output to correspond the expectations. Perhaps make separate flags for different output formats too
- Check bug with reading length shift 17 bits instead of documented(?) 16 bits. AND with corresponding timestamp that fits the other bits of the word
- Watch out for all the "Watch it" comments
- Write readme.md properly so that it gives an impression of me being a good programmer
- Add argparser
- Test with more data files
