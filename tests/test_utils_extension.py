# -*- coding: utf-8 -*-
"""
# test_utils_extension

@author: Jason Zhu <jason.zhuyx@gmail.com>
@created: 2017-02-22

"""
import json
import os
import pytz
import unittest

from mock import Mock, MagicMock, patch, mock_open

from pyapi.utils.extension import DateTimeUtc
from pyapi.utils.extension import DictEncoder, JsonEncoder
from pyapi.utils.extension import byteify
from pyapi.utils.extension import get_attr
from pyapi.utils.extension import get_hash
from pyapi.utils.extension import get_json
from pyapi.utils.extension import get_list_subsets
from pyapi.utils.extension import pickle_object
from pyapi.utils.extension import pickle_to_str

from logging import getLogger
LOGGER = getLogger(__name__)


class DateTimeUtcTest():
    """
    DateTimeUtcTest includes all unit tests for DateTimeUtc
    """

    def test_DateTimeUtc(self):
        """
        test pyapi.utils.extension.DateTimeUtc
        """
        dt = DateTimeUtc()
        self.assertEqual(dt.tzinfo, pytz.utc)


class EncodeTest(object):
    """class EncodeTest to test DictEncoder and pickle_object"""
    def __init__(self):
        """constructor for EncodeTest"""
        self.name = 'pickle class name'
        self.dump = 'dump property'
        self.test = 'pickle test'


class ExtensionTests(unittest.TestCase):
    """ExtensionTests
    ExtensionTests includes all unit tests for extension module
    """
    def setUp(self):
        self.hash_file = "cyberint_hash.json"
        self.test_path = os.path.dirname(os.path.realpath(__file__))
        self.proj_path = os.path.dirname(self.test_path)
        self.repo_path = os.path.dirname(self.proj_path)
        self.util_path = os.path.join(self.proj_path, "utils")
        self.hash_path = os.path.join(self.util_path, self.hash_file)
        self.mswb_path = os.path.join(self.repo_path, "database/catelog.mwb")
        self.salt = "363ccea406657ce5280662fad028772bbc88d9545e209f21093462c95af544c3"
        with open(self.hash_path, 'rb') as f:
            self.hash_data = json.loads(f.read())
        pass

    def tearDown(self):
        pass

    def test_DictEncoder(self):
        """
        test pyapi.utils.extension.DictEncoder
        """
        import json
        test = EncodeTest()
        expected = """
        {"test": "pickle test", "name": "pickle class name", "dump": "dump property"}
        """.strip()
        result = json.dumps(test, cls=DictEncoder)
        self.assertEqual(result, expected)

    def test_byteify(self):
        """
        test pyapi.utils.extension.byteify
        """
        # coding: utf8
        std_in = "中国"
        output = byteify(std_in)
        self.assertEqual(output, "\xe4\xb8\xad\xe5\x9b\xbd")

        json_text = '''{
            "a": "aaa",
            "dict": {"dev": "good", "test": "pass", "prod": "好"},
            "list": ["中国", "USA"]
        }'''
        expected = '''{
    "a": "aaa",
    "dict": {
        "test": "pass",
        "prod": "\\u597d",
        "dev": "good"
    },
    "list": [
        "\\u4e2d\\u56fd",
        "USA"
    ]\n}'''
        json_obj = json.loads(json_text)
        dump_txt = json.dumps(json_obj, indent=4).replace(", ", ",")
        self.assertNotEqual(dump_txt, expected)
        json_obj = json.loads(json_text, object_hook=byteify)
        dump_txt = json.dumps(json_obj, indent=4).replace(", ", ",")
        self.assertEqual(dump_txt, expected)

    def test_check_duplicate_key(self):
        """
        test pyapi.utils.extension.check_duplicate_key
        """
        tests = [
            {
                "input": [("a", "aaa"), ("a", "aa"), ("b", "bbb")],
                "result": None,
                "error": True
            }, {
                "input": [("a", "aaa"), ("a2", "aa"), ("b", "bb")],
                "result": {"a": "aaa", "a2": "aa", "b": "bb"},
                "error": False
            },
        ]
        for test in tests:
            result = None
            if test["error"]:
                with self.assertRaises(KeyError) as context:
                    result = check_duplicate_key(test["input"])
                    msg = "{}".format(context.exception)
                    self.assertTrue(
                        "Duplicate key specified: " in context.exception, msg)
            else:
                result = check_duplicate_key(test["input"])
            self.assertEqual(result, test["result"])

    def test_check_valid_md5(self):
        """
        test pyapi.utils.extension.check_valid_md5
        """
        tests = [
            {"input": "-this is not a valid md5 at all-", "expected": False},
            {"input": "00000000000000000000000000000000", "expected": False},
            {"input": "01110101001110011101011010101001", "expected": False},
            {"input": "ffffffffffffffffffffffffffffffff", "expected": False},
            {"input": "A32efC32c79823a2123AA8cbDDd3231c", "expected": False},
            {"input": "affa687a87f8abe90d9b9eba09bdbacb", "expected": True},
            {"input": "C787AFE9D9E86A6A6C78ACE99CA778EE", "expected": True},
        ]
        for test in tests:
            result = check_valid_md5(test['input'])
            self.assertEqual(result, test['expected'])

    def test_dict_encoder(self):
        """
        test pyapi.utils.extension.DictEncoder
        """
        test = EncodeTest()
        expected = """
        {"test": "pickle test", "name": "pickle class name", "dump": "dump property"}
        """.strip()
        result = json.dumps(test, cls=DictEncoder)
        self.assertEqual(result, expected)

    def test_json_encoder(self):
        """
        test pyapi.utils.extension.DictEncoder
        """
        class JsonEncoderTest(object):
            def __init__(self):
                self.age = 33
                self.name = "Test Name"
                self.ns = set([3, 1, 4])
                self.ss = set(["x", "y", "z"])
                print "\n"
                pass

        tests = [
            {
                "obj": JsonEncoderTest(),
                "out": """
                {"age": 33, "name": "Test Name", "ns": [3, 1, 4], "ss": ["y", "x", "z"]}
                       """.strip()
            },
            {
                "obj": {"x": "xyz", "a": "abc", "n": [3, 1, 4], "none": None},
                "out": '{"a": "abc", "n": [3, 1, 4], "none": null, "x": "xyz"}',
            },
            {
                "obj": None,
                "out": 'null',
            },
        ]
        for test in tests:
            result = json.dumps(test["obj"], cls=JsonEncoder, sort_keys=True)
        self.assertEqual(result, test["out"])

    def test_get_attr(self):
        """
        test pyapi.utils.extension.get_attr
        """
        aaa = ['a', 'aa', 'aaa']
        obj = [
            {
                'list': [{'a': 1}, {'b': 2}, {'c': {'c1': 31, 'c2': 32}}],
                'test': {'x': 100, 'y': 200, 'z': 'zzz'},
                'okey': True,
            }
        ]
        self.assertEqual(get_attr(obj, *[0, 'list', 0, 'a']), 1)
        self.assertEqual(get_attr(obj, *[0, 'list', 2, 'c', 'c2']), 32)
        self.assertEqual(get_attr(obj, *[0, 'list', 2, 'd']), None)
        self.assertEqual(get_attr(obj, *[0, 'test', 'x']), 100)
        self.assertEqual(get_attr(obj, *[1, 'list']), None)
        self.assertEqual(get_attr(obj, *['foo']), None)
        self.assertEqual(get_attr(obj, *[aaa]), None)
        self.assertEqual(get_attr(aaa, *[3]), None)

    def test_get_camel_title_word(self):
        """
        test pyapi.utils.extension.get_camel_title_word
        """
        tests = [
            {'input': 'This is a test', 'output': 'ThisIsATest'},
            {'input': 'yet another test', 'output': 'YetAnotherTest'},
            {'input': 'N0Needchange', 'output': 'N0Needchange'},
            {'input': 'MalWare C2', 'output': 'MalwareC2'},
            {'input': 'MalWare_C2', 'output': 'MalwareC2'},
            {'input': 'MalWare_C2_DGA', 'output': 'MalwareC2DGA'},
            {'input': 'Malware-c2', 'output': 'MalwareC2'},
            {'input': 'Some.Thing.Complete?!', 'output': 'SomeThingComplete'},
            {'input': 'Exploit_KIT', 'output': 'ExploitKIT'},
            {'input': 'It\'s good', 'output': 'ItSGood'},
            {'input': 'Born in the USA', 'output': 'BornInTheUSA'},
            {'input': '', 'output': ''},
        ]
        for test in tests:
            expected = test['output']
            result = get_camel_title_word(test['input'])
            self.assertEqual(result, expected)

        tests = [
            {'input': 'It\'s good', 'output': 'ItsGood'},
            {'input': 'Yet Another TEST', 'output': 'YetAnotherTest'},
            {'input': 'M&M in CAPITALIZED', 'output': 'MMInCapitalized'},
            {'input': '', 'output': ''},
        ]
        for test in tests:
            expected = test['output']
            result = get_camel_title_word(test['input'], False)
            self.assertEqual(result, expected)

    def test_get_hash(self):
        """
        test pyapi.utils.extension.get_hash
        """
        for key in self.hash_data:
            result = get_hash(key, self.salt)
            expected = self.hash_data[key]
            msg = "key '{}' hash should be '{}' [not '{}']".format(
                key, expected, result)
            self.assertEqual(result, expected, msg)

    def test_get_hash_from_file(self):
        """
        test pyapi.utils.extension.get_hash from file
        """
        result = get_hash(self.mswb_path, "", "<file>")
        self.assertNotEqual(result, "")

    def test_get_hash_from_large_file(self):
        """
        test pyapi.utils.extension.get_hash from large file
        """
        orig_func = os.path.getsize
        os.path.getsize = MagicMock(return_value=3*1024*1024*1024)
        result = get_hash(self.mswb_path, "", "<file>")
        os.path.getsize = orig_func
        self.assertNotEqual(result, "")

    def test_get_hash_on_exception(self):
        """
        test pyapi.utils.extension.get_hash on exception
        """
        orig_func = os.path.getsize
        os.path.getsize = MagicMock(side_effect=Exception('x', 'msg'))
        result = get_hash("non-exist/path/file", "", "<file>")
        result = get_hash(self.mswb_path, "", "<file>")
        os.path.getsize = orig_func
        self.assertEqual(result, "")

    def test_get_json(self):
        """
        test pyapi.utils.extension.get_json
        """
        tests = [
            {
                "obj": {'a': ['a1', 'a2'], 'b': {'b1': 'b', 'b2': 'bb'}},
                "out": '{\n"a": [\n"a1", \n"a2"\n], \n"b": {\n"b1": "b", \n"b2": "bb"\n}\n}'
            }
        ]
        for test in tests:
            result = get_json(test['obj'], indent=0)
            self.assertEqual(result, test['out'])

    def test_list_subsets(self):
        test_list = [num for num in range(0, 102)]
        subset_list = get_list_subsets(test_list, 25)
        self.assertIn(test_list[0:25], subset_list)
        self.assertIn(test_list[25:50], subset_list)
        self.assertIn(test_list[50:75], subset_list)
        self.assertIn(test_list[75:100], subset_list)
        self.assertIn(test_list[100:], subset_list)

    def test_pickle_object(self):
        """
        test pyapi.utils.extension.pickle_object
        """
        test = EncodeTest()
        result = pickle_object(test, 'dump')
        class_name = 'tests.test_utils_extension.EncodeTest'
        self.assertEqual(test.dump, 'dump property')
        self.assertTrue(result.get('py/object').endswith(class_name))
        self.assertIsNone(result.get('dump'))

    def test_pickle_to_str(self):
        """
        test pyapi.utils.extension.pickle_to_str
        """
        obj = EncodeTest()
        tests = [
            [],
            ['dump', 'test', 'py/object'],
            ['dump'],
        ]
        expected = [{
            "py/object": "pyapi.tests.test_utils_extension.EncodeTest",
            "name": obj.name,
            "dump": obj.dump,
            "test": obj.test,
        }, {
            "name": obj.name,
        }, {
            "py/object": "pyapi.tests.test_utils_extension.EncodeTest",
            "name": obj.name,
            "test": obj.test,
        }]
        # for i in xrange(len(tests)):
        #     result = pickle_to_str(obj, *tests[i])
        #     self.assertEqual(result, json.dumps(expected[i]))
        for i, test in enumerate(tests):
            result = pickle_to_str(obj, *test)
            self.assertEqual(result, json.dumps(expected[i]))
