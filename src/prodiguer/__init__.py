# -*- coding: utf-8 -*-

"""
.. module:: prodiguer.__init__.py

   :copyright: @2013 Institute Pierre Simon Laplace (http://esdocumentation.org)
   :license: GPL / CeCILL
   :platform: Unix
   :synopsis: Top level package intializer.

.. moduleauthor:: Institute Pierre Simon Laplace (ES-DOC) <dev@esdocumentation.org>

"""
__version__ = '0.1.0.0'


# Module imports.
from os.path import dirname, abspath, join

from . import (
	api,
	cv, 
	db,
	# mq,
	utils,
	)



# Module exports.
__all__ = [
	'api',
	'config',
	'configure',
	'cv',
	'db',
	# 'mq',
	'utils',
]


# Config filename.
_CONFIG_FILENAME = 'config.json'


# Library configuration data.
config = utils.config

# Library configuration assignment.
configure = config.set
