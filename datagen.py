"""
Prepare training structures for FCC-Ni using an EMT calculator and a
Monte Carlo rattle approach for generating displacements.

Runs in approximately 10 seconds on an Intel Core i5-4670K CPU.
"""
from pathlib import Path
from ase.calculators.emt import EMT
from ase.calculators.singlepoint import SinglePointCalculator
from hiphive.structure_generation import generate_mc_rattled_structures
from hiphive import ClusterSpace, StructureContainer, ForceConstantPotential
from hiphive.utilities import prepare_structures
from trainstation import Optimizer

from aiida.engine import calcfunction, workfunction
from aiida import orm



@calcfunction
def generate_mc_rattled(node, n_structures, rattled_std, minimum_distance):
    """Generate MC rattled structures"""
    atoms_ideal = node.get_ase()
    rattled_std = rattled_std.value
    minimum_distance = minimum_distance.value
    n_structures = n_structures.value
    structures = generate_mc_rattled_structures(atoms_ideal, n_structures, rattled_std, minimum_distance)
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
def fit_hiphive(prim, atoms_ideal, **kwargs):
    """Perform fitting with hiphive"""
    print(kwargs)
    # set up cluster space - these are hard-coded here for simplicity
    cutoffs = [5.0, 4.0, 4.0]
    prim = prim.get_ase()
    cs = ClusterSpace(prim, cutoffs)
    print(cs)
    cs.print_orbits()

    # Deserialize the stored data
    struct_labels = {int(s.split('_')[1]):s for s in kwargs if 'structure_' in s}
    force_labels = {int(s.split('_')[1]):s for s in kwargs if 'forces_' in s}
    rattled_structures = []
    for sid, slabel in struct_labels.items():
        forces = kwargs[force_labels[sid]].get_array('forces')
        atoms = kwargs[slabel].get_ase()
        atoms.calc = SinglePointCalculator(atoms=atoms, forces=forces)
        rattled_structures.append(atoms)

    atoms_ideal = atoms_ideal.get_ase()

    # ... and structure container
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

@workfunction
def run_example(prim_node):
    """Run a hiphive fitting example"""
    # parameters - hardcoded here for simplicity
    cell_size = 4
    n_structures = 5
    cell_size = 4
    rattle_std = 0.03
    minimum_distance = 2.3

    ideal_node = orm.StructureData(ase=prim_node.get_ase().repeat(cell_size))
    rattled = generate_mc_rattled(ideal_node, orm.Int(n_structures), orm.Float(rattle_std), orm.Float(minimum_distance))

    fit_data = {}
    for key, value in rattled.items():
        i = int(key.split('_')[1])
        force_node = run_emt(value)
        fit_data[f'forces_{i:05d}'] = force_node
        fit_data[f'structure_{i:05d}'] = value
    
    fit_output = fit_hiphive(prim_node, ideal_node, **fit_data)
    print("Created data", fit_output)
    return fit_output