# -*- coding: utf-8 -*-

"""
.. module:: api.utils.ws.py
   :copyright: @2015 IPSL (http://ipsl.fr)
   :license: GPL/CeCIL
   :platform: Unix, Windows
   :synopsis: API web socket utility functions.

.. moduleauthor:: Mark Conway-Greenslade <momipsl@ipsl.jussieu.fr>


"""
import collections

import tornado.websocket

from prodiguer.utils import config, rt
from prodiguer.utils.data_convertor import jsonify



# Cached web socket clients.
_WS_CLIENTS = collections.defaultdict(list)


def get_client_count(key=None):
    """Returns count of connected clients.

    :param key: Web socket client cache key.
    :param type: str

    :returns: Web socket client count.
    :rtype: int

    """
    if key is not None:
        return len(_WS_CLIENTS[key])
    else:
        return reduce(lambda x, y: x + len(y), _WS_CLIENTS.values(), 0)


def on_write(key, data):
    """Broadcasts web socket message to relevant clients.

    :param key: Web socket client cache key.
    :param type: str

    :param data: Data dictionary to send to client.
    :param data: dict

    """
    data = jsonify(data)
    for client in _WS_CLIENTS[key]:
        try:
            client.write_message(data)
        except tornado.websocket.WebSocketClosedError:
            _WS_CLIENTS[key].remove(client)


def on_connect(key, client):
    """Caches a client connection.

    :param key: Web socket client cache key.
    :param type: str

    :param client: Web socket handler pointer.
    :type client: torndao.websocket.WebSocketHandler

    """
    if client not in _WS_CLIENTS[key]:
        _WS_CLIENTS[key].append(client)
        rt.log_api("WS {0} :: connection opened :: clients = {1}.".format(key, len(_WS_CLIENTS[key])))


def on_disconnect(key, client):
    """Removes a client connection from cache.

    :param key: Web socket client cache key.
    :param type: str

    :param c: Web socket handler pointer.
    :param c: torndao.websocket.WebSocketHandler

    """
    if client in _WS_CLIENTS[key]:
        _WS_CLIENTS[key].remove(client)
        rt.log_api("WS {0} :: connection closed :: clients = {1}.".format(key, len(_WS_CLIENTS[key])))


def clear_cache(key=None):
    """Removes client connections from cache.

    :param key: Web socket client cache key.
    :param type: str

    """
    global _WS_CLIENTS

    if key is None:
        _WS_CLIENTS = {}
    elif key in _WS_CLIENTS:
        del _WS_CLIENTS[key]


def pong_WS_CLIENTS():
    """Pongs clients.

    """
    logged = False
    for app in _WS_CLIENTS.keys():
        for client in _WS_CLIENTS[app]:
            if not logged:
                rt.log_api("Ponging websocket clients.")
                logged = True
            try:
                client.write_message("pong")
            except tornado.websocket.WebSocketClosedError:
                _WS_CLIENTS[app].remove(client)


def keep_alive():
    """Sends a websocket ping to all clients to keep them open.

    """
    def _do():
        pong_WS_CLIENTS()
        keep_alive()

    # Do this every N seconds so as to keep client connections open.
    delay = config.api.websocketKeepAliveDelayInSeconds
    if delay:
        rt.log_api("Websocket keep alive every {0} seconds.".format(delay))
        tornado.ioloop.IOLoop.instance().call_later(delay, _do)
