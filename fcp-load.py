from pathlib import Path
from aiida import manage, orm, profile_context
from aiida.storage.sqlite_zip.backend import SqliteZipBackend
from aiida.tools.visualization import Graph
from aiida import load_profile
from hiphive import ForceConstantPotential

archive_profile = SqliteZipBackend.create_profile('hiphive-example.aiida')
print(archive_profile)
load_profile(archive_profile)

g = Graph()
g.recurse_ancestors(orm.load_node("6280fc"))
g.graphviz.render("fcp-provenance", format="png")
fcp_node = orm.load_node("6280fc")
print(fcp_node.base.repository.list_object_names())
fcp_node.base.repository.copy_tree(Path("fcp-node").absolute(), ".")
fcp = ForceConstantPotential.read("fcp-node/fcc-nickel.fcp")
print(fcp)
