"""
# aws module includes functions for aws
"""
# External libraries
import boto3

from pyapi.config import settings
from pyapi.utils import logger

LOGGER = logger.get_logger(__name__)


def get_s3_client():
    """
    Get S3 client
    note: This function can be customized to accept configurations
    """
    return boto3.session.Session().client('s3')


def get_s3_object_resource(bucket_name, key):
    """
    Get S3 Bucket resource
    note: This function can be customized to accept configurations
    """
    return boto3.resource('s3').Object(bucket_name, key)


def get_sns_client():
    """
    Retrieves SNS client.
    :return: The SNS client
    """
    session = boto3.Session()
    sns_client = session.client('sns')
    return sns_client


def raise_alarm(msg, subject):
    """
    raise alarm
    """
    LOGGER.info("***Sounding the Alarm!***\n" + msg)
    sns_client = get_sns_client()
    response = sns_client.publish(
        TopicArn=settings('sns.topic_arn'),
        Message=msg,
        Subject=subject
    )
    try:
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200, \
            "ERROR Publishing to sns failed!"
    except KeyError:
        LOGGER.error("Error: Response did not contain HTTPStatusCode\n")
        LOGGER.error(response)
