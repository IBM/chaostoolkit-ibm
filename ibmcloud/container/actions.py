from chaoslib.types import Configuration, Secrets
from ibmcloud import create_ibmcloud_api_client, tag_virtual_instance, tag_lb
from ibm_cloud_sdk_core import ApiException
from ibm_cloud_sdk_core import BaseService, DetailedResponse

from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from logzero import logger
from .ContainerService import ContainerService, CreateAttachementModel, DeleteAttachementModel
from ibm_vpc import VpcV1

__all__ = [
    "detach_volume_from_worker", "attach_volume_to_worker"
]


def detach_volume_from_worker(configuration: Configuration,
                              cluster_id: str,
                              volume_id: str,
                              worker_id: str):
    """
    detach_volume_from_worker: attach volume to worker nodes
    attr cluster_id str: Cluster ID 
    attr volume_id str: VolumeID
    attr worker_id str: Worker node ID
    """

    # Retrieve API Key from Configuration and create authenticator Object
    api_key = configuration.get("api_key")
    authenticator = IAMAuthenticator(api_key)

    # Create vpcV1 Api Service to retrieve the volumeattachementID needed by delete attachement method
    service = VpcV1('2020-06-02', authenticator=authenticator, generation=int(2))
    url = configuration.get("service_url", 'https://dallas.iaas.cloud.ibm.com/v1')
    service.service_url = url
    volume = service.get_volume(volume_id)._to_dict()
    if (volume['result']['volume_attachments'][0] is None):
        raise ValueError('This disk is not attached to any worker nodes')
    volume_attachment = volume['result']['volume_attachments'][0]['id']

    # Create Delete Attachement Model
    deleteAttachement = DeleteAttachementModel(cluster=cluster_id, volumeID=volume_id,
                                               volumeAttachmentID=volume_attachment, worker=worker_id)

    # Instatiate ContaierService to connect containers API
    service = ContainerService(authenticator)
    service.delete_raw_block_storage(deleteAttachement)


def attach_volume_to_worker(configuration: Configuration,
                            cluster_id: str,
                            volume_id: str,
                            worker_id: str):
    """
    attach_volume_to_worker: attach volume to worker nodes
    attr cluster_id str: Cluster ID 
    attr volume_id str: VolumeID
    attr worker_id str: Worker node ID
    """

    # Retrieve API Key from Configuration and create authenticator Object
    api_key = configuration.get("api_key")
    authenticator = IAMAuthenticator(api_key)

    # Create Attached model using input param
    attachement = CreateAttachementModel(cluster=cluster_id, volumeID=volume_id, worker=worker_id)

    # Instatiate ContaierService to connect containers API
    service = ContainerService(authenticator)
    service.add_raw_block_storage(attachement)
