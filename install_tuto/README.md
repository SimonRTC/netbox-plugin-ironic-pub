# How to install NetBox and its plugin

To install NetBox and its plugin, you can do it by yourself or follow this tutorial that provides files to automatically deploy them in Kubernetes.

## Summary

1. [Requirements](#requirements)

2. [Helm Chart](#helm-chart)

3. [Installation of NetBox](#installation-of-netbox)

4. [Makefile](#makefile-commands)
    
    4.1. [Single-task commands](#single-task-commands)
    
    4.2. [Complete commands](#complete-commands)


## Requirements

You need to have helm and kubernetes installed on your computer / VM.

The `~/netbox-chart` folder of this repo must be the `/home/debian/netbox-chart` of your computer / VM so that the provided Makefile works. If it is not the case, modify the Makefile so that the paths correspond.

In the same folder as the Makefile, you have to store a file `netbox.sql` which initialize your database.

## Helm Chart

In your `Chart.yaml` file (in the `~/netbox-chart` folder of the repo), you can change the chart version of NetBox, Postgresql and Redis.

You can change NetBox version in the `values.yaml` file (in the `~/netbox-chart` folder of the repo) by replacing the version tag here :

```yaml
image:
  repository: netboxcommunity/netbox
  pullPolicy: IfNotPresent
  # Overrides the image tag whose default is the chart appVersion.
  tag: "v3.7.8"
```

## Installation of NetBox

After this part of the tuto, you will have something like this using the `tree` command:

```bash
debian@netbox-plugin:/$ tree /opt/ -L 2
/opt/
├── netbox
│   ├── CHANGELOG.md
│   ├── CONTRIBUTING.md
│   ├── LICENSE.txt
│   ├── NOTICE
│   ├── README.md
│   ├── SECURITY.md
│   ├── base_requirements.txt
│   ├── contrib
│   ├── docker-entrypoint.sh
│   ├── docs
│   ├── launch-netbox.sh
│   ├── mkdocs.yml
│   ├── netbox
│   ├── netbox_ironic
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── scripts
│   ├── setup.py
│   ├── upgrade.sh
```

To install NetBox, download NetBox files at `/opt/netbox` to have the right volume mount. You can find the correct version of NetBox here, by choosing the corresponding tag (here v3.7.8): https://github.com/netbox-community/netbox/tree/v3.7.8. This version has to be the same as your version in the `values.yaml` file.

You also have to install `python3.11` at this specific path `/usr/bin/python3.11` (or use a symlink).

Add the files `docker-entrypoint.sh` and `launch-netbox.sh` in your `/opt/netbox` folder (both available in the `opt/netbox` folder of this repo).

Add the file `configuration.py` in your `/opt/netbox/netbox/netbox` folder (available in the `opt/netbox/netbox/netbox` folder of this repo)

Add the folder `netbox-ironic` and the file `setup.py` of this repo in your `/opt/netbox` folder.

In your `/opt` folder, use the command `chown -R 1000:1000 netbox` so that you can easily modify the files and have all the permission access you need.

## Makefile commands

### Single-task commands

In the folder that contains the Makefile, you can run several single-task commands:

* `make install` will remove the previous venv in the `/opt/netbox` folder to reset it properly, install NetBox with the values defined in the provided `values.yaml` file;

* `make init_pod_db` will initialize the database pod with the `netbox.sql` file;

* `make add_superuser` will create a superuser for NetBox named 'root' with 'administrator' as password;

* `make collectstatic` will run the command `python /opt/netbox/netbox/manage.py collectstatic --noinput` in your venv;

* `make migrate` will run the commands `python /opt/netbox/netbox/manage.py makemigrations $(PLUGIN)` and `python /opt/netbox/netbox/manage.py migrate` in your venv;

* `make forward` will forward your VM port on your computer port so that you can access the NetBox frontend from your favorite web browser;

* `make delete_netbox` will delete the pod netbox (the deployment will automatically relaunch it);

* `make wait_netbox` will wait for netbox pod to be ready;

* `make uninstall` will uninstall the netbox app;

* `make delete` will delete all the PVs and PVCs.

### Complete commands

In the folder that contains the Makefile, you can run several complete commands:

* `make` (or `make run`) will `install init_pod_db add_superuser collectstatic migrate forward` so that you will have a running NetBox app if everything works fine;

* `make update` will `delete_netbox wait_netbox forward` so that it will relaunch the pod netbox to include modifications (e.g. plugin's modifications);

* `make clean` will `uninstall delete` so that you will have a clean working environment.

The command `make clean && make` will restart the NetBox app from scratch.
