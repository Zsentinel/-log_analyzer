#!/bin/usr/python
import socket
import serial
import argparse
import time
import tailer
import json
import threading
import re

# -*- coding: utf-8 -*-


class Test(object):
    def __init__(self, jsonFileStraregy):
        self.syslog = open("sysAnalize.log", 'w+', 0)
        with open(self.jsonFileStraregy, 'r') as load_json:
            self.pars_json = json.loads(load_json.read())

    def detectEvent(self, line):
        if len(self.pars_json.keys()) == 0:
            self.syslog.write('All events are completed'+'\n\r')
            exit(0)

        for events in self.pars_json.keys():
            if events in line:
                self.syslog.write('Found event - ' + events + '\n\r')
                for execCommands in self.pars_json[events]:
                    self.syslog.write('Execute commands - ' + execCommands + '\n\r')
                    if 'del' in execCommands:
                        self.pars_json.pop(events)
                        break
                    elif 'sysSleep' in execCommands:
                        findSec = re.search(r'(\d+)', execCommands)
                        self.syslog.write('Waiting ' + findSec.group(1) + ' sec' + '\n\r')
                        time.sleep(int(findSec.group(1)))
                    else:
                        self.sendCommands(execCommands)
                        time.sleep(1)


class SerialConnection(Test):
    def __init__(self, jsonFileStraregy, inputOutputLog, connection):
        self.jsonFileStraregy = jsonFileStraregy
        self.inputOutputLog = inputOutputLog
        self.connection = connection
        super(SerialConnection, self).__init__(self.jsonFileStraregy,)
        try:
            self.ser = serial.Serial(self.connection, 38400, rtscts=0, parity='O', xonxoff=0, bytesize=8, stopbits=1, timeout=2)
        except:
            self.syslog.write('Unable to connect to Serial Port' + '\n\r')
            exit(1)

    def start(self):
        tReadLines = threading.Thread(target = self.writeSeriealLog)
        tSendIfEvent = threading.Thread(target = self.readOutput)
        tReadLines.start()
        tSendIfEvent.start()

    def readOutput(self):
        self.syslog.write('Reading output log has started' + '\n\r')
        for line in tailer.follow(open(self.inputOutputLog)):
            self.detectEvent(line)

    def writeSeriealLog(self):
        logOut = open(self.inputOutputLog, 'w', 0)
        self.syslog.write('Writing to output log has started' + '\n\r')
        while True:
            try:
                value = unicode(self.ser.readline(), "utf-8")
                logOut.writelines(value)
            except:
                pass

    def sendCommands(self, execCommands):
        self.ser.write((b'!%s' + '\n\r') % execCommands)


class txtFile(Test):
    def __init__(self, jsonFileStraregy, inputOutputLog, connection):
        self.jsonFileStraregy = jsonFileStraregy
        self.inputOutputLog = inputOutputLog
        self.connection = connection
        super(txtFile, self).__init__(self.jsonFileStraregy)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)

    def start(self):
        self.syslog.write('Reading has started' + '\n\r')
        for line in tailer.follow(open(self.inputOutputLog)):
            self.detectEvent(line)

    def sendCommands(self, execCommands):
        self.sock.sendto(('%s' % execCommands), (self.connection, 65432))
        try:
            data = self.sock.recv(1024)
        except:
            self.syslog.write('UNABLE TO CONNECT TO STB !' + '\n\r')
            return
        self.syslog.write(data + '\n\r')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', help='Enter serieal port ot STB', required=True)
    parser.add_argument('-j', '--json', help='Json', required=True)
    parser.add_argument('-log', '--log', help='Enter Log File', required=True)
    args = parser.parse_args()

    if 'USB' in args.source:
        test = SerialConnection(args.json, args.log, args.source)
    else:
        test = txtFile(args.json, args.log, args.source)

    test.start()


if __name__ == '__main__':
    main()
