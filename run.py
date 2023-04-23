"""
Run the fitting
"""

from aiida import orm, load_profile
from ase.build import bulk
from datagen import run_example

if __name__ == "__main__":

    load_profile()
    #
    # setup
    prim = bulk('Ni', cubic=True)
    prim_node = orm.StructureData(ase=prim)
    run_example(prim_node)