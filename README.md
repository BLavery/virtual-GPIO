virtual-GPIO
============
**2017 note:
This project works. I think it works well.
But there has been minimal interest shown since its posting.
It is now no longer subject to any maintenance
or revision. Sometimes the marketplace just
doesn't want/need some offerings. It's called life.**

Arduino as a "GPIO" device attached to PC or Raspberry Pi, which run python control script.

Give your Raspberry Pi precise counters, easy IR receiver, analog inputs.
Give your PC a virtual GPIO on a USB port. Add SPI, I2C, analog & digital pins, servo control, etc.

Supported:
  - GPIO digital in/out  D2-D13  A0-A5
  - PWM out  8bit - 6 pins
  - high performance PWM option, or as pulse generator 1Hz to 1MHz
  - analog Read  10bit  8 pins
  - SPI master, multiple choice for CE pin
  - pulseout 1-250 uSec [arduino coded]
  - pulsein   0-25 mSec [arduino coded, not native arduino version]
  - servo    pins3-10
  - ir remote rx
  - SMBus / I2C master
  - 2 software (arduino-polled) counters / quadEncoders
  - Hardware pin counter x 1 on d5
  - Twin INT0/INT1 counters on d2/d3
  - AVR raw register access
  - Auto-find for PC end serial port

Generally about 800 instructions/sec achievable on PC, depending on call type, and 200/sec on rPi.

"virtGPIO.py" is the PC end of "virtual-gpio", ie using arduino as a GPIO device on PC (python on linux).
This module uses USB serial to power and control the arduino.

The ARDUINO end is the sketch "VirtGPIO.ino".
Shields, attached modules etc are NOT generally coded at the arduino end. Such support is to be coded at the PC end.
(Exceptions:  infrared remote codes reader, and background stepper)
Atmega328 is assumed.

Main files:
  - VirtGPIO.ino (and its acompanying library files) essential - sketch for Arduino end.
  - virtGPIO.py essential library at Raspberry Pi or PC.
  - collection of example python files demonstrating use of virtual GPIO.

Documentation on GPIO calls:  See http://virtgpio.blavery.com

  - Changes made V0.9 -> v0.9.5  :
  - Added serialConfig.py for port settings
  - Sonar removed from virtGPIO core, out to simple example script
  - SPI devices get individual control of mode
  - i2c - option to disable arduino's internal pullups
  - SPI.xfer2() out to 80 chars, and added unlimited SPI.writebytes()
  - Improved RPI syntax compatibility
  - Now Python 2.7 / Python 3.3 compatible

DISCLAIMER on the associated libraries (mcp23017, lcd16x2, nokia5110, nrf24, tft144) - these are a work in progress, and recently have been exercised more against virtual-GPIO than Raspberry Pi. There are sure to be various updates/corrections to those. The virtual-GPIO core library itself (v0.9.5) should be fairly intact.  BL 5 Nov 2014.

V0.9.5
November 2014
