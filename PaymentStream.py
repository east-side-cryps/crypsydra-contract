from boa3.builtin import NeoMetadata, metadata, public
from boa3.builtin.contract import Nep17TransferEvent, abort
from boa3.builtin.interop.contract import GAS, call_contract
from boa3.builtin.interop.runtime import calling_script_hash, executing_script_hash, get_time, check_witness
from boa3.builtin.interop.binary import base64_encode, base64_decode
from boa3.builtin.interop.json import json_serialize, json_deserialize
from boa3.builtin.interop.storage import get, put
from boa3.builtin.type import UInt160
from typing import Any, List, Dict, cast

@metadata
def manifest_metadata() -> NeoMetadata:
    meta = NeoMetadata()
    meta.author = "Joe Stewart"
    meta.description = "Streaming Payments"
    meta.email = "joe@coz.io"
    return meta

on_transfer = Nep17TransferEvent


def concat(a: str, b: str) -> str:
    return a + b


@public
def verify() -> bool:
    """
    Executed by the verification trigger when a spend transaction references 
    the contract as sender. Always returns false in this contract

    Returns:
        bool: False
    """    
    return False

"""
stream = {
    deposit: int,
    remaining: int,
    sender: str,
    recipient: str,
    start: int,
    stop: int
}
"""

def newStream() -> Dict[str, Any]:
    new_id = get('streams/last_id').to_int() + 1
    put('streams/last_id', new_id)
    stream = {'id': new_id}
    return stream


def loadStream(stream_id: str) -> Dict[str, Any]:
    """
    Load and deserialize a stream object from storage

    Args:
        stream_id (str): Stream ID

    Returns:
        Dict[str, Any]: Deserialized sale object
    """    
    s = get('streams/' + stream_id)
    assert len(s) > 0, 'no such stream exists'
    stream: Dict[str, Any] = json_deserialize(s)
    assert stream, 'stream deserialization failure'
    return stream

@public 
def getStream(stream_id: str) -> str:
    return get(concat('streams/', stream_id))

@public
def withdraw(stream_id: str, amount: int) -> bool:
    stream = loadStream(stream_id)
    recipient = base64_decode(cast(str,stream['recipient']))
    assert check_witness(recipient), 'recipient signature not found'

    # calculate maximum amount that can be withdrawn at this time
        
    current_time = get_time
    start_time = cast(int, stream['start'])
    stop_time = cast(int, stream['stop'])
    deposit = cast(int, stream['deposit'])
    remaining = cast(int, stream['remaining'])

    if current_time >= stop_time:
        available = remaining
    else:
        total_seconds = (stop_time - start_time) // 1000
        rate = deposit // total_seconds

        elapsed_seconds = (current_time - start_time) // 1000
        available = rate * elapsed_seconds

    assert available >= amount, 'withdrawal amount exceeds available funds'

    stream['remaining'] = remaining - amount

    call_contract(GAS, 'transfer', [executing_script_hash, recipient, amount, None])

    put(concat('streams/', cast(str, stream['id'])), json_serialize(stream))
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

            put(concat('streams/', cast(str, stream['id'])), json_serialize(stream))

            return
    abort()