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
import smtplib
from email.mime.text import MIMEText
from superlance.process_state_monitor import ProcessStateMonitor

doc = """\
Base class for common functionality when monitoring process state changes
and sending email notification
"""

class ProcessStateEmailMonitor(ProcessStateMonitor):

    def __init__(self, **kwargs):
        ProcessStateMonitor.__init__(self, **kwargs)
        
        self.fromEmail = kwargs['fromEmail']
        self.toEmail = kwargs['toEmail']
        self.subject = kwargs.get('subject', 'Alert from supervisord')
            
    def sendBatchNotification(self):
        email = self.getBatchEmail()
        if email:
            self.sendEmail(email)
            
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
        msg = MIMEText(email['body'])
        msg['Subject'] = email['subject']
        msg['From'] = email['from']
        msg['To'] = email['to']

        s = smtplib.SMTP('localhost')
        s.sendmail(email['from'], [email['to']], msg.as_string())
        s.quit()
