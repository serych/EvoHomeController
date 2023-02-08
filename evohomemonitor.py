# Evohome Monitor
# Copyright (c) 2023 JaSe
# Python 3.x
# Requires pyserial module which can be installed using 'python -m pip3 install pyserial'
# Program to log Honeywell Evohome devices activity 
# works with RF -> serial converter for example https://github.com/ghoti57/evofw3
# inspired by https://github.com/Evsdd/Evohome_Controller
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
from datetime import datetime

output_log = open("evohome.log", "a") # zápis do logu append  ("w" for rewrite instead of append)

ComPort = serial.Serial("COM4")   # on linuxes something like:  /dev/ttyUSB0
ComPort.baudrate = 115200          # set Baud rate
ComPort.bytesize = 8              # Number of data bits = 8
ComPort.parity   = 'N'            # No parity
ComPort.stopbits = 1              # Number of Stop bits = 1
ComPort.timeout = 1               # Read timeout = 1sec

send_data = bytearray('\r\n','ASCII') # wakeup serial to air interface
No = ComPort.write(send_data)
# Set-up Controller and Zone information
ControllerID = 0x55555  # Set this to any value as long as ControllerTYPE=1 349525 dekadicky

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

Zone_num = 4          # Number of zones

Device_count = 1      # Count of devices successfully bound

Sync_dur = 60    # Time interval between periodic SYNC messages (sec)
SyncTXT = '{0:04X}'.format(Sync_dur * 10)
Sync_time = time.time()

Com_BIND = '1FC9'        # Evohome Command BIND
Com_SYNC = '1F09'        # Evohome Command SYNC
Com_NAME = '0004'        # Evohome Command ZONE_NAME
Com_SETP = '2309'        # Evohome Command ZONE_SETPOINT
Com_TEMP = '30C9'        # Evohome Command ZONE_TEMP
Com_ZUNK = '0100'        # Evohome Command ZONE_UNK (unknown)
Com_DATE = '313F'        # Evohome Command DATE_TIME
Com_WNDO = '12B0'        # Evhome Windows sensor
Com_HDMD = '3150'        # Evohome Heat Demand
# funkce vrací boolean, true pokud v datech je zadaný typ zprávy a příkaz
def eh_is_cmd(data, msg_type,cmd):
    d_msg_type = data[4:6]             # Extract message type
    d_dev1 = data[11:20]               # Extract deviceID 1
    d_dev2 = data[21:30]               # Extract deviceID 2
    d_dev3 = data[31:40]               # Extract deviceID 3
    d_cmnd = data[41:45]               # Extract command
    return (d_msg_type) == bytes(msg_type,'ascii') and (d_cmnd == bytes(cmd,'ascii'))
#void, pošle data do logu, do konzole a na sériový port
def eh_send(verb, adr1, adr2, adr3, code, data):
    if adr1 == '':
        adr1 = '--:------'
    if adr2 == '':
        adr2 = '--:------'
    if adr3 == '':
        adr3 = '--:------'
    lenght = len(data)//2
    send_data = '{0} --- {1} {2} {3} {4} {5:03} {6}\r\n'.format(verb, adr1, adr2, adr3, code, lenght, data)
    print('>>:\t{0}'.format(send_data))
    print("{0} ->:\t{1}".format(datetime.now(),send_data), file=output_log)
    No = ComPort.write(bytes(send_data,'ascii'))
    return

def devhex2str(dev):  # converts
    return "{0:02}:{1:06}".format((ControllerID & 0xFC0000) >> 18,
                                  ControllerID & 0x03FFFF)

ControllerTXT = devhex2str(ControllerID)  #0x55555

# Populate zone name Hex strings
for i in range(0,Zone_num):
    Hex_name = ''.join('{0:02X}'.format(ord(c)) for c in Zone_INFO[i][1])
    Hex_pad = ''.join('00' for j in range(len(Zone_INFO[i][1]),20))
    Zone_INFO[i][2] = Hex_name + Hex_pad

# Populate setpoint Hex strings
for i in range(0,Zone_num):
    Hex_name = '{0:04X}'.format(int(float(Zone_INFO[i][3]) * 100))
    Zone_INFO[i][4] = Hex_name
    print('Zone {0}:({1}:{2}):(0x{3}):({4}:0x{5})'.format(i+1,Zone_INFO[i][0],Zone_INFO[i][1],Zone_INFO[i][2],Zone_INFO[i][3],Zone_INFO[i][4])) #py3
# print('ControllerID=0x{0:06X} ({1})'.format(ControllerID, ControllerTXT))  #py3
##### End of setup

print("", file=output_log)  # log sepparator
print("=========================== {0} ===========================".format(datetime.now()), file=output_log)

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
            print("{0} <-:\t{1}".format(datetime.now(),data), file=output_log)

            ##### Check if device has already been defined
            i = 0
            while (i < Device_count and Zone_INFO[i][0] != dev1):
                i += 1
            i -= 1
            ##### Received BIND message
            i = 0   # provizorní testovací řešení
            if eh_is_cmd(data, ' I', Com_BIND) and (dev1 != bytes(ControllerTXT,'ascii')):
                send_data = '{0:02}2309{1:06X}{2:02}30C9{3:06X}{4:02}1FC9{5:06X}'.format(i, ControllerID, i, ControllerID, i,ControllerID)
                eh_send(' I', ControllerTXT, '', ControllerTXT, Com_BIND, send_data)

                if (Zone_INFO[i][0] != dev1):  # New Device
                    Zone_INFO[i][0] = dev1
                    # TO DO: wait and check for confirmation of successful binding - W BIND message from device
                    print('Binding complete for Zone %d:(%s):(%s)' % (Device_count+1,Zone_INFO[Device_count][0],Zone_INFO[Device_count][1]))
                    Device_count += 1
                for j in range(0,Device_count):
                    print('Zone_INFO: {0}:{1}:{2}:{3}'.format(j+1,Zone_INFO[j][0],Zone_INFO[j][1],Zone_INFO[j][3]))
            elif (Device_count > 0 and i < Device_count and bytes(Zone_INFO[i][0],'ascii') == dev1):          # Only process messages further if message is from a device defined in Zone_INFO

                if  eh_is_cmd(data, ' W', Com_BIND):
                    #((msg_type == ' W') and (cmnd == '%04X' % Com_BIND)): ##### Received BIND confirmation, respond with ZONE_NAME, SYNC and ZONE_SETPOINT
                    send_data = '{0:02}00{1}'.format(i, Zone_INFO[i][2])
                    eh_send(' I', ControllerTXT, '', ControllerTXT, Com_NAME, send_data)
                    # send_data = bytearray(b'I --- %s --:------ %s %04X 022 %02d00%s\r\n' % (ControllerTXT, ControllerTXT, Com_NAME, i, Zone_INFO[i][2]))
                    eh_send(' W', ControllerTXT, dev1, '', Com_SYNC, 'FF0BB8') # 5min SYNC 0x0BB8 = 3000 (300.0sec) # bylo ControllerTXT '' ControllerTXT
                    #send_data = bytearray(b'W --- %s --:------ %s %04X 003 FF0BB8\r\n' % (ControllerTXT, ControllerTXT, Com_SYNC)) # 5min SYNC 0x0BB8 = 3000 (300.0sec)
                    send_data = '{0:02}{1}'.format(i, Zone_INFO[i][4])
                    eh_send(' I', ControllerTXT, dev1, '', Com_SETP, send_data) # SETPOINT (bylo viz výše)
                    # send_data = bytearray(b'I --- %s --:------ %s %04X 003 %02d%s\r\n' % (ControllerTXT, ControllerTXT, Com_SETP, i, Zone_INFO[i][4]))
                elif eh_is_cmd(data, 'RQ', Com_SYNC):  ##### Received SYNC request, respond with SYNC
                    # ((msg_type == 'RQ') and (cmnd == '%04X' % Com_SYNC)):
                    send_data = '00{0:04X}'.format(int((Sync_dur - (time.time() - Sync_time)) * 10))        # Calculate remaining time until next SYNC
                    eh_send('RP', ControllerTXT, dev1, '', Com_SYNC, send_data)
                    # send_data = bytearray(b'RP --- %s %s --:------ %04X 003 00%s\r\n' % (ControllerTXT, dev1, Com_SYNC, SendTXT))

                elif eh_is_cmd(data, 'RQ', Com_NAME): ##### Received Zone NAME request
                    send_data = '{0:02}00{1}'.format(i, Zone_INFO[i][2])
                    eh_send('RP', ControllerTXT, Zone_INFO[i][0], '',Com_NAME, send_data)

                elif eh_is_cmd(data, ' I', Com_TEMP): ##### Received TEMP message, send echo response from controller
                    Zone_INFO[i][5] = '{}'.format(data[52:56])  # store TEMP in Zone_INFO
                    eh_send(' I', ControllerTXT, Zone_INFO[i][0], '',Com_TEMP, Zone_INFO[i][5])
                    print('====== Zone Info (TEMP) ===')
                    for j in range(0,Zone_num):
                        print('\t{0}:{1}:{2}:{3}:{4}'.format(j+1,Zone_INFO[j][0],Zone_INFO[j][1],Zone_INFO[j][4],Zone_INFO[j][5]))

                elif eh_is_cmd(data, ' I', Com_SETP): ##### Received SETP message, send echo response from controller
                    send_data = '{0:02}{1}'.format(i, Zone_INFO[i][4])
                    eh_send(' I', ControllerTXT, Zone_INFO[i][0], '',Com_SETP, send_data)

                elif eh_is_cmd(data, 'RQ', Com_ZUNK):  ##### Received UNK request
                    eh_send('RP', ControllerTXT, Zone_INFO[i][0], '',Com_ZUNK, data[46:60])

                elif eh_is_cmd(data, 'RQ', Com_DATE): ##### Received DATE request
                    today = datetime.datetime.now()
                    SendTXT = '{0:02X}'.format(int((today.hour)))+\
                              '{0:02X}'.format(int((today.minute)))+\
                              '{0:02X}'.format(int((today.second)))+\
                              '{0:02X}'.format(int((today.day)))+\
                              '{0:02X}'.format(int((today.month)))+\
                              '{0:04X}'.format(int((today.year)))
                    print('Datum: ' + SendTXT)
                    eh_send('RP', ControllerTXT, Zone_INFO[i][0], '',Com_DATE, SendTXT)

    else: #  ((time.time() - Sync_time) >=  Sync_dur)
        print("int")
        print("{0} ** Interval".format(datetime.now()), file=output_log)
        Sync_time = time.time()
        if (Device_count > 0):
            ##### Send periodic SYNC message followed by ZONE_SETPOINT and ZONE_TEMP for all zones
            send_data = 'FF{0}'.format(SyncTXT)
            eh_send(' I', ControllerTXT, "", ControllerTXT, Com_SYNC, send_data) # Send SYNC period

            send_data = ''.join(('{0:02d}'.format(j) + Zone_INFO[j][4]) for j in range(0, Device_count)) #prepare SETPOINT data for zone
            eh_send(' I', ControllerTXT, "", ControllerTXT, Com_SETP, send_data) #send SETPOINT data

            send_data = ''.join(('{0:02d}'.format(j) + Zone_INFO[j][5]) for j in range(0, Device_count)) #prepare TEMPERATURE data for zone
            eh_send(' I', ControllerTXT, "", ControllerTXT, Com_TEMP, send_data)

# TODO: This section is redundant at the moment
ComPort.close()                   # Close the COM Port (
file.close(output_log)



