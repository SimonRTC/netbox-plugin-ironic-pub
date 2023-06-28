from setuptools import find_packages, setup

setup(
    name='netbox-ironic',
    version='0.1',
    description='An NetBox plugin to retrieve information from Openstack Ironic',
    install_requires=['openstacksdk'],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)