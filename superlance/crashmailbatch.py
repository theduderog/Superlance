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

# A event listener meant to be subscribed to PROCESS_STATE_CHANGE
# events.  It will send mail when processes that are children of
# supervisord transition unexpectedly to the EXITED state.

# A supervisor config snippet that tells supervisor to use this script
# as a listener is below.
#
# [eventlistener:crashmailbatch]
# command=python crashmailbatch
# events=PROCESS_STATE,TICK_60

doc = """\
crashmailbatch.py [--interval=<batch interval in minutes>]
        [--toEmail=<email address>]
        [--fromEmail=<email address>]
        [--subject=<email subject>]

Options:

--interval  - batch cycle length (in minutes).  The default is 1 minute.
                  This means that all events in each cycle are batched together
                  and sent as a single email
                  
--toEmail   - the email address to send alerts to

--fromEmail - the email address to send alerts from

--subject - the email subject line

A sample invocation:

crashmailbatch.py --toEmail="you@bar.com" --fromEmail="me@bar.com"

"""

import os
import sys

from supervisor import childutils

class CrashMailBatch:

    def __init__(self, **kwargs):
        self.interval = kwargs.get('interval', 1)
        self.fromEmail = kwargs['fromEmail']
        self.toEmail = kwargs['toEmail']
        self.subject = kwargs.get('subject', 'Alert from supervisord')
        
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
        if headers['eventname'] == 'PROCESS_STATE_EXITED':
            self.handleProcessExitEvent(headers, payload)
        elif headers['eventname'] == 'TICK_60':
            self.handleTick60Event(headers, payload)
    
    def handleProcessExitEvent(self, headers, payload):
        msg = self.generateProcessExitMsg(headers, payload)
        if msg:
            self.writeToStderr(msg)
            self.batchMsgs.append(msg)
    
    def generateProcessExitMsg(self, headers, payload):
        pheaders, pdata = childutils.eventdata(payload+'\n')
        
        if int(pheaders['expected']):
            return None
        
        txt = 'Process %(groupname)s:%(processname)s (pid %(pid)s) died \
unexpectedly' % pheaders
        return '%s -- %s' % (childutils.get_asctime(self.now), txt)

    def handleTick60Event(self, headers, payload):
        self.batchMins += 1
        if self.batchMins >= self.interval:
            self.sendBatch()
            
    def sendBatch(self):
        email = self.getBatchEmail()
        if email:
            self.sendEmail(email)
        self.clearBatch()
    
    def getBatchMinutes(self):
        return self.batchMins
    
    def getBatchMsgs(self):
        return self.batchMsgs
        
    def clearBatch(self):
        self.batchMins = 0;
        self.batchMsgs = [];
    
    def getBatchEmail(self):
        if len(self.batchMsgs):
            return {
                'to': self.toEmail,
                'from': self.fromEmail,
                'subject': self.subject,
                'body': '\n'.join(self.getBatchMsgs()),
            }
        return None
        
    def sendEmail(self, email):
        import smtplib
        from email.mime.text import MIMEText
        
        msg = MIMEText(email['body'])
        msg['Subject'] = email['subject']
        msg['From'] = email['from']
        msg['To'] = email['to']

        s = smtplib.SMTP('localhost')
        s.sendmail(email['from'], [email['to']], msg.as_string())
        s.quit()

    def writeToStderr(self, msg):
        self.stderr.write(msg)
        self.stderr.flush()

def main():
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option("-i", "--interval", dest="interval", type="int",
                      help="batch interval in minutes (defaults to 1 minute)")
    parser.add_option("-t", "--toEmail", dest="toEmail",
                      help="destination email address")
    parser.add_option("-f", "--fromEmail", dest="fromEmail",
                      help="source email address")
    parser.add_option("-s", "--subject", dest="subject",
                      help="email subject")
    (options, args) = parser.parse_args()
    
    if not options.toEmail:
        parser.print_help()
        sys.exit(1)
    if not options.fromEmail:
        parser.print_help()
        sys.exit(1)
        
    if not 'SUPERVISOR_SERVER_URL' in os.environ:
        sys.stderr.write('Must run as a supervisor event listener\n')
        sys.exit(1)
        
    crash = CrashMailBatch(**options.__dict__)
    crash.run()

if __name__ == '__main__':
    main()