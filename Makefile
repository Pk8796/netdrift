.PHONY: lab-up lab-down check heal watch test lint

lab-up:
	sudo containerlab deploy -t lab/topo.clab.yml

lab-down:
	sudo containerlab destroy -t lab/topo.clab.yml

check:
	netdrift check

heal:
	netdrift reconcile --auto-heal --once

watch:
	netdrift reconcile --auto-heal --metrics

test:
	pytest -q

lint:
	ruff check netdrift tests
