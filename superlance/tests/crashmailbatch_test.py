import unittest
import mock
import time
from StringIO import StringIO

class CrashMailBatchTests(unittest.TestCase):
    fromEmail = 'testFrom@blah.com'
    toEmail = 'testTo@blah.com'
    subject = 'Test Alert'
    now = 1279677400.1
    unexpectedErrorMsg = '2010-07-20 18:56:40,099 -- Process bar:foo \
(pid 58597) died unexpectedly'
    
    def _getTargetClass(self):
        from superlance.crashmailbatch import CrashMailBatch
        return CrashMailBatch
        
    def _makeOneMocked(self, **kwargs):
        kwargs['stdin'] = StringIO()
        kwargs['stdout'] = StringIO()
        kwargs['stderr'] = StringIO()
        kwargs['fromEmail'] = kwargs.get('fromEmail', self.fromEmail)
        kwargs['toEmail'] = kwargs.get('toEmail', self.toEmail)
        kwargs['subject'] = kwargs.get('subject', self.subject)
        kwargs['now'] = self.now
        
        obj = self._getTargetClass()(**kwargs)
        obj.sendEmail = mock.Mock()
        return obj

    def getProcessExitedEvent(self, pname, gname, expected,
                                eventname='PROCESS_STATE_EXITED'):
        headers = {
            'ver': '3.0', 'poolserial': '7', 'len': '71',
            'server': 'supervisor', 'eventname': eventname,
            'serial': '7', 'pool': 'checkmailbatch',
        }
        payload = 'processname:%s groupname:%s from_state:RUNNING expected:%d \
pid:58597' % (pname, gname, expected)
        return (headers, payload)
        
    def getTick60Event(self):
        headers = {
            'ver': '3.0', 'poolserial': '5', 'len': '15',
            'server': 'supervisor', 'eventname': 'TICK_60',
            'serial': '5', 'pool': 'checkmailbatch',
        }
        payload = 'when:1279665240'
        return (headers, payload)

    def test_generateProcessExitMsg_expected(self):
        crash = self._makeOneMocked()
        hdrs, payload = self.getProcessExitedEvent('foo', 'bar', 1)
        self.assertEquals(None, crash.generateProcessExitMsg(hdrs, payload))

    def test_generateProcessExitMsg_unexpected(self):
        crash = self._makeOneMocked()
        hdrs, payload = self.getProcessExitedEvent('foo', 'bar', 0)
        msg = crash.generateProcessExitMsg(hdrs, payload)
        self.assertEquals(self.unexpectedErrorMsg, msg)
        
    def test_handleEvent_exit_expected(self):
        crash = self._makeOneMocked()
        hdrs, payload = self.getProcessExitedEvent('foo', 'bar', 1)
        crash.handleEvent(hdrs, payload)
        self.assertEquals([], crash.getBatchMsgs())
        self.assertEquals('', crash.stderr.getvalue())

    def test_handleEvent_exit_unexpected(self):
        crash = self._makeOneMocked()
        hdrs, payload = self.getProcessExitedEvent('foo', 'bar', 0)
        crash.handleEvent(hdrs, payload)
        self.assertEquals([self.unexpectedErrorMsg], crash.getBatchMsgs())
        self.assertEquals(self.unexpectedErrorMsg, crash.stderr.getvalue())

    def test_handleEvent_non_exit(self):
        crash = self._makeOneMocked()
        hdrs, payload = self.getProcessExitedEvent('foo', 'bar', 0,
                                            eventname='PROCESS_STATE_FATAL')
        crash.handleEvent(hdrs, payload)
        self.assertEquals([], crash.getBatchMsgs())
        self.assertEquals('', crash.stderr.getvalue())

    def test_handleEvent_tick_interval_expired_with_msgs(self):
        crash = self._makeOneMocked()
        #Put msgs in batch
        hdrs, payload = self.getProcessExitedEvent('foo', 'bar', 0)
        crash.handleEvent(hdrs, payload)
        hdrs, payload = self.getProcessExitedEvent('bark', 'dog', 0)
        crash.handleEvent(hdrs, payload)
        self.assertEquals(2, len(crash.getBatchMsgs()))
        #Time expired
        hdrs, payload = self.getTick60Event()
        crash.handleEvent(hdrs, payload)
        
        #Test that batch messages are now gone
        self.assertEquals([], crash.getBatchMsgs())
        #Test that email was sent
        self.assertEquals(1, crash.sendEmail.call_count)
        # print crash.sendEmail.call_args
        emailCallArgs = crash.sendEmail.call_args[0]
        self.assertEquals(1, len(emailCallArgs))
        expected = {
            'body': '2010-07-20 18:56:40,099 -- Process bar:foo (pid '
                    '58597) died unexpectedly\n2010-07-20 18:56:40,099 '
                    '-- Process dog:bark (pid 58597) died unexpectedly',
            'to': 'testTo@blah.com',
            'from': 'testFrom@blah.com',
            'subject': 'Test Alert',
        }
        self.assertEquals(expected, emailCallArgs[0])

    def test_handleEvent_tick_interval_expired_without_msgs(self):
        crash = self._makeOneMocked()
        #Time expired
        hdrs, payload = self.getTick60Event()
        crash.handleEvent(hdrs, payload)
        #Test that email was not sent
        self.assertEquals(0, crash.sendEmail.call_count)

    def test_handleEvent_tick_interval_not_expired(self):
        crash = self._makeOneMocked(interval=3)
        hdrs, payload = self.getTick60Event()
        crash.handleEvent(hdrs, payload)
        self.assertEquals(1, crash.getBatchMinutes())
        crash.handleEvent(hdrs, payload)
        self.assertEquals(2, crash.getBatchMinutes())


if __name__ == '__main__':
    unittest.main()         