"""
# s3_storage module includes storage interface implementation for s3

@author: Jason Zhu <jason.zhuyx@gmail.com>
@created: 2017-09-01
"""
from pyapi.utils import s3


class S3Storage(object):
    """
    class S3Storage implements a storage interface for AWS S3 per bucket
    """
    def __init__(self, bucket):
        """
        Initializes a S3Storage per specified @bucket
        """
        self.bucket = bucket
        pass

    def create(self, key_path, content=''):
        """
        Create an s3 key per @key_path with specified @content.
        Note: any existing key_path will be overwritten.
        """
        return s3.create_key(content, key_path, bucket=self.bucket)

    def delete(self, key_path):
        """
        Delete an s3 key per specified @key_path
        """
        return s3.delete_key(key_path, bucket=self.bucket)

    def exists(self, key_path):
        """
        Check if specified s3 @key_path exists. Return True or False.
        """
        return s3.check_key(key_path, bucket=self.bucket)

    def get_content(self, key_path):
        """
        Get the content (string) per specified s3 @key_path
        """
        return s3.get_content(key_path, bucket=self.bucket)

    def get_json_data(self, key_path):
        """
        Get JSON data (object) from specified s3 @key_path
        """
        return s3.get_json_data(key_path, bucket=self.bucket)

    def get_last_modified(self, key_path):
        """
        Get the last modified (offset-aware datetime) per specified s3 @key_path
        """
        s3_obj = s3.get_key(key_path, bucket=self.bucket)
        return None if s3_obj is None else s3_obj.last_modified

    def get_parquet_content(self, key_path):
        """
        Get parquet data content (string) from specified s3 @key_path
        """
        return s3.get_parquet_data(key_path, bucket=self.bucket)

    def move(self, source_name, target_name):
        """
        Move an s3 key from @source_name to @target_name
        """
        return s3.mv_key(source_name, target_name, bucket=self.bucket)

    def process(self, a_func, prefix, **kwargs):
        """
        Process all s3 keys with @prefix by @a_func (function pointer)
        """
        return s3.process_keys(a_func, prefix=prefix, **kwargs)

    def save(self, key_path, content=''):
        """
        Save @content (string) to an s3 @key_path.
        Note: any existing key_path will be overwritten.
        """
        return s3.copy_contents_to_bucket(content, key_path, bucket=self.bucket)
