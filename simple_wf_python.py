#!/usr/bin/env python3

import traceback
import os
import subprocess


def prepare_pdb(input_pdb_dir, haddock_img):
    print(os.getcwd())
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
        print("Preparing: " + os.getcwd())
        os.chdir(input_pdb_dir)
        print(os.getcwd())

        singularity_cmd = ["singularity", "run", "-e", haddock_img, "cp ligand* run1-ranair/toppar >&/dev/null"]
        print(" ".join(singularity_cmd))
        subprocess.run(singularity_cmd, shell=True)

        os.chdir('run1-ranair')
        print("I'm in " + os.getcwd())
        cmd = ["patch", "-p0",  "-i",  "../../../data/run.cns.patch-ranair"]
        print(" ".join(cmd))
        subprocess.run(cmd, shell=True)

        return os.path.abspath(os.path.join(input_pdb_dir, 'run.param'))



def run_haddock(input_run1_air_dir, haddock_img):
    print(os.getcwd())
    os.chdir(input_run1_air_dir)
    print(os.getcwd())
    singularity_cmd = ["singularity", "run", "-e", haddock_img, "/usr/bin/python", "/software/haddock2.4/Haddock/RunHaddock.py"]
    print(" ".join(singularity_cmd))
    subprocess.run(singularity_cmd, shell=True)


if __name__ == '__main__':
    print("First line main")
    pdbs_dir = "/home/bsc19/bsc19275/haddock/BM5-clean/HADDOCK-ready/"
    haddock_img = "/home/bsc19/bsc19275/haddock/BM5-clean/haddock24.sif"

    for pdb_dir in os.listdir(pdbs_dir):
        run_param_path = prepare_pdb(os.path.join(pdbs_dir, pdb_dir), haddock_img)
        run_haddock(os.path.join(pdbs_dir, 'run1-ranair'), haddock_img)
