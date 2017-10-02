# pyapi.utils


<br/><a name="contents"></a>
## Contents

  * [DynamoDB Object](#dynamodb-object)



<br/><a name="dynamodb-object"></a>
## DynamoDB Object

### DynamoDB Data Type Descriptors

  DynamoDB object uses the following data type descriptors:
  * `S` - String (`str`)
  * `N` - Number (`int`, or `float` if contains '.')
  * `B` - Binary
  * `BOOL` - Boolean (`bool`)
  * `NULL` - Null (`None`)
  * `M` - Map (`dict`)
  * `L` - List (`list`)
  * `SS` - String Set (`set`)
  * `NN` - Number Set (`set`)
  * `BB` - Binary Set (`set`)

  See [Data Type Descriptors](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Programming.LowLevelAPI.html#Programming.LowLevelAPI.DataTypeDescriptors).

### DynamoDB Serializer/Deserializer

  A few options to convert between Python object and DynamoDB object:

  * boto3 types

    ```
    from boto3.dynamodb import types

    dz = types.TypeDeserializer()
    sz = types.TypeSerializer()

    python_obj = {"aList": ["0x33", "", 1, 99, {"a": ['3.1415926', 42]}]}
    dynamo_obj = sz.serialize(python_obj)

    assert python_obj == dz.deserialize(dynamo_obj)
    ```
    Note: This does not support mixed types.

  * [dynamodb-json](https://github.com/Alonreznik/dynamodb-json)

    ```
    from boto3.dynamodb import types
    from dynamodb_json import json_util as dyjson

    obj = {"nList": [3,1,4,1,5,9,2,6]}
    dyo = dyjson.dumps(obj)

    assert obj == dyjson.loads(dyo)
    ```
    Note:
    - This does not support set of numbers or strings.
    - See also
      - [dynamodb-mapper](https://pypi.org/project/dynamodb-mapper/)
      - [dynamo_objects](https://github.com/serebrov/dynamo_objects)

  * pyapi.utils.dynamodb

    ```
    from boto3.dynamodb import types
    from pyapi.utils.dynamodb import unmarshal

    obj = {"nSet": set([3,1,4,1,5,9,2,6])}
    dyo = types.TypeSerializer().serialize(obj)

    assert obj == unmarshal(dyo)
    ```



&raquo; Back to <a href="#contents">Contents</a> | <a href="../../README.md">Home</a> &laquo;
