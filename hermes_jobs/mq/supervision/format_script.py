# -*- coding: utf-8 -*-

"""
.. module:: supervisor_format_script.py
   :copyright: Copyright "Mar 21, 2015", Institute Pierre Simon Laplace
   :license: GPL/CeCIL
   :platform: Unix
   :synopsis: Formats supervision scripts in readiness for dispatch.

.. moduleauthor:: Mark Conway-Greenslade <momipsl@ipsl.jussieu.fr>


"""
from hermes_jobs.mq import utils
from prodiguer import mq
from prodiguer.db import pgres as db
from prodiguer.db.pgres.dao_monitoring import retrieve_job
from prodiguer.db.pgres.dao_monitoring import retrieve_latest_job_period
from prodiguer.db.pgres.dao_monitoring import retrieve_latest_job_period_counter
from prodiguer.db.pgres.dao_monitoring import retrieve_simulation
from prodiguer.db.pgres.dao_superviseur import retrieve_supervision
from prodiguer.utils import config
from prodiguer.utils import logger
from prodiguer.utils import mail
import superviseur



def get_tasks():
    """Returns set of tasks to be executed when processing a message.

    """
    return (
        _unpack_content,
        _set_data,
        _authorize,
        _verify,
        _format,
        _enqueue_script_dispatch,
        )


class ProcessingContextInfo(mq.Message):
    """Message processing context information.

    """
    def __init__(self, props, body, decode=True):
        """Object constructor.

        """
        super(ProcessingContextInfo, self).__init__(
            props, body, decode=decode)

        self.job = None
        self.job_period = None
        self.job_uid = None
        self.simulation = None
        self.supervision = None
        self.supervision_id = None
        self.script = None
        self.user = None


def _unpack_content(ctx):
    """Unpacks message being processed.

    """
    ctx.job_uid = ctx.content['job_uid']
    ctx.simulation_uid = ctx.content['simulation_uid']
    ctx.supervision_id = int(ctx.content['supervision_id'])


def _set_data(ctx):
    """Sets data also required by script formatter.

    """
    # Escape if simulation not found.
    # ... happens if 8888 message was subsequently sent.
    ctx.simulation = retrieve_simulation(ctx.simulation_uid)
    if ctx.simulation is None:
        msg = "Supervision not possible: simulation not found: sim-uid={}"
        logger.log_mq_warning(msg.format(ctx.simulation_uid))
        ctx.abort = True
        return

    # Escape if login is None.
    # ... happens in testing when 0000 message have not yet been received.
    if ctx.simulation.compute_node_login is None:
        msg = "Supervision not possible: simulation login unspecified: sim-uid={}"
        logger.log_mq_warning(msg.format(ctx.simulation_uid))
        ctx.abort = True
        return

    ctx.job = retrieve_job(ctx.job_uid)
    ctx.job_period = retrieve_latest_job_period(ctx.simulation_uid)
    ctx.job_period_counter = retrieve_latest_job_period_counter(ctx.simulation_uid)
    ctx.supervision = retrieve_supervision(ctx.supervision_id)


def _authorize(ctx):
    """Verifies that the user has authorized supervision.

    """
    try:
        ctx.user = superviseur.authorize(ctx.simulation.compute_node_login)
    except UserWarning as err:
        logger.log_mq_warning("Supervision unauthorized: {}".format(err))
        ctx.abort = True


_EMAIL_SUBJECT = u"HERMES-SUPERVISOR :: COMPUTE JOB FAILURE :: USER={}; JOB={}; MACHINE={}."

# Operator email body template.
_EMAIL_BODY = u"""Dear HERMES platform user {},

The following issue has been detected:

Machine:\t\t\t{}
Login/User:\t\t{}
Job name:\t\t{}
Job number:\t\t{}

A compute job failed within the period {} ({}-{}) for the {}{} time.  Jobs that fail more than {} times within the same output period require your attention.

Further information:

    https://hermes.ipsl.upmc.fr/static/simulation.detail.html?uid={}
    https://hermes.ipsl.upmc.fr/static/simulation.monitoring.html?login={}

Best regards,

The HERMES Platform

"""


def _get_email_subject(ctx):
    """Returns subject of email to be sent to user.

    """
    return _EMAIL_SUBJECT.format(
        ctx.user.login,
        ctx.job.scheduler_id,
        ctx.simulation.compute_node_machine_raw)


def _get_job_failure_count_suffix(count):
    count = int(count)
    if count in [1, 21, 31, 41, 51]:
        return "st"
    if count in [2, 22, 32, 42, 52]:
        return "nd"
    if count in [3, 23, 33, 43, 53]:
        return "rd"
    return "th"


def _get_email_body(ctx):
    """Returns body of email to be sent to user.

    """
    return _EMAIL_BODY.format(
        ctx.user.login,
        ctx.simulation.compute_node_machine_raw.upper(),
        ctx.user.login,
        ctx.job.scheduler_id,
        ctx.simulation.name,
        ctx.job_period.period_id,
        ctx.job_period.period_date_begin,
        ctx.job_period.period_date_end,
        ctx.job_period_counter[1],
        _get_job_failure_count_suffix(ctx.job_period_counter[1]),
        config.apps.monitoring.maxJobPeriodFailures,
        ctx.simulation.uid,
        ctx.user.login
        )


def _verify(ctx):
    """Verifies that the job formatting is required.

    """
    # Verify that most recent job period failure is within allowed limit.
    if ctx.job_period.period_id is None:
        logger.log_mq_warning("Job period empty")
    elif ctx.job_period.period_id == 1:
        logger.log_mq("Period number 1, supervision not needed")
        ctx.abort = True 
    elif ctx.job_period_counter[1] > config.apps.monitoring.maxJobPeriodFailures:
        mail.send_email(config.alerts.emailAddressFrom,
            ctx.user.email,
            _get_email_subject(ctx),
            _get_email_body(ctx))
        logger.log_mq("Too many tries for the last job period, mail sent to user and supervision abort")
        ctx.abort = True


def _format(ctx):
    """Formats the script for the job to be executed at the compute node.

    """
    # Set dispatch parameters to be passed to dispatcher.
    params = superviseur.FormatParameters(
        ctx.simulation,
        ctx.job,
        ctx.job_period,
        ctx.supervision,
        ctx.user
        )

    # Format script to be dispatched to HPC for execution.
    try:
        ctx.supervision.script = superviseur.format_script(params)
    # ... handle formatting errors
    # TODO define error strategy
    except:
        ctx.abort = True
    else:
        db.session.commit()


def _enqueue_script_dispatch(ctx):
    """Enqueues a script dispatch messages.

    """
    utils.enqueue(mq.constants.MESSAGE_TYPE_8200, {
        "supervision_id": ctx.supervision_id
    })
