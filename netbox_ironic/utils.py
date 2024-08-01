def get_baremetal_node_id(instance):
    baremetal_node_id = None
    for field, value in dict(instance.get_custom_fields()).items():
        if field.name == "baremetal_node_id" and value != '—':
            baremetal_node_id = value
    return baremetal_node_id
