#!/usr/bin/env python
from __future__ import print_function

import json

from WMCore.Services.StompAMQ.StompAMQ import StompAMQ


class stompAMQ(StompAMQ):
    """
    Overriding :py:mod:`WMCore.Services.StompAMQ.StompAMQ.StompAMQ`'s
    :py:func:`_send_single` method. The default ``destination`` -- **queue** is
    not authorizing me to write.
    """

    def _send_single(self, conn, notification):
        """
        Send a single notification to `conn`
        :param conn: An already connected stomp.Connection
        :param notification: A dictionary as returned by `make_notification`
        :return: The notification body in case of failure, or else None
        """
        try:
            body = notification.pop('body')
            conn.send(destination='/topic/{}'.format(self._topic),
                      headers=notification,
                      body=json.dumps(body),
                      ack='auto')
            self.logger.debug('Notification %s sent', str(notification))
        except Exception as exc:
            self.logger.error(
                'Notification: %s not send, error: %s', str(notification), str(exc))
            return body
        return
