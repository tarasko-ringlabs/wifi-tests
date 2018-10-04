#!/usr/bin/python2
#__counter 16


import sys
from jfwusb import JfwUsb

if len(sys.argv) > 1:
    target_dbm=int(sys.argv[1])
else:
    target_dbm=0.0


print("Attenuator set to dBm: %d" % target_dbm)

#find all JFW USB devices
try: jusb = JfwUsb()
except Exception as e:
    print(e)
    sys.exit(1)

# divide read value by 100 for dB
print("\nRead Attenuator (device #1)")
try: print("   Atten (Device #1) = {}dB".format(jusb.Read(1)/100))
except Exception as e: print(e)

print("Set Attenuator %ddB\n" % target_dbm)
try: jusb.Set(1, target_dbm*100)
except Exception as e: print(e)

