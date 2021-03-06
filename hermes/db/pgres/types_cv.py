# -*- coding: utf-8 -*-

"""
.. module:: hermes.db.types_cv.py
   :platform: Unix
   :synopsis: Hermes controlled vocabulary database tables.

.. moduleauthor:: Mark Conway-Greenslade <momipsl@ipsl.jussieu.fr>


"""
from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import UniqueConstraint

from hermes.db.pgres.entity import Entity



# Database schema.
_SCHEMA = 'cv'


class ControlledVocabularyTerm(Entity):
    """Represents a CV term.

    """
    # SQLAlchemy directives.
    __tablename__ = 'tbl_cv_term'
    __table_args__ = (
        UniqueConstraint('typeof' ,'name'),
        {'schema':_SCHEMA}
    )

    # Attributes.
    typeof = Column(Unicode(127), nullable=False)
    name = Column(Unicode(127), nullable=False)
    display_name = Column(Unicode(127))
    synonyms = Column(Unicode(1023))
    uid = Column(Unicode(63), nullable=False, unique=True)
    sort_key = Column(Unicode(127))

