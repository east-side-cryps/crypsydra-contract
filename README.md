<a name="Crypsydra"></a>
# Crypsydra

<a name="Crypsydra.newStream"></a>
#### newStream

```python
newStream() -> Dict[str, Any]
```

Create an empty stream object with the next ID in the sequence

**Returns**:

  Dict[str, Any]: Stream object

<a name="Crypsydra.loadStream"></a>
#### loadStream

```python
loadStream(stream_id: int) -> Dict[str, Any]
```

Load and deserialize a stream object from storage

**Arguments**:

- `stream_id` _int_ - Stream ID
  

**Returns**:

  Dict[str, Any]: Deserialized stream object

<a name="Crypsydra.deleteStream"></a>
#### deleteStream

```python
deleteStream(stream: Dict[str, Any])
```

Delete a stream from storage

**Arguments**:

- `stream` _Dict[str, Any]_ - Stream object

<a name="Crypsydra.saveStream"></a>
#### saveStream

```python
saveStream(stream: Dict[str, Any])
```

Save a string to storage and trigger on_create event

**Arguments**:

- `stream` _Dict[str, Any]_ - Stream object

<a name="Crypsydra.getAmountAvailableForWithdrawal"></a>
#### getAmountAvailableForWithdrawal

```python
getAmountAvailableForWithdrawal(stream: Dict[str, Any]) -> int
```

Calculate the maximum amount that can be withdrawn at this time

**Arguments**:

- `stream` _Dict[str, Any]_ - Stream object
  

**Returns**:

- `int` - amount that can be withdrawn

<a name="Crypsydra.verify"></a>
#### verify

```python
@public
verify() -> bool
```

Executed by the verification trigger when a spend transaction references
the contract as sender. Always returns false in this contract

**Returns**:

- `bool` - False

<a name="Crypsydra.getStream"></a>
#### getStream

```python
@public
getStream(stream_id: int) -> str
```

Return a stream object as JSON string

**Arguments**:

- `stream_id` _bytes_ - Stream ID
  

**Returns**:

- `str` - JSON-serialized stream object

<a name="Crypsydra.getSenderStreams"></a>
#### getSenderStreams

```python
@public
getSenderStreams(sender: str) -> str
```

Get all streams where address is sender

**Arguments**:

- `sender` _str_ - address as base64-encoded scripthash
  

**Returns**:

- `str` - JSON array of stream IDs
  
<a name="Crypsydra.getRecipientStreams"></a>
#### getRecipientStreams

```python
@public
getRecipientStreams(recipient: str) -> str
```

Get all streams where address is recipient

**Arguments**:

- `recipient` _str_ - address as base64-encoded scripthash
  

**Returns**:

- `str` - JSON array of stream IDs
  
<a name="Crypsydra.withdraw"></a>
#### withdraw

```python
@public
withdraw(stream_id: int, amount: int) -> bool
```

Withdraw funds from contract to recipient. Can be triggered by
either recipient or sender

**Arguments**:

- `stream_id` _int_ - Stream ID
- `amount` _int_ - Amount to withdraw
  

**Returns**:

- `bool` - Success or failure

<a name="Crypsydra.cancelStream"></a>
#### cancelStream

```python
@public
cancelStream(stream_id: int) -> bool
```

Cancel stream and make final disbursal of funds from contract
to recipient and remainder to sender. Can be triggered by
either recipient or sender

**Arguments**:

- `stream_id` _int_ - Stream ID
  

**Returns**:

- `bool` - Success or failure

<a name="Crypsydra.onNEP17Payment"></a>
#### onNEP17Payment

```python
@public
onNEP17Payment(t_from: UInt160, t_amount: int, data: List[Any])
```

Triggered by a payment to the contract, which creates a new stream

**Arguments**:

- `t_from` _UInt160_ - Sender of GAS
- `t_amount` _int_ - Amount of GAS sent
- `data` _List[Any]_ - Parameters for operations

