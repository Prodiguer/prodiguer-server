# -*- coding: utf-8 -*-

"""
.. module:: prodiguer.__init__.py

   :copyright: @2013 Institute Pierre Simon Laplace (http://esdocumentation.org)
   :license: GPL / CeCILL
   :platform: Unix
   :synopsis: Top level package intializer.

.. moduleauthor:: Institute Pierre Simon Laplace (ES-DOC) <dev@esdocumentation.org>

"""
__version__ = '0.2.0.0'


from os.path import dirname, abspath, join

from . import (
	api,
	cv,
	db,
	mq,
	utils,
	)
from .utils import config, convert, mail, runtime, runtime as rt


# Module exports.
__all__ = [
	'api',
	'config',
	'convert',
	'cv',
	'db',
	'mq',
	'utils',
]

