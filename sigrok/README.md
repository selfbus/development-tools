Sigrok Stuff
============

This project contains stuff for the free Sigrok signal analysis software.
See www.sigrok.org

The decoders directory contains protocol decoders for pulseview.

Example on how to capture a recording on the commandline:

sigrok-cli -d fx2lafw --time 20s --config samplerate=100k --channels 0=ETS,1=FT12,2=BUS -t ETS=10 -w -o mycapture.sr

This captures 20 seconds at 100kHz from the 3 channels of the fx2lafw logic analyzer 
(any Saelae Logic / USBee compatible device). The capturing starts when the channel "ETS"
changes from 1 to 0.  The result is stored in mycapture.sr

