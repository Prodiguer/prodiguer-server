# -*- coding: utf-8 -*-

"""
.. module:: monitoring_job_start.py
   :copyright: Copyright "Apr 26, 2013", Institute Pierre Simon Laplace
   :license: GPL/CeCIL
   :platform: Unix
   :synopsis: Consumes monitoring job start messages.

.. moduleauthor:: Mark Conway-Greenslade <momipsl@ipsl.jussieu.fr>


"""
import datetime

import arrow
from prodiguer import cv
from prodiguer import mq
from prodiguer.db import pgres as db
from prodiguer.utils import config
from prodiguer.utils import logger
from prodiguer_jobs.mq import utils



# Map of job types to warning delay message types.
_WARNING_DELAY_MESSAGE_TYPES = {
    cv.constants.JOB_TYPE_COMPUTING: mq.constants.MESSAGE_TYPE_1199,
    cv.constants.JOB_TYPE_POST_PROCESSING: mq.constants.MESSAGE_TYPE_2199,
    cv.constants.JOB_TYPE_POST_PROCESSING_FROM_CHECKER: mq.constants.MESSAGE_TYPE_3199
}

# Map of message to job types.
_MESSAGE_JOB_TYPES = {
    mq.constants.MESSAGE_TYPE_0000: cv.constants.JOB_TYPE_COMPUTING,
    mq.constants.MESSAGE_TYPE_1000: cv.constants.JOB_TYPE_COMPUTING,
    mq.constants.MESSAGE_TYPE_2000: cv.constants.JOB_TYPE_POST_PROCESSING,
    mq.constants.MESSAGE_TYPE_3000: cv.constants.JOB_TYPE_POST_PROCESSING_FROM_CHECKER
}


def get_tasks():
    """Returns set of tasks to be executed when processing a message.

    """
    return [
        _drop_obsoletes,
        unpack_message_content,
        persist_job,
        _persist_simulation_updates,
        enqueue_job_warning_delay,
        _enqueue_front_end_notification
    ]


class ProcessingContextInfo(mq.Message):
    """Message processing context information.

    """
    def __init__(self, props, body, decode=True):
        """Object constructor.

        """
        super(ProcessingContextInfo, self).__init__(
            props, body, decode=decode)

        self.job = None
        self.job_accounting_project = None
        self.job_is_startup = self.props.type == mq.constants.MESSAGE_TYPE_0000
        self.job_pp_name = None
        self.job_pp_date = None
        self.job_pp_dimension = None
        self.job_pp_component = None
        self.job_pp_file = None
        self.job_simulation_uid = None
        self.job_type = _MESSAGE_JOB_TYPES[self.props.type]
        self.job_uid = None
        self.job_warning_delay = None


def _drop_obsoletes(ctx):
    """Drops messages considered obsolete.

    """
    # If the field 'command' exists then this was
    # from a version of libIGCM now considered obsolete.
    if "command" in ctx.content:
        ctx.abort = True


def unpack_message_content(ctx):
    """Unpacks message being processed.

    """
    ctx.job_accounting_project = ctx.content.get('accountingProject')
    ctx.job_pp_name = ctx.content.get('postProcessingName')
    ctx.job_pp_date = ctx.content.get('postProcessingDate')
    ctx.job_pp_dimension = ctx.content.get('postProcessingDimn')
    ctx.job_pp_component = ctx.content.get('postProcessingComp')
    ctx.job_pp_file = ctx.content.get('postProcessingFile')
    ctx.job_simulation_uid = ctx.content['simuid']
    ctx.job_uid = ctx.content['jobuid']
    ctx.job_warning_delay = ctx.content.get(
        'jobWarningDelay', config.apps.monitoring.defaultJobWarningDelayInSeconds)


def persist_job(ctx):
    """Persists job info to db.

    """
    ctx.job = db.dao_monitoring.persist_job_01(
        ctx.job_accounting_project,
        ctx.job_warning_delay,
        ctx.msg.timestamp,
        ctx.job_type,
        ctx.job_uid,
        ctx.job_simulation_uid,
        is_startup=ctx.job_is_startup,
        post_processing_name=ctx.job_pp_name,
        post_processing_date=ctx.job_pp_date,
        post_processing_dimension=ctx.job_pp_dimension,
        post_processing_component=ctx.job_pp_component,
        post_processing_file=ctx.job_pp_file
        )


def _persist_simulation_updates(ctx):
    """Updates simulation (compute jobs only)

    """
    # Skip if not processing a compute job.
    if ctx.job_type != cv.constants.JOB_TYPE_COMPUTING:
        return

    # Ensure simulation is not considered to be in an error state.
    db.dao_monitoring.persist_simulation_02(
        None,
        False,
        ctx.job_simulation_uid
        )


def enqueue_job_warning_delay(ctx):
    """Places a delayed message indicating the amount of time
    before the job is considered to be late.

    """
    # Calculate expected job completion moment.
    expected = arrow.get(ctx.job.execution_start_date) + \
               datetime.timedelta(seconds=ctx.job.warning_delay)

    # Calculate time delta until system must check if job is late or not. 
    now = arrow.get()
    delta_in_s = int((expected - now).total_seconds())
    if delta_in_s < 0:
        delta_in_s = 0
    delta_in_ms = (delta_in_s + 1) * 1000
    logger.log_mq("Enqueuing job late warning message with delay = {}".format(delta_in_ms))

    # Enqueue.
    utils.enqueue(
        _WARNING_DELAY_MESSAGE_TYPES[ctx.job_type],
        # delay_in_ms=delta_in_ms,
        delay_in_ms=5000,
        payload={
            "job_uid": ctx.job_uid,
            "simulation_uid": ctx.job_simulation_uid
        }
    )


def _enqueue_front_end_notification(ctx):
    """Places a message upon the front-end notification queue.

    """
    # Skip if simulation start (0000) message not received.
    simulation = db.dao_monitoring.retrieve_simulation(ctx.job_simulation_uid)
    if simulation is None:
        return

    # Skip if simulation is obsolete (i.e. it was restarted).
    if simulation.is_obsolete:
        return

    utils.enqueue(mq.constants.MESSAGE_TYPE_FE, {
        "event_type": u"job_start",
        "job_uid": unicode(ctx.job_uid),
        "simulation_uid": unicode(ctx.job_simulation_uid)
        })