# Evohome Controller Moje vývojová verze
# Copyright (c) 2023 JaSe
# Python 3.x
# Requires pyserial module which can be installed using 'python -m pip3 install pyserial'
# Prototype program to provide controller functionality for Evohome HR92 devices
# based on https://github.com/Evsdd/Evohome_Controller
#
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


from __future__ import print_function
import serial as serial                    # import the modules
import time
import datetime

output_log = open("Evohome_Controller.log", "w")

ComPort = serial.Serial("COM4")   # open port /dev/ttyUSB0
ComPort.baudrate = 115200          # set Baud rate
ComPort.bytesize = 8              # Number of data bits = 8
ComPort.parity   = 'N'            # No parity
ComPort.stopbits = 1              # Number of Stop bits = 1
ComPort.timeout = 1               # Read timeout = 1sec

send_data = bytearray('\r\n','ASCII')
No = ComPort.write(send_data)
# Set-up Controller and Zone information
ControllerID = 0x55555            # Set this to any value as long as ControllerTYPE=1

# Zone definition: deviceID placeholder (TYPE:ADRR),
#                  name, placeholder for name (Hex string),
#                  setpoint, placeholder for setpoint (Hex string),
#                  placeholder for temp (Hex string)
Zone_INFO = [
    ['04:092553','Obyvak','','24.5','',''],  # 04:092553
    ['','Kuchyne','','22.5','',''],  # 04:092555
    ['','Loznice','','18.0','',''],  # 04:092539
    ['','Pokojicek','','20.5','','']  # 04:092791
]

Zone_num = 4                      # Number of zones

Device_count = 1                  # Count of devices successfully bound

Sync_dur = 60                    # Time interval between periodic SYNC messages (sec)
SyncTXT = '{0:04X}'.format(Sync_dur * 10)
Sync_time = time.time()

Com_BIND = 0x1FC9                 # Evohome Command BIND
Com_SYNC = 0x1F09                 # Evohome Command SYNC
Com_NAME = 0x0004                 # Evohome Command ZONE_NAME
Com_SETP = 0x2309                 # Evohome Command ZONE_SETPOINT
Com_TEMP = 0x30C9                 # Evohome Command ZONE_TEMP
Com_UNK = 0x0100                  # Evohome Command ZONE_UNK (unknown)
Com_DATE = 0x313F                 # Evohome Command DATE_TIME


# Create controller values required for message structure
ControllerTYPE = (ControllerID & 0xFC0000) >> 18;
ControllerADDR = ControllerID & 0x03FFFF;
#ControllerTXT = bytearray(b'%02d:%06d' %(ControllerTYPE, ControllerADDR))
ControllerTXT = bytes("{0:02}:{1:06}".format(ControllerTYPE, ControllerADDR),"utf-8") #py3

# Populate zone name Hex strings
for i in range(0,Zone_num):
    Hex_name = ''.join('{0:02X}'.format(ord(c)) for c in Zone_INFO[i][1])
    Hex_pad = ''.join('00' for j in range(len(Zone_INFO[i][1]),20))
    Zone_INFO[i][2] = Hex_name + Hex_pad

# Populate setpoint Hex strings
for i in range(0,Zone_num):
    Hex_name = '{0:04X}'.format(int(float(Zone_INFO[i][3]) * 100))
    Zone_INFO[i][4] = Hex_name
    # print('Zone %d:(%s:%s):(0x%s):(%s:0x%s)' % (i+1,Zone_INFO[i][0],Zone_INFO[i][1],Zone_INFO[i][2],Zone_INFO[i][3],Zone_INFO[i][4]))
    print('Zone {0}:({1}:{2}):(0x{3}):({4}:0x{5})'.format(i+1,Zone_INFO[i][0],Zone_INFO[i][1],Zone_INFO[i][2],Zone_INFO[i][3],Zone_INFO[i][4])) #py3
# print('ControllerID=0x%06X (%s)' % (ControllerID, ControllerTXT))
print('ControllerID=0x{0:06X} ({1})'.format(ControllerID, ControllerTXT))  #py3
##### End of setup

##### Main message processing loop (infinite)
while True:
    if ((time.time() - Sync_time) <  Sync_dur):

        data = ComPort.readline()        # Wait and read data

        if data:                         # Only proceed if line read before timeout

            msg_type = data[4:6]             # Extract message type
            dev1 = data[11:20]               # Extract deviceID 1
            dev2 = data[21:30]               # Extract deviceID 2
            dev3 = data[31:40]               # Extract deviceID 3
            cmnd = data[41:45]               # Extract command

            print(data)                      # print the received data
            print(data, file=output_log)

            ##### Check if device has already been defined
            i = 0
            while (i < Device_count and Zone_INFO[i][0] != dev1):
                i += 1

            ##### Received BIND message
            # if ((msg_type == ' I') and (dev1 != ControllerTXT) and (cmnd == '%04X' % Com_BIND)):
            if ((msg_type == b' I') and (dev1 != ControllerTXT) and (cmnd == b'1FC9')):

                send_data = bytearray(b'I --- %s --:------ %s %04X 018 %02d2309%06X%02d30C9%06X%02d1FC9%06X\r\n' % (ControllerTXT, ControllerTXT, Com_BIND, i, ControllerID, i, ControllerID, i,ControllerID))
                print('Send:(%s)' % send_data)
                No = ComPort.write(send_data)
                if (Zone_INFO[i][0] != dev1):  # New Device
                    Zone_INFO[i][0] = dev1
                    # TO DO: wait and check for confirmation of successful binding - W BIND message from device
                    print('Binding complete for Zone %d:(%s):(%s)' % (Device_count+1,Zone_INFO[Device_count][0],Zone_INFO[Device_count][1]))
                    Device_count += 1
                for j in range(0,Device_count):
                    print('Zone_INFO:%d:(%s):(%s):(%s)' % (j+1,Zone_INFO[j][0],Zone_INFO[j][1],Zone_INFO[j][4]))
            elif (Device_count > 0 and i < Device_count and Zone_INFO[i][0] == dev1):          # Only process messages further if message is from a device defined in Zone_INFO

                if ((msg_type == ' W') and (cmnd == '%04X' % Com_BIND)): ##### Received BIND confirmation, respond with ZONE_NAME, SYNC and ZONE_SETPOINT
                    send_data = bytearray(b'I --- %s --:------ %s %04X 022 %02d00%s\r\n' % (ControllerTXT, ControllerTXT, Com_NAME, i, Zone_INFO[i][2]))
                    print('Send:(%s)' % send_data)
                    No = ComPort.write(send_data)
                    send_data = bytearray(b'W --- %s --:------ %s %04X 003 FF0BB8\r\n' % (ControllerTXT, ControllerTXT, Com_SYNC)) # 5min SYNC 0x0BB8 = 3000 (300.0sec)
                    print('Send:(%s)' % send_data)
                    No = ComPort.write(send_data)
                    send_data = bytearray(b'I --- %s --:------ %s %04X 003 %02d%s\r\n' % (ControllerTXT, ControllerTXT, Com_SETP, i, Zone_INFO[i][4]))
                    print('Send:(%s)' % send_data)
                    No = ComPort.write(send_data)
                elif ((msg_type == 'RQ') and (cmnd == '%04X' % Com_SYNC)): ##### Received SYNC request, respond with SYNC
                    SendTXT = '{0:04X}'.format(int((Sync_dur - (time.time() - Sync_time)) * 10))        # Calculate remaining time until next SYNC
                    send_data = bytearray(b'RP --- %s %s --:------ %04X 003 00%s\r\n' % (ControllerTXT, dev1, Com_SYNC, SendTXT))
                    print('Send:(%s)' % send_data)
                    No = ComPort.write(send_data)
                elif ((msg_type == 'RQ') and (cmnd == '%04X' % Com_NAME)): ##### Received NAME request
                    send_data = bytearray(b'RP --- %s %s --:------ %04X 022 %02d00%s\r\n' % (ControllerTXT, dev1, Com_NAME, i, Zone_INFO[i][2]))
                    print('Send:(%s)' % send_data)
                    No = ComPort.write(send_data)
                elif ((msg_type == ' I') and (cmnd == '%04X' % Com_TEMP)): ##### Received TEMP message, send echo response from controller
                    Zone_INFO[i][5] = data[52:56]  # store TEMP in Zone_INFO
                    send_data = bytearray(b'I --- %s --:------ %s %04X 003 %02d%s\r\n' % (ControllerTXT, ControllerTXT, Com_TEMP, i, Zone_INFO[i][5]))
                    print('Send:(%s)' % send_data)
                    No = ComPort.write(send_data)
                elif ((msg_type == ' I') and (cmnd == '%04X' % Com_SETP)): ##### Received SETP message, send echo response from controller
                    send_data = bytearray(b'I --- %s --:------ %s %04X 003 %02d%s\r\n' % (ControllerTXT, ControllerTXT, Com_SETP, i, Zone_INFO[i][4]))
                    print('Send:(%s)' % send_data)
                    No = ComPort.write(send_data)
                elif ((msg_type == 'RQ') and (cmnd == '%04X' % Com_UNK)): ##### Received UNK request
                    send_data = bytearray(b'RP --- %s %s --:------ %04X %s\r\n' % (ControllerTXT, dev1, Com_UNK, data[46:60]))
                    print('Send:(%s)' % send_data)
                    No = ComPort.write(send_data)
                elif ((msg_type == 'RQ') and (cmnd == '%04X' % Com_DATE)): ##### Received DATE request
                    today = datetime.datetime.now()
                    SendTXT = '{0:02X}'.format(int((today.hour)))+'{0:02X}'.format(int((today.minute)))+'{0:02X}'.format(int((today.second)))+'{0:02X}'.format(int((today.day)))+'{0:02X}'.format(int((today.month)))+'{0:04X}'.format(int((today.year)))
                    send_data = bytearray(b'RP --- %s %s --:------ %04X 009 00FC%s\r\n' % (ControllerTXT, dev1, Com_DATE, SendTXT))
                    print('Send:(%s)' % send_data)
                    No = ComPort.write(send_data)

    else: #  ((time.time() - Sync_time) >=  Sync_dur)
        print("int")
        Sync_time = time.time()
        if (Device_count > 0):
            ##### Send periodic SYNC message followed by ZONE_SETPOINT and ZONE_TEMP for all zones
            send_data = bytearray('I --- %s --:------ %s %04X 003 FF%s\r\n' % (ControllerTXT, ControllerTXT, Com_SYNC, SyncTXT),'ASCII')
            print('Send:(%s)' % send_data)
            print('>>>>:(%s)' % send_data, file=output_log)
            No = ComPort.write(send_data)
            SendTXT = ''.join(('{0:02d}'.format(j) + Zone_INFO[j][4]) for j in range(0, Device_count))
            Send_len = len(SendTXT) / 2
            send_data = bytearray('I --- %s --:------ %s %04X %03d %s\r\n' % (ControllerTXT, ControllerTXT, Com_SETP, Send_len, SendTXT),'ASCII')
            print('Send:(%s)' % send_data)
            print('>>>>:(%s)' % send_data, file=output_log)
            No = ComPort.write(send_data)
            SendTXT = ''.join(('{0:02d}'.format(j) + Zone_INFO[j][5]) for j in range(0, Device_count))
            send_data = bytearray('I --- %s --:------ %s %04X %03d %s\r\n' % (ControllerTXT, ControllerTXT, Com_TEMP, Send_len, SendTXT),'ASCII')
            print('Send:(%s)' % send_data)
            print('>>>>:(%s)' % send_data, file=output_log)
            No = ComPort.write(send_data)

# TODO: This section is redundant at the moment
ComPort.close()                   # Close the COM Port (
file.close(output_log)



