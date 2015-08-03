# -*- coding: utf-8 -*-

"""
.. module:: prodiguer.db.dao.py
   :platform: Unix
   :synopsis: Set of core data access operations.

.. moduleauthor:: Mark Conway-Greenslade <momipsl@ipsl.jussieu.fr>


"""
import random

from prodiguer.db.pgres import session
from prodiguer.db.pgres import validator
from prodiguer.db.pgres import validator_dao as my_validator
from prodiguer.utils import decorators




@decorators.validate(my_validator.validate_delete)
def delete(entity):
    """Marks entity instance for deletion.

    :param db.Entity item: A supported entity instance.

    """
    session.delete(entity)


@decorators.validate(my_validator.validate_delete_all)
def delete_all(etype):
    """Deletes all entities of passed type.

    :param class etype: A supported entity type.

    """
    delete_by_facet(etype)


@decorators.validate(my_validator.validate_delete_by_facet)
def delete_by_facet(etype, filter_expression=None):
    """Delete entity instance by id.

    :param class etype: A supported entity type.
    :param expression filter_expression: Facet filter expression.

    """
    validator.validate_entity_type(etype)

    qry = session.query(etype)
    if filter_expression:
        qry = qry.filter(filter_expression)
    qry.delete()


@decorators.validate(my_validator.validate_delete_by_id)
def delete_by_id(etype, entity_id):
    """Delete entity instance by id.

    :param class etype: A supported entity type.
    :param int entity_id: id of entity.

    """
    delete_by_facet(etype, etype.id==entity_id)


@decorators.validate(my_validator.validate_delete_by_name)
def delete_by_name(etype, entity_name):
    """Deletes an entity instance by it's name.

    :param class etype: A supported entity type.
    :param unicode entity_name: Name of entity.

    """
    delete_by_facet(etype, etype.name==entity_name)


@decorators.validate(my_validator.validate_exec_query)
def exec_query(etype, qry, get_iterable=False):
    """Executes a query and return result (sorted if is a collection).

    :param class etype: A supported entity type.
    :param expression qry: A SqlAlchemy query expression.
    :param bool get_iterable: Flag indicating whether to return an iterable or not.

    :returns: Entity or entity collection.
    :rtype: Sub-class of db.Entity

    """
    return sort(etype, qry.all()) if get_iterable else qry.first()


@decorators.validate(my_validator.validate_get_all)
def get_all(etype):
    """Gets all instances of the entity.

    :param class etype: A supported entity type.

    :returns: Entity collection.
    :rtype: list

    """
    return get_by_facet(etype, order_by=etype.id, get_iterable=True)


@decorators.validate(my_validator.validate_get_by_facet)
def get_by_facet(etype, qfilter=None, order_by=None, get_iterable=False):
    """Gets entity instance by facet.

    :param class etype: A supported entity type.
    :param expression qfilter: Query filter expression.
    :param expression order_by: Sort expression.
    :param bool get_iterable: Flag indicating whether to return an iterable or not.

    :returns: Entity or entity collection.
    :rtype: Sub-class of db.Entity

    """
    qry = session.query(etype)
    if qfilter is not None:
        qry = qry.filter(qfilter)
    if order_by is not None:
        qry = qry.order_by(order_by)

    return exec_query(etype, qry, get_iterable)


@decorators.validate(my_validator.validate_get_by_id)
def get_by_id(etype, entity_id):
    """Gets entity instance by id.

    :param class etype: A supported entity type.
    :param int entity_id: An entity identifier.

    :returns: Entity with matching id.
    :rtype: Sub-class of db.Entity

    """
    return get_by_facet(etype, qfilter=etype.id==entity_id)


@decorators.validate(my_validator.validate_get_by_name)
def get_by_name(etype, entity_name):
    """Gets an entity instance by it's name.

    :param class etype: A supported entity type.
    :param unicode entity_name: Name of entity.

    :returns: Entity with matching name.
    :rtype: Sub-class of db.Entity

    """
    return get_by_facet(etype, qfilter=etype.name==entity_name)


@decorators.validate(my_validator.validate_get_count)
def get_count(etype, qfilter=None):
    """Gets count of entity instances.

    :param class etype: A supported entity type.
    :param expression qfilter: Query filter expression.

    :returns: Entity collection count.
    :rtype: int

    """
    validator.validate_entity_type(etype)

    qry = session.query(etype)
    if qfilter is not None:
        qry = qry.filter(qfilter)

    return qry.count()


@decorators.validate(my_validator.validate_exec_query)
def get_random(etype):
    """Returns a random instance.

    :param class etype: Type of instance to be returned.

    :returns: A random item from the cache.
    :rtype: Sub-class of db.Entity

    """
    collection = get_all(etype)
    if len(collection):
        return collection[random.randint(0, len(collection) - 1)]


@decorators.validate(my_validator.validate_get_random_sample)
def get_random_sample(etype):
    """Returns a random instance sample.

    :param class etype: Type of instances to be returned.

    :returns: A random sample from the db.
    :rtype: list

    """
    collection = get_all(etype)
    if len(collection):
        return random.sample(collection, random.randint(1, len(collection)))

    return []


@decorators.validate(my_validator.validate_insert)
def insert(entity):
    """Adds a newly created model to the session.

    :param db.Entity item: A supported entity instance.

    """
    session.add(entity)

    return entity


@decorators.validate(my_validator.validate_sort)
def sort(etype, collection):
    """Sorts collection via type sort key.

    :param class etype: A supported entity type.
    :param iterable collection: Collection of entities.

    :returns: Sorted collection.
    :rtype: list

    """
    return [] if collection is None else etype.get_sorted(collection)