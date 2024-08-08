from uuid import UUID
import socket

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
    segments = ip_to_test.split('.')
    if len(segments) != 4 :
        return False
    try:
        socket.inet_aton(ip_to_test)
    except socket.error:
        return False
    return True
