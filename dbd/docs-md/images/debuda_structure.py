# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

"""
This script generates a diagram of the communication flow in Debuda.
To run it, you need to install the `diagrams` package:
pip install diagrams
"""

from diagrams import Cluster, Diagram, Edge
from diagrams.programming.flowchart import Action
from diagrams.generic import Node


graph_attr = {
    "layout":"dot",
    "compound":"true",
    "splines":"spline",
    }

node_attr = {
    "shape":"box",
	"labelloc": "c",
	"height": "0.8",
	"width": "2",
    }

with Diagram(name="Debuda's communication flow", filename="debuda-structure", show=False, graph_attr=graph_attr):
	contexts_holder = Cluster("0", graph_attr={"label":"Debuda Contexts"})
	with contexts_holder:	
		contexts = [
			Node("Limited", **node_attr),
			Node("Buda", **node_attr),
			Node("Metal", **node_attr),
		]

	ifcs_holder = Cluster("1", graph_attr={"label":"Device interfaces"})
	with ifcs_holder:
		ifcs = [
			Node("Caching mechanism", **node_attr),
			Node("Local (pybind)", **node_attr),
			Node("Remote server", **node_attr),
			Node("Cached", **node_attr),
		]

	device = Node("Device", **node_attr)

	contexts[1] >> Edge(ltail="cluster_0", lhead="cluster_1", color="black") >> ifcs[0]
	ifcs[0] >> Edge(color="black") >> [ifcs[1], ifcs[2]] >> Edge(color="black") >> device
