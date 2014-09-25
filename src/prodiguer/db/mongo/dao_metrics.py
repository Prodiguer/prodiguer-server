# -*- coding: utf-8 -*-

"""
.. module:: prodiguer.db.mongo.dao_metrics.py
   :platform: Unix
   :synopsis: Set of metrics related data access operations.

.. moduleauthor:: Mark Conway-Greenslade (formerly Morgan) <momipsl@ipsl.jussieu.fr>


"""
from collections import OrderedDict

from bson.objectid import ObjectId

import utils



# Name of pymongo db in which metrics are stored.
_DB_NAME = "metrics"

# Token that mongo injected fields are preffixed with.
_MONGO_FIELD_PREFIX = "_"

# Token of object identifier that each inserted record is associated with.
_MONGO_OBJECT_ID = "_id"


def _format_group_id(group_id):
    """Returns a formatted group id."""
    return None if not group_id else group_id.strip().lower()


def _fetch(action, include_db_id=True):
    """Fetches data form db."""
    if include_db_id:
        return action(as_class=OrderedDict)
    return action({}, {'_id': 0}, as_class=OrderedDict)


def build_indexes(group_id):
    """Builds metric group db indexes.

    :param str group_id: ID of a metric group.

    """
    group_id = _format_group_id(group_id)
    collection = utils.get_db_collection(_DB_NAME, group_id)

    # TODO index factory by group id.
    indexes = [
        ("Institute", pymongo.ASCENDING),
        ("Model", pymongo.ASCENDING),
        ("Var", pymongo.ASCENDING),
        ("Freq", pymongo.ASCENDING),
    ]

    collection.create_index(indexes)


def add(group_id, metrics):
    """Persists a set of metrics to the database.

    :param str group_id: ID of the metric group being added.
    :param list metrics: Set of metric being added.

    :returns: Set of line id's of newly inserted metrics.
    :rtype: list

    """
    group_id = _format_group_id(group_id)
    collection = utils.get_db_collection(_DB_NAME, group_id)

    return collection.insert(metrics)


def delete(group_id):
    """Deletes a group of metrics.

    :param str group_id: ID of a metric group to be deleted.

    :returns: Names of remaining metric groups.
    :rtype: list

    """
    group_id = _format_group_id(group_id)
    mg_db = utils.get_db(_DB_NAME)

    mg_db.drop_collection(group_id)

    return mg_db.collection_names()[1:]


def delete_lines(group_id, line_ids):
    """Deletes a group of metrics.

    :param str group_id: ID of a metric group.
    :param list line_ids: ID's of individual lines within a metric group.

    :returns: Original and updated line counts.
    :rtype: tuple

    """
    group_id = _format_group_id(group_id)
    collection = utils.get_db_collection(_DB_NAME, group_id)

    count = collection.count()
    for line_id in line_ids:
        collection.remove({_MONGO_OBJECT_ID: ObjectId(line_id)})

    print count, collection.count()
    return count, collection.count()


def exists(group_id):
    """Returns a flag indicating whether metrics collection already exists.

    :param str group_id: ID of the metric group being added.

    :returns: True if collection exists false otherwise.
    :rtype: bool

    """
    group_id = _format_group_id(group_id)

    return group_id in fetch_list()


def fetch(group_id, include_db_id):
    """Returns a group of metrics.

    :param str group_id: ID of the metric group being returned.
    :param bool include_db_id: Flag indicating whether to include db id.

    :returns: A group of metrics.
    :rtype: dict

    """
    group_id = _format_group_id(group_id)
    collection = utils.get_db_collection(_DB_NAME, group_id)

    return list(_fetch(collection.find, include_db_id))


def fetch_columns(group_id, include_db_id):
    """Returns set of column names associated with a group of metrics.

    :param str group_id: ID of a metric group.
    :param bool include_db_id: Flag indicating whether to include db id.

    :returns: Set of column names associated with a group of metrics.
    :rtype: list

    """
    group_id = _format_group_id(group_id)
    collection = utils.get_db_collection(_DB_NAME, group_id)
    row = _fetch(collection.find_one, include_db_id)

    return row.keys() if row else []


def fetch_count(group_id):
    """Returns count of number of metrics within a group.

    :param str group_id: ID of a metric group.

    :returns: Count of number of metrics within a group.
    :rtype: int

    """
    group_id = _format_group_id(group_id)
    collection = utils.get_db_collection(_DB_NAME, group_id)

    return collection.count()


def fetch_filtered(group_id, include_db_id, filter):
    """Returns a filtered group of metrics.

    :param str group_id: ID of the metric group being returned.
    :param bool include_db_id: Flag indicating whether to include db id.
    :param dict filter: Flag indicating whether to include db id.

    :returns: A group of metrics.
    :rtype: dict

    """
    group_id = _format_group_id(group_id)
    collection = utils.get_db_collection(_DB_NAME, group_id)

    return list(_fetch(collection.find, include_db_id))


def fetch_list():
    """Returns set of groups within metrics database.

    :returns: set of groups within metrics database.
    :rtype: list

    """
    mg_db = utils.get_db(_DB_NAME)

    return mg_db.collection_names()[1:]


def fetch_setup(group_id):
    """Returns setup data associated with a group of metrics.

    The setup data is the set of unique values for each field within the metric group.

    :param str group_id: ID of a metric group.

    :returns: Setup data associated with a group of metrics.
    :rtype: dict

    """
    group_id = _format_group_id(group_id)
    collection = utils.get_db_collection(_DB_NAME, group_id)

    return [sorted(collection.distinct(c)) for c in fetch_columns(group_id, False)]