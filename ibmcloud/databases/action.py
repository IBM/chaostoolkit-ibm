# -*- coding: utf-8 -*-
from logzero import logger
from chaoslib.types import Configuration
from ibmcloud import create_ibmcloud_databases_client
from ibm_cloud_databases import CloudDatabasesV5

# import simplejson as json


__all__ = ["kill_connection"]


def kill_connection(
        configuration: Configuration,
        deployment_id: str
):
    service = create_ibmcloud_databases_client(configuration)
    service.kill_connections(id=deployment_id)
