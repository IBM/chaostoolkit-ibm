# -*- coding: utf-8 -*-
from logzero import logger
from chaoslib.types import Configuration
from ibmcloud import create_ibmcloud_databases_client
from ibm_cloud_databases import CloudDatabasesV5

# import simplejson as json


__all__ = ["probe_deployment"]


def probe_deployment(
        configuration: Configuration,
        deployment_id: str
) -> bool:
    """
    Very simple probe to check

    :param Configuration configuration: Configuration for the IBM cloud configuration
    :param str deployment_id: deployment_id as appear on IBM cloud portal
    :return bool: return True if exists
    """
    service = create_ibmcloud_databases_client(configuration)
    try:
        service.get_deployment_info(id=deployment_id).get_result()
        return True
    except:
        return False
