#!/usr/bin/env python
# Copyright (c) 2017 Adafruit Industries
# Author: Tony DiCola & James DeVito
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import time
import signal

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

import os
import sys
import psutil

import socket

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess

class GracefulKiller:
	kill_now = False
	def __init__(self):
		signal.signal(signal.SIGINT, self.exit_gracefully)
		signal.signal(signal.SIGTERM, self.exit_gracefully)
		signal.signal(signal.SIGHUP, self.exit_gracefully)

	def exit_gracefully(self,signum, frame):
		self.kill_now = True

pidfile = "/var/run/status.pid"

# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used
# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

# Beaglebone Black pin configuration:
# RST = 'P9_12'
# Note the following are only used with SPI:
# DC = 'P9_15'
# SPI_PORT = 1
# SPI_DEVICE = 0

# 128x32 display with hardware I2C:
# disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

# Note you can change the I2C address by passing an i2c_address parameter like:
# disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, i2c_address=0x3C)

# Alternatively you can specify an explicit I2C bus number, for example
# with the 128x32 display you would use:
# disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, i2c_bus=2)

# 128x32 display with hardware SPI:
# disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

# 128x64 display with hardware SPI:
# disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

# Alternatively you can specify a software SPI implementation by providing
# digital GPIO pin numbers for all the required display pins.  For example
# on a Raspberry Pi with the 128x32 display you might use:
# disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, dc=DC, sclk=18, din=25, cs=22)

killer=GracefulKiller()

pid = str(os.getpid())

def bytes2human(n):
    """
    >>> bytes2human(10000)
    '9.8 K'
    >>> bytes2human(100001221)
    '95.4 M'
    """
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.2f%s' % (value, s)
    return '%.2fB' % (n)

def readConfig():
    config=configparser.ConfigParser()
    config.sections()
    config.read('/etc/status.cfg')

def main():
    if os.path.isfile(pidfile):
        print "%s already exists, exiting" % pidfile
        sys.exit()
    file(pidfile, 'w').write(pid)
    hostname=os.uname()[1]
    try:

            # Initialize library.
            disp.begin()

            # Clear display.
            disp.clear()
            disp.display()

            # Create blank image for drawing.
            # Make sure to create image with mode '1' for 1-bit color.
            width = disp.width
            height = disp.height
            image = Image.new('1', (width, height))

            # Get drawing object to draw on image.
            draw = ImageDraw.Draw(image)

            # Draw a black filled box to clear the image.
            draw.rectangle((0,0,width,height), outline=0, fill=0)

            # Load default font.
            font = ImageFont.load_default()

            # Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
            # Some other nice fonts to try: http://www.dafont.com/bitmap.php
            # font = ImageFont.truetype('Minecraftia.ttf', 8)
            top=0
            lheight=8

            while True:
                    if not killer.kill_now:
                        # Draw a black filled box to clear the image.
                        draw.rectangle((0,0,width,height), outline=0, fill=0)

                        # Shell scripts for system monitoring from here : https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
                        stats=psutil.net_if_stats()
                        for nic, addrs in psutil.net_if_addrs().items():
                            if nic!="lo":
                                for addr in addrs:
                                    if addr.family == socket.AF_INET:
                                        draw.rectangle((0,0,width,height), outline=0,fill=0)
                                        draw.text((1,lheight*0), "### "+hostname+" ###", font=font, fill=255)
                                        nicname=str(nic)+"     "
                                        draw.text((1, lheight*1), nicname[:5]+":"+str(addr.address), font=font, fill=255)

                                        CPU=psutil.cpu_percent(interval=0)
                                        cputimes=psutil.cpu_times_percent(interval=0)

                                        cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
                                        MemUsage = subprocess.check_output(cmd, shell = True )
                                        cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
                                        Disk = subprocess.check_output(cmd, shell = True )

                                        # Write two lines of text.

                                        draw.text((1, lheight*2),     "CPU: " + str(CPU)+"%", font=font, fill=255)
                                        draw.text((1, lheight*3), "us: "+str(int(cputimes.user))+" ni: "+str(int(cputimes.nice))+" sy: "+str(int(cputimes.system)), font=font, fill=255)
                                        draw.text((1, lheight*4),    str(MemUsage),  font=font, fill=255)
                                        draw.text((1, lheight*5),    str(Disk),  font=font, fill=255)

                                        # Display image.
                                        disp.image(image)
                                        disp.display()
                                        time.sleep(5)
                    else:
                        draw.rectangle((0,0,width,height), outline=0,fill=0)
                        draw.text((1,top), "shutting down")
                        draw.text((1,top+8),"daemon")
                        disp.image(image)
                        disp.display()

                        os.unlink(pidfile)
                        exit
    finally:
            os.unlink(pidfile)

if __name__ == '__main__':
    main()
