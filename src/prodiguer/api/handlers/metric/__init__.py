# -*- coding: utf-8 -*-

"""
.. module:: prodiguer.api.handlers.metric.__init__.py
   :copyright: Copyright "Feb 7, 2013", Earth System Documentation
   :license: GPL/CeCIL
   :platform: Unix, Windows
   :synopsis: Simulation metric package initializer.

.. moduleauthor:: Mark Conway-Greenslade <momipsl@ipsl.jussieu.fr>


"""
from .add import AddRequestHandler
from .delete import DeleteRequestHandler
from .fetch import FetchRequestHandler
from .fetch_columns import FetchColumnsRequestHandler
from .fetch_count import FetchCountRequestHandler
from .fetch_list import FetchListRequestHandler
from .fetch_setup import FetchSetupRequestHandler
