#!/usr/bin/env python

# OpenSignals TCP/IP Client module for CARMEn
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.


# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================

import socket
import json
import threading
import select
import queue
import pandas as pd



# ==============================================================================
# -- Classes -------------------------------------------------------------------
# ==============================================================================

class OpenSignalsTCPClient(object):
    def __init__(self):
        self.tcpIp = '127.0.0.1'
        self.tcpPort = 5555
        self.buffer_size = 99999

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.inputCheck = []
        self.outputCheck = []
        self.isChecking = False
        self.isAcquiring = False
        self.msgQueue = queue.Queue()

        self.txtFile = SaveAcquisition()

        self.deviceStarted = False

    def connect(self):
        self.socket.connect((self.tcpIp, self.tcpPort))
        self.outputCheck.append(self.socket)
        self.isChecking = True

    def start(self):
        thread = threading.Thread(target=self.msgChecker)
        thread.daemon = True
        thread.start()

    def stop(self):
        self.isChecking = False
        self.socket.close()

    def msgChecker(self):
        while self.isChecking:
            readable, writable, exceptional = select.select(self.inputCheck, self.outputCheck, self.inputCheck)
            for s in readable:
                message = s.recv(self.buffer_size)
                if not self.isAcquiring:
                    #print(message)
                    self.inputCheck = []
                else:
                    #print(message)
                    message = json.loads(message)
                    message = message["returnData"]
                    if not self.txtFile.getHasHeader():
                        newLine = json.dumps(message) + "\n"
                        self.txtFile.addData(newLine)
                    else:
                        if not self.deviceStarted:
                            self.deviceStarted = True
                        dataframe = []
                        for device in message.keys():
                            try:
                                dataframe.append(pd.DataFrame(message[device]))
                            except:
                                dataframe.append(pd.Series(message[device]))
                        dataframe = pd.concat(dataframe, axis=1, ignore_index=True)
                        for line in dataframe.values:
                            self.txtFile.addData('\n')
                            self.txtFile.addData(",".join([str(x) for x in line]))

            for s in writable:
                try:
                    next_msg = self.msgQueue.get_nowait()
                except queue.Empty:
                    pass
                else:
                    # print("send ")
                    self.socket.send(str(next_msg).encode())

            for s in exceptional:
                print("exceptional ", s)

    def addMsgToSend(self, data):
        self.msgQueue.put(data)
        if self.socket not in self.outputCheck:
            self.outputCheck.append(self.socket)
        if self.socket not in self.inputCheck:
            self.inputCheck.append(self.socket)

    def setIsAcquiring(self, isAcquiring):
        self.isAcquiring = isAcquiring
        if self.isAcquiring:
            self.txtFile = SaveAcquisition()
            self.txtFile.start()
        else:
            self.txtFile.stop()


class SaveAcquisition(object):
    def __init__(self):
        self.fileTxt = None
        self.hasHeader = False

    def start(self):
        #self.fileTxt = open("tct_Acquisition.txt", "w")
        pass

    def addData(self, data):
        #self.fileTxt.write(data)
        self.hasHeader = True

    def stop(self):
        #self.fileTxt.close()
        print("Stop")

    def getHasHeader(self):
        return self.hasHeader
