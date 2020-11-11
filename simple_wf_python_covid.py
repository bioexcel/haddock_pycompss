#!/usr/bin/env python3

import traceback
import os
import subprocess
from pycompss.api.task import task
from pycompss.api.constraint import constraint
from pycompss.api.parameter import *
from pycompss.api.api import compss_wait_on
from pycompss.api.api import compss_barrier
import psutil
import shutil
import fileinput
from distutils.dir_util import copy_tree
import tarfile


@constraint(computing_units="48")
@task(on_failure = 'IGNORE')
def prepare_pdb(input_pdb_dir, pdb_dir, haddock_img):
    #print(os.getcwd())

    #process = psutil.Process(os.getpid())

    #process_name = process.name()
    key = 'TMPDIR'
    value = os.getenv(key) 
    jobidkey = 'SLURM_JOB_ID'
    jobid = os.getenv(jobidkey)

    scratch_dir = value 
    print("Copying " + input_pdb_dir + " in " + scratch_dir)
    shutil.copytree(input_pdb_dir, scratch_dir + '/' + pdb_dir)
    input_pdb_dir = scratch_dir + '/' + pdb_dir 
    #print('AFFINITY for proc' + process_name + ' ' + str(os.getpid()) +': ' + str(len(os.sched_getaffinity(os.getpid()))))
    pdb_id = os.path.basename(input_pdb_dir)
    with open(os.path.join(input_pdb_dir, 'run.param'), 'w') as runparam:
        runparam.write('HADDOCK_DIR=/software/haddock2.4' + '\n')
        runparam.write('AMBIG_TBL=./ambig.tbl' + '\n')
        runparam.write('N_COMP=2' + '\n')
        runparam.write('PDB_FILE1=./' + pdb_id + '_r_u.pdb' + '\n')
        runparam.write('PDB_FILE2=./' + pdb_id + '_l_u.pdb' + '\n')
        runparam.write('PROJECT_DIR=./' + '\n')
        runparam.write('PROT_SEGID_1=A' + '\n')
        runparam.write('PROT_SEGID_2=B' + '\n')
        runparam.write('RUN_NUMBER=1-ranair' + '\n')
        if os.path.exists(os.path.join(input_pdb_dir, 'hbonds.tbl')):
            runparam.write('HBOND_FILE=hbonds.tbl' + '\n')
        #print("Preparing: " + os.getcwd())
        os.chdir(input_pdb_dir)
        #print(os.getcwd())

    singularity_cmd = ["singularity", "run", "-e", haddock_img, "'cp ligand* run1-ranair/toppar'"]
    print(" ".join(singularity_cmd))
    subprocess.run(singularity_cmd)
       
    print('Going to patch....\n\n\n\n')
    os.chdir(input_pdb_dir + '/run1-ranair')
    print("I'm in " + os.getcwd())
    cmd = ["patch", "-p0",  "-i",  "/gpfs/scratch/bsc19/bsc19275/BM5-clean/data/run.cns.patch-ranair"]
    print(" ".join(cmd))
    subprocess.call(cmd)

    for line in fileinput.FileInput("run.cns", inplace=1):
        line=line.replace("{===>} cpunumber_1=2;","{===>} cpunumber_1=48;")
        print(line)
    
    print(os.getcwd())
    input_run1_air_dir = os.getenv('TMPDIR') + '/' + pdb_dir + '/run1-ranair' 
    os.chdir(input_run1_air_dir)
    print(os.getcwd())


    singularity_cmd = ["singularity", "run", "-e",  haddock_img, "'/usr/bin/python /software/haddock2.4/Haddock/RunHaddock.py >&haddock.out'"]
    print(" ".join(singularity_cmd))
    process = subprocess.call(singularity_cmd)
    if(process == 0): 
        file_name =  os.getenv('TMPDIR') + "/" + jobid + "_" + pdb_dir + ".tgz"
        tar = tarfile.open(file_name, "w:gz")
        os.chdir(input_run1_air_dir)
        for name in os.listdir("."):
            tar.add(name)
        tar.close()

        gpfs_scratch = "/gpfs/scratch/bsc19/bsc19275/" + jobid + "/"
        print("Copying " + file_name + " in " + gpfs_scratch)
        shutil.move(file_name, gpfs_scratch)
        shutil.rmtree(input_run1_air_dir, ignore_errors=True) 
        


if __name__ == '__main__':
    print("First line main")
    pdbs_dir = "/gpfs/scratch/bsc19/bsc19275/BM5-clean/HADDOCK-ready/"
    haddock_img = "/gpfs/scratch/bsc19/bsc19275/BM5-clean/haddock24_v1.2.sif"

    jobidkey = 'SLURM_JOB_ID'
    jobid = os.getenv(jobidkey)

    gpfs_scratch = "/gpfs/scratch/bsc19/bsc19275/" + jobid

    os.mkdir(gpfs_scratch)
    i=0
    for pdb_dir in os.listdir(pdbs_dir):
        #if (pdb_dir=='1T6B'):
        print("About to run in " + pdb_dir)
        #pdb_dir = "1T6B/"
        run_param_path = prepare_pdb(os.path.join(pdbs_dir, pdb_dir), pdb_dir, haddock_img)
        
        i+=1
        #if (i==80):
        #    break
    compss_barrier(no_more_tasks=True)

    #file_name = "/gpfs/scratch/bsc19/bsc19275/" + jobid + "_runhaddock.tgz"
    #tar = tarfile.open(file_name, "w:gz")
    #os.chdir(gpfs_scratch)
    #for name in os.listdir("."):
    #    tar.add(name)
    #tar.close()

    #os.chdir("/gpfs/scratch/bsc19/bsc19275") 
    #shutil.rmtree(gpfs_scratch, ignore_errors=True)
        
        
