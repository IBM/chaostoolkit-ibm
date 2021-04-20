from chaoslib.discovery.discover import discover_actions, discover_probes, initialize_discovery_result
from chaoslib.types import Configuration, Discovery, DiscoveredActivities, Secrets
from logzero import logger
from typing import List
from ibm_vpc import VpcV1
from ibm_cloud_databases import CloudDatabasesV5
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException
from ibm_platform_services import GlobalTaggingV1
import os

import importlib

__all__ = ["create_ibmcloud_api_client", "discover", "__version__", "tag_virtual_instance"]
__version__ = '0.1.0'

from ibm_vpc import VpcV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core import ApiException


def create_ibmcloud_databases_client(configuration: Configuration) -> CloudDatabasesV5:
    api_key = configuration.get("api_key")
    service_url = configuration.get("service_url")
    os.environ["CLOUD_DATABASES_URL"] = service_url
    os.environ["CLOUD_DATABASES_APIKEY"] = api_key
    service = CloudDatabasesV5.new_instance()
    return service


def create_ibmcloud_api_client(configuration: Configuration) -> VpcV1:
    api_key = configuration.get("api_key")
    gen = configuration.get("generation", 2)
    url = configuration.get("service_url", 'https://api.au-syd.databases.cloud.ibm.com/v5/ibm/')
    authenticator = IAMAuthenticator(api_key)
    service = VpcV1('2020-06-02', authenticator=authenticator, generation=int(gen))
    service.service_url = url
    return service


def discover(discover_system: bool = True) -> Discovery:
    """
    Discover IBM Cloud capabilities offered by this extension.
    """
    logger.info("Discovering capabilities from chaostoolkit-ibmcloud")

    discovery = initialize_discovery_result(
        "chaostoolkit-ibmcloud", __version__, "ibmcloud")
    discovery["activities"].extend(load_exported_activities())
    return discovery


def tag_lb(lb_id: str, service: VpcV1, configuration: Configuration, *args):
    lb_ins = service.get_load_balancer(lb_id)._to_dict()
    crn = lb_ins['result']['crn']
    resource = {'resource_id': crn}
    resources = [resource]
    api_key = configuration.get("api_key")
    authenticator = IAMAuthenticator(api_key)
    global_tagging = GlobalTaggingV1(authenticator=authenticator)
    arr = ['chaostoolkit']
    arr.append(*args)
    global_tagging.attach_tag(resources=resources, tag_names=arr)


def tag_virtual_instance(instance_id: str, configuration: Configuration, service: VpcV1, tagname: str):
    ins = service.get_instance(id=instance_id)._to_dict()
    crn = (ins['result']['crn'])
    resource = {'resource_id': crn}
    resources = [resource]
    api_key = configuration.get("api_key")
    authenticator = IAMAuthenticator(api_key)
    global_tagging = GlobalTaggingV1(authenticator=authenticator)
    global_tagging.attach_tag(resources=resources, tag_names=['chaostoolkit', tagname])


###############################################################################
# Private functions
###############################################################################
def load_exported_activities() -> List[DiscoveredActivities]:
    """
    Extract metadata from actions and probes exposed by this extension.
    """
    activities = []
    activities.extend(discover_probes("ibmcloud.vpc.probes"))
    activities.extend(discover_actions("ibmcloud.vpc.actions"))
    activities.extend(discover_actions("ibmcloud.container.actions"))
    activities.extend(discover_actions("ibmcloud.middleware.probes"))
    activities.extend(discover_actions("ibmcloud.databases.probes"))
    return activities
