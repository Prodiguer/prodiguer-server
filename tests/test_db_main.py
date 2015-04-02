# -*- coding: utf-8 -*-

"""
.. module:: test_db.py

   :copyright: @2015 IPSL (http://ipsl.fr)
   :license: GPL / CeCILL
   :platform: Unix
   :synopsis: Encapsulates db tests.

.. moduleauthor:: IPSL (ES-DOC) <dev@esdocumentation.org>

"""
import inspect



def test_db_import_package():
    from prodiguer import db

    modules = [
        db,
        db.dao,
        db.session,
        db.setup,
        db.type_factory,
    ]
    for module in modules:
        assert inspect.ismodule(module)        
