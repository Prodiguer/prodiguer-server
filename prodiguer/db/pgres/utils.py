# -*- coding: utf-8 -*-

"""
.. module:: db.utils.py
   :copyright: @2015 IPSL (http://ipsl.fr)
   :license: GPL/CeCIL
   :platform: Unix, Windows
   :synopsis: Database utility functions.

.. moduleauthor:: Mark Conway-Greenslade <momipsl@ipsl.jussieu.fr>


"""
import datetime

from prodiguer.db.pgres import dao
from prodiguer.db.pgres import convertor



def get_sorted_list(entity_type, key='name'):
    """Returns a sorted list of db entities formatted for front-end.

    :param db.Entity entity: Entity instance.
    :param expression key: Collection sort key.

    :returns: A sorted list of entites in dictionary format ready to be returned to front-end.
    :rtype: list

    """
    return sorted(get_list(entity_type),
                  key=lambda instance: instance[key].lower())


def get_list(entity_type):
    """Returns a list of db entities formatted for front-end.

    :param db.Entity entity: Entity instance.

    :returns: A list of entites in dictionary format ready to be returned to front-end.
    :rtype: list

    """
    return get_collection(dao.get_all(entity_type))


def get_collection(entity_collection):
    """Returns a list of db entities formatted for front-end.

    :param db.Entity entity: Entity instance.

    :returns: A list of entites in dictionary format ready to be returned to front-end.
    :rtype: list

    """
    return [get_item(e) for e in entity_collection]


def format_date_fields(obj):
    """Formats date fields within passed dictionary.

    """
    for key, val in obj.items():
        if type(val) == datetime.datetime:
            obj[key] = unicode(val)


def get_item(instance):
    """Returns a db entity formatted for front-end.

    :param db.Entity entity: Entity instance.

    :returns: Entity information in dictionary format ready to be returned to front-end.
    :rtype: dict

    """
    # Convert to a dictionary.
    obj = convertor.to_dict(instance)

    # Set name attribute (if required).
    if 'name' not in obj:
        try:
            obj['name'] = instance.name
        except AttributeError:
            pass

    # Remove row meta-info.
    del obj["id"]
    del obj["row_create_date"]
    del obj["row_update_date"]

    # Format date fields
    format_date_fields(obj)

    return obj