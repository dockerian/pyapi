import unittest

import boto3
from mock import MagicMock, patch
from moto import mock_dynamodb2

from pyapi.utils.extension import get_json, pickle_object
from pyapi.utils.dynamodb import DatabaseProvider, \
    get_records_by_key, \
    get_column_map, get_column_list, get_column_string_set, \
    unmarshal

from tests.test_helper_utils import \
    create_basic_table, \
    get_example_sketch_vector


class DynamoDbTests(unittest.TestCase):

    def test_get_column_list(self):
        """
        Test pyapi.utils.dynamodb.get_list
        """
        tests = [
            {
                "rec": {"a": {"L": "aaa"}, "b": "bbb"},
                "col": "a",
                "out": "aaa"
            },
            {
                "rec": {"a": {"NS": {"aa": "aaa"}}, "b": "bbb"},
                "col": "a",
                "out": []
            },
            {
                "rec": {"a": {"L": ["aa", "aaa"]}, "b": "bbb"},
                "col": "a",
                "out": ['aa', 'aaa']
            },
        ]
        for test in tests:
            result = get_column_list(test['rec'], test['col'])
            self.assertEqual(result, test['out'])
        pass

    def test_get_column_map(self):
        """
        Test pyapi.utils.dynamodb.get_map
        """
        tests = [
            {
                "rec": {"a": {"M": "aaa"}, "b": "bbb"},
                "col": "a",
                "out": "aaa"
            },
            {
                "rec": {"a": {"M": {"aa": "aaa"}}, "b": "bbb"},
                "col": "b",
                "out": {}
            },
            {
                "rec": {"a": {"M": {"aa": "aaa"}}, "b": "bbb"},
                "col": "a",
                "out": {"aa": "aaa"}
            },
        ]
        for test in tests:
            result = get_column_map(test['rec'], test['col'])
            self.assertEqual(result, test['out'])
        pass

    def test_get_column_string_set(self):
        """
        Test pyapi.utils.dynamodb.get_string_set
        """
        tests = [
            {
                "rec": {"a": {"SS": "aaa"}, "b": "bbb"},
                "col": "a",
                "out": "aaa"
            },
            {
                "rec": {"a": {"M": {"aa": "aaa"}}, "b": "bbb"},
                "col": "b",
                "out": set()
            },
            {
                "rec": {"a": {"L": ["aa", "aaa"]}, "b": "bbb"},
                "col": "a",
                "out": set()
            },
        ]
        for test in tests:
            result = get_column_string_set(test['rec'], test['col'])
            self.assertEqual(result, test['out'])
        pass

    @mock_dynamodb2
    @patch('boto3.client')
    def test_get_dynamodb_client(self, client):
        """
        test pyapi.utils.extension.get_dynamodb_client
        """
        dynamo_client = MagicMock()
        client.return_value = dynamo_client
        DatabaseProvider._db_client = None
        result = DatabaseProvider.get_db_client()
        client.assert_called_with('dynamodb')
        self.assertTrue(dynamo_client == result)
        DatabaseProvider._db_client = None

    @mock_dynamodb2
    @patch('boto3.resource')
    def test_get_dynamodb_resource(self, resource):
        """
        test pyapi.utils.extension.get_dynamodb_resource
        """
        dynamo_resource = MagicMock()
        resource.return_value = dynamo_resource
        DatabaseProvider._db_resource = None
        result = DatabaseProvider.get_db_resource()
        resource.assert_called_with('dynamodb')
        self.assertTrue(dynamo_resource == result)
        DatabaseProvider._db_resource = None

    @mock_dynamodb2
    def test_get_data_records_by_key(self):
        table_name = 'UnitTest'
        test_indicator = {
            'guid': 'deez_tests',
            'indicator': 'someIndicator.com',
            'threat_class': 'MalwareC2'
        }
        expected = [test_indicator]
        create_basic_table(table_name)
        dynamo_db_client = boto3.client('dynamodb')
        dynamo_db_client.put_item(TableName=table_name,
                                  Item={'guid': {'S': test_indicator['guid']},
                                        'indicator': {'S': test_indicator['indicator']},
                                        'threat_class': {'S': test_indicator['threat_class']}})

        actual = get_records_by_key(table_name,
                                    [{'guid': test_indicator['guid'], 'indicator': test_indicator['indicator']}])
        self.assertEqual(expected, actual)

    def test_marshal(self):
        """
        Testing utils.dynamodb.marshal function
        """
        from boto3.dynamodb import types
        blist = [
            types.Binary(b'\x03'),
            types.Binary(b'\x01'),
            types.Binary(b'\x04'),
        ]
        tests = [
            None,
            0,
            -1234567890,
            98765432101234567890,
            42,
            "",
            "abcd efghijklm\nopqrs\tuvwxyz",
            [],
            ["a", "b", "c"],
            [1, 200, 3, 400, 501, 600],
            {},
            False, True,
            {
                "aList": ["0x33", "", 1, 99, {"a": ['3.1415926', 42]}],
                "aMap": {
                    "key1": "v1",
                    "key2": "v2",
                    "key3": "v3",
                    "keys": set(["v1", "v2", "v3"]),
                    "more": {
                        "nested": {
                            "d1": ["d", "dd", "ddd"],
                            "d2": {
                                "dict": {"k1": 1, "k2": 2},
                                "list": ["k1", "k2", "k3", "k4", "k5"],
                                "nSet": set([3, 1, 4, 1, 5, 9, 2, 6]),
                                "flag": True,
                            }
                        }
                    }
                },
            },
            {
                "bList": blist,
                "bSet": set(blist),
            },
            {
                "nList": [3, 1, 4, 1, 5, 9, 2, 6],
            },
        ]

        dz = types.TypeDeserializer()
        sz = types.TypeSerializer()

        for test in tests:
            serialized = sz.serialize(test)
            result1 = dz.deserialize(serialized)
            result2 = unmarshal(serialized)
            result3 = unmarshal(test)
            msg1 = 'result1: {}'.format(get_json(pickle_object(result1)))
            msg2 = 'result2: {}'.format(get_json(pickle_object(result2)))
            msg3 = 'result3: {}'.format(get_json(pickle_object(result3)))
            self.assertEqual(result1, test, msg1)
            self.assertEqual(result2, test, msg2)
            self.assertEqual(result3, test, msg3)

    def test_marshal_mixed(self):
        """
        Testing utils.dynamodb.marshal function with mixed data type descriptors
        """
        dynamo_obj1 = {
            "Attributes": {
                "threat_class": {
                    "S": "MalwareC2DGA"
                },
                "requested": {
                    "M": {
                        "tide": {
                            "L": [
                                {
                                    "M": {
                                        "depends": {
                                            "S": "threat_score"
                                        },
                                        "required": {
                                            "BOOL": False
                                        }
                                    }
                                }
                            ]
                        },
                        "threat_score": {
                            "L": []
                        },
                        "active_dns": {
                            "L": []
                        }
                    }
                },
                "expiration_time": {
                    "N": "1540507159"
                },
                "indicator": {
                    "S": "bryanbakotich.com"
                },
                "source": {
                    "S": "bambenek_OSINT_DGA"
                },
                "threat_family": {
                    "S": "TinyBanker"
                },
                "guid": {
                    "S": "156db533b6172d7953a5a2a4eb81ee07"
                }
            }
        }
        python_obj1 = {
            "Attributes": {
                "expiration_time": 1540507159,
                "guid": "156db533b6172d7953a5a2a4eb81ee07",
                "indicator": "bryanbakotich.com",
                "requested": {
                    "active_dns": [],
                    "threat_score": [],
                    "tide": [{"depends": "threat_score", "required": False}]
                },
                "source": "bambenek_OSINT_DGA",
                "threat_class": "MalwareC2DGA",
                "threat_family": "TinyBanker",
            }
        }
        tests = [
            {"obj": dynamo_obj1, "out": python_obj1},
            {
                "obj": {"nList": [{"N": "3.1415926"}, {"N": "2.17"}]},
                "out": {"nList": [3.1415926, 2.17]},
            }
        ]

        for test in tests:
            result = unmarshal(test['obj'])
            msg = 'result: {}'.format(get_json(pickle_object(result)))
            self.assertEqual(result, test['out'], msg)
