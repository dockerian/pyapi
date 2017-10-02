"""
# test_utils_aws

@author: Jason Zhu <jason.zhuyx@gmail.com>
"""
import boto3
import json
import unittest

from pyapi.utils.aws import print_bucket_size, get_sns_client, raise_alarm
from pyapi.config import settings
from pyapi.utils.extension import pickle_to_str
from mock import MagicMock, patch


class TestAwsUtils(unittest.TestCase):
    """
    TestAwsUtils includes all unit tests for pyapi.utils.aws module
    """
    def setUp(self):
        self.example_message = "TESTING PLEASE IGNORE"
        self.example_subject = "TESTING PLEASE IGNORE"

    def tearDown(self):
        pass

    @patch('pyapi.utils.aws.boto3')
    def test_print_bucket_size(self, mock_boto3):
        """
        test pyapi.utils.aws.print_bucket_size
        """
        all_buckets = {
            "Buckets": [
                {"Name": "bucket_0"},
                {"Name": "bucket_1"},
                {"Name": "bucket_2"},
                {"Name": "bucket_3"},
            ]
        }
        stats = {
            "Datapoints": [
                {"Average": 0},
                {"Average": 11},
                {"Average": 202},
                {"Average": 3003},
                {"Average": 40004},
                {"Average": 500005},
            ]
        }
        mock_client = MagicMock()
        mock_client.get_metric_statistics.return_value = stats
        mock_client.list_buckets.return_value = all_buckets
        mock_boto3.client.return_value = mock_client

        result = print_bucket_size()
        expected = len(all_buckets["Buckets"]) \
            * sum(a["Average"] for a in stats["Datapoints"])
        self.assertEqual(result, expected)

    @patch('pyapi.utils.aws.boto3')
    def test_sns_client(self, mock_boto3_session):
        expected_result = "I'm a client!"
        mock_session = MagicMock()
        mock_session.client.return_value = expected_result
        mock_boto3_session.Session.return_value = mock_session
        returned_result = get_sns_client()
        # Test the sns client
        self.assertEqual(expected_result, returned_result)
        mock_session.client.assert_called_once_with('sns')

    @patch('pyapi.utils.aws.get_sns_client')
    def test_raise_alarm(self, mock_get_sns_client):
        expected_response = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_sns_client = MagicMock()
        mock_sns_client.publish.return_value = expected_response
        mock_get_sns_client.return_value = mock_sns_client
        raise_alarm(self.example_message, self.example_subject)

        # Test with successful publish
        mock_sns_client.publish.assert_called_once_with(
            TopicArn=settings('sns.topic_arn'),
            Message=self.example_message,
            Subject=self.example_subject)
        mock_sns_client.reset_mock()
        expected_response = {"It's over 9000!": 9001}
        mock_sns_client.publish.return_value = expected_response
        raise_alarm(self.example_message, self.example_subject)
        # Test with unsuccessful publish
        mock_sns_client.publish.assert_called_once_with(
            TopicArn=settings('sns.topic_arn'),
            Message=self.example_message,
            Subject=self.example_subject)

        mock_sns_client.reset_mock()
        expected_response = {
            'ResponseMetadata': {
                'RetryAttempts': 0, 'HTTPStatusCode': 400,
                'RequestId': '37e288bd-24bd-5cb0-98f3-d94dda3e7306',
                'HTTPHeaders': {
                  'x-amzn-requestid': '37e288bd-24bd-5cb0-98f3-d94dda3e7306',
                  'date': 'Tue, 25 Jul 2017 08:07:30 GMT',
                  'content-length': '294', 'content-type': 'text/xml'}},
             u'MessageId': '5706ed1d-3e52-5061-a2b5-bcedc0d10fd7'}
        mock_sns_client.publish.return_value = expected_response
        # Test for key error
        self.assertRaises(AssertionError, raise_alarm,
                          self.example_message, self.example_subject)
        mock_sns_client.publish.assert_called_once_with(
            TopicArn=settings('sns.topic_arn'),
            Message=self.example_message,
            Subject=self.example_subject)
