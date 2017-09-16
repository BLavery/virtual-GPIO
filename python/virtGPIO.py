#!/usr/bin/python
# -*- coding: utf-8 -*-

# virtGPIO.py   V0.9.7

"""
"Virtual GPIO" uses an arduino as a GPIO device to a Raspberry Pi or PC.
This system uses USB serial (or rPi's UART) to control (and power??) the arduino.
This file is the PC end of "virtual-gpio", ie the python library module that your own python code imports.
This code is compatible with python 2.7 and python 3.3.
Includes functionality of "import RPi.GPIO" and "import smbus" and "import spidev"

"""

# PC instructions (Linux or Windows or Mac):
# You require python 2.7 or 3.3 installed, and "pyserial".
# The arduino simply stays connected to PC by USB cable.
# On Windows, you may need to experiment with COM port numbers assigned to Arduino.

# Raspberry Pi instructions:
# You require "pyserial" installed on the rPi.
# You may choose: (1) USB cable between, or (2) TTL wires from rPi uart pins to arduino uart pins.
# Here is how to configure for using the rPi's inbuilt uart:
# (sudo) edit /boot/cmdline.txt to remove the two phrases "console=ttyAMA0,115200  kgdboc=ttyAMA0,115200"
# (sudo) edit /etc/inittab to comment out the line containing "/dev/ttyAMA0" (the last line?)
# (sudo) edit /boot/config.txt by adding a new line "init_uart_clock=16000000"
# Reboot the rPi.
# Now, (1) uart is free and available for virtGPIO (rx -> tx and tx -> rx),
#      (2) and it can go at baudrate speeds way over the usual 115200,
# Configured as above, the rPi's own GPIO-uart works quite well with virtGPIO arduino at 500000 baud.
# But see WARNING below on interfacing tx and rx wires.

# Probably you can power the arduino from rPi's 5V supply, even using UART connection.
# But any substantial current requirement (eg servos beyond one small test one) needs provision of proper supply.

# WARNING: rPI UART 3.3V TX and RX LINES MUST NOT CONNECT DIRECTLY TO 5V RX and TX OF ARDUINO ...
#   ... You must use some form of voltage level shifting to 5V arduino, or use a 3.3V version arduino.

# ADDITIONALLY ...
# Want to load the arduino sketch via this same rPi uart line?  Refer to notes at top of "VirtGPIO.ino"



if __name__ == '__main__':
    print ("virtGPIO.py is an importable module for PC or Raspberry Pi:")
    print ("...  import virtGPIO as GPIO")
    print ("virtGPIO.py talks by USB-serial with ARDUINO-ftdi loaded with VirtGPIO.ino")
    print ("")
    exit()


import time
try:
    import serial
except:
    print("Virtual-GPIO ERROR: pyserial seems not installed on your python?")
    exit()
import sys
import glob
import os


def hardResetARD():
    Serial.setDTR(False)
    time.sleep(0.3)
    Serial.setDTR(True)
    time.sleep(3)   # and wait for it

def softResetARD():
    # reset Arduino in software. (AVR registers may not be initialised to full reset)
    _SerialWrite("0-");
    time.sleep(2.1)


def _i8(x):
    # x is either an int8 or a single character string
    # Used for processing _SerialRead characters from either str (python2) or bytes (python3)
    # return is always int8
    if type(x) == type(""):
        return ord(x)
    return x

def _SerialWrite(s):
    # accepts List (of int8), or string (to int7), free choice, or mixed. Avoid strings with chrs over 0x7f
    if type(s) == type(""):  # type str
        if sys.version_info.major == 2:   # python2
            Serial.write(s)     #  py2 accepts strings (with int8) directly
        else:  # python3
            Serial.write(s.encode('UTF-8'))   # -> bytes.  But only to 7-bit int
    else:   # type list
        if sys.version_info.major == 2:
            Serial.write(''.join(chr(e) for e in s))   # -> str incl int8
        else:
            Serial.write(bytes(s))    # -> bytes with int8


def _SerialRead(count=1):
    r = Serial.read(count)
    # python2 returns type str of int8      strr[x] -> "?"
    # python3 returns type bytes of int8    bb[x] ->  int8
    # receiving routines to handle the difference!  [_i8() function useful]
    return r


def _serial_ports():
    #  <http://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python>
    if sys.platform.startswith('win'):
        ports = ['COM' + str(i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this is to exclude your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


Serial = None
verboseSetup = False
STDTIMEOUT = 0.8

# Following are DEFAULT portnames and baudrates that are attempted for virtGPIO.
# Optional file serialConfig.py can override these defaults.
baudlist = [500000, 115200, 250000]
portlist = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyAMA0', 'COM1', "COM3", "COM8", "COM9"]
# (these lists may be edited. 500000 baud recommended, list it first.)
# (I'm not a Mac person. So of course, I haven't tested a Mac.
#           Try "ls /dev/tty.*" in terminal to help find your Mac serial port name.)
# Alternatively (BETTER!), use optional file "serialConfig.py" to override the baud and port settings above.

try:
    from serialConfig import *
except:
    pass

if portlist == "SMART":
    portlist = _serial_ports()
    if verboseSetup:
        print ("SMART Serial Port Seek:"),
        print (portlist)
elif verboseSetup:
    print ("Ports to test:")
    print (portlist)


for k in range(len(portlist)):
    try:
        Serial = serial.Serial(portlist[k], 9600, timeout=STDTIMEOUT, dsrdtr=False)
        break;
    except:
        pass

if type(Serial) == type(None):
    print ("Failed to initialise Serial Port.")
    print ("Tried %s." % portlist)
    print ("Check your port name??")
    exit()


if verboseSetup:
    print ("Device found at %s " % Serial.port)


if not Serial.port == "/dev/ttyAMA0":
    # NOT for Raspberry Pi UART port: it has no DTR line
    if verboseSetup:
        print ("Attempting hard reset of arduino ...")
    hardResetARD()

# Now, we know that the serial port exists. It COULD be another device, not our arduino !
# Try certain baudrates to talk with arduino ...
if verboseSetup:
    print ("Baudrates to test:")
    print (baudlist)

for k in range(len(baudlist)):
    try:
        if verboseSetup:
            print ("Trying baudrate"),
            print (baudlist[k])
        Serial.setBaudrate(baudlist[k])   # Try each baudrate in turn from our list
    except:
        print ("Device at %s can not operate at baudrate %d" % (Serial.port,baudlist[k]))
        print ("Change options in 'serialConfig.py'")
        exit()
    time.sleep(0.1)
    if verboseSetup:
        print ("Try Ping @"),
        print (Serial.baudrate)
    _SerialWrite("=")  # The sync() call used as a "ping"
    ping = _SerialRead()   # Fetch one reply character
    if len(ping)>0:
        if _i8(ping[0]) == ord("="):    # Does this look like correct response?
            break;
    if k==(len(baudlist)-1):   # tried & failed on all options
            print ("Arduino not in contact. Tried baudrates"),
            print (baudlist)
            exit()
if verboseSetup:
    print ("Found Arduino @ baudrate %d " % Serial.baudrate)

if Serial.port == "/dev/ttyAMA0":   # Raspberry Pi GPIO uart?
    # on rPi UART mode we needed to establish serial contact before reset: this reset is a software command.
    if verboseSetup:
        print ("Soft reset of arduino ...")
    softResetARD()

if verboseSetup:
    print ("Successful Setup")
    print ("")

# END OF SETUP

# All below is API for user functions















######################################################################


HIGH = 1
LOW = 0

A0 = 14   # the analog pins
A1 = 15
A2 = 16
A3 = 17
A4 = 18
A5 = 19
A6 = 20
A7 = 21

OUT = 1
IN = 0


# RPI.GPIO constants for compatibility:
PUD_UP = 22
PUD_DOWN = 21
PUD_OFF = 20
BCM = 11
BOARD = 10
VERSION = "0.9.7"
RPI_REVISION = 0

def setmode(mode):
    # Compatibility for rpi code GPIO.setmode(GPIO.BOARD/BCM)
    pass

def cleanup():
    GPIO.softReset()

def setwarnings(mode):
    # Not used. Compatibility for rpi code GPIO.setwarnings(false)
    pass


def setup(dpin, mode, pull_up_down=0):
    # Cast it into arduino numbers
    INPUT_PULLUP = 2
    if pull_up_down == PUD_UP:
        mode = INPUT_PULLUP
    if pull_up_down == PUD_DOWN:
        print ("Virtual-GPIO (arduino) has no pulldown. Continuing ...")
    _SerialWrite("s" + chr(dpin) + chr(mode));
def pinMode(dpin, mode):   # arduino style
    setup(dpin, mode)

def output(dpin, hilo):
    _SerialWrite("w" + chr(dpin) + chr(hilo))
    _SerialRead()  # sync only
def digitalWrite(dpin, hilo):  # arduino style
    output(dpin, hilo)

def input(dpin):
    _SerialWrite("r" + chr(dpin))
    return _serialread1int8(0xff)
def digitalRead(dpin):    # arduino style
    input(dpin)

def digitalPreciseRead(pin):
    # Uses analog comparator on to compare the pin's ANALOG volts against 1.1V chip reference.
    # ONLY for pins d7 and A0-A7
    AVR.bitClear(AVR.ADCSRA, 7)   # disable ADC
    AVR.write8(AVR.ACSR, 0x40);  # set internal ref 1.1 for comparator
    if pin == 7:
        AVR.write8(AVR.ADCSRB, 0)  # set d7 as input
    elif (pin>= A0 and pin <= A7):
        AVR.write8(AVR.ADCSRB, (pin-14) + 0x40)  # set adc mux address 0-7 as input
    else:
        AVR.bitSet(AVR.ADCSRA, 7)   # re-enable ADC
        return 0xf4   # == f4 bad pin
    r = ((~AVR.read8(AVR.ACSR)) >> 5) & 1   # comparator output bit
    AVR.bitSet(AVR.ADCSRA, 7)   # re-enable ADC
    return r


def digitalReadAll():
    return (AVR.read8(AVR.PIND) & 0xf6) +  ((AVR.read8(AVR.PINB)&0x3f)<<8)
    # d2 to d7, and d8 to d13

def pwmWrite(dpin, dcycle):
    _SerialWrite("p" + chr(dpin) + chr(dcycle))   # 8bit write
    # p3 p11 Timer2,  p9 p10 Timer1,   p5 p6 Timer0
    # This is the regular analogWrite of the arduino


def analogRead(apin):  # regular arduino style analog read
    # HOWEVER, use the A0 A1 numbering (ie 14-21, not 0-7)
    if apin<=7:
        apin += 14
    _SerialWrite("a" + chr(apin))
    return _serialread2int16(0xfffa)

def analogReadAll():
    _SerialWrite("A")
    buf2 = _SerialRead(16)
    # pyserial's serial.read() returns STRING or BYTES (of 16 CHARs)
    # but we want LIST of 8 x 16-bit integers as our return format
    L = len(buf2)
    if L<16:        # timeout?
        buf3 = [0] * 8    # empty dummy of the correct length/format
    else:
        buf3 = []
        for k in range(8):
            buf3.append(_i8(buf2[k*2]) + 256*_i8(buf2[1+k*2]))
    return buf3

def pulseOut(dpin, mode, usec):   # pulse to 255 uSec
    _SerialWrite("U")
    _SerialWrite([dpin, mode&1, usec])


def pulseIn(pin, hilo, timeout1, timeout2):   #  pulsein
    # int timeouts: To start 20 - 5000 usec, length 100uSec - 25000uSec   8 bit
    _SerialWrite("I" + chr(pin) + chr(hilo))
    _SerialWrite([timeout1//20,  timeout2//100])
    # 16-bit integer return in uSec
    return _serialread2int16(0xfff2)
    # Note return error codes could be FFE3 (pin conflict), FFFF (not idle),
    #    FFFE (not started on time), FFFA (fail to finish in time)
    # These come from pulse_In function or case 'I' section in VirtGPIO.ino


def analogHiSpeed():
        # This moves ADC clock from divider 128 to divider 16
        # Not very useful for single analog reads, but some speedup for analogReadAll()
        AVR.bitClear(AVR.ADCSRA, AVR.ADPS0);
        AVR.bitClear(AVR.ADCSRA, AVR.ADPS1);
        AVR.bitSet(AVR.ADCSRA, AVR.ADPS2);

def setActivityLed(pin):
  _SerialWrite ("_" + chr(pin))
  # The Activity Pin defaults as d13. It flashes ON while arduino is processing one incoming serial packet.
  # Can be anytime reassigned to be a different pin, or to 0 which means disabled.
  # Other need for pin13 needs ActivityPin to have been reassigned first. (Altho SPI will "kick" it off anyway)


###############################################

class _AVR_:    # class not intended to be instantiated by an outside script
    ADCSRA = 0x7a
    ADPS0 = 0
    ADPS1 = 1
    ADPS2 = 2
    TCNT1 = 0x84   # (0x84 lsB    0x85 msB)
    TCCR1A = 0x80
    TCCR1B = 0x81
    CS10 = 1
    CS11 = 2
    CS12 = 4
    PINB = 0x23    # direct register addresses of digital inputs
    PINC = 0x26
    PIND = 0x29
    PORTB = 0x25
    PORTC = 0x28
    PORTD = 0x2b
    DDRB = 0x24
    DDRC = 0x27
    DDRD = 0x2a
    ACSR = 0x50
    ADCSRA = 0x7a
    ADCSRB = 0x7B

    # add to this list from 328 manual as needed

    def __init__(self):
        pass


    def read8(self, register):
       _SerialWrite("#")
       _SerialWrite([register])
       return _serialread1int8(0)

    def write8(self, register, data8):
        _SerialWrite("*")
        _SerialWrite([register, data8])


    def read16(self, register, errcode=0):
       _SerialWrite("@")
       _SerialWrite([register])
       return _serialread2int16(errcode)

    def write16(self, register, data16):
        _SerialWrite("&")
        _SerialWrite([register, data16&0xff, data16>>8])


    def bitSet(self, register, bit):
        _SerialWrite("[")
        _SerialWrite([register&0xff, bit])

    def bitClear(self, register, bit):
        _SerialWrite("]")
        _SerialWrite([register&0xff, bit]);

AVR = _AVR_()
# We pre-define the AVR object HERE. Outside script can now use this AVR object this way.

###############################################



class Servo:
    # Using any servos disables PWM on pins 9-10  (uses Timer1)

    def __init__(self, pin):   #  pin 3 - 10
        setup(pin, OUT)    # fix V0.9.7
        self.pin = pin
        pass

    def write(self, value):
        _SerialWrite("V" + chr(self.pin))   # 2-10
        _SerialWrite([value])  #  0-180

    def stop(self):
        _SerialWrite("v" + chr(self.pin))


###############################################



class SpiDev:
    # minimal emulation of rPi-style spidev
    # Note arduino pin 10 is conventionally used as the CSN/SS* output pin.  It ought be preferred as first CE.
    # This code supports any number of devices on SPI bus,
    # Some of the comments below imply RF24L01 2.4GHz transceiver is attached to SPI ...
    # ... however the SPI should be generic enough anyway.

    max_speed_hz = 0  # not currently implemented

    def __init__(self):
        self.mode = 0   # default
        return

    def mode(self, mode):
        self.mode = mode&3

    def max_speed_hz(self, speed):
        pass

    def open(self, bus, device):
        # bus is for RPI syntax compatibility only
        # Also, where RPI uses 0 or 1 for device (CE0, CE1), virtGPIO uses actual chip enable pin
        self.cePin = device
        _SerialWrite("S" + chr(self.cePin));  # take SPI control of pins 11-13, plus CE-pin


    # RPI compatible:
    #     import spidev                spidev module.   Contains SpiDev class.
    #                                  (On virtGPIO, (virt)GPIO module contains SpiDev class)
    #     mySPI = spidev.SpiDev()      Create SpiDev object
    #     mySPI.open(bus, device)      bus 0 (Model B) or bus 0 / 1 (Model B+)   device = 0 or 1 (CE0 CE1)
    #     mySPI.mode = 2               SPI mode 0 to 3
    #     mySPI.xfer2([listofTXint8])  Returns RX list of int8



    def xfer2(self, buf):
        #  buf arrives as a list of 8-bit integers,
        #  max len 127, but this is unrealistic as the serial buffer is only 127. Suggest use <80
        #  buf includes first byte = cmd byte, plus the payload  - RF24
        #  At the arduino, the CE* select is automatically asserted (low) around this block.
        L = len(buf)
        # set it as STRING of CHARS for serial.write:
        #print "X" + chr(self.cePin) + chr(self.mode) + chr(L) + ''.join(chr(e) for e in buf)
        _SerialWrite("X" + chr(self.cePin) + chr(self.mode) + chr(L))
        _SerialWrite(buf)
        buf2 = _SerialRead(L)
        # pyserial's serial.read() returns STRING or BYTES (of CHARs)
        # but we want LIST of 8-bit integers as our return format
        L2 = len(buf2)
        if L2<L:        # timeout?
            buf3 = [0] * L    # empty dummy of the correct length/format
            buf3[0] = 0xfe    # our fail flag: optionally caller can watch for this.
        else:
            buf3 = []
            for k in range(L):
                buf3.append(_i8(buf2[k]))
        return buf3
        # return = same length as input, on RF24, first byte of return is STATUS


    def write(self, buf):
        return self.writebytes(buf)

    def writebytes(self, buf):   # one-way spi write,
        #  handles large blocks of data, breaks into chunks of 60
        #  At the arduino, the CE* select is automatically asserted (low) around this WHOLE (multi-)block.
        L = len(buf)

        while L > 60:
            buf1 = buf[0:60]  # save leading 60
            buf = buf[60:]    # dump leading 60
            L -= 60           # and counter drops by 60
            # process precisely 60 with TO_BE_CONTIN flag
            _SerialWrite("x" + chr(self.cePin) + chr(0x10 + self.mode) + chr(60))
            _SerialWrite(buf1)
            _SerialRead()  # wait on some reply  ( for syncing)

        # Now we have 1 to 60 in last block
        _SerialWrite("x" + chr(self.cePin) + chr(self.mode) + chr(L))
        _SerialWrite(buf)
        _SerialRead()  # wait on a reply
        return

    def fill(self, count16, data16):
        # Repetitive write of 1 or 2 bytes. NOT a RPI function!
        # Useful for TFT clear screen operations on virt-gpio (for speed)
        _SerialWrite("g" + chr(self.cePin) + chr(self.mode))
        _SerialWrite([count16&0xff, count16>>8,  data16&0xff, data16>>8])
        _SerialRead()  # just for sync-ing

    def close(self):
        print ("SPI CLOSE not supported")

###############################################

class SerialTx:
    # up to five TTL (5V) "COM ports", transmit only, bit-banged (no interrupts or timers)
    # unbuffered, 2400 baud, blocking (exc port 0) until sent.
    # All ports are at same baudrate, compiled at arduino.
    # (Can recompile to 75 300 2400 9600 19200 38400 57600.)
    # PORT 0 IS DIFFERENT: output at arduino is buffered and transmitted by loop() when idle.
    # Ports 1 to 4 are direct transmit.
    # Port 0 was used for internal sketch diagnostic. Using it here will over-ride diag use.

    # To send binary data, submit it as a character string.

    def __init__(self, port, pin):  # port 0-4, pin any digital-out capable pin
        self.port = port
        _SerialWrite([0xc0, port, pin])

    def Print(self, x):   # single parameter
        if not (type(x) == type ("123")):
                x = str(x)   # Whatever format, coerce it into string
        _SerialWrite([0xc1, self.port, len(x)])
        _SerialWrite(x)
        return _serialread1int8(0)

    def PrintLN(self, x):
        x = str(x) + "\n"
        return self.Print(x)

    def Write(self, x):
        self.Print(chr(x))


###################################################

class SerialRx:
    # pin 8 only
    def __init__(self, baud):
        _SerialWrite([0xd0, 3])

    def available(self):
        _SerialWrite([0xd1])
        # returns a count
        return _serialread1int8(0)

    def read(self, count):
        _SerialWrite([0xd2, count])
        buf2 = _SerialRead(count)
        # pyserial's serial.read() returns STRING or BYTES (of CHARs)
        # but we want LIST of 8-bit integers as our return format
        L2 = len(buf2)
        if L2<count:        # timeout?
            buf3 = [0] * count    # empty dummy of the correct length/format
        else:
            buf3 = []
            for k in range(count):
                buf3.append(_i8(buf2[k]))
        return buf3

###############################################

class PWM:
    pin = 0

    def __init__(self, pin, freq):
        self.pin = pin

    def start(self, dc):
        pwmWrite(self.pin, dc)

    def changeFrequency(self, freq):
        pass

    def changeDutyCycle(self, dc):
        pwmWrite(self.pin, dc)

    def stop(self):
        pwmWrite(self.pin, 0)


###############################################

class I2C:

    def __init__(self, enablePullups = True):
        _SerialWrite("!" + chr(enablePullups))

    # 3 primary calls:

    def write(self, port, txbuf):
        # txbuf = list of integers
        if len(txbuf) > 32:
            print ("I2C limit at arduino is 32 chars !!")
        L = len(txbuf)
        _SerialWrite("W" + chr(L) + chr(port))
        _SerialWrite(txbuf);
        _SerialRead()   # just for syncing   v0.9.5


    def read(self, port, count):
        # returns list, with result code then []*count
        _SerialWrite("c")
        _SerialWrite([count, port])
        buf2 = _SerialRead(count)
        count2 = len(buf2)
        buf3 = [0] * (count+1)    # empty dummy of the correct length/format
        if count2<count:        # timeout?
            buf3[0] = 0xf3    # our fail flag: optionally caller can watch for this.
        else:
            for k in range(count):
                buf3[k+1] = _i8(buf2[k])
        return buf3

    def writeRead(self, port, txchr, rxcount):   # accepts ONE byte of tx before rx
        self.write(port, [txchr])
        return self.read(port, rxcount)


    def detect(self):
        # Diagnostic function   equiv to i2cdetect utility in linux
        _SerialWrite("?")
        time.sleep(0.05)
        while(Serial.inWaiting()):   # anything to report
            print ("I2C detected at: \\0x%02x " % _i8(_SerialRead()))



    # FOLLOWING ARE SMBus STYLE COMMANDS (derived):

    def read_byte(self, addr):
        r=self.read(addr, 1)
        return r[1]

    def read_byte_data(self, addr, cmd):
        r = self.writeRead(addr, cmd, 1)
        return r[1]

    def read_word_data(self, addr, cmd):
        pass  # nyi

    def write_byte(self, addr, cmd):
        self.write(addr, [cmd])

    def write_byte_data(self, addr, cmd, data):
        self.write( addr, [cmd, data])

    def write_word_data(self, addr, cmd, data):
        pass  # nyi

    def write_block_data(self, addr, cmd, data):
        pass   # nyi

    def write_i2c_block_data(self, addr, cmd, data):   # March 2015
        self.write( addr, [cmd]+data)



###############################################

class Stepper:
    WIRE2 = 2
    WIRE4 = 4
    def __init__(self, id, wires, pin1, stepsPerRev):   # wires 2 or 4.
        _SerialWrite([0xb1, id & 1, wires & 7, pin1, stepsPerRev&0xff, stepsPerRev >>8])
        self.id = id&1
        self.SPR = stepsPerRev

    def setSpeedRPM(self, speedRPM):   #  integer speed in RPM (positive number)
        _SerialWrite([0xb2, self.id, speedRPM&0xff, speedRPM>>8])
        self.speedRPM = abs(speedRPM)

    def step(self, steps, wait=True):   # steps negative for reverse rotation +-32000
        self.steps = abs(steps)
        steps = cInt16(steps)
        _SerialWrite([0xb3, self.id, steps&0xff, steps>>8] )
        if wait:
            self.waitToFinish()

    def stepsLeft(self):
        _SerialWrite([0xb4, self.id] )
        return _serialread2int16(0)

    def waitToFinish(self):
        wtime = ((1.3 * self.steps) // self.speedRPM) * 60 // self.SPR
        t1 = time.time()
        r=0
        while (time.time() - t1) < wtime:
            if self.stepsLeft() == 0:
                r=1
                break
        return r    # optional return code 0=timeout   1=normal finish



###############################################

class Intcounter:   # two counters using INT0 and INT1
    # These counters operate only on pins d2/d3. (This is a 328 chip hardware constraint.)
    # if QUAD encoder selected, d2 pairs with d4,  d3 pairs with d5

    RISING = 0x03   # AVR code
    FALLING = 0x02  # AVR code
    CHANGE =  0x01  # AVR code
    QUAD = 0x05     # change + 0x04

    def __init__(self, pin, mode):    # pin 2 or 3, mode as above
        if pin==2 or pin == 3:
            _SerialWrite("2" + chr(pin) + chr(mode))


    def read(self, andZero=False):   # optional counter clear, read as time-matched pair.
      _SerialWrite("," + chr(andZero &1))
      c0 = _serialread2int16(0xffff)
      c1 = _serialread2int16(0xffff)
      return [c0, c1]



###############################################

class HWcounter:    # true (one-only) 16bit MCU hardware counter: no interrupts.
    # This counter operates only on pin d5. (This is a 328 chip hardware constraint.)
    # This function kills any other timer1 operation (or PWM on pins 9, 10)


    def __init__(self):
      AVR.write8(AVR.TCCR1A, 0)  # reset timer/counter control register A
      AVR.write8(AVR.TCCR1B, AVR.CS10+AVR.CS11+AVR.CS12) # Counter on external pin, rising edge
      self.zero()
      # once initialised, the counter always is active

    def zero(self):   # CLEAR the counter to 0x0000
      AVR.write16(AVR.TCNT1, 0)

    def read(self):
      return AVR.read16(AVR.TCNT1, 0xffff)



###############################################


class InfraRedRx:
    # Uses Timer2, so PWM on p3, p11 disabled

    def __init__(self, pin):
      self.devicenum = 0   # ID of hand remote
      _SerialWrite("F" + chr(pin & 0x0f))

    def read(self):     # fetch IR code from remote
        _SerialWrite("f");
        ir = _serialread4int32(0xffffffff)
        self.devicenum = ir & 0xFFFF
        return (ir >>16)&0xff

    def device(self):    # read remote device number of latest read
        return self.devicenum
        # only valid immediately after a read


###############################################

class PWMplus:
    # only pins 9 &/or 10.  Uses Timer1

    def __init__(self):
        _SerialWrite ([0x81])
        self.pinBusy = [0,0]

    def setPeriod(self, usec):   # usec from 1 to 1,000,000
        _SerialWrite ([0x82, usec & 0x0000ff, (usec & 0x0FF00)>>8, usec//65536] )

    def initPin(self, pin, duty):   # pin = 9 or 10 only.  duty 0 to 1023
        if pin < 9 or pin > 10:
            return
        if self.pinBusy[pin-9]:
            self.changeDuty(pin, duty)
            return
        self.pinBusy[pin-9] = 1
        _SerialWrite ([0x83, pin, duty & 0x00ff, duty >>8])

    def changeDuty(self,pin,duty):
        _SerialWrite ([0x84, pin, duty & 0x00ff, duty >>8])


    def releasePin(self,pin):
        if pin < 9 or pin > 10:
            return
        _SerialWrite ([0x85, pin] )
        self.pinBusy[pin-9] = 0

    def stop(self):
        _SerialWrite ([0x86, 0])

    def restart(self):
        _SerialWrite ([0x86, 1])

    def tone(self, pin, freq):
        self.setPeriod(1000000 // freq)
        self.initPin(pin, 511)

    def noTone(self, pin):
        self.releasePin(pin)

###############################################


# DIAGNOSTIC/DEBUG STUFF:

class Trace:   #developer use.
    def __init__(self):
        pass
    def Start(self):
            _SerialWrite("^")

    def Stop(self):
       _SerialWrite("<")

    def Print(self):
        _SerialWrite(">")
        # Will not print if Serial0 (ie COM port 0) is not initialised

def mopup():
    # Testing only
    #time.sleep(.003)
    #print "Mop up: " ,
    while(Serial.inWaiting()):   # anything to mopup???
        r=_SerialRead()
        print ("   {%x}" % ( _i8(r))),


###############################################


def sync(timeout = 0.25, printping = False):   # 0.5 - 1.0 mSec when no catchup needed
    # Use in user code after several non-reporting commands, so that sender can not
    # get too many serial characters ahead of slave unit.
    # Only likely calls that MIGHT need this are multiple AVR.write, Servo.write, SerialTX.write
    # Note GPIO.output and I2C.write should be immune, with inbuilt sync function.

    # Also useable as a visible "ping"
    _SerialWrite("=")
    Serial.timeout = timeout
    r=_serialread1int8(0xf6)
    Serial.timeout = STDTIMEOUT
    if printping:
        # Diagnostic use
        print ("Ping response %s %x" % (chr(r),r) )   # should report "=" chr
    return r

def readFreePins():
  # Diagnostic tool
  _SerialWrite ("q")
  print ("")
  print (" GP pins    AAAAAAAA111100000000TR")
  print (" 1=free     76543210321098765432rd")
  print (bin(0x80300000 | _serialread4int32(0)))
  # top bit: just to align the display. Bits for A6 A7 added for display. They remain always avbl.


def VccRead():
  _SerialWrite("+")
  return _serialread2int16(0)/1000.0


def printCompileDate():
  # Diagnostic tool
  _SerialWrite('t')
  time.sleep(.05)
  print ("")
  print ("Compile/Load Date:  " ),
  datstr=""
  while(Serial.inWaiting()):
    datstr += chr(_i8(_SerialRead()[0]))
  print (datstr)

def getVersion():
    _SerialWrite('T')
    return _serialread1int8(0)


def clearResetFlag():       # at slave
    _SerialWrite("i")

def resetFlagIsOn():        # optional test whether slave has since suffered a reset
    return (readFlags() & 1)

def readFlags():
    # Flag bits (confirm at VirtGPIO.ino):
    # enum {F_reset=0, F_spi, F_svo, F_ir, F_i2c, F_intctr, F_pwm,
    #        F_stepr, F_actled, F_nospi, F_TxCom, F_RxCom, F_badchar=15};
    _SerialWrite("n");
    return _serialread2int16(0xff)

def restart_program():
    #Restarts the current program.
    python = sys.executable
    os.execl(python, python, * sys.argv)

def checkPinsFree(pinslist):
    # returns false if ANY of the pins is reserved
    _SerialWrite ("q")
    a = _serialread4int32(0)
    for k in range(len(pinslist)):
        if not (a & (1<<pinslist[k])):
            return False
    return True

################################################################################

# INTERNAL SUBROUTINES

def _serialread4int32(errorflag32):
      # read 4 byte and format as a python integer
      # if read fail, return known error flag
      a = _SerialRead(4)
      if len(a) >3 :
          return _i8(a[0]) + (_i8(a[1])<<8) + (_i8(a[2]) << 16) + (_i8(a[3]) << 24)
      else:
          return errorflag32

def _serialread2int16(errorflag16):
      # read 2 byte and format as a python integer
      # if read fail, return known error flag
      a = _SerialRead(2)
      if len(a) >1 :
          return _i8(a[0]) + (_i8(a[1])<<8)
      else:
          return errorflag16

def _serialread1int8(errorflag8):
      # read 1 bytes and format as python integer
      a = _SerialRead()
      if len(a) :
          return _i8(a[0])
      else:
          return (errorflag8 & 0xff)


from ctypes import *
def cByte(i):
        return c_ubyte(i).value
def cInt16(i):
        return c_ushort(i).value
def cInt32(i):
        return c_uint(i).value
def cInt32FromFloat(f):
        return cInt32(int(f))
def str1FromByte(i):
        return chr(cByte(i))


# Still flagged for possible change:
# 1. HWcounter enhance to more than 16 bits - eg see "Arduino Internals" ebook
# 2. arduino end - more robust serial timeouts
# 3. Clean python docstrings


# Changes made V0.9 -> v0.9.5  :
# Added serialConfig.py for port settings
# Sonar removed from virtGPIO core, out to simple example script
# SPI devices get individual control of mode
# i2c - option to disable arduino's internal pullups
# SPI.xfer2() out to 80 chars, and added unlimited SPI.writebytes()
# Improved RPI syntax compatibility
# Now Python 2.7 / Python 3.3 compatible

"""
 * Copyright (c) 2014 Brian Lavery <vgpio@blavery.com>   http://virtgpio.blavery.com
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
"""


