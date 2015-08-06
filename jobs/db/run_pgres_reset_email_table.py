# -*- coding: utf-8 -*-

"""
.. module:: run_pgres_reset_email_table.py
   :copyright: Copyright "Apr 26, 2013", Institute Pierre Simon Laplace
   :license: GPL/CeCIL
   :platform: Unix
   :synopsis: Resets prodiguer mq.tbl_message_email table.

.. moduleauthor:: Mark Conway-Greenslade <momipsl@ipsl.jussieu.fr>


"""
from prodiguer.db import pgres as db
from prodiguer.utils import config
from prodiguer.utils import logger



def _main():
    """Main entry point.

    """
    logger.log_db("Reset email table begins")

    # Start session.
    db.session.start(config.db.pgres.main)

    # Delete all records in table.
    db.dao.delete_all(db.types.MessageEmail)

    # End session.
    db.session.end()

    logger.log_db("Reset email table complete")


if __name__ == '__main__':
    _main()
