from extras.plugins import PluginConfig

class NetBoxIronicConfig(PluginConfig):
    name = 'netbox_ironic'
    verbose_name = ' NetBox Ironic'
    description = 'Manage Openstack Ironic nodes in Netbox'
    version = '0.1'
    base_url = 'ironic'
    required_settings = ['OS_AUTH_URL', 'OS_USERNAME', 'OS_PASSWORD']
    default_settings = {
        'OS_PROJECT_DOMAIN_NAME': 'Default',
        'OS_REGION_NAME': 'RegionOne',
        'OS_USER_DOMAIN_NAME': 'Default',
        'OS_PROJECT_NAME': 'admin',
        'OS_BAREMETAL_ENDPOINT_OVERRIDE': '',
        'OS_COMPUTE_ENDPOINT_OVERRIDE': '',
    }

config = NetBoxIronicConfig