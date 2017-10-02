<img align="right" src="http://welcome.hp-ww.com/country/us/en/cs/images/i/header-footer/caas-hf-v3/hp-logo-pr.gif"></img>

# Helion Addin Ecosystems Automation

## About

This repository contains the applications for the Addins Ecosystem project/team, including the Ansible playbooks required to deploy, manage and maintain working environments.

## Usage

### Preparation

Install the Kickstart CLI:
``` bash
cd pyapi/tools/automation/kickstart
./install_kickstart.sh
```
This process will NOT create your local `~/.kickstart` folder, only get you set to use Kickstart. The first time you create an environment or import an existing environment from a .tar file, then `~/.kickstart` file will be created

### Import an existing environment from an exported tar file
``` bash
./kick.sh env import {tar file}
```

If you need to use an existing environment, there are several defined on the [HP Cloud Wiki](http://wiki.hpcloud.net/display/paas/Environment+Orchestration). Look in the section called __Environments__.

If this is your first environment, this will create a `.kickstart` folder in your home folder, and populate it using the contents of the .tar file. If you already have a `.kickstart` folder (at least one environment already exists), it will simply import the environment from the tar file into your `.kickstart` folder.

### Create an environment
Use Kickstart to create a 'named' environment that will hold the specific configuration attributes for that environment, ie: region, cloud account, tenant, etc.
``` bash
./kick.sh env add {my-env-name}
```
If this is your first environment, this will create a `.kickstart` folder in your home folder, and populate it with your new environment information. If you already have a `.kickstart` folder, it will simply add the new environment information to that folder.

Open the `.kickstart` folder with a text editor, similar to this:
```
atom ~/.kickstart/
```

You should see something like this:
```
~/.kickstart/
├── environments
│   ├── demo-uswest
│   │   ├── inventory.json
│   │   └── kickstart.yml
│   └── test
│       ├── id_rsa
│       ├── id_rsa.pub
│       ├── inventory.json
│       └── kickstart.yml
└── kick.json
```
Here's the lowdown on the files and folders above.

On this machine, there are two environments defined: `demo-uswest` and `test`.

Each environment has:

- __inventory.json__ (*required*) - defines the instances that make up the environment. This file by default defines a single web instance. You will need to manually add all of the instances you want to this file. There is an  [example inventory file](pyapi/tools/automation/kickstart/examples/inventory.json) available if you need more detaiul on what that should look like. There is also a [more exhaustive example](https://github.com/hpcloud/Helion-CI/blob/v0.0.2/pyapi/tools/automation/kickstart/examples/inventory.json) of an inventory file within the Helion-CI project.

- __kickstart.yml__ (*required*) - outlines configuration items needed to allow Kickstart to talk to the cloud and orchestrate the deployment. This will include configuration attributes like:
  - username of the cloud account to use for the deploment
  - password of the cloud account to use for the deploment
  - the tenant of the cloud account the deploy will target
  - the network (typically specific to the cloud account) the deploy will use
  - the Keystone auth url
  - the region of the cloud to use
  - the image ID and flavor to be used for instances

  The contents of this file should be self-explanatory; however, an [example config file](pyapi/tools/automation/kickstart/examples/kickstart.yml) is available.

- __id_rsa__ (*optional*) - the private key used to access the deployed env.

  _If one doesn't exist when the environment is created for the first time, a new one will be generated._

  Be aware that the private key cannot be encrypted. Unencrypt the key or remove the passphrase before copying to the environment.

- __id_rsa.pub__ (*optional*) - the public key used to access the deployed env.

  _If one doesn't exist when the environment is created for the first time, a new one will be generated._

The `kick.json` file is used internally by Kickstart across environments to maintain the state of the current environment in use.

### Verify your current env
Review your currently selected env:
```
./kick.sh env
```
You should see something like the following:

```
Environment currently in use: demo-uswest
{
    "demo-uswest": {
        "config_file": "~/.kickstart/environments/demo-uswest/kickstart.yml",
        "inventory_file": "~/.kickstart/environments/demo-uswest/inventory.json",
        "remote_login": "ubuntu",
        "ssh_private_keyfile": "~/.kickstart/environments/demo-uswest/id_rsa",
        "ssh_public_keyfile": "~/.kickstart/environments/demo-uswest/id_rsa.pub"
    },
    "test": {
        "config_file": "~/.kickstart/environments/test/kickstart.yml",
        "inventory_file": "~/.kickstart/environments/test/inventory.json",
        "remote_login": "ubuntu",
        "ssh_private_keyfile": "~/.kickstart/environments/test/id_rsa",
        "ssh_public_keyfile": "~/.kickstart/environments/test/id_rsa.pub"
    }
}
```

### Export an environment
``` bash
./kick.sh env export {filename}
```
  This will result in a .tar file being created.

### Use an environment / set current env
``` bash
./kick.sh env use {my-env-name}
```

### Deploy the default playbook
``` bash
./deploy.sh
```

The deploy script deploys the entire environment based on the [site.yml](pyapi/tools/automation/kickstart/ansible/roles/site.yml) that points to the Ansible playbooks that define our deployment architecture.

### Remote to one of the nodes

Get a list of hosts in the env:
```
cat ~/.kickstart/environments/test/inventory.json
```

The returned json should look like this:
``` json
{
  "web": {
    "hosts": [
      "web-n01"
    ],
  "vars": {
    "public": true
    }
  }
}
```

Remote to the web node:
```
./kick.sh remote web-n01
```

### Remote to the conductor, view the ansible log file
If you need to review the ansible log file, you'll need to hop on the conductor:

```
./kick.sh remote ansible-conductor
cat /var/log/ansible.log
```
