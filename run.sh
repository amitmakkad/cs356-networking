#!/usr/bin/bash

readonly ENV="env"

gnome-terminal --tab -- bash -c "source $ENV/bin/activate; sudo mn -c; ryu-manager node_discovery.py --observe-links; exec bash"
gnome-terminal --tab -- bash -c "sudo mn -c; sudo python3 custom_topo.py; exec bash"