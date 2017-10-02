"""
# extension module

@author: Jason Zhu <jason.zhuyx@gmail.com>
@created: 2017-02-20

"""

import hashlib
import json
import jsonpickle
import os
import pytz

class DictEncoder(json.JSONEncoder):
    """
    Default encoder for json.dumps
    """
    def default(self, obj):
        """default encoder"""
        return obj.__dict__


class JsonEncoder(json.JSONEncoder):
    """
    Default encoder for python set. Example: json.dumps(obj, cls=JsonEncoder)
    """
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return obj.__dict__


def byteify(data, ignore_dicts=False):
    """
    Return byteified data
    """
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [byteify(item, ignore_dicts=True) for item in data]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            byteify(key, ignore_dicts=True): byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data


def check_duplicate_key(pairs):
    """
    Check duplicate key in pairs
    """
    result = dict()
    for key, val in pairs:
        if key in result:
            raise KeyError("Duplicate key specified: %s" % key)
        result[key] = val
    return result


# noinspection PyTypeChecker
def check_valid_md5(data):
    """
    Check if input data is a valid md5 hash string

    Note: some other regular expressions -
        r"\b[a-f\d]{32}\b|\b[A-F\d]{32}\b"
        r"(?i)(?<![a-z0-9])[a-f0-9]{32}(?![a-z0-9])"
    """
    if not isinstance(data, basestring):
        return False
    reiter = re.finditer(r"\b(?!^[\d]*$)(?!^[a-fA-F]*$)([a-f\d]{32}|[A-F\d]{32})\b", data)
    result = [match.group(1) for match in reiter]
    return True if result else False


def get_attr(obj, *args):
    """
    Get nested attributes
    """
    data = None
    if obj:
        data = obj
        try:
            for key in args:
                if isinstance(key, basestring):
                    data = data.get(key, None)
                elif isinstance(key, int) and isinstance(data, list):
                    data = data[key] if len(data) >= (key - 1) else None
                else:
                    data = None  # bad key type
                if not data:
                    return None
        except:
            return None
    return data


def get_camel_title_word(target_str, keep_capitals=True):
    """
    Get camel title (each word starts with upper case letter)
    Note:
        Use `keep_capitals=False` converting "One USA" to "OneUsa"
    """
    str_words = re.sub(r'[^\w\s]', ' ', str(target_str)).replace('_', ' ')
    if keep_capitals:
        str_words = ' '.join(
            w if w.isupper() else w.title() for w in str_words.split())
    else:
        str_words = ' '.join(
            w if len(w) == 1 else w.capitalize() for w in str_words.split())
    return str_words.replace(' ', '')


def get_hash(string_input="", salt="", hash_type="sha256"):
    """
    Get hash for @string_input, with @salt, by one of following hash types
        md5, sha1, sha256, sha512, or <file> (using sha256 for <file>)
    """
    if not isinstance(string_input, basestring) or \
       not isinstance(salt, basestring) or not string_input:
        return ""

    hash_default = hashlib.sha256
    hash_methods = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hash_default,
        "sha512": hashlib.sha512,
        "<file>": hash_default,
    }
    hash_func = hash_methods.get(str(hash_type).lower(), hash_default)
    file_path = string_input
    file_size = 0

    data = string_input
    if hash_type == "<file>":
        data = ""
        try:
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                if file_size >= 1024 * 1024 * 1024:  # in bytes
                    with open(file_path, 'rb') as srcfile:
                        for chunk in iter(lambda: srcfile.read(4096), b""):
                            hash_func().update(chunk)
                    result = hash_func().hexdigest()
                    return result
                elif file_size > 0:
                    with open(file_path, 'rb') as srcfile:
                        data = srcfile.read()
        except Exception as ex:
            print "Error: {}".format(ex)
            return ""

    return hash_func(salt + data).hexdigest() if data else ""


def get_json(obj, indent=4):
    """
    Get formatted JSON dump string
    """
    return json.dumps(obj, sort_keys=True, indent=indent)


def get_list_subsets(object_list, subset_size):
    """
    Breaks a larger list apart into a list of smaller subsets.
    :param object_list: The initial list to be broken up
    :param subset_size: The maximum size of the smaller subsets
    :return: A list of subsets whose size are equal to subset_size. The last subset may be smaller if the object list
    doesn't divide evenly.
    """
    total_objects = len(object_list)
    total_subsets = total_objects/subset_size if total_objects % subset_size == 0 else (total_objects/subset_size) + 1
    subsets = []
    for subset in range(0, total_subsets):
        if subset == total_subsets - 1:
            subsets.append(object_list[subset_size * subset:])
        else:
            subsets.append(object_list[subset_size * subset:subset_size * (subset + 1)])
    return subsets


def pickle_object(obj, *rm_keys):
    """
    Convert an object to serialized JSON object
    """
    json_obj = json.loads(jsonpickle.encode(obj))

    for key in rm_keys:
        try:
            json_obj.pop(key, None)
        except AttributeError:
            # This just catches for all exceptions for the empty host samples portion
            pass

    return json_obj


def pickle_to_str(obj, *rm_keys):
    """
    Convert an object to JSON string of serialized JSON object
    """
    json_obj = pickle_object(obj, *rm_keys)

    return json.dumps(json_obj)
