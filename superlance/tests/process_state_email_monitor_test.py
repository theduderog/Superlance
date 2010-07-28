import unittest
import mock
import time
from StringIO import StringIO

class ProcessStateEmailMonitorTests(unittest.TestCase):
    fromEmail = 'testFrom@blah.com'
    toEmail = 'testTo@blah.com'
    subject = 'Test Alert'
    
    def _getTargetClass(self):
        from superlance.process_state_email_monitor import ProcessStateEmailMonitor
        return ProcessStateEmailMonitor
        
    def _makeOneMocked(self, **kwargs):
        kwargs['stdin'] = StringIO()
        kwargs['stdout'] = StringIO()
        kwargs['stderr'] = StringIO()
        kwargs['fromEmail'] = kwargs.get('fromEmail', self.fromEmail)
        kwargs['toEmail'] = kwargs.get('toEmail', self.toEmail)
        kwargs['subject'] = kwargs.get('subject', self.subject)
        
        obj = self._getTargetClass()(**kwargs)
        obj.sendEmail = mock.Mock()
        return obj
    
    def test_sendBatchNotification(self):
        testMsgs = ['msg1', 'msg2']
        monitor = self._makeOneMocked()
        monitor.batchMsgs = testMsgs
        monitor.sendBatchNotification()
        
        #Test that email was sent
        self.assertEquals(1, monitor.sendEmail.call_count)
        emailCallArgs = monitor.sendEmail.call_args[0]
        self.assertEquals(1, len(emailCallArgs))
        expected = {
            'body': 'msg1\nmsg2',
            'to': 'testTo@blah.com',
            'from': 'testFrom@blah.com',
            'subject': 'Test Alert',
        }
        self.assertEquals(expected, emailCallArgs[0])

if __name__ == '__main__':
    unittest.main()