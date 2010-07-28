#!/usr/bin/env python -u
##############################################################################
#
# Copyright (c) 2007 Agendaless Consulting and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################
doc = """\
Base class for common functionality when monitoring process state changes
"""

import os
import sys

from supervisor import childutils

class ProcessStateMonitor:

    # In child class, define a list of events to monitor
    processStateEvents = []

    def __init__(self, **kwargs):
        self.interval = kwargs.get('interval', 1)
        
        self.debug = kwargs.get('debug', False)
        self.stdin = kwargs.get('stdin', sys.stdin)
        self.stdout = kwargs.get('stdout', sys.stdout)
        self.stderr = kwargs.get('stderr', sys.stderr)
        
        self.now = kwargs.get('now', None)
        
        self.batchMsgs = []
        self.batchMins = 0
 
    def run(self):
        while 1:
            hdrs, payload = childutils.listener.wait(self.stdin, self.stdout)
            self.handleEvent(hdrs, payload)
            childutils.listener.ok(self.stdout)
    
    def handleEvent(self, headers, payload):
        if headers['eventname'] in self.processStateEvents:
            self.handleProcessStateChangeEvent(headers, payload)
        elif headers['eventname'] == 'TICK_60':
            self.handleTick60Event(headers, payload)
    
    def handleProcessStateChangeEvent(self, headers, payload):
        msg = self.generateProcessStateChangeMsg(headers, payload)
        if msg:
            self.writeToStderr(msg)
            self.batchMsgs.append(msg)

    """
    Override this method in child classes to customize messaging
    """
    def generateProcessStateChangeMsg(self, headers, payload):
        return None

    def handleTick60Event(self, headers, payload):
        self.batchMins += 1
        if self.batchMins >= self.interval:
            self.sendBatchNotification()
            self.clearBatch()
            
    """
    Override this method in child classes to send notification
    """
    def sendBatchNotification(self):
        pass
    
    def getBatchMinutes(self):
        return self.batchMins
    
    def getBatchMsgs(self):
        return self.batchMsgs
        
    def clearBatch(self):
        self.batchMins = 0;
        self.batchMsgs = [];

    def writeToStderr(self, msg):
        self.stderr.write(msg)
        self.stderr.flush()