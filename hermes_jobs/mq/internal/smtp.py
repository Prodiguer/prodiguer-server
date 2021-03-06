# -*- coding: utf-8 -*-

"""
.. module:: smtp.py
   :copyright: Copyright "Mar 21, 2015", Institute Pierre Simon Laplace
   :license: GPL/CeCIL
   :platform: Unix
   :synopsis: Enqueues messages embedded in enqueued emails received from libIGCM.

.. moduleauthor:: Mark Conway-Greenslade <momipsl@ipsl.jussieu.fr>


"""
import base64
import copy
import json
import uuid

from hermes import config
from hermes import mq
from hermes.db import pgres as db
from hermes.utils import logger
from hermes.utils import mail



def get_tasks():
    """Returns set of tasks to be executed when processing a message.

    """
    return (
        _set_email,
        _set_msg_b64,
        _set_msg_json,
        _set_msg_dict,
        _drop_excluded_messages,
        _drop_incorrelateable_messages,
        _process_attachments,
        _set_msg_ampq,
        _enqueue_messages,
        _log_stats,
        _log_incorrelateable,
        _persist_stats,
        _dequeue_email,
        _close_imap_client
        )


def get_error_tasks():
    """Returns set of tasks to be executed when a message processing error occurs.

    """
    return _close_imap_client


class ProcessingContextInfo(mq.Message):
    """Message processing context information.

    """
    def __init__(self, props, body, decode=True, validate_props=True):
        """Object constructor.

        """
        super(ProcessingContextInfo, self).__init__(props, body, decode=decode, validate_props=validate_props)

        self.email = None
        self.email_attachments = None
        self.email_body = None
        self.email_uid = self.content['email_uid']
        self.email_rejected = False
        self.email_server_id = self.content['email_server_id']
        self.imap_client = None
        self.msg_ampq = []
        self.msg_ampq_error = []
        self.msg_b64 = []
        self.msg_json = []
        self.msg_json_error = []
        self.msg_dict = []
        self.msg_dict_error = []
        self.msg_dict_excluded = []
        self.msg_dict_incorrelateable = []


def _set_email(ctx):
    """Set email to be processed.

    """
    # Point to email server.
    mail.set_server(ctx.email_server_id)

    # Connect to imap server.
    ctx.imap_client = mail.connect()

    # Download & decode email.
    body, attachments = mail.get_email(ctx.email_uid, ctx.imap_client)
    ctx.email = body.get_payload(decode=True)
    ctx.email_body = body
    ctx.email_attachments = [a.get_payload(decode=True) for a in attachments]


def _set_msg_b64(ctx):
    """Sets base64 encoded messages to be processed.

    """
    ctx.msg_b64 += [l for l in ctx.email.splitlines() if l]


def _set_msg_json(ctx):
    """Set json encoded messages to be processed.

    """
    for msg in ctx.msg_b64:
        try:
            ctx.msg_json.append(base64.b64decode(msg))
        except:
            ctx.msg_json_error.append(msg)


def _set_msg_dict(ctx):
    """Set dictionary encoded messages to be processed.

    """
    for msg in ctx.msg_json:
        try:
            ctx.msg_dict.append(json.loads(msg))
        except:
            try:
                msg = msg.replace('\\', '')
                ctx.msg_dict.append(json.loads(msg))
            except:
                ctx.msg_dict_error.append(msg)


def _drop_excluded_messages(ctx):
    """Drops messages that are excluded due to their type.

    """
    def _is_excluded(msg):
        """Determines whether the message is deemed to be excluded.

        """
        return 'msgProducerVersion' not in msg or \
               msg['msgCode'] in config.mq.excludedTypes

    ctx.msg_dict_excluded = [m for m in ctx.msg_dict if _is_excluded(m)]
    ctx.msg_dict = [m for m in ctx.msg_dict if m not in ctx.msg_dict_excluded]


def _drop_incorrelateable_messages(ctx):
    """Drops messages that are excluded as they cannot be correlated to a simulation.

    """
    for msg in ctx.msg_dict:
        if msg.get('simuid') is not None:
            try:
                uuid.UUID(msg.get('simuid'))
            except ValueError:
                ctx.msg_dict_incorrelateable.append(msg)
    ctx.msg_dict = [m for m in ctx.msg_dict if m not in ctx.msg_dict_incorrelateable]


def _process_attachments_0000(ctx):
    """Processes email attachments for message type 0000.

    """
    msg = ctx.msg_dict[0]
    msg['configuration'] = ctx.email_attachments[0]


def _process_attachments_7010(ctx):
    """Processes email attachments for message type 7010.

    """
    data = ctx.email_attachments[0]
    data = base64.encodestring(data)
    msg = ctx.msg_dict[0]
    msg['data'] = data


def _process_attachments_7100(ctx):
    """Processes email attachments for message type 7100.

    """
    msg = ctx.msg_dict[0]
    ctx.msg_dict = []
    for attachment in ctx.email_attachments:
        new_msg = copy.deepcopy(msg)
        new_msg['msgUID'] = unicode(uuid.uuid4())
        new_msg['metrics'] = base64.encodestring(attachment)
        ctx.msg_dict.append(new_msg)


# Map of attachment handlers to message types.
_ATTACHMENT_HANDLERS = {
    '0000': _process_attachments_0000,
    '7010': _process_attachments_7010,
    '7100': _process_attachments_7100
}


def _process_attachments(ctx):
    """Processes an email attchment.

    """
    # Escape if attachment is not associated with a single message.
    if len(ctx.msg_dict) != 1:
        return

    # Escape if message type is not mapped to a handler.
    msg = ctx.msg_dict[0]
    msg_code = msg['msgCode']
    if msg_code not in _ATTACHMENT_HANDLERS:
        return

    # Escape if there are no attachments to process.
    if not ctx.email_attachments:
        msg = "Message type {} email has no attachments and therefore cannot be processed.".format(msg['msgCode'])
        logger.log_mq_error(msg)
        ctx.email_rejected = True
        return

    # Invoke handler.
    _ATTACHMENT_HANDLERS[msg_code](ctx)


def _set_msg_ampq(ctx):
    """Set AMPQ messages to be dispatched.

    """
    if ctx.email_rejected:
        return

    for msg in ctx.msg_dict:
        try:
            props = _get_ampq_props(ctx, msg)
            payload = _get_ampq_payload(msg)
            msg_ampq = mq.Message(props, payload)
        except Exception as err:
            ctx.msg_ampq_error.append((msg, err))
        else:
            ctx.msg_ampq.append(msg_ampq)


def _get_ampq_props(ctx, msg):
    """Returns an AMPQ basic properties instance, i.e. message header.

    """
    # Decode nano-second precise message timestamp.
    _, ts_utc, ts_int, _ = mq.get_timestamps(msg['msgTimestamp'])

    return mq.utils.create_ampq_message_properties(
        user_id=mq.constants.USER_HERMES,
        producer_id=msg['msgProducer'],
        producer_version=msg['msgProducerVersion'],
        message_id=msg['msgUID'],
        message_type=msg['msgCode'],
        timestamp=ts_int,
        headers={
            'timestamp': unicode(ts_utc.isoformat()),
            'timestamp_raw': unicode(msg['msgTimestamp']),
            'correlation_id_1': msg.get('simuid'),
            'correlation_id_2': None if msg.get('jobuid') in (None, "N/A") else msg.get('jobuid'),
            'email_id': ctx.email_uid
        })


def _get_ampq_payload(obj):
    """Return ampq message payload by stripping out non-platform platform attributes.

    """
    return {k: v for k, v in obj.iteritems() if not k.startswith("msg")}


def _enqueue_messages(ctx):
    """Enqueues messages upon MQ server.

    """
    # Escape if email rejected.
    if ctx.email_rejected:
        return

    mq.produce(ctx.msg_ampq, connection_url=config.mq.connections.main)


def _dequeue_email(ctx):
    """Removes email from mailbox after processing.

    """
    # TODO - get email server configuration
    if mail.SERVER.deleteProcessed:
        mail.delete_email(ctx.email_uid, client=ctx.imap_client)
    elif ctx.email_rejected:
        mail.move_email(ctx.email_uid,
                        client=ctx.imap_client,
                        folder=mail.SERVER.mailbox_rejected)
    else:
        mail.move_email(ctx.email_uid, client=ctx.imap_client)


def _close_imap_client(ctx):
    """Closes imap client after use.

    """
    try:
        mail.disconnect(ctx.imap_client)
    except:
        logger.log_mq_warning("IMAP server disconnection error, error was discarded.")


def _log_stats(ctx):
    """Logs processing statistics.

    """
    # Escape if email rejected.
    if ctx.email_rejected:
        return

    msg = "Email uid: {};  ".format(ctx.email_uid)
    msg += "Incoming: {};  ".format(len(ctx.msg_b64))
    if ctx.msg_json_error:
        msg += "Base64 decoding errors: {};  ".format(len(ctx.msg_json_error))
    if ctx.msg_dict_error:
        msg += "JSON encoding errors: {};  ".format(len(ctx.msg_dict_error))
    if ctx.msg_ampq_error:
        msg += "AMPQ encoding errors: {};  ".format(len(ctx.msg_ampq_error))
    if ctx.msg_dict_excluded:
        msg += "Type Exclusions: {};  ".format(len(ctx.msg_dict_excluded))
    msg += "Outgoing: {}.".format(len(ctx.msg_ampq))

    logger.log_mq(msg)


def _log_incorrelateable(ctx):
    """Logs incorrelateable messages.

    """
    err = "Message cannot be correlated to a simulation: type={}, uid={}"
    for m in ctx.msg_dict_incorrelateable:
        logger.log_mq_warning(err.format(m['msgCode'], m['msgUID']))


def _persist_stats(ctx):
    """Persists processing statistics.

    """
    def _get_date(func):
        """Returns a date field from the email headers.

        """
        # N.B. override errors as email headers can be inconsistent.
        try:
            return func(ctx.email_body).datetime
        except Exception as err:
            # logger.log_mq_warning("Email date decoding error: {}.".format(err))
            return None


    def _get_outgoing_message_count(type_id):
        """Returns count of messages dispatched to MQ server.

        """
        return len([m for m in ctx.msg_ampq if m.props.type == type_id])


    db.dao_mq.persist_message_email_stats(
        ctx.email_server_id,
        ctx.email_uid,
        ctx.email_rejected,
        arrival_date=_get_date(mail.get_email_arrival_date),
        dispatch_date=_get_date(mail.get_email_dispatch_date),
        incoming=len(ctx.msg_b64),
        errors_decoding_base64=len(ctx.msg_json_error),
        errors_decoding_json=len(ctx.msg_dict_error),
        errors_encoding_ampq=len(ctx.msg_ampq_error),
        excluded=len(ctx.msg_dict_excluded),
        outgoing=len(ctx.msg_ampq),
        outgoing_0000=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_0000),
        outgoing_0100=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_0100),
        outgoing_1000=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_1000),
        outgoing_1001=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_1001),
        outgoing_1100=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_1100),
        outgoing_1900=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_1900),
        outgoing_1999=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_1999),
        outgoing_2000=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_2000),
        outgoing_2100=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_2100),
        outgoing_2900=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_2900),
        outgoing_2999=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_2999),
        outgoing_7000=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_7000),
        outgoing_7010=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_7010),
        outgoing_7011=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_7011),
        outgoing_7100=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_7100),
        outgoing_8888=_get_outgoing_message_count(mq.constants.MESSAGE_TYPE_8888)
        )
