# -*- coding: utf-8 -*-

"""
.. module:: cv.io.py
   :copyright: Copyright "December 01, 2014", IPSL
   :license: GPL/CeCIL
   :platform: Unix, Windows
   :synopsis: Controlled vocabulary IO manager.

.. moduleauthor:: Mark Conway-Greenslade <momipsl@ipsl.jussieu.fr>


"""
import json
import os

from hermes.cv import accessor as ta
from hermes.utils import logger
from hermes.utils import shell



def _get_path_to_archive():
    """Return path to CV data archive.

    """
    return shell.get_repo_path(['hermes-cv', 'data'])


def _get_path_to_term_type(term):
    """Return path to CV term type.

    """
    term_fpath = _get_path_to_archive()
    term_fpath = os.path.join(term_fpath, ta.get_type(term))

    return term_fpath


def _get_path_to_term(term):
    """Return path to CV term.

    """
    term_fpath = _get_path_to_term_type(term)
    term_fpath = os.path.join(term_fpath, ta.get_name(term))
    term_fpath += ".json"

    return term_fpath


def read(log=True):
    """Reads terms from file system.

    """
    def _load(filepath):
        """Loads JSON from a CV file.

        """
        with open(filepath, 'r') as cv_file:
            try:
                return json.loads(cv_file.read())
            except ValueError:
                logger.log_cv_warning("CV file load error: {0}".format(filepath))
                return None

    # Set directory to CV archive.
    dir_archive = _get_path_to_archive()
    if log:
        logger.log_cv("CV data files @ {0}".format(dir_archive))

    # Set CV files to be loaded from archive.
    termset = []
    for walked in os.walk(dir_archive):
        cv_dir = walked[0]
        cv_files = walked[2]
        termset += [os.path.join(cv_dir, f) for f in cv_files]

    # Load CV files.
    termset = [_load(f) for f in termset]

    # Convert CV files from JSON to dict.
    return [term for term in termset if term]


def write(term):
    """Writes a term to file system.

    :param dict term: Term to be written to file system.

    """
    term_type_dir = _get_path_to_term_type(term)
    if not os.path.exists(term_type_dir):
        os.makedirs(term_type_dir)

    term_filepath = _get_path_to_term(term)
    with open(term_filepath, 'w') as cv_file:
        cv_file.write(json.dumps(term, indent=4))


def delete(term):
    """Deletes a term from file system.

    :param dict term: Term to be deleted from file system.

    """
    term_filepath = _get_path_to_term(term)
    os.remove(term_filepath)
    logger.log_cv("CV file deleted: {0}".format(term_filepath))

