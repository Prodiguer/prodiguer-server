# -*- coding: utf-8 -*-

"""
.. module:: prodiguer.web.ops.heartbeat.py
   :copyright: @2015 IPSL (http://ipsl.fr)
   :license: GPL/CeCIL
   :platform: Unix, Windows
   :synopsis: Operations heartbeat request handler.

.. moduleauthor:: Mark Conway-Greenslade <momipsl@ipsl.jussieu.fr>


"""
import tornado

from prodiguer.web import utils_handler
from prodiguer.utils import rt



class ListEndpointsRequestHandler(tornado.web.RequestHandler):
    """Operations list endpoints request handler.

    """
    def prepare(self):
        """Called at the beginning of request handling."""
        self.output = {
            'endpoints': [
                r'/api/1/monitoring/fe/setup',
                r'/api/1/monitoring/fe/ws',
                r'/api/1/monitoring/event',
                r'/api/1/metric/add',
                r'/api/1/metric/delete',
                r'/api/1/metric/fetch',
                r'/api/1/metric/fetch_count',
                r'/api/1/metric/fetch_columns',
                r'/api/1/metric/fetch_list',
                r'/api/1/metric/fetch_setup',
                r'/api/1/metric/rename',
                r'/api/1/metric/set_hashes',
                r'/api/1/ops/heartbeat',
                r'/api/1/ops/endpoints'
                ]
            }


    def _write(self, error=None):
        """Write response output."""
        utils_handler.write_response(self, error)


    def _log(self, error=None):
        """Logs execution."""
        utils_handler.log("ops", self, error)


    def get(self):
        # Define tasks.
        tasks = {
            "green": (
                self._write,
                self._log,
                ),
            "red": (
                self._write,
                self._log,
                )
        }

        # Invoke tasks.
        rt.invoke(tasks)