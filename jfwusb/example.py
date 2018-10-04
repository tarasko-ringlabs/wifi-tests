""" Examples for working with JFW USB devices. (Not Test Systems) """
import sys
from jfwusb import JfwUsb


import time
from threading import Thread
'''
Examples using the JfwUsb() class
'''
# find all JFW USB devices
try: jusb = JfwUsb()
except Exception as e:
    print(e)
    sys.exit(1)

# list devices
print("List of USB devices")
print(jusb.GetList())

# set programmable attenuator
'''
!assuming! device 1 is a programmable attenuator that can be set to 12dB.
Attenuator values are expressed as the desired value multiplied by 100. This
format allows for expressing attenuation values from 0dB to 127.75dB using
integers instead of floats.
try/except is used to catch the failure case
'''
print("Set Attenuator (device #1) to 12dB\n   (No Response Expected)")
try: jusb.Set(1, 50)
except Exception as e: print(e)

# read programmable attenuator
'''
!assuming! device 1 is a programmable attenuator
try/except is used to catch the failure case (Error reading device)
'''
# divide read value by 100 for dB
print("\nRead Attenuator (device #1)")
try: print("   Atten (Device #1) = {}dB".format(jusb.Read(1)/100))
except Exception as e: print(e)

# set programmable switch
'''
!assuming! device 2 is a programmable switch that can be set the common to port 1.
!assuming! device 2 is a programmable switch that has off state (port 0).
try/except is used to catch the failure case
'''
print("\nSet Switch (device #2)")
try:
    print("   Set Switch to port 1\n      (No Response Expected):")
    jusb.Set(2, 1) # set switch to port 1
    print("   Set Switch to its off State\n      (No Response Expected):")
    jusb.Set(2, 0) # set switch to off state (0) defines "offstate"
except Exception as e: print(e)

# read programmable switch
'''
!assuming! device 2 is a programmable switch.
Returned value is the common to port X expression.
Zero(0) denotes no connection to common.
try/except is used to catch the failure case (Error reading device)
'''
print("\nRead Switch (device #2)")
try: print("   Switch (Device #2) = {}".format(jusb.Read(2)))
except Exception as e: print(e)

'''
Working directly with JFW_USB()
'''

# import library
from jfwusb import JFW_USB

try: jusb = JFW_USB()
except Exception as e: print(e)

# set/read devices by serial number
print("\nSet Attenuator (Serial# 1234) to 0dB")
for device in jusb.Devices:
    try:
        if device.Serial == "1234":
            device.Set(0)
            print("   Atten ({}) = {}dB".format(device.Serial, device.Read()/100))
    except Exception as e: print(e)

# set all attenuators to max value
print("\nSetting all attenuators to MaxdB")
for device in jusb.Devices:
    try:
        if (device.Type == JFW_USB.DeviceType.Attenuator):
            device.Set(device.Hardware.Max)
            print("   Atten ({}) = {}dB".format(device.Name, device.Read()/100))
    except Exception as e: print(e)

# referencing specific devices based on serial numbers
at1 = None
at2 = None
for device in jusb.Devices:
    if device.Serial == "1234": at1 = device
    elif device.Serial == "2233": at2 = device

# attenuator handover
if at1 and at2:
    print("\nHandover of two attenuators")
    for db in range(1000, 3100, at1.Hardware.Step):
        at1.Set(db)
        at2.Set(4000 - db)
        print("   AT1={}dB AT2={}dB".format(at1.Read()/100, at2.Read()/100))
