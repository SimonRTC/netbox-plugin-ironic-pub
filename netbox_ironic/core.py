import openstack
from openstack.exceptions import SDKException
from .exception import AtelierException
from django.contrib import messages

from extras.plugins import get_plugin_config

class OpenstackConnector:

    def __init__(self):
        try:
            self.conn = openstack.connect(
                auth_url=get_plugin_config('netbox_ironic', 'OS_AUTH_URL'),
                project_name=get_plugin_config('netbox_ironic', 'OS_PROJECT_NAME'),
                username=get_plugin_config('netbox_ironic', 'OS_USERNAME'),
                password=get_plugin_config('netbox_ironic', 'OS_PASSWORD'),
                region_name=get_plugin_config('netbox_ironic', 'OS_REGION_NAME'),
                user_domain_name=get_plugin_config('netbox_ironic', 'OS_USER_DOMAIN_NAME'),
                project_domain_name=get_plugin_config('netbox_ironic', 'OS_PROJECT_DOMAIN_NAME'),
                baremetal_endpoint_override=get_plugin_config('netbox_ironic', 'OS_BAREMETAL_ENDPOINT_OVERRIDE'),
                compute_endpoint_override=get_plugin_config('netbox_ironic', 'OS_COMPUTE_ENDPOINT_OVERRIDE'),
            )
        except SDKException as e:
            raise AtelierException(messages.ERROR, 'Openstack', e)

    def get_ironic_info(self, baremetal_node_uuid):
        try:
            return self.conn.baremetal.get_node(baremetal_node_uuid)
        except SDKException as e:
            raise AtelierException(messages.WARNING, 'Ironic', e)

    def get_port_info(self, instance_uuid):
        try:
            neutron=self.conn.network
            return list(neutron.ports(device_id=instance_uuid))
        except SDKException as e:
            raise AtelierException(messages.WARNING, 'Neutron (ports)', e)

    def get_network_info(self, network_id):
        try:
            neutron=self.conn.network
            return neutron.get_network(network_id)
        except SDKException as e:
            raise AtelierException(messages.WARNING, 'Neutron (networks)', e)

    def get_nova_info(self, server_id):
        try:
            return self.conn.compute.get_server(server_id)
        except SDKException as e:
            raise AtelierException(messages.WARNING, 'Nova', e)

    def get_server_actions(self, server_id):
        try:
            return list(self.conn.compute.server_actions(server_id))
        except SDKException:
            return []

    def get_node_actions(self, node):
        request = node._prepare_request(requires_id=True)

        response = self.conn.session.get(
            openstack.utils.urljoin(self.conn.endpoint_for("baremetal", "public"), "nodes", node["uuid"], "/history"),
            headers=request.headers,
            microversion='1.78',
            microversion_service_type='baremetal'
        )
        return response.json()['history']
