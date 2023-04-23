"""
Prepare training structures for FCC-Ni using an EMT calculator and a
Monte Carlo rattle approach for generating displacements.

Runs in approximately 10 seconds on an Intel Core i5-4670K CPU.
"""
from pathlib import Path
from aiida import orm, load_profile
from ase.io import write
from ase.build import bulk
from ase.calculators.emt import EMT
from ase.calculators.singlepoint import SinglePointCalculator
from hiphive.structure_generation import generate_mc_rattled_structures
from ase.io import read
from hiphive import ClusterSpace, StructureContainer, ForceConstantPotential
from hiphive.utilities import prepare_structures
from trainstation import Optimizer

from aiida.engine import calcfunction



@calcfunction
def generate_mc_rattled(node, n_structures, rattled_std, minimum_distance):
    """Generate MC rattled structures"""
    atoms_ideal = node.get_ase()
    rattled_std = rattled_std.value
    minimum_distance = minimum_distance.value
    n_structures = n_structures.value
    structures = generate_mc_rattled_structures(atoms_ideal, n_structures, rattle_std, minimum_distance)
    out = {f"structure_{i:05d}": orm.StructureData(ase=atoms) for i, atoms in enumerate(structures)}
    return out

@calcfunction
def run_emt(node):
    """Run EMT to compute the forces for an atom""" 
    atoms = node.get_ase()
    atoms.calc = EMT()
    forces = atoms.get_forces()
    array = orm.ArrayData()
    array.set_array("forces", forces)
    return array

@calcfunction
def fit_hiphive(atoms_ideal, **kwargs):
    """Perform fitting with hiphive"""
    print(kwargs)
    # set up cluster space
    cutoffs = [5.0, 4.0, 4.0]
    cs = ClusterSpace(prim, cutoffs)
    print(cs)
    cs.print_orbits()

    # ... and structure container
    struct_labels = {int(s.split('_')[1]):s for s in kwargs if 'structure_' in s}
    force_labels = {int(s.split('_')[1]):s for s in kwargs if 'forces_' in s}
    rattled_structures = []
    for sid, slabel in struct_labels.items():
        forces = kwargs[force_labels[sid]].get_array('forces')
        atoms = kwargs[slabel].get_ase()
        atoms.calc = SinglePointCalculator(atoms=atoms, forces=forces)
        rattled_structures.append(atoms)

    atoms_ideal = atoms_ideal.get_ase()

    structures = prepare_structures(rattled_structures, atoms_ideal)
    sc = StructureContainer(cs)
    for structure in structures:
        sc.add_structure(structure)
    print(sc)

    opt = Optimizer(sc.get_fit_data())
    opt.train()
    print(opt)

    # construct force constant potential
    fcp = ForceConstantPotential(cs, opt.parameters)
    fcp.write('fcc-nickel.fcp')
    print(fcp)
    # output node
    fcp_node = orm.SinglefileData(Path('fcc-nickel.fcp').absolute())
    opt_summary = orm.Str(opt.__str__())
    return {'fcp': fcp_node, 'opt': opt_summary}

if __name__ == "__main__":

    load_profile()
    #
    # parameters
    n_structures = 5
    cell_size = 4
    rattle_std = 0.03
    minimum_distance = 2.3

    # setup
    prim = bulk('Ni', cubic=True)
    atoms_ideal = orm.StructureData(ase=prim.repeat(cell_size))

    rattled = generate_mc_rattled(atoms_ideal, orm.Int(n_structures), orm.Float(rattle_std), orm.Float(minimum_distance))

    fit_data = {}
    for key, value in rattled.items():
        i = int(key.split('_')[1])
        force_node = run_emt(value)
        fit_data[f'forces_{i:05d}'] = force_node
        fit_data[f'structure_{i:05d}'] = value
    
    fit_output = fit_hiphive(atoms_ideal, **fit_data)
    print("Created data", fit_output)
