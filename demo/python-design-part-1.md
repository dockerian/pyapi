# Python class vs module

  * [Python class mechanism](#class)
  * [Python module](#module)
  * [Summary](#summary)

> In object-oriented programming design, using class module is one solution to
  have dependencies injected and encapsulated in constructor (class initialization)
  with all public methods defining/implementing clear interfaces (contract).
  Although <a target="\_link" href="https://www.python.org/">Python</a> is
  not a typical OO language (nor a preference many developers using that way),
  it has <code>class</code> mechanism to accomplish such task.
  Let's take a first look on python <a target="\_link" href="https://docs.python.org/2/tutorial/classes.html">class</a>.

<br/><a name="class"></a>
## 1. Python class mechanism

  The following demo is to write a <a target="\_link" href="http://docs.openstack.org/developer/python-swiftclient/swiftclient.html">swiftclient</a> wrapper to access object store on <a target="\_link" href="https://en.wikipedia.org/wiki/OpenStack">OpenStack</a> (cloud computing platform). Since swift client API methods requires certain dependencies (e.g. auth token, swift URL, and container name), it would be nice to wrap them in a class object instead of calling API methods with these in parameters. For example, ideal coding in application domain should look like this -


  ```python
  from keystone import get_auth_token
  from swift import get_swift, Swift

  # Use built-in swift_class module to get an instance of Swift
  swift = get_swift()

  # Otherwise, if dependencies (e.g. swift_url and container_name) in app domain
  auth_token = get_auth_token()
  swift = Swift(auth_token, swift_url, container_name)

  # Once we have a Swift instance ...
  afile = swift.get_file_contents('foo.txt')
  files = swift.get_files_in_container()

  ```

  Notice that if application settings need to be separated from swift module (most likely in a large-scale project), the class instantiation will be in application domain (where e.g. settings belong to); otherwise, the swift module could have a <code>get_swift()</code> function to construct a swift instance (like in this demo). The class module and unit tests are listed as below.

  <a name="swift"></a>
  See <code>common/swift.py</code> (<code>Swift</code> class) -

  ```python
  # swift.py (Swift class)
  import logging
  import mimetypes
  import sys

  from swiftclient import client as swift_client
  from swiftclient.exceptions import ClientException
  from keystone import get_auth_token
  from config import settings

  logger = logging.getLogger(__name__)


  # ================================================
  # Swift instance initialization
  # ================================================
  def get_swift():
      """
      Get a Swift instance per application settings
      """
      auth_token = get_auth_token()
      container = settings('swift_container')
      swift_url = settings('swift_url')
      swift = Swift(auth_token, swift_url, container)
      return swift


  # ================================================
  # Swift class
  # ================================================
  class Swift(object):
      def __init__(self, auth_token, swift_url, container_name):
          """
          Initialize a Swift instance
          """
          self.auth_token = auth_token
          self.swift_url = swift_url
          self.container = container_name
          self.connection = self._get_connection()

      def _get_connection(self):
          try:
              return swift_client.Connection(
                  preauthurl=self.swift_url,
                  preauthtoken=self.auth_token,
                  retries=5,
                  auth_version='1',
                  insecure=True)
          except Exception as e:
              err_message = "Exception raised initiating a swift connection."
              logger.exception(err_message)
              raise

      def check_container(self):
          """
          Determine if default container missing in Swift
          """
          try:
              headers, container_list = self.connection.get_account()
              for container in container_list:
                  if container['name'] == self.container:
                      return True
              return False
          except Exception as e:
              err_message = "Exception raised on checking container exists."
              logger.exception(err_message)
              raise

      def ensure_container_exists(self):
          """
          Ensure default container exists in Swift.
          """
          # Determine if necessary container missing; if so, create it
          container_exists = self.check_container()
          if (not container_exists):
              try:
                  response = {}
                  self.connection.put_container(
                      self.container, response_dict=response)
              except Exception as e:
                  err = "Exception on creating container {0}.".format(
                      self.container)
                  logger.exception(err)
                  raise

      def get_file_contents(self, file_name):
          """
          Function wrapper to perform 'get_object' call on Swift
          """
          try:
              response_dict = {}
              # Response from Swift:
              #     a tuple of (response headers, the object contents)
              #     The response headers will be a dict and all header names
              #     will be lowercase.
              response = self.connection.get_object(
                  self.container,
                  file_name,
                  response_dict=response_dict)
              file_contents = response[1]
              return file_contents
          except Exception as e:
              err = "Exception on getting {0} from Swift.".format(file_name)
              logger.exception(err)
              raise

      def get_files_in_container(self):
          result = self.connection.get_container(
              self.container, full_listing=True)
          return result[1]

      def save_file(self, file_name, file_contents):
          """
          Function wrapper to perform 'put_object' call Swift
          """
          try:
              self.ensure_container_exists()
              response = {}
              # Example of response from put_object call -
              # {
              #     'status': 201,
              #     'headers': {
              #         'content-length': '0',
              #         'last-modified': 'Fri, 17 Jul 2015 04:43:56 GMT',
              #         'connection': 'keep-alive',
              #         'etag': 'd41d8cd98f00b204e9800998ecf8427e',
              #         'x-trans-id': 'txeddbca07d8e744deae343-0055a8880c',
              #         'date': 'Fri, 17 Jul 2015 04:43:57 GMT',
              #         'content-type': 'text/html; charset=UTF-8'},
              #     'reason': 'Created',
              #     'response_dicts': [{
              #         'status': 201,
              #         'headers': {
              #             'content-length': '0',
              #             'last-modified':
              #             'Fri, 17 Jul 2015 04:43:56 GMT',
              #             'connection': 'keep-alive',
              #             'etag': 'd41d8cd98f00b204e9800998ecf8427e',
              #             'x-trans-id': 'txeddbca07d8e744deae343-0055a8880c',
              #             'date': 'Fri, 17 Jul 2015 04:43:57 GMT',
              #             'content-type': 'text/html; charset=UTF-8'},
              #             'reason': 'Created'}]}
              self.connection.put_object(
                  self.container,
                  file_name,
                  file_contents,
                  content_length=sys.getsizeof(file_contents),
                  content_type=mimetypes.guess_type(file_name, strict=True)[0],
                  response_dict=response)
              return response
          except Exception as e:
              err_message = "Exception on saving file contents to Swift.\n"
              logger.exception(err_message)
              raise

  ```

  <a name="swift_tests"></a>
  See <code>common/tests/swift_tests.py</code> (Unit tests for <code>Swift</code> class) -

  ```python
  # swift_tests.py
  import logging
  import mock
  import os
  import StringIO
  import sys
  import tarfile
  import unittest

  from pyramid import testing
  from mock import Mock, MagicMock, patch, mock_open
  from swiftclient.exceptions import ClientException

  from swift import Swift
  logger = logging.getLogger(__name__)


  class SwiftClassTests(unittest.TestCase):
      @patch('swiftclient.client.Connection')
      def setUp(self, mock_connection):
          self.config = testing.setUp()
          self.auth_token = Mock()
          self.account_data = ([{}], [{'name': 'container1'}])
          self.container = 'container1'
          self.container_data = ([{}], [{'name': 'file1'}, {'name': 'file2'}])
          self.swift_url = 'http://0.0.0.0'
          self.connection = Mock()
          # patch('common.swift.Swift.get_connection',
          #       return_value=self.connection
          mock_connection.return_value = self.connection
          self.swift = Swift(
              self.auth_token, self.swift_url, self.container)

      def tearDown(self):
          testing.tearDown()

      @patch('swiftclient.client.Connection')
      def test_constructor(self, mock_connection):
          self.assertEqual(self.swift.auth_token, self.auth_token)
          self.assertEqual(self.swift.swift_url, self.swift_url)
          self.assertEqual(self.swift.connection, self.connection)
          self.assertEqual(self.swift.container, self.container)

      @patch('swiftclient.client.Connection')
      def test_connection_exception(self, mock_connection):
          error_message = 'CONNECTION ERROR'
          mock_connection.side_effect = Exception(error_message)
          with self.assertRaises(Exception) as cm:
              result = Swift(self.auth_token, self.swift_url, self.container)
              self.assertEqual(str(cm.exception), error_message)

      def test_check_container_exception(self):
          name = 'foo'
          error_message = 'PUT CONTAINER ERROR'
          self.swift.connection.get_account.side_effect \
              = Exception(error_message)
          with self.assertRaises(Exception) as cm:
              result = self.swift.check_container()
              self.assertEqual(str(cm.exception), error_message)
              self.assertFalse(result)

      def test_check_container_when_false(self):
          self.swift.connection.get_account.return_value = self.account_data
          self.swift.container = 'dummy'
          result = self.swift.check_container()
          self.assertFalse(result)

      def test_check_container_when_true(self):
          self.swift.connection.get_account.return_value = self.account_data
          result = self.swift.check_container()
          self.assertTrue(result)

      def test_check_file_exists(self):
          self.swift.check_container = MagicMock()
          self.swift.check_container.return_value = True
          self.swift.connection.get_container = MagicMock()
          self.swift.connection.get_container.return_value = self.container_data
          result = self.swift.check_file_exists('fileX')
          self.assertFalse(result)
          result = self.swift.check_file_exists('file1')
          self.assertTrue(result)

      def test_check_file_exists_no_container(self):
          self.swift.check_container = MagicMock()
          self.swift.check_container.return_value = False
          result = self.swift.check_file_exists('filename')
          self.assertFalse(result)

      def test_ensure_container_exists(self):
          success = {'status': 200}

          def mock_put_success(container_name, response_dict):
              logger.debug(
                  'Called with {0} {1}'.format(container_name, response_dict))
              response_dict['status'] = success['status']

          with patch.object(
                  self.swift.connection, 'get_account',
                  return_value=self.account_data):
              with patch.object(
                      self.swift.connection, 'put_container',
                      side_effect=mock_put_success) as mocked_put:
                  self.swift.ensure_container_exists()
                  mocked_put.assert_called()

      def test_ensure_container_exists_exception(self):
          error_message = 'PUT CONTAINER ERROR'

          with patch.object(
                  self.swift.connection, 'get_account',
                  return_value=self.account_data):
              with patch.object(
                      self.swift.connection, 'put_container',
                      side_effect=Exception(error_message)) as mocked_put:
                  self.swift.check_container = MagicMock()
                  self.swift.check_container.return_value = False
                  with self.assertRaises(Exception) as cm:
                      self.swift.ensure_container_exists()
                      self.assertEqual(str(cm.exception), error_message)

      def test_get_file_contents(self):
          response = ([{}], '_filecontents')
          self.swift.connection.get_object = MagicMock()
          self.swift.connection.get_object.return_value = response
          result = self.swift.get_file_contents('file_name')
          self.assertEqual(result, response[1])

      def test_get_file_contents_exeption(self):
          error_message = 'Exception on get object'
          self.swift.connection.get_object = MagicMock()
          self.swift.connection.get_object.side_effect = Exception(error_message)
          with self.assertRaises(Exception) as cm:
              result = self.swift.get_file_contents('file_name')
              self.assertEqual(str(cm.exception), error_message)

      def test_get_files_in_container(self):
          self.swift.connection.get_container = MagicMock()
          self.swift.connection.get_container.return_value = self.container_data
          result = self.swift.get_files_in_container()
          self.assertEqual(result, self.container_data[1])

      @patch('mimetypes.guess_type')
      @patch('sys.getsizeof')
      def test_save_file_contents(self, mock_getsizeof, mock_guess_type):
          success = {'status': 200}

          def mock_put_success(
                  container_name, file_name, contents,
                  content_length, content_type, response_dict):
              response_dict['status'] = success['status']

          file_name = 'filename'
          contents = MagicMock()
          mock_getsizeof.return_value = 999
          mock_guess_type.return_value = ['filetype']
          with mock.patch.object(
                  self.swift.connection, 'put_object',
                  side_effect=mock_put_success) as mocked_put:
              self.swift.check_container = MagicMock()
              self.swift.check_container.return_value = True
              self.swift.save_file_contents(file_name, contents)
              mocked_put.assert_called_with(
                  self.container,
                  file_name, contents,
                  content_length=999, content_type='filetype',
                  response_dict=success)

      @patch('mimetypes.guess_type')
      @patch('sys.getsizeof')
      def test_save_file_contents_Exception(
              self, mock_getsizeof, mock_guess_type):
          file_name = 'filename'
          contents = MagicMock()
          mock_getsizeof.return_value = 999
          mock_guess_type.return_value = ['filetype']
          error_message = "SWIFT PUT OBJECT ERROR"
          self.swift.connection.put_object.side_effect = Exception(error_message)
          self.swift.check_container = MagicMock()
          self.swift.check_container.return_value = False
          with self.assertRaises(Exception) as cm:
              self.swift.save_file_contents(file_name, contents)
              self.assertEqual(str(cm.exception), error_message)

  ```

<br/><a name="module"></a>
## 2. Python module

  In use of Python class mechanism (as in above example), it takes a couple steps (of initialization, if no <a target="\_link" href="https://en.wikipedia.org/wiki/Dependency_injection">dependency injection</a> used) before all class methods are accessible. Next, let's see a comparison on how to make <code>swift</code> functions (more in a traditional python style) available right after <code>import</code> the module, in order to have fewer lines (under certain conditions, see discussion on next) of code as demonstrated below. The full source code (with <code>config</code>, <code>keystone</code> modules, and unit tests) are included at the end.

  Beware of how <code>@checks_config</code> decorator is used, in <code>swift_module.py</code>, to guarantee properly instantiating a <code>SwiftConfig</code> if any <code>swift</code> method is called without one. One benefit using optional <code>config=None</code> parameter is to have some flexibility that a <code>config</code> can be either specified by the caller or created by <code>swift</code> module automatically. This makes <code>swift</code> module methods have same signatures (without <code>config</code>), comparing to class mechanism. But disadvantage (of such hiding) also appears that each auto-creation of a <code>config</code> by the decorator will have a different instance.


  ```python
  import swift_module as swift

  # optionally to get a swift config first (see SwiftConfig in swift_module.py)
  config = swift.get_swift_config()
  # swift module functions are available after the import
  a_file = swift.get_file_contents('foo.txt', config=config)
  allist = swift.get_files_in_container(config=config)

  ```

  <a name="config"></a>
  See <code>common/config.py</code>

  ```python
  import logging
  import pyramid

  logger = logging.getLogger(__name__)


  def checks_config(config_func):
      """
      Get decorator to use config_func as initiator for 'config' arg

      Keyword arguments:
      config_func -- a function to get proper configuration
      """
      def checks_config_decorator(original_func):
          """
          Call decorated original_func with checking its 'config' arg

          Keyword arguments:
          func -- original function to be decorated
          """
          def _arg_index_of(func, name):
              """
              Get the index of a named arg on a func call
              """
              import inspect
              argspec = inspect.getargspec(func)
              for i in range(len(argspec[0])):
                  if (argspec[0][i] == name):
                      logger.debug("argspec[0][{0}]=={1}".format(i, name))
                      return i
              return -1

          def _checks_config_wrapper(*args, **kwargs):
              """
              Check 'config' arg before calling original_func
              Call specified config_func if 'config' arg value is None.
              """
              arg_idx = _arg_index_of(original_func, 'config')
              has_arg = 0 <= arg_idx and arg_idx < len(args)
              arg_cfg = args[arg_idx] if (has_arg) else None
              kwa_cfg = kwargs.get('config')
              if (kwa_cfg is None and arg_cfg is None):
                  # logger.debug('Getting config by {0}'.format(config_func))
                  kwargs['config'] = config_func()
              return original_func(*args, **kwargs)

          # calls the original function with checking proper configuration
          return _checks_config_wrapper
      # returns a decorated function
      return checks_config_decorator


  def settings(item):
      """
      Get a reference to the settings in the .ini file
      """
      registry = pyramid.threadlocal.get_current_registry()
      return registry.settings.get(item, None)

  ```

  <a name="keystone"></a>
  See <code>common/keystone.py</code>

  ```python
  from config import settings
  from keystoneclient.v2_0 import client as keystone_client
  from logging import getLogger
  logger = getLogger(__name__)


  def get_auth_token():
      """
      Get an auth token from Keystone.
      """
      try:
          keystone = keystone_client.Client(
              username=settings('cloud_username'),
              password=settings('cloud_password'),
              tenant_name=settings('cloud_project_name'),
              auth_url=settings('cloud_auth_url'),
              insecure=True)
          return keystone.auth_ref['token']['id']
      except Exception as e:
          logger.error(
              "Exception authenticating against Keystone")
          logger.exception("Details: {0}".format(e))
          raise

  ```

  <a name="swift_module"></a>
  See <code>common/swift_module.py</code>

  ```python
  # swift_module.py
  import logging
  import mimetypes
  import sys

  from config import checks_config, settings
  from keystone import get_auth_token
  from swiftclient import client as swift_client
  from swiftclient.exceptions import ClientException

  logger = logging.getLogger(__name__)


  # ================================================
  # Swift configuration class
  # ================================================
  class SwiftConfig(object):
      def __init__(self, auth_token, swift_url, container_name):
          """
          Initialize a Swift configuration instance
          """
          self.auth_token = auth_token
          self.swift_url = swift_url
          self.container = container_name
          self.connection = self._get_connection()

      def _get_connection(self):
          """
          Get a connection to Swift object store
          """
          try:
              return swift_client.Connection(
                  preauthurl=self.swift_url,
                  preauthtoken=self.auth_token,
                  retries=5,
                  auth_version='1',
                  insecure=True)
          except Exception as e:
              err_message = "Exception raised initiating a swift connection."
              logger.exception(err_message)
              raise

  # ToDo [zhuyux]: considering singleton for SwiftConfig instance
  _swift_config_singleton = None

  # ================================================
  # Swift configuration initialization
  # ================================================
  def get_swift_config():
      """
      Get a SwiftConfig instance per application settings
      """
      auth_token = get_auth_token()
      container = settings('swift_container')
      swift_url = settings('swift_url')
      swift_cfg = SwiftConfig(auth_token, swift_url, container)
      return swift_cfg


  def _get_config():
      """
      This is a fixed/non-mockable func pointer for @checks_config decorator
      """
      # logger.debug('get_swift_config={0}'.format(get_swift_config))
      return get_swift_config()

  # ================================================
  # Swift module interfaces
  # ================================================

  @checks_config(config_func=_get_config)
  def check_container(config=None):
      """
      Check if default container exists in Swift

      Keyword arguments:
      config -- an instance of SwiftConfig (optional, default None)
      """
      try:
          logger.debug('Checking container {0}'.format(config.container))
          headers, container_list = config.connection.get_account()
          for container in container_list:
              logger.debug("--- container: {0}".format(container['name']))
              if (container['name'] == config.container):
                  logger.debug('--- found {0}'.format(config.container))
                  return False
          logger.debug('--- missing container {0}'.format(config.container))
          return True
      except Exception as e:
          err_message = "Exception raised on checking container exists."
          logger.exception(err_message)
          raise


  @checks_config(config_func=_get_config)
  def check_file_exists(file_name, config=None):
      """
      Check if specified file exists in Swift store

      Keyword arguments:
      file_name -- the name of the file to be checked in Swift store
      config -- an instance of SwiftConfig (optional, default None)
      """
      if (check_container(config=config)):
          files = get_files_in_container(config=config)
          for file in files:
              if (file['name'] == file_name):
                  return True
      return False


  @checks_config(config_func=_get_config)
  def ensure_container_exists(config=None):
      """
      Ensure default container exists in Swift.

      Keyword arguments:
      config -- an instance of SwiftConfig (optional, default None)
      """
      container_exists = check_container(config=config)
      if (not container_exists):
          try:
              response = {}
              config.connection.put_container(
                  config.container, response_dict=response)
              logger.debug(
                  "--- Container {0} created".format(config.container))
              logger.debug("--- Response {0}".format(response))
          except Exception as e:
              err = "Exception on creating container {0}.".format(
                  config.container)
              logger.exception(err)
              raise


  @checks_config(config_func=_get_config)
  def get_file_contents(file_name, config=None):
      """
      Function wrapper to perform 'get_object' call on Swift

      Keyword arguments:
      file_name -- the name of the file in Swift store
      config -- an instance of SwiftConfig (optional, default None)
      """
      try:
          response_dict = {}
          # Response from Swift:
          #   a tuple of (response headers, the object contents)
          #   The response headers will be a dict and all header names
          #   will be in lower case.
          response = config.connection.get_object(
              config.container,
              file_name,
              response_dict=response_dict)
          file_contents = response[1]
          return file_contents
      except Exception as e:
          err = "Exception on getting {0} from Swift.".format(file_name)
          logger.exception(err)
          raise


  @checks_config(config_func=_get_config)
  def get_files_in_container(config=None):
      """
      Get info of all files in default Swift container

      Keyword arguments:
      config -- an instance of SwiftConfig (optional, default None)
      """
      result = config.connection.get_container(
          config.container, full_listing=True)
      return result[1]


  @checks_config(config_func=_get_config)
  def save_file(file_name, file_contents, config=None):
      """
      Function wrapper to perform 'put_object' call Swift

      Keyword arguments:
      file_name -- the name of the file to be saved
      file_contents -- the contents of the file to be saved in Swift store
      config -- an instance of SwiftConfig (optional, default None)
      """
      try:
          # Ensure the default container exists
          ensure_container_exists(config=config)
          # Push the file contents to Swift
          response = {}
          config.connection.put_object(
              config.container,
              file_name,
              file_contents,
              content_length=sys.getsizeof(file_contents),
              content_type=mimetypes.guess_type(file_name, strict=True)[0],
              response_dict=response)
          return response
      except Exception as e:
          err = "Exception on saving file contents to Swift.\n"
          logger.exception(err)
          raise

  ```

  <a name="swift_module_tests"></a>
  See <code>common/tests/swift_module_tests.py</code>

  ```python
  import logging
  import mock
  import os
  import StringIO
  import sys
  import tarfile
  import unittest

  import common.swift_module as swift

  from pyramid import testing
  from mock import Mock, MagicMock, patch, mock_open
  from swiftclient.exceptions import ClientException

  logger = logging.getLogger(__name__)


  class SwiftTests(unittest.TestCase):
      @patch('common.swift_module.get_auth_token')
      @patch('swiftclient.client.Connection')
      def setUp(self, mock_swift_connection, mock_get_auth_token):
          self.config = testing.setUp()
          self.auth_token = MagicMock()
          self.account_data = ([{}], [{'name': 'container1'}])
          self.container = 'container1'
          self.container_data = ([{}], [{'name': 'file1'}, {'name': 'file2'}])
          self.swift_url = 'http://0.0.0.0'
          self.setting = 'dummy setting'
          self.connection = Mock()
          mock_swift_connection.return_value = self.connection
          mock_get_auth_token.return_value = self.auth_token

          self.swift_cfg = swift.SwiftConfig(
              self.auth_token, self.swift_url, self.container)
          self.swift_cfg.connection.get_account.return_value = self.account_data

      def tearDown(self):
          testing.tearDown()

      @patch('swiftclient.client.Connection')
      def test_swift_config(self, mock_connection):
          self.assertEqual(self.swift_cfg.auth_token, self.auth_token)
          self.assertEqual(self.swift_cfg.swift_url, self.swift_url)
          self.assertEqual(self.swift_cfg.connection, self.connection)
          self.assertEqual(self.swift_cfg.container, self.container)

      @patch('swiftclient.client.Connection')
      def test_swift_config_exception(self, mock_connection):
          error_message = 'CONNECTION ERROR'
          mock_connection.side_effect = Exception(error_message)
          with self.assertRaises(Exception) as cm:
              result = swift.SwiftConfig(
                  self.auth_token, self.swift_url, self.container)
              self.assertEqual(str(cm.exception), error_message)

      def test_check_container_exception(self):
          error_message = 'GET ACCOUNT ERROR'
          self.swift_cfg.connection.get_account.side_effect \
              = Exception(error_message)
          with self.assertRaises(Exception) as cm:
              result = swift.check_container(config=self.swift_cfg)
              self.assertEqual(str(cm.exception), error_message)
              self.assertFalse(result)

      @patch('common.swift_module.get_swift_config')
      def test_check_container_when_false(self, mock_get_config):
          mock_get_config.return_value = self.swift_cfg
          self.swift_cfg.container = '-=#=-dummy-=#=-'
          result = swift.check_container()
          self.assertFalse(result)

      @patch('common.swift_module.get_auth_token')
      @patch('swiftclient.client.Connection')
      def test_check_container_when_true(
              self, mock_swift_connection, mock_get_auth_token):
          mock_swift_connection.return_value = self.connection
          mock_get_auth_token.return_value = self.auth_token
          result = swift.check_container(config=self.swift_cfg)
          self.assertTrue(result)
          self.swift_cfg.container = '-=#=-dummy-=#=-'
          result = swift.check_container(config=self.swift_cfg)
          self.assertFalse(result)

      @patch('common.swift_module.get_swift_config')
      @patch('common.swift_module.check_container')
      def test_check_file_exists(self, mock_check_container, mock_get_config):
          mock_check_container.return_value = True
          mock_get_config.return_value = self.swift_cfg
          self.swift_cfg.connection.get_container = MagicMock()
          self.swift_cfg.connection.get_container.return_value = \
              self.container_data
          result = swift.check_file_exists('fileX')
          self.assertFalse(result)
          result = swift.check_file_exists('file1')
          self.assertTrue(result)

      @patch('common.swift_module.check_container')
      def test_check_file_exists_no_container(self, mock_check_container):
          mock_check_container.return_value = False
          result = swift.check_file_exists('filename', config=self.swift_cfg)
          self.assertFalse(result)

      def test_ensure_container_exists(self):
          success = {'status': 200}

          def mock_put_success(container_name, response_dict):
              logger.debug(
                  'Called with {0} {1}'.format(container_name, response_dict))
              response_dict['status'] = success['status']

          with patch.object(
                  self.swift_cfg.connection, 'get_account',
                  return_value=self.account_data):
              with patch.object(
                      self.swift_cfg.connection, 'put_container',
                      side_effect=mock_put_success) as mocked_put:
                  swift.ensure_container_exists(config=self.swift_cfg)
                  mocked_put.assert_called()

      def test_ensure_container_exists_exception(self):
          error_message = 'PUT CONTAINER ERROR'

          with patch.object(
                  self.swift_cfg.connection, 'get_account',
                  return_value=self.account_data):
              with patch.object(
                      self.swift_cfg.connection, 'put_container',
                      side_effect=Exception(error_message)) as mocked_put:
                  with self.assertRaises(Exception) as cm:
                      import common.swift
                      swift.ensure_container_exists(config=self.swift_cfg)
                      self.assertEqual(str(cm.exception), error_message)

      def test_get_file_contents(self):
          import common.swift
          response = ([{}], '_filecontents')
          self.swift_cfg.connection.get_object = MagicMock()
          self.swift_cfg.connection.get_object.return_value = response
          result = swift.get_file_contents('file_name', config=self.swift_cfg)
          self.assertEqual(result, response[1])

      def test_get_file_contents_exeption(self):
          error_message = 'Exception on get object'
          self.swift_cfg.connection.get_object = MagicMock()
          self.swift_cfg.connection.get_object.side_effect = Exception(error_message)
          with self.assertRaises(Exception) as cm:
              swift.get_file_contents('file_name', config=self.swift_cfg)
              self.assertEqual(str(cm.exception), error_message)

      def test_get_files_in_container(self):
          self.swift_cfg.connection.get_container = MagicMock()
          self.swift_cfg.connection.get_container.return_value = \
              self.container_data
          result = swift.get_files_in_container(config=self.swift_cfg)
          self.assertEqual(result, self.container_data[1])

      @patch('common.config.settings')
      @patch('common.swift_module.get_auth_token')
      @patch('swiftclient.client.Connection')
      def test_get_swift_config(
              self, mock_connection, mock_get_auth_token, mock_settings):
          mock_connection.return_value = self.connection
          mock_get_auth_token.return_value = self.auth_token
          mock_settings.return_value = self.setting
          result = swift.get_swift_config()
          self.assertEqual(result.auth_token, self.auth_token)
          self.assertEqual(result.connection, self.connection)
          self.assertEqual(result.container, self.setting)
          self.assertEqual(result.swift_url, self.setting)

      @patch('mimetypes.guess_type')
      @patch('sys.getsizeof')
      def test_save_file(self, mock_getsizeof, mock_guess_type):
          success = {'status': 200}

          def mock_put_success(
                  container_name, file_name, contents,
                  content_length, content_type, response_dict):
              response_dict['status'] = success['status']

          mock_getsizeof.return_value = 999
          mock_guess_type.return_value = ['filetype']
          with mock.patch.object(
                  self.swift_cfg.connection, 'put_object',
                  side_effect=mock_put_success) as mocked_put:
              import common.swift
              swift.check_container = MagicMock()
              swift.check_container.return_value = True
              filename = 'filename'
              contents = MagicMock()
              swift.save_file(filename, contents, config=self.swift_cfg)
              mocked_put.assert_called_with(
                  self.container,
                  filename, contents,
                  content_length=999, content_type='filetype',
                  response_dict=success)

      @patch('mimetypes.guess_type')
      @patch('sys.getsizeof')
      def test_save_file_Exception(
              self, mock_getsizeof, mock_guess_type):
          import common.swift
          mock_getsizeof.return_value = 999
          mock_guess_type.return_value = ['filetype']
          error_message = "SWIFT PUT OBJECT ERROR"
          self.swift_cfg.connection.put_object.side_effect = \
              Exception(error_message)
          swift.check_container = MagicMock()
          swift.check_container.return_value = False
          with self.assertRaises(Exception) as cm:
              filename = 'filename'
              contents = MagicMock()
              swift.save_file(filename, contents, config=self.swift_cfg)
              self.assertEqual(str(cm.exception), error_message)

  ```

<br/><a name="summary"></a>
## Summary

  Programmers like to write simple code (to make it clear and easy to understand, thus easier to share, test, and maintain). Sure there is always a cost of effort. In OO design (either with C++, Java, or C#), dependency injection pattern has been applied, not only to write less and cleaner code, but also to support the concept of "<b>programming to interfaces, not implementations</b>" - forcing us to honor the contracts.

  Python began as a C-like scripting language. Its class mechanism and dependency injection are not widely adopted. However, good design pattern concepts should apply on large scale projects. The demo above has given a comparison of how to program to interfaces in two different ways. Since the class demo does not use any dependency injection, it has fewer lines of code as in <code>swift</code> class module, but more lines on class initialization.

  On the other hand, the python module way has encapsulated all dependencies in <code>swift</code> module, all methods become immediately accessible after the <code>import</code>. This is not the best example to prove using "traditional" python module is better. Because, if there are more dependencies coming from different domains or tiers, it would be difficult to achieve the same result (without writing a lot of wrappers or decorators).

  If any module method has simple interface and dependencies, python module is just working fine (plus a little complication on <code>config</code> in this demo); otherwise, if it ends up requiring many parameters (or dependencies), python class should be in a design consideration - after all, there must be a bigger reason of introducing <code>class</code> into python than just pleasing OO developers.

  **Next topic**: [Python Class in Design](python-design-part-2.md) of this "<a target="\_blog" href="//boathill.wordpress.com/tag/let-code-speak/">Let Code Speak</a>"
  series will use a more complicate task to demonstrate how python classes are
  used in OOP design. All source code in this demo are downloadable in this
  repository.
