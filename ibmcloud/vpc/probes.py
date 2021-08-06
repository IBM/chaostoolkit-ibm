# -*- coding: utf-8 -*-
from typing import Any, Dict

from chaoslib.types import Configuration, Secrets
from ibmcloud import create_ibmcloud_api_client
from ibm_cloud_sdk_core import ApiException
from logzero import logger

# import simplejson as json


__all__ = ["get_virtual_servers"]


def get_virtual_servers(configuration: Configuration,
                        resource_group_id: str = None,
                        name: str = None,
                        vpc_id: str = None,
                        vpc_name: str = None,
                        vpc_crn: str = None) -> Dict[str, Any]:
    """
    List all instances.

    This request lists all instances in the region.
    :para Configuration configuration: Configuration contains API KEY
    :param str resource_group_id: (optional) Filters the collection to
        resources within one of the resource groups identified in a comma-separated
        list of resource group identifiers.
    :param str name: (optional) Filters the collection to resources with the
        exact specified name.
    :param str vpc_id: (optional) Filters the collection to resources in the
        VPC with the specified identifier.
    :param str vpc_crn: (optional) Filters the collection to resources in the
        VPC with the specified CRN.
    :param str vpc_name: (optional) Filters the collection to resources in the
        VPC with the exact specified name.
    :return: A `Dict[str, Any]` containing the result, headers and HTTP status code.
      
    """
    service = create_ibmcloud_api_client(configuration)
    try:
        instances = \
            service.list_instances(resource_group_id=resource_group_id, name=name, vpc_id=vpc_id, vpc_crn=vpc_crn,
                                   vpc_name=vpc_name).get_result()['instances']
    except ApiException as e:
        logger.error("List instances failed with status code " +
                     str(e.code) + ": " + e.message)
    return instances
