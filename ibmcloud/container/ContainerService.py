from ibm_cloud_sdk_core import BaseService, DetailedResponse
from ibm_cloud_sdk_core.authenticators.authenticator import Authenticator
import json

from .common import get_sdk_headers

class ContainerService(BaseService):
    #TODO: Update the URL for container cloud for volume attach 
    DEFAULT_SERVICE_URL="https://containers.cloud.ibm.com/global/v2"

    def __init__(
        self,
        authenticator: Authenticator = None,
    ) -> None:
        """
        Construct a new client for the vpc service.

        :param str version: Requests the version of the API as of a date in the
               format `YYYY-MM-DD`. Any date up to the current date may be provided.
               Specify the current date to request the latest version.

        :param Authenticator authenticator: The authenticator specifies the authentication mechanism.
               Get up to date information from https://github.com/IBM/python-sdk-core/blob/master/README.md
               about initializing the authenticator of your choice.
        """

        BaseService.__init__(self,
                             service_url=self.DEFAULT_SERVICE_URL,
                             authenticator=authenticator)

    def add_raw_block_storage(self, 
                           createAttachementModel: 'CreateAttachementModel',
                           **kwargs) -> DetailedResponse:
        """
        Create volume attached , attach volume to worker node
        """

        if createAttachementModel is None:
            raise ValueError('createAttachementModel must be provided')

        headers = {}

        data = json.dumps(createAttachementModel)
        headers['content-type'] = 'application/json'
        headers['X-Auth-Resource-Group-ID'] = 'default'
        if 'headers' in kwargs:
            headers.update(kwargs.get('headers'))
        headers['Accept'] = 'application/json'

        url = '/storage/createAttachment'
        request = self.prepare_request(method='POST',
                                       url=url,
                                       headers=headers,
                                       data=data)
        response = self.send(request)
        return response        
        
    def delete_raw_block_storage(self, 
                           deleteAttachementModel: 'DeleteAttachementModel',
                           **kwargs) -> DetailedResponse:
        """
        Create volume attached , attach volume to worker node
        """

        if DeleteAttachementModel is None:
            raise ValueError('deleteAttachementModel must be provided')

        headers = {}

        data = json.dumps(deleteAttachementModel)
        headers['content-type'] = 'application/json'
        headers['X-Auth-Resource-Group-ID'] = 'default'
        if 'headers' in kwargs:
            headers.update(kwargs.get('headers'))
        headers['Accept'] = 'application/json'

        url = '/storage/deleteAttachment'
        request = self.prepare_request(method='POST',
                                       url=url,
                                       headers=headers,
                                       data=data)
        response = self.send(request)
        return response        

class DeleteAttachementModel(dict):
    """
    DeleteAttachementModel.

    :attr str cluster: clusterID or cluster name
    :attr str volumeID:  Volume ID for Block Storage
    :attr str volumeAttachmentID: Volume attachedmend to be retrived via VPC APIS
    :worker str worker: Worker node ID 
    """

    def __init__(self,
                 cluster: str,
                 volumeID: str,
                 volumeAttachmentID: str,
                 worker: str) -> None:
        dict.__init__(self, cluster=cluster, volumeAttachmentID=volumeAttachmentID, volumeID=volumeID, worker=worker)        

class CreateAttachementModel(dict):
    """
    CreateAttachementModel.

    :attr str cluster: clusterID or cluster name
    :attr str volumeID:  Volume ID for Block Storage
    :worker str worker: Worker node ID 
    """

    def __init__(self,
                 cluster: str,
                 volumeID: str,
                 worker: str) -> None:
        dict.__init__(self, cluster=cluster, volumeID=volumeID, worker=worker)



