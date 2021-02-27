# -*- coding: utf-8 -*-
from typing import Any, Dict

from chaoslib.types import Configuration, Secrets
from ibmcloud import create_ibmcloud_api_client, tag_virtual_instance, tag_lb
from ibmcloud.vpc.constants import REBOOT, START, STOP
from ibm_cloud_sdk_core import ApiException
from ibm_cloud_sdk_core import BaseService, DetailedResponse
from ibm_vpc.vpc_v1 import VolumeIdentityById, VolumeIdentity

from ibm_vpc.vpc_v1 import NetworkACLPrototypeNetworkACLByRules as ACLNetworkByRules
from ibm_vpc.vpc_v1 import  NetworkACLRulePrototypeNetworkACLContextNetworkACLRuleProtocolAll as ACLRule
from ibm_vpc.vpc_v1 import VPCIdentityById, NetworkACLIdentityById, SubnetPatch
from logzero import logger
import paramiko
import time

__all__ = [
            "create_instance_action", "delete_load_balancer", 
            "remove_volume_from_instance", "add_volume_to_instance", 
            "add_network_latency","start_multiple_instances", 
            "stop_multiple_instances",
            "delete_load_balancer_members",
            "cordon_subnet"
        ]

class CommandExecuter(object):
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password
    
    def __enter__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.hostname, username=self.username, password=self.password)
        return self.client

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.client.close()


def add_network_latency(configuration: Configuration, 
                        instance_id: str,                        
                        username: str,
                        password: str,
                        duration: int = 30,
                        delay: int = 300,
                        jitter: int = 50,
                        interface: str = None,
                        hostname: str = None,
                        timeout: int = 60,
                        tag: bool = False ):    
    if hostname == None:
        service = create_ibmcloud_api_client(configuration)
        if tag:
            tag_virtual_instance(configuration=configuration, instance_id=instance_id, service=service, tagname='add_network_latency')
        response = service.list_instance_network_interfaces(instance_id=instance_id)._to_dict()     
        output_dict = [attachment for attachment in response['result']['network_interfaces'] if len(attachment['floating_ips'])>0]   
        hostname = output_dict[0]['floating_ips'][0]['address']

    with CommandExecuter(hostname=hostname, username=username, password=password) as client:                
        #client.exec_command('ls')
        #If interface not provided pick up the first none local interface
        if interface == None:
            _, stdout, _ = client.exec_command("ip addr | grep UP | grep -v LOOPBACK | awk -F':' '{print $2}' | sed -e 's/^[[:space:]]*//'")
            interface = next(stdout).strip()
        _, stdout, _ = client.exec_command(f'sudo tc qdisc add dev {interface} root netem delay {delay}ms {jitter}ms;sleep {duration};sudo tc qdisc del dev {interface} root')

def cordon_subnet(configuration: Configuration,
                      vpc_id: str,
                      zone: str = None,
                      subnet_id: str = None):
    """
    cordon subnet create and attach ACL rule to deny all, ingress/egress traffic from specific subnet
    This logic check the current ACL name and create new acl with the following naming chaos-<current_acl>
    This logic enable to rollback this action when needed
    to cordon subnet 
        "method": [
        {
            "type": "action",
            "name": "ACL cordon instances at zone au-syd-1",
            "provider": {
                "type": "python",
                "module": "ibmcloud.vpc.actions",
                "func": "cordon_subnet",
                "arguments": {
                    "vpc_id": "r026-fcfd2d0e-c752-4b88-8282-0f714a812c19",
                    "subnet_id": "02i7-c7d8183d-85da-4b0f-9fde-a1c022fe37e2",
                    "zone": "au-syd-2"
                }
            }
        }
    ]
    attr vpc_id str: VPC  Id
    attr zone str: Optional - Zone useful to apply to all subnet in specific Zone to simulate zonal failure
    attr subnet_id str: Optional - subnet ID attack specific subnet id
    """

    if subnet_id is None and zone is None:
        raise ValueError('Either subnet_id or zone_id or both must be provided')
    
    service = create_ibmcloud_api_client(configuration)

    # Get target subnets
    subnets = []
    
    if vpc_id is not None:
        # list all subnet
        subnets = [subnet for subnet in service.list_subnets()._to_dict()['result']['subnets'] if subnet['vpc']['id'] == vpc_id]

    if subnet_id is not None:
        subnets = [subnet for subnet in subnets if subnet['id'] == subnet_id]

    if zone is not None:
        subnets = [subnet for subnet in subnets if subnet['zone']['name'] == zone]
    

    if len(subnets) == 0:
        raise ("No subnets match found")

    for subnet in subnets:

        # Create ACL with deny all rules

        # Create Rule and add it to rule List  NetworkACLRulePrototypeNetworkACLContextNetworkACLRuleProtocolAll
        chaos_acl_name = 'chaos-' + subnet['network_acl']['name']
        
        rules = [
                ACLRule(
                    action=ACLRule.ActionEnum.DENY, 
                    source='0.0.0.0/0', 
                    protocol=ACLRule.ProtocolEnum.ALL, 
                    destination='0.0.0.0/0', 
                    direction=ACLRule.DirectionEnum.INBOUND
                ),
                ACLRule(
                    action=ACLRule.ActionEnum.DENY, 
                    source='0.0.0.0/0', 
                    protocol=ACLRule.ProtocolEnum.ALL, 
                    destination='0.0.0.0/0', 
                    direction=ACLRule.DirectionEnum.OUTBOUND
                )
        ]
        # Create NetworkACLPrototypeNetworkACLByRules using previous rule
        vpc_identity = VPCIdentityById(vpc_id)
        acl = ACLNetworkByRules(vpc=vpc_identity, name=chaos_acl_name,rules=rules)
        # service.create_network_acl()
        network_acl = service.create_network_acl(network_acl_prototype=acl)
        acl = network_acl._to_dict()['result']
        network_acl_identity = NetworkACLIdentityById(id=acl['id'])
        subnet_patch = SubnetPatch(network_acl = network_acl_identity)
        service.update_subnet (subnet['id'], subnet_patch)

def uncordon_subnet(configuration: Configuration,
                      vpc_id: str,
                      zone: str = None,
                      subnet_id: str = None,
                      delete_chaos_acl: bool =True ):
    """
    Effective only as rollbakc to cordon subnet create attach the subnet to original subnet 
    This logic enable to rollback this action when needed
        "method": [
        {
            "type": "action",
            "name": "ACL cordon instances at zone au-syd-1",
            "provider": {
                "type": "python",
                "module": "ibmcloud.vpc.actions",
                "func": "cordon_subnet",
                "arguments": {
                    "vpc_id": "r026-fcfd2d0e-c752-4b88-8282-0f714a812c19",
                    "subnet_id": "02i7-c7d8183d-85da-4b0f-9fde-a1c022fe37e2",
                    "zone": "au-syd-2"
                }
            }
        }
    ]    
    attr vpc_id str: VPC  Id
    attr zone str: Optional - Zone useful to apply to all subnet in specific Zone to simulate zonal failure
    attr subnet_id str: Optional - subnet ID attack specific subnet id
    """
    if subnet_id is None and zone is None:
        raise ValueError('Either subnet_id or zone_id or both must be provided')
    
    service = create_ibmcloud_api_client(configuration)

    # Get target subnets
    subnets = []
    
    if vpc_id is not None:
        # list all subnet
        subnets = [subnet for subnet in service.list_subnets()._to_dict()['result']['subnets'] if subnet['vpc']['id'] == vpc_id]

    if subnet_id is not None:
        subnets = [subnet for subnet in subnets if subnet['id'] == subnet_id]

    if zone is not None:
        subnets = [subnet for subnet in subnets if subnet['zone']['name'] == zone]
    

    if len(subnets) == 0:
        raise ("No subnets match found")

    for subnet in subnets:
        # Check if the ACL name contains chaos- at the begining 
        # If not make a warning and skip this subnet to other one 
        if subnet['network_acl']['name'].startswith('chaos-'):
            # Get original ACL ID to restore it
            original_acl_name = subnet['network_acl']['name'][6:]
            # Get Chaos ACL ID to delete for clean up
            chaos_acl_id = subnet['network_acl']['id']
            acls = service.list_network_acls()._to_dict()['result']['network_acls']
            original_acl = [acl for acl in acls if acl['name'] == original_acl_name]
            network_acl_identity = NetworkACLIdentityById(id=original_acl[0]['id'])
            subnet_patch = SubnetPatch(network_acl = network_acl_identity)
            service.update_subnet (subnet['id'], subnet_patch)
            if delete_chaos_acl: service.delete_network_acl(chaos_acl_id)
        else:
            logger.warn("The following subnet does not start with chaos- will be skipped")

def remove_volume_from_instance(configuration: Configuration,
                              volume_id: str,
                              instance_id: str,
                              tag: bool = False):
    service = create_ibmcloud_api_client(configuration)
    try:
        if tag:
            tag_virtual_instance(configuration=configuration, instance_id=instance_id, service=service, tagname='remove_volume_from_instance')            
        res = service.list_instance_volume_attachments(instance_id=instance_id)
        dict = res._to_dict()
        output_dict = [attachment for attachment in dict['result']['volume_attachments'] if attachment['volume']['id'] == volume_id]
        volume_attachment_id = output_dict[0]['id']
        service.delete_instance_volume_attachment(instance_id=instance_id, id=volume_attachment_id)
    except  ApiException as e:
        logger.error("Action instances failed with status code " +
              str(e.code) + ": " + e.message)

def add_volume_to_instance(configuration: Configuration,
                           volume_id: str,
                           instance_id: str,
                           auto_delete: bool = None,
                           tag: bool = False):
    service = create_ibmcloud_api_client(configuration)
    try:
        if tag:
            tag_virtual_instance(configuration=configuration, instance_id=instance_id, service=service, tagname='add_volume_to_instance')  
        identity = VolumeIdentityById(volume_id)
        service.create_instance_volume_attachment(instance_id=instance_id, volume=identity, delete_volume_on_instance_delete=auto_delete)
    except ApiException as e:
        logger.error("Action add_volume_to_instance failed with status code " +
              str(e.code) + ": " + e.message)

def create_instance_action(configuration: Configuration,
                          type: str,
                          instance_id: str,
                          force: bool = None,
                          tag: bool = False):
    service = create_ibmcloud_api_client(configuration)
    try:
        if tag:
            tag_virtual_instance(configuration=configuration, instance_id=instance_id, service=service, tagname='create_instance_action')  
        service.create_instance_action(type=type ,instance_id=instance_id, force=force)
    except  ApiException as e:
        logger.error("Action instances failed with status code " +
              str(e.code) + ": " + e.message)

def stop_multiple_instances(configuration: Configuration,
                            vpc_id: str,
                            zone: str = None,
                            random: bool = False,
                            tag: bool = False                            
                  ):
    service = create_ibmcloud_api_client(configuration)
    instances = service.list_instances(vpc_id=vpc_id).get_result()['instances']
    output_dict = [instance for instance in instances if instance['zone']['name'] == zone]   
    for instance in output_dict:
        if instance['status']=='running':
            service.create_instance_action(type='stop' ,instance_id=instance['id'], force=False)
            if tag:
                tag_virtual_instance(configuration=configuration, instance_id=instance['id'], service=service, tagname='stop_multiple_instances')      


def start_multiple_instances(configuration: Configuration,
                            vpc_id: str,
                            zone: str = None,
                            random: bool = False,
                            tag: bool = False                            
                  ):
    service = create_ibmcloud_api_client(configuration)
    instances = service.list_instances(vpc_id=vpc_id).get_result()['instances']
    output_dict = [instance for instance in instances if instance['zone']['name'] == zone]   
    for instance in output_dict:
        if instance['status']=='stopped':            
            service.create_instance_action(type='start' ,instance_id=instance['id'], force=False)
            if tag:
                tag_virtual_instance(configuration=configuration, instance_id=instance['id'], service=service, tagname='start_multiple_instances')      

def delete_load_balancer(configuration: Configuration, id: str):
    service = create_ibmcloud_api_client(configuration)
    try:
        service.delete_load_balancer(id=id)
    except ApiException as e:
        logger.error("Delete LoadBalancer failed with status code " +
              str(e.code) + ": " + e.message)



def delete_load_balancer_members(configuration: Configuration,
                                 id: str,
                                 vpc_id: str,
                                 zone: str = None,
                                 instance_id: str = None,
                                 pool_id: str = None,
                                 random: bool = False):
    service = create_ibmcloud_api_client(configuration)
    try:
        #List Load Balancer Pool
        lb_pools = service.list_load_balancer_pools(load_balancer_id=id)._to_dict()['result']['pools']

        #Filter pools if Pool Id specified
        if pool_id != None:
            lb_pools = [lb_pool for lb_pool in lb_pools  if  pool_id != None and lb_pool['id'] == pool_id]

        #List instanceas in specific VPCS
        instances = service.list_instances(vpc_id=vpc_id).get_result()['instances']

        #Filter instances in case of instnace_id mentioned 
        if instance_id != None:
            instances = [instance for instance in instances if instance['id'] == instance_id]

        #Filter zone 
        if zone != None:
            instances = [instance for instance in instances if instance['zone']['name'] == zone] 

        for pool in lb_pools:
            member_list = service.list_load_balancer_pool_members(load_balancer_id=id, pool_id=pool['id'])._to_dict()
            all_members = member_list['result']['members']
            for member in all_members: 
                #print(member)               
                ip_address =  member['target']['address']
                port = member['port']
                weight = member['weight']
                current_instance = [instance for instance in instances if instance['network_interfaces'][0]['primary_ipv4_address'] == ip_address]                
                if len(current_instance) > 0:
                    tag_lb(id, service, configuration, ip_address + ':' + str(port) +':' + str(weight))
                    service.delete_load_balancer_pool_member(id, pool['id'],member['id'])
                    #TODO Replace with checking lb status
                    time.sleep(30) 

                

    except ApiException as e:
        logger.error("Delete Load balancer memebers " + str(e.code) + ": " + e.message)
