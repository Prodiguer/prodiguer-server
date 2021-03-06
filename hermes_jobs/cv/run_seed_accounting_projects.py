# -*- coding: utf-8 -*-

"""
.. module:: run_seed_accounting_projects.py
   :copyright: Copyright "Mar 21, 2015", Institute Pierre Simon Laplace
   :license: GPL/CeCIL
   :platform: Unix
   :synopsis: One off job to seed accouting project controlled vocabulary.

.. moduleauthor:: Mark Conway-Greenslade <momipsl@ipsl.jussieu.fr>


"""
from hermes import cv
from hermes.db import pgres as db
from hermes.db.pgres import dao_monitoring as dao



def _get_accounting_projects():
    """Returns set of accounting projects.

    """
    with db.session.create():
        return dao.get_accounting_projects()


def _main():
    """Main entry point.

    """
    cv.session.insert([cv.create('accounting_project', ap.strip())
                       for ap in _get_accounting_projects() if ap and ap.strip()])
    cv.session.commit()


if __name__ == '__main__':
    _main()
