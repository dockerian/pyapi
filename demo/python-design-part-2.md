# Python Class in Design

<em><b><u>Abstract</u></b></em>: Review the discussion of comparing designs between Python class and module interfaces, and provide a more complicate demo to illustrate how to use Python classes to resolve dependencies, in following sections.

<ul>
  <li><a href="#design">Class Design</a></li>
  <li><a href="#common">Commonly-used Functions</a></li>
  <li><a href="#source">Source Code</a></li>
</ul>


  In last [part](python-design-part-1.md) ("Python class vs module"),
  the discussion has been slightly in favor of using
  <a target="\_blog" href="python-design-part-1.md#class">Python class</a>
  mechanism to inject dependencies (e.g. settings for swift store, in the demo)
  via a natural OOP approach, instead of traditional python (scripting) module
  methods (either passing dependencies in parameters or more complicatedly
  introducing <code>SwiftConfig</code> class and <code>@checks_config</code>
  decorator in <a target="\_blog" href="python-design-part-1.md#swift_module">swift module</a>).

  The idea of using class is to have some abstraction in design, so that
  an application can program to interfaces (e.g. <code>ISettings</code>
  and <code>IStore</code>) other than concrete implementations.

  Let's say to program the interface of <code>IStore</code>.
  The contracts are listed here -

  ```python
  get_files_list()
  get_file_contents(file_name)
  save_file(file_name, file_contents)
  ```

  By one implementation, of using [swiftclient](http://docs.openstack.org/developer/python-swiftclient/swiftclient.html)
  on object store, the [<code>Swift</code>](python-design-part-1.md#swift) class
  has encapsulated dependencies in constructor and merely exposed/implemented methods
  per above <code>IStore</code> contracts.

  In other situation or project, if backend store happened to be a database (or
  some file system), the implementation could be easily swapped by a concrete
  <code>DBStore</code> or <code>FileStore</code> class, certainly with different
  signatured constructor (since dependencies vary), but remained same interfaces
  so that application needs less code and logic change, and less regression.

  In this context, settings (e.g. user name, url, auth token, container name
  for swift, database connection string for db store, or a base directory
  for file system) are more about how a concrete implmentation exactly set up
  before the interface can be called. Such dependencies vary from implementations,
  and should be separated from major business logic (which should care only about
  <code>IStore</code> interface). Without encapsulation, the interface method
  signature would have to change for different store. For example, to get a file,
  a container name is required for swift store, but a base directory is
  needed for file store.

<a name="design"></a>
<h4 style="font-weight:bold;font-size:12pt;margin:24pt 0 9pt;">1. Class Design</h4>

  Continued on the topic, the next demo, also in python code, is to
  deploy package to <a target="\_link" href="http://docs.hpcloud.com/helion/devplatform/1.2/ALS-developer-trial-quick-start/">Helion Development Platform</a> (by using Application Lifecycle Service,
  a.k.a. ALS - a <a href="https://en.wikipedia.org/wiki/Cloud_Foundry">Cloud Foundry</a>-based,
  managed runtime environment).

  The procedure of the deployment is actually processing a batch of <a target="\_link" href="https://docs.hpcloud.com/als/v1/user/client/">Helion CLI</a> (<a target="\_link" href="https://docs.cloudfoundry.org/devguide/installcf/"><code>cf</code></a> equivalent tool) commands running against an ALS endpoint.
  The whole process could have any numbers of sequential steps (each runs a
  command, with arguments, and returns exit code). If any command failed,
  the process would stop and fail; otherwise, the process continued in success
  state to the last command.

  During the process (by an artificial deployment identifier), it would be ideal
  to log the status of each step with certain details.
  And the whole execution should be running in a fork thread or process in a
  typical GUI or web application so that the main process (likely the UI) won't
  be frozen and held on waiting for the execution completes. The status (with
  deployment info, might include some history and package details) is
  recorded/saved to a store (e.g. a swift or database) so that the main UI
  can use another thread or the web can call a (RESTful) service to check on
  the progress asynchronously per a deployment identifier.

  Although not quite enough "acceptance criteria" for a real project, the
  above requirements have provided some basic to start a design: a
  <code>Deployment</code> can launch a <code>Process</code> and also call on an
  <code>IStatus</code> (which is separated from how status is recorded and retrieved).
  There is an encapsulated <code>Package</code> model could be part of
  <code>Deployment</code> and passed along the process.
  The <code>Process</code> is the interface to execute the <code>Batch</code>.
  And in this case, since ALS is a concrete service that the deployment process
  will target to, it can be bound to the <code>Process</code> (but not to
  <code>Deployment</code> or <code>Batch</code>).
  The design is fully described as in below.


<h5 style="font-weight:bold;font-size:11.5pt;margin:16pt 0 6pt;">1.1. Batch</h5>

  * <em><b><u>Usage</u></b></em>: A class module contains a batch (a series of shell commands, with CWD, target status on success, accepted exit code, or allowing non-zero exit code)
  * <em><b><u>Dependencies</u></b></em>: CWD (default working directory specified)
  * <em><b><u>Interfaces</u></b></em>:

    ```python
    add(self, command, expected_status, description='', accept_error=False)
    ```

<h5 style="font-weight:bold;font-size:11.5pt;margin:16pt 0 6pt;">1.2. BatchProcess <span style="font-weight:normal;">(optionally implements an <code>IProcess</code>)</span></h5>

  * <em><b><u>Usage</u></b></em>: A class module represent a batch process (e.g. loop through each command in a batch sequentially and use <code>subprocess</code> to execute the command)
  * <em><b><u>Dependencies</u></b></em>: <code>Batch</code> instance, and <code>IStatus</code> interface (or a function pointer to set status record on each step of the process)
  * <em><b><u>Interfaces</u></b></em>:

    ```python
    execute(self)
    ```

<h5 style="font-weight:bold;font-size:11.5pt;margin:16pt 0 6pt;">1.3. HelionCliComposer</h5>

  * <em><b><u>Usage</u></b></em>: A class module wrapper to compose Helion CLI command
  * <em><b><u>Dependencies</u></b></em>: ALS cluster endpoint, user name (admin email), login password, and optional CWD (working directory)


<h5 style="font-weight:bold;font-size:11.5pt;margin:16pt 0 6pt;">1.4. Package (Model)</h5>

  * <em><b><u>Usage</u></b></em>: A model class represent package-related information (e.g. manifest, package/file type, destination, etc.)
  * <em><b><u>Dependencies</u></b></em>: None, or a more detailed package manifest (including type and destination)


<h5 style="font-weight:bold;font-size:11.5pt;margin:16pt 0 6pt;">1.5. DeploymentStatus <span style="font-weight:normal;">(<code>IStatus</code> interface)</span></h5>

  * <em><b><u>Usage</u></b></em>: A class module represent an interface of getting and setting status (against, e.g. swift or db store)
  * <em><b><u>Dependencies</u></b></em>: <code>Package</code>, <code>IStore</code> (Swift or DB store for status record)
  * <em><b><u>Interfaces</u></b></em>:

    ```python
    get_status(self, deployment_id)
    set_status(self, deployment_id, status)
    ```

<h5 style="font-weight:bold;font-size:11.5pt;margin:16pt 0 6pt;">1.6. Deployment</h5>

  * <em><b><u>Usage</u></b></em>: A class module represent a deployment process (e.g. process package and deployment info, build batch commands, and kick off batch process)
  * <em><b><u>Dependencies</u></b></em>: <code>Package</code>, <code>HelionCliComposer</code>, <code>IProcess</code>, and <code>IStatus</code>
  * <em><b><u>Interfaces</u></b></em>:

  ```python
  deploy(self)
  ```

<a name="common"></a>
<h4 style="font-weight:bold;font-size:12pt;margin:24pt 0 9pt;">2. Commonly-used Functions</h4>

  Based on the [<code>Swift</code> class](python-design-part-1.md#swift) (in
  last [part](python-design-part-1.md)), it is easy and straightforward to
  add more functions related to the store. Assuming to use the store saving
  both packages and deployment state records, the following piece is a partial
  of <code>Swift</code> class to include 3 more methods:
  * <code>check_file_exists</code>,
  * <code>check_package_exists</code> and
  * <code>get_deployment_list</code>.
  Noticing latter two methods have some business logic (about package and deployment)
  that may not belong to a "pure" <code>IStore</code> interface, it would be a
  design decision how services are structured and if they should be in
  <code>Deployment</code> or another middle tier class.

  See <code>swift.py</code> (partial of <code>Swift</code> class) -

  ```python
    def check_file_exists(self, file_name):
        if (not self.check_container()):
            return False
        result = self.connection.get_container(
                container_name, full_listing=True)
        for file in result[1]:
            if (file['name'] == file_name):
                return True
        return False

    def check_package_exists(self, package_name):
        file_name = '{0}.tar.gz'.format(package_name)
        return self.check_file_exists(file_name)

    def get_deployment_list(self):
        deployment_list = []
        result = self.connection.get_files_in_container()
        regex = re.compile('^deployment_(.+).json$')
        for file in result:
            filename = file['name']
            re_match = regex.search(filename)
            add_flag = \
                file['content_type'] == 'application/json' and \
                re_match is not None
            if (add_flag):
                try:
                    file_contents = self.get_file_contents(filename)
                    item = json.loads(file_contents)
                    deployment_list.append(item)
                except Exception:
                    continue
        return deployment_list
  ```

  Another helper module is <code>utils.py</code>, which could have commonly
  used functions that do not belong to any of classes in this demo.
  There is no need to wrap these functions into a class.
  In other OOP language (like Java or C#), they are usually grouped as
  <code>public static</code> methods. Python module serves the same perfectly here.
  The <code>utils.py</code> module also includes a <code>get_store</code> method.
  This is to demonstrate as a factory to construct a <code>IStore</code> object,
  especially in a multi-project environment when <code>IStore</code> implementations
  come from a <code>common</code> namespace but dependencies (e.g.
  <code>settings</code>) in application domain.

  See <code>utils.py</code> -

  ```python
  # utils.py
  import re
  import StringIO
  import shutil
  import tarfile

  from config import settngs
  from keystone import get_auth_token
  from swift_class import get_swift, Swift
  from logging import getLogger
  logger = getLogger(__name__)


  def delete_directory_tree(dir_path):
      """
      Cleanup a directory
      """
      if (dir_path):
          try:
              logger.info('Deleting {0}'.format(dir_path))
              # Clean up working directory
              shutil.rmtree(dir_path, ignore_errors=True)
              logger.info('Deleted dir: {0}'.format(dir_path))
          except Exception as e:
              err_message = \
                  'Failed to clean up working directory "{0}".' \
                  .format(dir_path)
              logger.exception(err_message)


  def extract_manifest_from_package(file_contents):
      """
      Extract the manifest from the vendor package
      """
      manifest_regex = '^.+[/]manifest.json$'
      pattern = re.compile(manifest_regex, re.IGNORECASE)

      # tarfile - https://docs.python.org/2/library/tarfile.html
      manifest = None
      with tarfile.TarFile.open(
              mode='r:gz',
              fileobj=StringIO.StringIO(file_contents)) as tar_package:
          for tarinfo in tar_package.getmembers():
              if (pattern.search(tarinfo.name)):
                  manifest = tar_package.extractfile(tarinfo.name).read()
                  break
      return manifest


  def get_store():
      """
      Get a Swift instance per application settings
      """
      auth_token = get_auth_token()
      container = settings('swift_container')
      swift_url = settings('swift_url')
      swift = Swift(auth_token, swift_url, container)
      return swift

  ```

  The last piece in this discussion section is <code>Batch</code>
  and <code>BatchProcess</code>. Both of them are very self-contained
  and have nothing specifically related to major business logic (<code>Deployment</code>
  in this case). The separation here is used to isolate each problem domain
  without too much dependencies at interface level. Envision that the deployment
  business might need to target on a different platform or require to call a
  RESTful service instead of a batch of commands, the <code>deploy</code> interface
  in <code>Deployment</code> would be rewritten to call a different process.
  The <code>deploy</code> call could have minimum, or even no code change (if
  an <code>IProcess</code> is defined).

  See <code>batch.py</code> (<code>Batch</code> and <code>BatchProcess</code>) -

  ```python
  # batch.py
  import json
  import os
  import subprocess
  import threading

  from logging import getLogger
  logger = getLogger(__name__)


  class Batch(object):
      def __init__(self, cwd):
          """
          Initialize an instance of Batch
          Params:
              cwd: current working directory (where the batch to be executed)
          """
          self.batch_cmds = []
          self.cwd = os.path.abspath(os.path.expanduser(cwd))

      def add(self, status, command, accept_error=False):
          """
          Add a command to batch, with expected status on success, and
          optionally allowing non-zero exit code by accept_error=True
          """
          self.batch_cmds.append({
              'accept_error': accept_error,
              'command': command,
              'cwd': self.cwd,
              'exit_code': 0,
              'status': status,
              'stdout': '',
          })

      def clear(self):
          self.batch_cmds = []


  class BatchProcess(object):
      def __init__(self, batch, set_status_func):
          """
          Initialize an instance of BatchProcess
          """
          self.batch_cmds = batch.batch_cmds
          self.set_status = set_status_func
          self.started = False
          self.success = False

      def execute(self):
          """
          Start to execute a batch process
          """
          can_continue = True
          self.started = True
          self.set_status('STARTED')

          logger.info('Batch:\n{0}'.format(self.batch_cmds))
          for next_cmd in self.batch_cmds:
              logger.info('CWD=={0}'.format(next_cmd['cwd']))
              logger.info('next cmd:\n{0}'.format(
                  json.dumps(next_cmd, indent=2, sort_keys=True)))
              accept_error = next_cmd['accept_error']
              cmd = next_cmd['command']
              # ToDo [zhuyux]: add timeout mechnisam
              proc = subprocess.Popen(
                  cmd,
                  cwd='{0}'.format(next_cmd['cwd']),
                  stderr=subprocess.STDOUT,
                  stdout=subprocess.PIPE)
              next_cmd['stdout'] = proc.communicate()[0]
              stdout = next_cmd['stdout'].decode('string_escape')
              logger.info('stdout:\n{0}'.format(stdout))
              exit_code = proc.returncode

              if (accept_error or exit_code == 0):
                  self.set_status(next_cmd['status'])
              else:
                  logger.error('Exit code {0} from {1}'.format(exit_code, cmd))
                  next_cmd['exit_code'] = exit_code
                  can_continue = False
                  break

          self.set_status('SUCCESS' if can_continue else 'FAILED')
          self.success = can_continue
          return can_continue

  ```

<a name="source"></a>
<h4 style="font-weight:bold;font-size:12pt;margin:24pt 0 9pt;">3. Source Code</h4>

  This section mainly lists rest of the source code at core business of the
  <code>Deployment</code>. By this far, it should be clear to see how a class
  is designed to be highly cohesive (to its own problem domain) but also loosely
  decoupled from other classes, modules, or layers. Dependencies between
  each class/module are kept at minimum by object constructor or a factory,
  while interfaces are maintained clean and consistent regardless of concrete
  implementations. Services are self-contained and swappable without affecting
  too much on other part of the application. The design thought is for Python
  classes, but applies as generic in any programming practice.

  See <code>helion_cli.py</code> (<code>HelionCliComposer</code> class) -

  ```python
  #helicon_cli.py
  import os


  class HelionCliComposer(object):
      def __init__(self, endpoint, username, password, cwd=None):
          """
          Initialize an instance of HelionCliComposer
          """
          self.cwd = None
          if (cwd is not None):
              self.cwd = os.path.abspath(os.path.expanduser(cwd))
          self.endpoint = endpoint
          self.username = username
          self.password = password
          pass

      def get_delete_cmd(self, name):
          return [
              'helion', 'delete',
              '--target', '{0}'.format(self.endpoint),
              '-n', '{0}'.format(name)]

      def get_list_cmd(self):
          return ['helion', 'list', '--target', '{0}'.format(self.endpoint)]

      def get_login_cmd(self):
          return [
              'helion', 'login',
              '{0}'.format(self.username),
              '--credentials', 'username: {0}'.format(self.username),
              '--password', '{0}'.format(self.password),
              '--target', '{0}'.format(self.endpoint)]

      def get_logout_cmd(self):
          return ['helion', 'logout']

      def get_push_cmd(self, name, path):
          if (self.cwd is not None):
              path = '{0}/{1}'.format(self.cwd, path)
          return [
              'helion', 'push',
              '--target', '{0}'.format(self.endpoint),
              '--as', '{0}'.format(name),
              '--path', '{0}'.format(path),
              '--no-prompt']

      def get_target_cmd(self):
          return ['helion', 'target', self.endpoint]

  ```

  See <code>package.py</code> (<code>Package</code> class) -

  ```python
  # package.py
  import re
  import os

  from logging import getLogger
  logger = getLogger(__name__)


  class Package(object):
      def __init__(self, package_id, package_path, endpoint_url=None):
          """
          Initialize an instance of Package
          Params:
              package_id: package id or name
              package_path: full path of the package (including file name)
          """
          self.id = package_id
          self.file_name = os.path.basename(package_path)
          self.name = self.get_package_name(package_path)
          self.path = os.path.abspath(os.path.expanduser(package_path))
          self.destination = self.get_destination(endpoint_url, self.name)
          self.cwd = os.path.dirname(self.path)

      def get_destination(self, endpoint_url, package_name):
          """
          Get package destination url from endpoint and package name
          """
          dest = ''
          if (endpoint_url):
              regex = re.compile('^(http[s]?://)api\.(.+)$')
              re_match = regex.search(endpoint_url.strip('/'))
              if (re_match is not None):
                  prot = re_match.group(1)
                  addr = re_match.group(2)
                  dest = '{0}{1}.{2}'.format(prot, package_name, addr)
          # returning package destination url
          return dest

      def get_package_manifest_filename(self):
          """
          Get package manifest filename (e.g. foo.json) without path
          """
          return '{0}.json'.format(self.name)

      def get_package_name(self, package_path):
          """
          Get package name (e.g. foo) from package path (e.g. '/path/foo.tar.gz')
          """
          pkg_file = os.path.basename(package_path)
          pkg_name = os.path.splitext(os.path.splitext(pkg_file)[0])[0]
          return pkg_name

  ```

  See <code>deploy_status.py</code> (<code>DeploymentStatus</code> class) -

  ```python
  # deploy_status.py
  import json
  import os

  from datetime import datetime
  from time import gmtime, strftime

  from logging import getLogger
  logger = getLogger(__name__)


  class DeploymentStatus(object):
      def __init__(self, package=None, store):
          """
          Initialize an instance of DeploymentStatus
          """
          self.package = package
          self.destination = '' if package is None else package.destination
          self.package_name = 'N/A' if package is None else package.name
          self.store = store

      def get_all(self):
          return self.store.get_deployment_list()

      def get_deployment_filename(self, id):
          filename = 'deployment_{0}.json'.format(id)
          return filename

      def get_status(self, id):
          """
          get status record (as json object) by deployment id
          """
          result = {
              'deploy_id': id,
              'deploy_status': '',
              'datetime': '',
              'destination': self.destination,
              'history': [],
              'package': self.package_name}
          try:
              filename = self.get_deployment_filename(id)
              contents = self.store.get_file_contents(filename)

              if (contents):
                  # logger.debug('Deployment status: {0}'.format(contents))
                  result = json.loads(contents)
          except Exception as e:
              logger.exception("Failed to get status for {0}.\n".format(id))
          # logger.debug('Deployment result: {0}'.format(result))
          return result

      def set_status(self, id, status):
          """
          set status record (json file) by deployment id and status (string)
          """
          logger.info('======= Setting status: "{0}" =======\n'.format(status))

          result = self.get_status(id)

          date_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
          history = result['history']
          record = '{0} ~ {1}'.format(date_time, status)
          if (type(history) is list):
              history.append(record)
          else:  # creating a history list
              history = [record]

          result['deploy_id'] = id
          result['deploy_status'] = status
          result['datetime'] = date_time
          result['destination'] = self.destination
          result['package'] = self.package_name
          result['history'] = history

          filename = self.get_deployment_filename(id)
          contents = json.dumps(result, sort_keys=True)
          self.store.save_file(container_name, filename, contents)

          return result

  ```

  See <code>deploy.py</code> (<code>Deployment</code> class) -

  ```python
  # deploy.py
  import os
  import shutil
  import tempfile

  from multiprocessing import Lock, Process, Queue
  from batch import Batch, BatchProcess

  from utils import delete_directory_tree
  from logging import getLogger
  logger = getLogger(__name__)


  class Deployment(object):
      def __init__(
              self,
              package, cli_composer, deploy_status,
              use_package_path=False):
          """
          Initialize an instance of Deployment
          """
          import uuid
          if (use_package_path):
              self.batch = Batch(package.cwd)
          else:
              self.batch = Batch(tempfile.mkdtemp())
          self.cli_composer = cli_composer
          self.cwd = self.batch.cwd
          self.cwd_use_package_path = use_package_path
          self.deployed = False
          self.deployment_id = '{0}'.format(uuid.uuid1())
          self.deploy_status = deploy_status
          self.package = package
          self.store = deploy_status.store  # backend store
          self.started = False

      def cleanup(self):
          """
          Cleanup Deployment BatchPrcess working directory
          """
          try:
              logger.info('Deleting deployment cwd={0}'.format(self.cwd))
              # Clean up working directory
              delete_directory_tree(self.cwd)
              logger.info('Deleted deploy deployment cwd.')
          except Exception as e:
              err_message = \
                  'Failed to clean up deployment cwd "{0}".' \
                  .format(self.cwd)
              logger.exception(err_message)

      def deploy(self):
          """
          Start a Deployment process
          """
          if (self.started):
              err = 'Deployment {0} already started'.format(self.deployment_id)
              raise Exception(err)

          self.get_deployment_batch()

          try:
              self.started = True
              self.download_package() # preparing package

              logger.info('Starting deployment ...')
              process = BatchProcess(self.batch, self.set_status)
              logger.debug('Batch process: {0}'.format(process))
              self.deployed = process.execute()
          except Exception as e:
              err_message = 'Exception on BatchProcess execution.'
              logger.exception(err_message)
              self.set_status('FAILED')
          else:
              logger.info('DONE deployment - {0}'.format(self.deployment_id))
          finally:
              self.cleanup()

      def download_package(self):
          if (self.cwd_use_package_path):
              self.set_status('DOWNLOADING')
              pkg_filename = self.package.file_name
              pkg_contents = store.get_file_contents(pkg_filename)
              logger.info('Downloading package {0} to {1}...'.format(
                  pkg_filename, self.package.path))
              with open(self.package.path, 'w') as package_file:
                  # write the package as a tar.gz into deployment cwd
                  package_file.write(pkg_contents)
          return self.package.path

      def get_deployment_batch(self):
          """
          Get a batch of commands for the deployment
          """
          pkg_path = self.package.path
          pkg_name = self.package.name

          self.batch.clear()
          # add unpacking script to batch
          logger.info('Adding batch to unpack {0} from {1}'.format(
              pkg_name, pkg_path))
          self.get_package_batch()

          # add deployment script to batch
          self.batch.add('TARGET', self.cli_composer.get_target_cmd())
          self.batch.add('LOGIN', self.cli_composer.get_login_cmd())
          self.batch.add(
              'REMOVED', self.cli_composer.get_delete_cmd(pkg_name), True)
          self.batch.add('LIST', self.cli_composer.get_list_cmd())
          self.batch.add('DEPLOYED', self.cli_composer.get_push_cmd(
              pkg_name, '{0}'.format(pkg_name)))
          self.batch.add('NEWLIST', self.cli_composer.get_list_cmd())
          self.batch.add('DIR', ['ls', '-al'])

      def get_package_batch(self):
          """
          Get a batch of commands for preparing the package
          """
          dst_path = self.cwd
          src_path = self.package.path
          pkg_name = self.package.name

          # no need this copy command if package path is used as cwd
          if (not self.cwd_use_package_path):
              copy_cmd = [
                  'cp', '-rf',
                  '{0}'.format(src_path),
                  '{0}'.format(dst_path)]
              self.batch.add('COPY', copy_cmd)

          view_cmd = [
              'tar', '-tvf',
              '{0}'.format(src_path)]
          # Assume any foo.tar.gz contains -
          #   - foo/foo.tar.gz (the package to deploy)
          #   - manifest.json
          unpack_cmd = [
              'tar', '-zxvf',
              '{0}'.format(src_path)]
          xtract_cmd = [
              'tar', '-zxvf',
              '{0}/{1}/{2}.tar.gz'.format(dst_path, pkg_name, pkg_name)]
          dir_cmd = [
              'ls', '-al',
              '{0}/{1}'.format(dst_path, pkg_name)]
          self.batch.add('PREVIEW', view_cmd)
          self.batch.add('UNPACK', unpack_cmd)
          self.batch.add('EXTRACT', xtract_cmd)
          self.batch.add('DIR', dir_cmd)

      def get_status(self):
          '''get status by self.deployment_id
          '''
          return self.deploy_status.get_status(self.deployment_id)
          # return status
          pass

      def set_status(self, status):
          '''set status by self.deployment_id
          '''
          self.deploy_status.set_status(self.deployment_id, status)

  ```

  See <code>deployment.py</code> (app module) -

  ```python
  # deployment.py
  import json
  import shutil
  import tempfile
  import traceback

  from multiprocessing import Process
  from subprocess import call, check_output, CalledProcessError

  from deploy import Deployment
  from deploy_status import DeploymentStatus
  from helion_cli import HelionCliComposer
  from package import Package
  from utils import delete_directory_tree, get_store
  from logging import getLogger
  logger = getLogger(__name__)


  def deploy_package(package_name, endpoint_url, username, password):
      """
      Deploy a package into destination (e.g. ALS/Cloud Foundry)
      Params:
          package_name - the name of the package to deploy
          endpoint_url - the destination (e.g. ALS/Cloud Foundry) endpoint URL
                         ie: 'https://api.15.126.129.33.xip.io'
          username - the user name (admin email) for destination login
          password - the password for destination login
      """
      store = get_store()

      if (not store.check_package_exists(package_name)):
          return {'status': 404}

      cwd = ''
      try:
          cwd = tempfile.mkdtemp()
          pkg_filename = '{0}.tar.gz'.format(package_name)
          package_path = '{0}/{1}'.format(cwd, pkg_filename)
          package = Package(package_name, package_path, endpoint_url)

          # instantiate a cli composer
          composer = HelionCliComposer(endpoint_url, username, password)

          deploy_status = DeploymentStatus(package, store)
          deployment = Deployment(package, composer, deploy_status, True)
          deployment_id = deployment.deployment_id

          deployment.set_status('INIT')

          # Start a new process to execute the deployment
          process = Process(
              name='deployment_{0}'.format(deployment_id),
              target=deployment.deploy)
          process.start()

          logger.info('Deployment {0} started for {1}.'.format(
              deployment_id, package_name))

          return {
              'status': 201,
              'deployment_id': deployment_id,
              'package': package_name}

      except Exception as e:
          stack_info = traceback.format_exc()
          error_message = "Exception on deploy {0}. Details:\n{1}".format(
              package_name, stack_info)
          logger.exception(error_message)
          delete_directory_tree(cwd)
          return {'status': 500, 'errors': error_message}


  def get_status(id):
      """
      Get the deployment status by id
      """
      try:
          logger.info("======= deployment::get_status =======")
          store = get_store()
          deploy_status = DeploymentStatus(store=store)
          result = deploy_status.get_status(id)

          logger.debug('Deployment result: {0}'.format(result))
          if result == {} or not result['deploy_status']:
              return {'status': 404}
          else:
              return {'status': 200, 'data': result}
      except Exception as e:
          stack_info = traceback.format_exc()
          error = "Exception on getting deployment status"
          error_message = "{0} for {1}. Details:\n{2}".format(
              error, id, stack_info)
          logger.exception(error_message)
          return {'status': 500, 'errors': error_message}

  ```
