from uuid import UUID
from ipaddress import ip_address, IPv4Address

def get_baremetal_node_id(instance):
    baremetal_node_id = None
    for field, value in dict(instance.get_custom_fields()).items():
        if field.name == "baremetal_node_id" and value != '—':
            baremetal_node_id = value
    return baremetal_node_id

def is_valid_uuid(uuid_to_test, version=4):
    try:
        UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return True

def is_valid_ipv4(ip_to_test):
    try:
        return type(ip_address(ip_to_test))==IPv4Address
    except ValueError:
        return False
