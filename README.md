# This project is a collection of actions and probes, gathered as an extension to the Chaos Toolkit. It targets the IBM Cloud platform.

[![Build Status](https://travis.ibm.com/Ahmed-Sayed-Hassan/chaostoolkit-ibmcloud.svg?token=Gz9qQvEsAkRRVj6sGwRD&branch=master)](https://travis.ibm.com/Ahmed-Sayed-Hassan/chaostoolkit-ibmcloud)


This project is a collection of [actions][] and [probes][], gathered as an
extension to the [Chaos Toolkit][chaostoolkit].

[actions]: http://chaostoolkit.org/reference/api/experiment/#action
[probes]: http://chaostoolkit.org/reference/api/experiment/#probe
[chaostoolkit]: http://chaostoolkit.org

### Desgin Principle and Contribution Guide.

Chaostoolkit can ba considered a [Low Code Development Platform](https://en.wikipedia.org/wiki/Low-code_development_platform#:~:text=A%20low%2Dcode%20development%20platform,traditional%20hand%2Dcoded%20computer%20programming.)  

The following guidelines  for chaostoolkit-ibmcloud
-----------------------------------------------------

* All resources can be located with information available directly on the IBM cloud portal, such as Instance ID, Volume ID, try to avoid ID that is hard to locate such as (Volume attachment ID)
* Instance ID is unique and available directly on IBM Cloud; try to use it to located other resources; for example, if you need an IP address, try to extract it from IP or floating IP.
* Do not delete resources unless it is the only way, try to stop, change the configuration to achieve the task, for example
  - Stop Virtual Instances instead of deleting it.
  - detach the volume
  - update LoadBalancer backend pool or listener instead.
* Ensure to provide the rollback action, for any action, for example 
  - Start Server after stopped it 
  - Attach the volume after detaching it.
* Tag any resources after executing the action with the following tags "chaostoolkit", "action-name"
* Add the required busy-wait in action itself as an option instead of depending on Pause only.
* Assume the default settings of Cloud environment as default parameters, still more advanced parameters can be added as optional, for example
  - Each Virtual Instance, by default, has one Local interface Loopback and one NIC for external access
  
*Not all those principles are applied yet to the current code but still work on Progress to apply them*

### Probes

|Category   |probe                | Description                               |
|-----------|---------------------|-------------------------------------------|
| VPC       |get_virtual_servers  | check the status of Virtual Instance      |
| Cloud Pak | probe_mq            | put and get message IBM MQ                |

### Actions

|Category |Action                      | Description                                            |
|---------|----------------------------|--------------------------------------------------------|
| VPC     |create_instance_action      | based on the type you can start, stop , restart Server |
| VPC     |delete_load_balancer        | Delete Loadbalancer                                    |
| VPC     |remove_volume_from_instance | De-attach Volume from  virtual Instance                |
| VPC     |add_volume_to_instance      | Attach Volume to virtual Instance                      |
| VPC     |start_multiple_instances    | turn on one or more Virtual Machines                   |
| VPC     |stop_multiple_instances     | turn off one or more virtual machines                  |
| VPC     |delete_load_balancer_members| Delete Load Balancer Members                           |
| VPC     |cordon_subnet               | Isolate a complete subnet via adding ACL with denyall  | 
| VPC     |uncordon_subnet             | restoring the orignal ACL should run after cordon_subnet|
| Linux   |add_network_latency         | Add Network Latency                                    |
| Linux   |add_drop_packet             | drop packets sent to specific IP                       |
| Container |detach_volume_from_worker | De-attach volume from VPC IKS/ROKS Worker Nodes        |
| Container |attach_volume_to_worker   | attach from to a VPC IKS/ROKS Worker node              |
## Install

This package requires Python 3.5+

To be used from your experiment, this package must be installed in the Python
environment where [chaostoolkit][] already lives.

```
$ pip install -U chaostoolkit-ibmcloud
```

## Usage

To use the probes and actions from this package, add the following to your
experiment file:

```json
{
    "version": "1.0.0",
    "title": "What is the impact of stopping Server?",
    "description": "This a dummy experiment.",
    "tags": [
        "tls"
    ],
    "configuration": {
        "api_key": "<api-key>",
        "generation": "2",
        "service_url": "https://jp-tok.iaas.cloud.ibm.com/v1"
    },
    "steady-state-hypothesis": {
        "title": "Application responds",
        "probes": [
            {
                "type": "probe",
                "name": "Check the a machine is running",
                "tolerance": {
                    "type": "jsonpath",
                    "path": "$[0].status",
                    "expect": "running"
                },
                "provider": {
                    "type": "python",
                    "module": "ibmcloud.vpc.probes",
                    "func": "get_virtual_servers",
                    "arguments": {
                        "name": "windows-jump"
                    }
                }
            }
        ]
    },
    "method": [
        {
            "type": "action",
            "name": "Stop Windows Jump Server",
            "provider": {
                "type": "python",
                "module": "ibmcloud.vpc.actions",
                "func": "create_instance_action",
                "arguments": {
                    "instance_id": "02g7_af1ee383-a6eb-4ed5-b9b7-fdbce23a25c2",
                    "type": "stop",
                    "force": false
                }
            },
            "pause": {
                "after": 30
            }
        },
        {
            "ref": "Check the a machine is running"
        }

    ],
    "rollbacks": [
        {
            "type": "action",
            "name": "Re-start Windows Jump Server",
            "provider": {
                "type": "python",
                "module": "ibmcloud.vpc.actions",
                "func": "create_instance_action",
                "arguments": {
                    "instance_id": "02g7_af1ee383-a6eb-4ed5-b9b7-fdbce23a25c2",
                    "type": "start",
                    "force": true
                }
            },
            "pause": {
                "after": 60
            }
        }
    ]
}

```

That's it!

Please explore the code to see existing probes and actions.

## Configuration


## Contribute

If you wish to contribute more functions to this package, you are more than
welcome to do so. Please, fork this project, make your changes following the
usual [PEP 8][pep8] code style, sprinkling with tests and submit a PR for
review.

[pep8]: https://pycodestyle.readthedocs.io/en/latest/

### Develop

If you wish to develop on this project, make sure to install the development
dependencies. But first, [create a virtual environment][venv] and then install
those dependencies.

[venv]: http://chaostoolkit.org/reference/usage/install/#create-a-virtual-environment

```console
$ pip install -r requirements-dev.txt -r requirements.txt
```

Then, point your environment to this directory:

```console
$ pip install -e .
```

Now, you can edit the files and they will be automatically be seen by your
environment, even when running from the `chaos` command locally.

### Test

To run the tests for the project execute the following:

```
$ pytest
```
