# Evohome Monitor
# Copyright (c) 2023 JaSe
# Python 3.x
# Requires pyserial module which can be installed using
# Program to log Honeywell Evohome devices activity 
# works with RF -> serial converter for example https://github.com/ghoti57/evofw3
# inspired by https://github.com/Evsdd/Evohome_Controller
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#from __future__ import print_function
import serial as serial                    # import the modules
from datetime import datetime
import signal
import sys

# Ctrl-C signal handler
def handler(signum, frame):
    res = input("Ctrl-c was pressed. Do you really want to exit? y/n ")
    if res == 'y':  # close gracefully and exit
        ComPort.close()               # Close the COM Port (
        output_log.close()  # close file
        exit(1)

signal.signal(signal.SIGINT, handler)   #assignment of Ctrl-C handler

output_log = open("monitor.log", "a") # zápis do logu append  ("w" for rewrite instead of append)

# Detect the operating system and set the appropriate serial port name
if sys.platform.startswith('linux'):
    PortString = "/dev/ttyUSB0"  # Edit the value as you need
elif sys.platform.startswith('win'):
    PortString = "COM4"          # Edit the value as you need
else:
    # For other operating systems
    PortString = ""  # You can set a default value here

ComPort = serial.Serial("COM4")   # on linuxes something like:  /dev/ttyUSB0
ComPort.baudrate = 115200          # set Baud rate
ComPort.bytesize = 8              # Number of data bits = 8
ComPort.parity   = 'N'            # No parity
ComPort.stopbits = 1              # Number of Stop bits = 1
ComPort.timeout = 1               # Read timeout = 1sec

send_data = bytearray('\r\n','ASCII') # wakeup serial to air interface
No = ComPort.write(send_data)

# Define your known device names in the table below
# ['xx:yyyyyy', 'name of device']
# if you don't know device addresses, run the program with only
# first two rows filled, wait for any frame and try to recognize
# which device is which. For example if you press the button on TRV
# it will typicaly send some frames.

device_names = [
    ['--:------','--:------'],  # --:------
    ['63:262142','Bcast'],      # Broadcast 63:262142
    ['01:087381','Contr'],      # example controler
    ['04:092553','Obyvak'],     # example TRV in living room
    ['04:092555','Kuchyne'],    # example TRV in kitchen
    ['04:092539','Loznice'],    # example TRV in bedroom
    ['04:092791','Pokojicek'],  # example TRV in children's room
]
# Command names
# If the program will find any other command in frames, it will call it ????
# and you can add the new line with the found unknown command and try
# to Google, what it is for and name it

commands = [
    ['1FC9','BIND'],  # Bind command
    ['1F09','SYNC'],  # Sync command
    ['0004','NAME'],  # ZoneName command
    ['2309','SETP'],  # ZoneSetpoint command
    ['30C9','TEMP'],  # ZoneTemperature command
    ['0100','ZUNK'],  # ZoneUnknown command
    ['313F','DATE'],  # DateTime command
    ['12B0','WNDO'],  # WindowSensor command
    ['3150','HDMD'],  # HeatDemand command
]

# Function to decode device addresses to names
def dev2name(dev):
    for row in device_names:
        if dev == row[0]:
            return row[1]
    else:
        return 'Unkn'   # if device address was not found

# Function to decode device addresses to names
def code2cmd(code):
    for row in commands:
        if code == row[0]:
            return row[1]
    else:
        return '????'   # if command was not found
##### End of setup

print("", file=output_log)  # log sepparator
print("=========================== {0} ===========================".
      format(datetime.now().strftime("%y-%m-%d %H:%M:%S")), file=output_log) # date/time of app start

##### Main message processing loop (infinite)
while True:

    b_data = ComPort.readline()        # Wait and read data
    # Only proceed if line is not empty and is not comment
    if b_data and (b_data[1] != ord('#')):
        data = b_data[:-2].decode('ascii')  # cut the \r\n end and convert to string
        msg_type = data[4:6]   # Extract message type ( I, W, RQ, RP )
        dev1 = data[11:20]     # Extract deviceID 1
        dev2 = data[21:30]     # Extract deviceID 2
        dev3 = data[31:40]     # Extract deviceID 3
        cmnd = data[41:45]     # Extract command

        desc = "{0} -> {1}/{2}: {3}|{4}".format(dev2name(dev1),
                                                dev2name(dev2),
                                                dev2name(dev3),
                                                msg_type,
                                                code2cmd(cmnd))
        print(desc)     #print the description of the frame to stout
        print("{0}: {1}".format(datetime.now().strftime("%y-%m-%d %H:%M:%S"),data),
              "\t# {0}".format(desc), file=output_log, flush = True)
