#!/usr/bin/env python3
"""Export physical noiseless circuits, full ledgers and exact tableau evidence.

No decoder, DEM, fault emission, Monte Carlo or solver is called.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from gross_design_bandle.codes.reference_profiles import load_reference_code
from gross_design_bandle.lpu.reference import build_reference_lpu
from gross_design_bandle.surgery.deformation import compile_deformation
from gross_design_bandle.circuits.protocol import build_physical_x1
from gross_design_bandle.circuits.memory import memory_schedule
from gross_design_bandle.circuits.primitive import primitive_schedule
from gross_design_bandle.circuits.checks import Check
from gross_design_bandle.algebra.pauli import Pauli
from gross_design_bandle.circuits.schedule import validate
from gross_design_bandle.validation.physical import check_tableau
from gross_design_bandle.validation.connectivity import installed_connectivity
from gross_design_bandle.integrations.sliding_window import extract_layers,DONOR_SHA256


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    files=[]
    def save(name,value):
        path=args.output_dir/name
        path.write_text(value if isinstance(value,str) else json.dumps(value,indent=2)+'\n')
        files.append({'path':name,'bytes':path.stat().st_size,'sha256':sha256(path.read_bytes()).hexdigest()})
    c=load_reference_code('gross','physical')
    df=compile_deformation(build_reference_lpu(c,'X'))
    physical=build_physical_x1(df,rounds=10)
    save('gross_X1_C10.stim',str(physical.to_stim())+'\n')
    save('gross_X1_C10.json',physical.to_dict())
    memory=memory_schedule(c,10)
    save('gross_memory_C10.stim',str(memory.to_stim())+'\n')
    save('gross_memory_C10.json',memory.to_dict())
    bell=Check.bell('signed_YZ',Pauli.from_word('YZ',('d0','d1'),-1),('d0',))
    primitive=primitive_schedule(bell)
    save('bell_negative_YZ.stim',str(primitive.to_stim())+'\n')
    save('bell_negative_YZ.json',primitive.to_dict())
    certificates=[check_tableau(physical.cycle,check,composite=True) for check in physical.cycle.checks]
    save('exact_tableau_checks.json',certificates)
    for name in ('gross','two_gross'):
        save(f'{name}_installed_connectivity.json',installed_connectivity(load_reference_code(name,'installed')))
    report={'scope':'phase04 physical noiseless construction, not paper equivalence',
            'schedule_constraints':validate(physical.cycle),'exact_tableau_check_count':len(certificates),
            'gross_X1_timing':physical.timing,'gross_memory_ticks':memory.duration,
            'cycle_schedule_sha256':physical.cycle.hash,'memory_schedule_sha256':memory.hash,
            'donor_source_sha256':DONOR_SHA256,'extracted_donor_layers':extract_layers(),
            'bell_tableau':check_tableau(primitive,bell),'sampled_shots':0,'decoder_called':False,
            'strict_paper_configuration':False,'open_items':['O1','O2','O3','O4','O5'],
            'files':files}
    (args.output_dir/'index.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','extracted_donor_layers')},indent=2))

if __name__=='__main__':
    main()
