"""
pyapi.utils.dynamodb module
"""
import boto3
import types

from functools import partial
from multiprocessing.dummy import Pool as ThreadPool
from pyapi.utils.extension import get_attr
from pyapi.utils.logger import get_logger

LOGGER = get_logger(__name__)


class DatabaseProvider(object):
    """
    A class to hold a singleton database client instance.
    """
    _db_client = None
    _db_resource = None

    @staticmethod
    def get_db_client():
        """
        Instantiates a singleton database client if one doesn't exist, the returns it.
        :return: A database client
        """
        if DatabaseProvider._db_client is None:
            DatabaseProvider._db_client = boto3.client('dynamodb')
        return DatabaseProvider._db_client

    @staticmethod
    def get_db_resource():
        """
        Instantiates a singleton database client if one doesn't exist, the returns it.
        :return: A database client
        """
        if DatabaseProvider._db_resource is None:
            DatabaseProvider._db_resource = boto3.resource('dynamodb')
        return DatabaseProvider._db_resource

    @staticmethod
    def get_table_resource(table_name):
        """
        Gets a table resource for the given table name.
        :param table_name: The name of the dynamod db table.
        :return: A table resource
        """
        return DatabaseProvider.get_db_resource().Table(table_name)


def batch_write_to_db(write_records, table_name):
    """
    Writes a batch of put records for a single dynamoDb table.
    :param write_records: A dictionary with at least a hash and/or sort key for the given table.
    :param table_name: the name of the dynamoDb table to be written to.
    :return: N/A
    """
    table = boto3.resource('dynamodb').Table(table_name)
    with table.batch_writer() as batch:
        for item in write_records:
            batch.put_item(Item=item)


def batch_delete_from_db(item_keys, table_name):
    """
    Deletes a list of items from dynamodb
    :param item_keys: A list of dictionaries that have a hash and/or sort key for the record
    :param table_name: The name of the table the deletion should happen against.
    :return: N/A
    """
    table = boto3.resource('dynamodb').Table(table_name)
    with table.batch_writer() as batch:
        for key in item_keys:
            batch.delete_item(Key=key)


def get_column_list(record, key, default=[]):
    """
    Get a list object from dynamodb record.

    @param {object} record: dynamodb record.
    @param {string} key: dynamodb column key.
    @param {list} default: default value returned if column doesn't exist
    """
    column_list = get_attr(record, *[key, 'L'])
    return default if column_list is None else column_list


def get_column_map(record, key, default={}):
    """
    Get a map object from dynamodb record.

    @param {object} record: dynamodb record.
    @param {string} key: dynamodb column key.
    @param {dictionary} default: default value returned if column doesn't exist
    """
    column_map = get_attr(record, *[key, 'M'])
    return default if column_map is None else column_map


def get_column_string_set(record, key, default=set()):
    """
    Get a string set from dynamodb record.

    @param {object} record: dynamodb record.
    @param {string} key: dynamodb column key.
    @param {list} default: default value returned if column doesn't exist
    """
    column_string_set = get_attr(record, *[key, 'SS'])
    return default if column_string_set is None else column_string_set


def unmarshal(obj):
    """
    Unmarshal a DynamoDB object to normal python JSON object.
    Supporting the following data type descriptors:
        S - String
        N - Number (int, or float if contains '.')
        B - Binary
        BOOL - Boolean (Bool)
        NULL - Null (None)
        M - Map (dict)
        L - List (list)
        SS - String Set
        NN - Number Set
        BB - Binary Set
    See
    - https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Programming.LowLevelAPI.html#Programming.LowLevelAPI.DataTypeDescriptors  # noqa
    - dynamodb-json (https://github.com/Alonreznik/dynamodb-json)

    @param obj: a DynamoDB object.
    @return: a normal Python object.
    """
    if type(obj) is not dict:
        if type(obj) is list:
            data = []
            for item in obj:
                data.append(unmarshal(item))
            return data
        if type(obj) is set:
            data = set()
            for item in obj:
                data.add(unmarshal(item))
            return data
        return obj

    result = {}
    for key, value in obj.items():
        if key == 'NULL':
            return None
        if key == 'BOOL' or key == 'S':
            return value
        if key == 'SS' and isinstance(value, list):
            return set(value)
        if key == 'NS' and isinstance(value, list):
            data = set()
            for n_item in value:
                data.add(float(n_item) if '.' in str(n_item) else int(n_item))
            return data
        if key == 'BS' and isinstance(value, list):
            data = set()
            for b_item in value:
                data.add(boto3.dynamodb.types.Binary(b_item))
            return data
        if key == 'B':
            return boto3.dynamodb.types.Binary(value)
        if key == 'N':
            return float(value) if '.' in str(value) else int(value)
        if key == 'M':
            return unmarshal(value)
        if key == 'L' and isinstance(value, list):
            data = []
            for item in value:
                data.append(unmarshal(item))
            return data

        # assuming no mixing with dynamoDB data type descriptors in a dict
        result[key] = unmarshal(value)

    return result
