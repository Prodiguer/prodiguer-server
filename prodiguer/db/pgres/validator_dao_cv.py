# -*- coding: utf-8 -*-

"""
.. module:: prodiguer.db.dao_cv.validator.py
   :copyright: Copyright "Apr 26, 2013", IPSL
   :license: GPL/CeCIL
   :platform: Unix
   :synopsis: CV data access operations validator.

.. moduleauthor:: Mark Conway-Greenslade <momipsl@ipsl.jussieu.fr>


"""
from prodiguer import cv



def validate_create_term(
    term_type,
    term_name,
    term_display_name,
    ):
    """Function input validator: create_term.

    """
    cv.validator.validate_term_type(term_type)
    cv.validator.validate_term_name(term_type, term_name)
    cv.validator.validate_term_display_name(term_display_name)


def validate_retrieve_term(term_type, term_name):
    """Function input validator: retrieve_term.

    """
    cv.validator.validate_term_type(term_type)
    cv.validator.validate_term_name(term_type, term_name)