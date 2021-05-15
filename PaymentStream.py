from boa3.builtin import NeoMetadata, metadata, public, CreateNewEvent
from boa3.builtin.contract import Nep17TransferEvent, abort
from boa3.builtin.interop.contract import GAS, call_contract
from boa3.builtin.interop.iterator import Iterator
from boa3.builtin.interop.runtime import calling_script_hash, executing_script_hash, get_time, check_witness
from boa3.builtin.interop.binary import base64_encode, base64_decode
from boa3.builtin.interop.json import json_serialize, json_deserialize
from boa3.builtin.interop.storage import get, put, delete, find
from boa3.builtin.type import UInt160
from typing import Any, List, Dict, cast

@metadata
def manifest_metadata() -> NeoMetadata:
    meta = NeoMetadata()
    meta.author = "Joe Stewart"
    meta.description = "Streaming Payments"
    meta.email = "joe@coz.io"
    return meta

# structure of stream object
"""
stream = {
    id: int,
    deposit: int,
    remaining: int,
    sender: str,
    recipient: str,
    start: int,
    stop: int
}
"""

# Events
on_transfer = Nep17TransferEvent

on_create = CreateNewEvent(
    [
        ('stream', str),
    ],
    'StreamCreated'
)

on_complete = CreateNewEvent(
    [
        ('stream_id', int),
    ],
    'StreamCompleted'
)

on_cancel = CreateNewEvent(
    [
        ('stream_id', int),
    ],
    'StreamCanceled'
)
on_withdraw = CreateNewEvent(
    [
        ('stream_id', int),
        ('requester', str),
        ('amount', int),
    ],
    'Withdraw'
)

# private functions

def newStream() -> Dict[str, Any]:
    """
    Create an empty stream object with the next ID in the sequence

    Returns:
        Dict[str, Any]: Stream object
    """    
    new_id = get('streams/last_id').to_int() + 1
    put('streams/last_id', new_id)
    stream = {'id': new_id}
    return stream


def loadStream(stream_id: int) -> Dict[str, Any]:
    """
    Load and deserialize a stream object from storage

    Args:
        stream_id (int): Stream ID

    Returns:
        Dict[str, Any]: Deserialized stream object
    """    
    s = get(b'streams/' + stream_id.to_bytes())
    assert len(s) > 0, 'no such stream exists'
    stream: Dict[str, Any] = json_deserialize(s)
    assert stream, 'stream deserialization failure'
    return stream


def deleteStream(stream: Dict[str, Any]):
    """
    Delete a stream from storage

    Args:
        stream (Dict[str, Any]): Stream object
    """    
    b_id = cast(bytes, stream['id'])

    delete(b'streams/' + b_id)

    sender_key = cast(bytes, stream['sender']) + b':' + b_id
    recipient_key = cast(bytes, stream['recipient']) + b':' + b_id

    delete(b'bysender/' + sender_key)
    delete(b'byrecipient/' + recipient_key)


def saveStream(stream: Dict[str, Any]):
    """
    Save a string to storage and trigger on_create event

    Args:
        stream (Dict[str, Any]): Stream object
    """    
    b_id = cast(bytes, stream['id'])
    i_id = cast(int, stream['id'])
    sender_key = cast(bytes, stream['sender']) + b':' + b_id
    recipient_key = cast(bytes, stream['recipient']) + b':' + b_id

    stream_json = cast(str, json_serialize(stream))

    put(b'streams/' + b_id, stream_json)
    put(b'bysender/' + sender_key, i_id)
    put(b'byrecipient/' + recipient_key, i_id)

    on_create(stream_json)


def getAmountAvailableForWithdrawal(stream: Dict[str, Any]) -> int:
    """
    Calculate the maximum amount that can be withdrawn at this time

    Args:
        stream (Dict[str, Any]): Stream object

    Returns:
        int: amount that can be withdrawn
    """    
    current_time = get_time
    start_time = cast(int, stream['start'])
    stop_time = cast(int, stream['stop'])
    deposit = cast(int, stream['deposit'])
    remaining = cast(int, stream['remaining'])

    if current_time >= stop_time:
        return remaining
    else:
        total_seconds = (stop_time - start_time) // 1000
        rate = deposit // total_seconds

        elapsed_seconds = (current_time - start_time) // 1000
        return rate * elapsed_seconds

# public functions

@public
def verify() -> bool:
    """
    Executed by the verification trigger when a spend transaction references 
    the contract as sender. Always returns false in this contract

    Returns:
        bool: False
    """    
    return False


@public 
def getStream(stream_id: int) -> str:
    """
    Return a stream object as JSON string

    Args:
        stream_id (bytes): Stream ID

    Returns:
        str: JSON-serialized stream object
    """    
    return cast(str, get(b'streams/' + stream_id.to_bytes()))


@public
def getSenderStreams(sender: str) -> Iterator:
    """
    Get all streams where address is sender

    Args:
        sender (str): address as base64-encoded scripthash

    Returns:
        int: Stream ID

    Yields:
        Iterator: Stream IDs
    """    
    return find('bysender/' + sender)


@public
def getRecipientStreams(recipient: str) -> Iterator:
    """
    Get all streams where address is recipient

    Args:
        recipient (str): address as base64-encoded scripthash

    Returns:
        int: Stream ID

    Yields:
        Iterator: Stream IDs
    """    
    return find('byrecipient/' + recipient)


@public
def withdraw(stream_id: int, amount: int) -> bool:
    """
    Withdraw funds from contract to recipient. Can be triggered by
    either recipient or sender

    Args:
        stream_id (int): Stream ID
        amount (int): Amount to withdraw

    Returns:
        bool: Success or failure
    """    
    stream = loadStream(stream_id)
    recipient = base64_decode(cast(str,stream['recipient']))
    sender = base64_decode(cast(str, stream['sender']))
    if check_witness(recipient):
        print("Recipient requesting withdrawal")
        requester = stream['recipient']
    elif check_witness(sender):
        # TODO: should sender be able to request an advance to recipient?
        print("Sender requesting withdrawal to recipient")
        requester = stream['sender']
    else:
        print("Must be sender or recipient to withdraw")
        abort()

    remaining = cast(int, stream['remaining'])
    available = getAmountAvailableForWithdrawal(stream)

    assert available >= amount, 'withdrawal amount exceeds available funds'

    stream['remaining'] = remaining - amount

    call_contract(GAS, 'transfer', [executing_script_hash, recipient, amount, None])

    if cast(int, stream['remaining']) == 0:
        deleteStream(stream)
        on_complete(cast(int, stream['id']))
    else:
        put(b'streams/' + cast(bytes, stream['id']), json_serialize(stream))

    on_withdraw(cast(int, stream['id']), cast(str, requester), amount)
    return True


@public
def cancelStream(stream_id: int) -> bool:
    """
    Cancel stream and make final disbursal of funds from contract
    to recipient and remainder to sender. Can be triggered by
    either recipient or sender

    Args:
        stream_id (int): Stream ID

    Returns:
        bool: Success or failure
    """    
    stream = loadStream(stream_id)
    recipient = base64_decode(cast(str,stream['recipient']))
    sender = base64_decode(cast(str, stream['sender']))
    if check_witness(recipient):
        print("Recipient requesting cancellation of stream")
    elif check_witness(sender):
        print("Sender requesting cancellation of stream")
    else:
        print("Must be sender or recipient to cancel stream")
        abort()

    available = getAmountAvailableForWithdrawal(stream)
    remaining = cast(int, stream['remaining']) - available

    call_contract(GAS, 'transfer', [executing_script_hash, recipient, available, None])
    call_contract(GAS, 'transfer', [executing_script_hash, sender, remaining, None])

    deleteStream(stream)
    on_cancel(cast(int, stream['id']))

    return True


@public
def onNEP17Payment(t_from: UInt160, t_amount: int, data: List[Any]):
    """
    Triggered by a payment to the contract, which creates a new stream

    Args:
        t_from (UInt160): Sender of GAS
        t_amount (int): Amount of GAS sent
        data (List[Any]): Parameters for operations
    """    
    if calling_script_hash == GAS:
        assert len(t_from) == 20, 'invalid address'
        assert t_amount > 0, 'no funds transferred'

        p_len = len(data)
        assert p_len > 1, 'incorrect data length'

        p_operation = cast(str, data[0])

        if p_operation == 'createStream':
            assert p_len == 4, 'incorrect arguments to createStream'
            recipient = cast(bytes, data[1])
            start_time = cast(int, data[2])
            stop_time = cast(int, data[3])

            current_time = get_time

            assert len(recipient) == 20, 'invalid recipient scripthash'
            assert start_time >= current_time, 'start time cannot be in the past'
            assert stop_time > start_time, 'stop time must be greater than start time'

            stream = newStream()

            stream['start'] = start_time
            stream['stop'] = stop_time
            stream['deposit'] = t_amount
            stream['remaining'] = t_amount
            stream['sender'] =  base64_encode(t_from)
            stream['recipient'] = base64_encode(recipient)

            saveStream(stream)
            return
    abort()