SHELL := /bin/bash
NETBOX_POD = $(shell kubectl get pods -o json | jq -r '.items[0].metadata.name')
PGSQL_POD = netbox-postgresql-0
REDIS_POD = netbox-redis-master-0
PLUGIN = netbox_ironic

run: install init_pod_db add_superuser collectstatic migrate forward

update: delete_netbox wait_netbox forward

clean: uninstall delete

install:
	cd /opt/netbox && \
		rm -rf venv netbox_ironic.egg-info && \
		/usr/bin/python3.11 -m venv venv && \
		source venv/bin/activate && \
		pip install -r requirements.txt > /dev/null && \
		python3 setup.py develop > /dev/null && \
		cd /home/debian/netbox-chart && \
		deactivate;\
	helm install netbox --set postgresql.postgresqlPostgresPassword=netbox --set postgresql.postgresqlPassword=netbox --set redis.auth.password=netbox bootc/netbox -f values.yaml;\
	echo "kubectl port-forward --address 0.0.0.0 svc/netbox 8080:80"

init_pod_db:
	kubectl wait --for=condition=Ready pod/$(PGSQL_POD) --timeout=300s;\
	kubectl cp netbox.sql $(PGSQL_POD):/tmp;\
	kubectl exec -it $(PGSQL_POD) -- bash -c 'PGPASSWORD=netbox psql netbox < /tmp/netbox.sql -U netbox' > /dev/null ;\

add_superuser:
	kubectl wait --for=condition=Ready pod/$(REDIS_POD) --timeout=300s;\
	kubectl exec -it $(NETBOX_POD) -- bash -c 'cd /opt/netbox && \
		source venv/bin/activate && \
		DJANGO_SUPERUSER_PASSWORD=administrator netbox/manage.py createsuperuser --no-input --username root --email root@root.com'

collectstatic:
	kubectl wait --for=condition=Ready pod/$(NETBOX_POD) --timeout=300s;\
	kubectl exec -it $(NETBOX_POD) -- bash -c 'source /opt/netbox/venv/bin/activate && \
		python /opt/netbox/netbox/manage.py collectstatic --noinput && \
		deactivate'

migrate:
	kubectl wait --for=condition=Ready pod/$(NETBOX_POD) --timeout=300s;\
	kubectl exec -it $(NETBOX_POD) -- bash -c 'source /opt/netbox/venv/bin/activate && \
		python /opt/netbox/netbox/manage.py makemigrations $(PLUGIN) && \
		python /opt/netbox/netbox/manage.py migrate && \
		deactivate'

forward:
	kubectl port-forward --address 0.0.0.0 svc/netbox 8080:80



delete_netbox:
	kubectl delete pod $(NETBOX_POD)

wait_netbox:
	kubectl wait --for=condition=Ready pod/$(NETBOX_POD) --timeout=300s

uninstall:
	helm uninstall netbox

delete:
	kubectl delete pvc --all
	kubectl delete pv --all
