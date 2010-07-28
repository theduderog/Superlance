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

from supervisor import childutils
from superlance.process_state_email_monitor \
    import ProcessStateEmailMonitor, createFromCmdLine

class CrashMailBatch(ProcessStateEmailMonitor):
    
    processStateEvents = ['PROCESS_STATE_EXITED']

    def __init__(self, **kwargs):
        ProcessStateEmailMonitor.__init__(self, **kwargs)
        self.now = kwargs.get('now', None)
 
    def getProcessStateChangeMsg(self, headers, payload):
        pheaders, pdata = childutils.eventdata(payload+'\n')
        
        if int(pheaders['expected']):
            return None
        
        txt = 'Process %(groupname)s:%(processname)s (pid %(pid)s) died \
unexpectedly' % pheaders
        return '%s -- %s' % (childutils.get_asctime(self.now), txt)

def main():
    crash = createFromCmdLine(CrashMailBatch)
    crash.run()

if __name__ == '__main__':
    main()