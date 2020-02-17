#!/usr/bin/env python3

import traceback
import os
from pycompss.api.task import task
from pycompss.api.constraint import constraint
from pycompss.api.parameter import *
from pycompss.api.api import compss_wait_on
import subprocess

@task(input_pdb_dir, haddock_img, returns=string )
def prepare_pdb(input_pdb_dir, haddock_img='/scratch/tmp/pmxHDD/BM5-clean/haddock24.sif'):
    pdb_id = os.path.basename(input_pdb_dir)
    with open(os.path.join(input_pdb_dir, 'run.param'), 'w') as runparam:
        runparam.write('HADDOCK_DIR=/software/haddock2.4' + '\n')
        runparam.write('AMBIG_TBL=./ambig.tbl' + '\n')
        runparam.write('N_COMP=2' + '\n')
        runparam.write('PDB_FILE1=./' + pdb_id + '_r_u.pdb' + '\n')
        runparam.write('PDB_FILE1=./' + pdb_id + '_l_u.pdb' + '\n')
        runparam.write('PROJECT_DIR=./' + '\n')
        runparam.write('PROT_SEGID_1=A' + '\n')
        runparam.write('PROT_SEGID_2=B' + '\n')
        runparam.write('RUN_NUMBER=1-ranair' + '\n')
        if os.path.exists(os.path.join(input_pdb_dir, 'hbonds.tbl')):
            runparam.write('HBOND_FILE=hbonds.tbl' + '\n')

        os.chdir(input_pdb_dir)

        singularity_cmd = [haddock_img, "cp ligand* run1-ranair/toppar >&/dev/null"]
        subprocess.run(singularity_cmd, shell=True)

        os.chdir('run1-ranair')
        cmd = ["patch", "-p0",  "-i",  "../../../data/run.cns.patch-ranair"]
        subprocess.run(cmd, shell=True)

        return os.path.abspath(os.path.join(input_pdb_dir, 'run.param'))


@task(input_run1_air_dir, haddock_img)
def run_haddock(input_run1_air_dir, haddock_img):
    os.chdir(input_run1_air_dir)
    singularity_cmd = [haddock_img, "/usr/bin/python", "/software/haddock2.4/Haddock/RunHaddock.py"]
    subprocess.run(singularity_cmd, shell=True)
    
pdbs_dir=""
haddock_img=""
for pdb_dir in os.listdir(pdbs_dir):
    run_param_path = prepare_pdb(pdbs_dir, haddock_img)
    compss_wait_on(run_param_path)
    run_haddock(pdbs_dir+'/run1-ranair', haddock_img)
    
