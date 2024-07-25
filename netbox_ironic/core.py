import openstack

from extras.plugins import get_plugin_config

class OpenstackConnector:

    def __init__(self):
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

    def get_ironic_info(self, baremetal_node_uuid):
        return self.conn.baremetal.get_node(baremetal_node_uuid)

    def get_port_info(self, instance_uuid):
        neutron=self.conn.network
        return list(neutron.ports(device_id=instance_uuid))

    def get_network_info(self, network_id):
        neutron=self.conn.network
        networks = neutron.networks()
        for network in networks:
            if network['id'] == network_id:
                return network
        return None

    def get_nova_info(self, server_id):
        try:
            return self.conn.compute.get_server(server_id)
        except Exception:
            return None

    def get_server_actions(self, server_id):
        try:
            return list(self.conn.compute.server_actions(server_id))
        except Exception:
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
