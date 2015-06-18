# -*- coding: utf-8 -*-

"""
.. module:: prodiguer.db.mongo.utils.py
   :platform: Unix
   :synopsis: Set of mongo db related utilty functions.

.. moduleauthor:: Mark Conway-Greenslade <momipsl@ipsl.jussieu.fr>


"""
import pymongo

from prodiguer.utils import config



def get_client():
    """Returns a mongo db server connection.

    :returns: Pymongo connection to MongoDB server.
    :rtype: pymongo.MongoClient

    """
    print config.db.mongodb.main
    return pymongo.MongoClient(config.db.mongodb.main)


def get_db(db_name):
    """Returns a pointer to a db.

    :param str db_name: Name of database to connect to.

    :returns: Pymongo pointer to MongoDB database.
    :rtype: pymongo.database.Database

    """
    client = get_client()

    return client[db_name]


def get_db_collection(db_name, collection_name):
    """Returns a pointer to a db collection.

    :param str db_name: Name of database to connect to.
    :param str collection_name: Name of collection to return a pointer to.

    :returns: Pymongo pointer to MongoDB collection.
    :rtype: pymongo.collection.Collection

    """
    db = get_db(db_name)

    return db[collection_name]
