"""
Load data from the archive, create provenance graph and exact the FCP stored
"""
from pathlib import Path
from aiida import orm
from aiida.storage.sqlite_zip.backend import SqliteZipBackend
from aiida.tools.visualization import Graph
from aiida import load_profile
from hiphive import ForceConstantPotential

archive_profile = SqliteZipBackend.create_profile('hiphive-example.aiida')
print(archive_profile)
load_profile(archive_profile)

uuid = "945e427"
g = Graph()
g.recurse_ancestors(orm.load_node(uuid))
g.graphviz.render("fcp-provenance", format="png")
fcp_node = orm.load_node(uuid)
print(fcp_node.base.repository.list_object_names())
fcp_node.base.repository.copy_tree(Path("fcp-node").absolute(), ".")
fcp = ForceConstantPotential.read("fcp-node/fcc-nickel.fcp")
print(fcp)
