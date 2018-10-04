
"""
This module provides access to JFW usb devices.

JFW_USB:    Interface class
JfwUsb:     Example/Convenience class demonstrating common tasks

Naming conventions
    underscore preceding name: _example, _Example, etc.
        signifies "private". Do not reference, can and will change.

    capitalized first character in class, method, property.
        signifies meant for public use.

    lower case first character in class, method, property.
        signifies not meant for public use.

"""
from enum import Enum
import os
import struct
import usb.core

__author__ = "JFW Industries. Inc"
__copyright__ = "Copyright 2017, JFW Industries. Inc"
__license__ = "All Rights Reserved"
__maintainer__ = "Adam Klinkel"
__email__ = "engr@jfwindustries.com"
__status__ = "Production"
__version__ = "1.0.1"

'''
Change Log

2-12-18 (v1.0.1):
    Added support for 0.25dB and 0.50dB attenuators.
'''

# Direct linter to accept personal choices in style and naming conventions.
# pylint: disable=C0103,C0321,C0330,W0702,W0311,W0703,R0902,R0903

class JfwUsbException(Exception):
    """ Default exception """
    pass

class JFW_USB():
    """
    Interface class for working with common JFW usb devices. (Not Test Systems)
    Notice:
        1) Attenuators values are expressed in terms of their dB value multiplied by 100.
        example: 12dB set/read would be 1200, 31.25dB set/read would be 3125
        2) The value of the offstate of a switch that has an off state is 0.
    """
    class DeviceType(Enum):
        """ Type of JFW USB device """
        Attenuator = 1
        Switch = 2

    class device_V1():
        """ First generation controller """

        class atten_V2():
            """ Second generation attenuator """

            @property
            def Min(self):
                """ Attenuator minimum value """
                return self._min
            @property
            def Max(self):
                """ Attenuator maximum value """
                return self._max
            @property
            def Step(self):
                """ Minimum unit value """
                return self._step
            @property
            def Type(self):
                """ Device type """
                return JFW_USB.DeviceType.Attenuator

            def CheckValue(self, value):
                """
                Device value range check
                Return: In_range(True), Out_of_range(False)
                """
                try:
                    if ((value >= self._min) and (value <= self._max)
                        and ((value % self._step) == 0)): return True
                except: pass
                return False

            def ToString(self):
                """ Key value pair string of hardware parameters """
                return "Type=Attenuator Min={0} Max={1} Step={2}" \
                    .format(self._min, self._max, self._step)

            def __init__(self, data, offset):
                try:
                    self._min, self._max, self._step \
                        = struct.unpack_from("H H H", data, offset)
                    weights = struct.unpack_from("8H", data, offset + 6)
                    temp = []
                    for n, weight in enumerate(weights):
                        temp.append((n, weight))
                    
                    self._weights = tuple(sorted(temp, reverse=True, key=lambda s: (s[1], s[0])))
                    self._wcount = 8 - self._weights.count(0)
                except:
                    raise JfwUsbException("Unable to identify Attenuator (Corrupt Flash)")

            def _set(self, value):
                """
                Transform dB $value to device bus $value
                Return: Success(bus $value), Fail(Exception)
                """
                bus = 0
                try:
                    if self.CheckValue(value):
                        if value == 0: return bus

                        for i, weight in enumerate(self._weights):
                            flag = False
                            if value >= self._weights[i][1]:
                                if ((i == len(self._weights) -1)
                                    or (self._weights[i][1] != self._weights[i+1][1])
                                    or (value >= 2*self._weights[i][1])):
                                    flag = True
                            if flag:
                                bus |= (1 << self._weights[i][0] )
                                value -= self._weights[i][1]                            

                        return bus
                except: pass
                raise JfwUsbException("Value out of range")

            def _read(self, bus):
                """
                Transform bus $value to dB $value
                Return: Success(db $value), Fail(Exception)
                """
                value = 0
                try:
                    for w in self._weights:
                        if bus & (1<<w[0]):
                            value += w[1]
                    if self.CheckValue(value):
                        return value
                except: pass
                raise JfwUsbException("Value out of range")

        class switch_V1():
            """ First generation switch """

            class OffStates(Enum):
                """ State of switch in the off state """
                Has_None = 0
                Reflective = 82
                Terminated = 84

            @property
            def OffState(self):
                """ Switch off state type """
                return self.OffStates(self._port0_type)
            @property
            def Ports(self):
                """ Number of ports available """
                return self._count
            @property
            def Type(self):
                """ Device Type """
                return JFW_USB.DeviceType.Switch

            def CheckValue(self, value):
                """
                Device value range check
                Return: In_range(True), Out_of_range(False)
                """
                try:
                    if ((value == self._port0_type == 0)
                        or (value <= self._count)): return True
                except: pass
                return False

            def ToString(self):
                """ Key value pairs string of hardware parameters """
                return "Type=Switch Ports={0} OffState={1}".format(self._count, self.OffState.name)

            def __init__(self, data, offset):
                try:
                    self._port0_type, self._port0_value, self._count \
                        = struct.unpack_from("B B B", data, offset)
                    self._ports = struct.unpack_from("{}B".format(self._count), data, offset + 3)
                except:
                    raise JfwUsbException("Unable to identify Switch (Corrupt Flash)")

            def _set(self, value):
                """
                Transform switch $value to bus $value
                Return: Success(bus $value), Fail(Exception)
                """
                try:
                    if self.CheckValue(value):
                        return self._port0_value if value == 0 else self._ports[value -1]
                except: pass
                raise JfwUsbException("Value out of range")

            def _read(self, bus):
                """
                Transform bus $value to switch $value
                Return: Success(switch $value), Fail(Exception)
                """
                if (bus == self._port0_value) and (self._port0_type != 0):
                    return 0
                for i, p in enumerate(self._ports):
                    if bus == p:
                        return i+1 # index starts at 1
                raise JfwUsbException("Value out of range")

        @property
        def Model(self):
            """ Device model name """
            return self._model
        @property
        def Serial(self):
            """ Device serial number """
            return self._serial
        @property
        def DateCode(self):
            """ Device datecode """
            return self._dcd
        @property
        def Type(self):
            """ Device type """
            return self._vdevice.Type
        @property
        def Hardware(self):
            """ Hardware specific accessors """
            return self._vdevice

        # Name property
        def _name_get(self):
            return self._name
        def _name_set(self, value):
            self._name = value
        Name = property(_name_get, _name_set)

        def Set(self, value):
            """
            Transform $value to device specific $value and send to device
            Return: Success(None), Fail(Exception)
            """
            # pylint: disable=W0212
            try:
                data = self._vdevice._set(value)
                self._writeGPIO(data)
            except Exception as e: raise e

        def Read(self):
            """
            Read device bus $value and transform into device specific $value
            Return: Success(device specific $value), Fail(Exception)
            """
            # pylint: disable=W0212
            try:
                data = [0]*16
                data[0] = 0x80
                self._device.write(self._ep_out, data)
                r = self._device.read(self._ep_in, 16)
                r = self._vdevice._read(r[10])
            except Exception as e: raise e
            return r

        def ToString(self):
            """
            Space delimited string of JFW USB devices
            Notice: Name is returned between double quotes to cover the case
                in which Name contains spaces
            """
            return "Model={} Name=\"{}\" Serial={} DateCode={} {} Value={}" \
                .format(self._model, self.Name, self._serial, self._dcd,
                    self._vdevice.ToString(), self.Read())

        def __init__(self, device):
            """ Device Name, Does Not Write to Device """
            self._name = None
            try:
                self._device = device
                self._raw = bytearray(256)
                self._ep_in = self._device[0][(2, 0)][0]    # fixed HID read endpoint
                self._ep_out = self._device[0][(2, 0)][1]   # fixed HID write endpoint

                # read device into __raw
                data = [0]*16
                data[0] = 0x20
                for i in range(0, 256):
                    data[1] = i
                    self._device.write(self._ep_out, data)
                    r = device.read(self._ep_in, 16)
                    self._raw[i] = r[3]

                # determine header version
                tmp = struct.unpack_from("I", self._raw, 4)[0]
                self._type = tmp & 0x00FF
                self._version = tmp & 0xFF00

                # unpack name and header
                self._vdevice = None
                name = model = serial = dcd = None
                if self._version == 256:
                    name, model, serial, dcd = struct.unpack_from("16s 16s 12s 8s", self._raw, 8)
                    if self._type == 1:
                        self._vdevice = self.atten_V2(self._raw, 100)
                    elif self._type == 2:
                        self._vdevice = self.switch_V1(self._raw, 100)

                if self._vdevice is None:
                    raise JfwUsbException("Unknown USB Device")
                self.Name = name.partition(b'\0')[0].decode('ascii')
                self._dcd = dcd.partition(b'\0')[0].decode('ascii')
                self._model = model.partition(b'\0')[0].decode('ascii')
                self._serial = serial.partition(b'\0')[0].decode('ascii')
            except Exception as e: raise e

        def _writeGPIO(self, value):
            """ GPIO write """
            data = [0]*16
            data[0] = 0x08
            data[11] = value # set bits
            data[12] = ~value & 0xFF # clear bits
            self._device.write(self._ep_out, data)

    def __init__(self):
        """
        Query USB bus for various JFW USB devices
        Return: Success(Tuple of Devices), Fail(Exception)
        """
        devices = []
        # find all JFW USB devices
        # first generation usb devices
        found = usb.core.find(find_all=True, idVendor=0x4d8, idProduct=0x00df)

        # identify JFW usb devices
        for device in found:
            try:
                if (os.name == "posix") and (device.is_kernel_driver_active(2)):
                    device.detach_kernel_driver(2)
                d = self.device_V1(device)
                devices.append(d)
            except Exception as e:
                print(e)
                pass    # matching USB device was not identified

        # second generation usb devices

        # direct access to devices.
        # (GetList, Set, Read exist for example control)
        if not devices:
            raise JfwUsbException("No JFW USB devices found")
        self.Devices = tuple(devices)


class JfwUsb():
    '''
    The intended use of this class is to demonstrate
    Listing, Setting, and Reading of JFW usb devices.
    '''
    def GetList(self):
        """
        Return list of attached JFW USB devices
        """
        r = ""
        for i, device in enumerate(self._jusb.Devices):
            r += "ID=" + str(i+1) + " " + device.ToString() + "\n"
        return r

    def Set(self, num, value):
        """
        Set device $num(reference by GetList ID field) to $value
        Return { Success: None; Fail: Exception }
        """
        device = None
        try:
            num -= 1 # people like indexes starting @ 1
            device = self._jusb.Devices[num]
        except: raise JfwUsbException('Error (Device Set): unknown device {}'.format(num))

        try: device.Set(value)
        except Exception as e: raise e

    def Read(self, num):
        """
        Read the $value of device $num(reference by GetList ID field)
        Return { Success: $value: Fail: Exception }
        """
        try:
            num -= 1 # people like indexes starting @ 1
            device = self._jusb.Devices[num]
        except: raise JfwUsbException('Error (Device Set): unknown device {}'.format(num))

        try: return device.Read()
        except Exception as e: raise e

    def __init__(self):
        try: self._jusb = JFW_USB()
        except Exception as e: raise e
