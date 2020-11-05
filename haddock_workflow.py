#!/usr/bin/env python3
import argparse
import glob
import os
import subprocess
import shutil
import pathlib
import tarfile
import logging
# import traceback
# import fileinput
# import psutil
# from distutils.dir_util import copy_tree
# from pycompss.api.parameter import *
# from pycompss.api.constraint import constraint
# from pycompss.api.task import task
# from pycompss.api.api import compss_wait_on
# from pycompss.api.api import compss_barrier


# @constraint(computing_units="48")
# @task(on_failure = 'IGNORE')
def run_haddock(input_path, patch_dir, haddock_singularity_image, scratch_dir=None, patch='ranair', nproc=48):
    """Generate parameter input file for haddock and initialize run"""
    logging.debug(f'Current pwd is {os.getcwd()}')

    # process = psutil.Process(os.getpid())
    # process_name = process.name()

    # FIXME: Is this the right way of defining the directory where the simulation will run?
    if not scratch_dir:
        key = 'TMPDIR'
        value = os.getenv(key)
        jobidkey = 'SLURM_JOB_ID'
        jobid = os.getenv(jobidkey)
        scratch_dir = value

    logging.info(f'Setting scratch_dir as {scratch_dir}')

    input_name = pathlib.PurePath(input_path).name
    target_path = f'{scratch_dir}/{input_name}'
    if os.path.isdir(target_path):
        logging.warning(f'{input_name} already in {scratch_dir}, REMOVING')
        shutil.rmtree(target_path)

    logging.info(f'Step 1 - Copying {input_name} to {scratch_dir}')
    shutil.copytree(input_path, target_path)

    logging.info(f'Step 2 - Creating parameter file for {input_name}')
    hbond_rest_check = os.path.exists(os.path.join(target_path, 'hbonds.tbl'))
    if hbond_rest_check:
        logging.info('hydrogen-bond restraints found')

    ligand_toppar = glob.glob(f'{target_path}/ligand*')
    if ligand_toppar:
        logging.info(f'ligand toppar found')

    param = 'HADDOCK_DIR=/software/haddock2.4\n'
    param += 'AMBIG_TBL=./ambig.tbl\n'
    param += 'N_COMP=2\n' + '\n'
    param += f'PDB_FILE1=./{input_name}_r_u.pdb\n'
    param += f'PDB_FILE2=./{input_name}_l_u.pdb\n'
    param += 'PROJECT_DIR=./\n'
    param += 'PROT_SEGID_1=A\n'
    param += 'PROT_SEGID_2=B\n'
    param += f'RUN_NUMBER=1-{patch}\n'

    if hbond_rest_check:
        param += 'HBOND_FILE=hbonds.tbl\n'

    param_file = os.path.join(target_path, 'run.param')
    with open(param_file, 'w') as fh:
        fh.write(param)

    logging.info('Step 3 - Initializing docking run')
    logging.debug(f'chdir into {target_path}')
    os.chdir(target_path)
    logging.debug(f'current path {os.getcwd()}')
    # FIXME: The singularity command might need to be tweaked
    singularity_cmd = [haddock_singularity_image]
    logging.debug(f'singularity command if {" ".join(singularity_cmd)}')
    logging.info('Executing Haddock singularity image')
    out = open(f'{target_path}/haddock.out', 'w')
    err = open(f'{target_path}/haddock.err', 'w')
    subprocess.call(singularity_cmd, stdout=out, stderr=err)

    run_dir = f'{target_path}/run1-{patch}'
    if not os.path.isdir(run_dir):
        logging.debug(f'run folder not found {run_dir}')
        logging.error(f'Setup failed for input {input_name}')
        # FIXME: How should pycompss handle this?
        exit()

    if ligand_toppar:
        logging.info('Copying ligand toppar to run directory')
        for toppar in ligand_toppar:
            shutil.copy(toppar, f'{run_dir}/toppar/')

    logging.info('Step 4 - Applying patch (run configuration)')
    patch_file = f'{patch_dir}/run.cns.patch-{patch}'
    logging.info(f'Selected patch is {patch_file}')
    logging.debug(f'chdir into {run_dir}')
    os.chdir(run_dir)
    logging.debug(f'current path {os.getcwd()}')
    cmd = ["patch", "-p0", "-i", patch_file]
    logging.debug(f'patch command is {" ".join(cmd)}')
    out = open(f'{run_dir}/patch.out', 'w')
    err = open(f'{run_dir}/patch.err', 'w')
    subprocess.call(cmd, stdout=out, stderr=err)

    logging.info('Step 5 - Parameter tweaking')
    logging.info(f'Changing parameter cpunumber_1 to {nproc}')
    with open('run.cns.edit', 'w') as out_fh:
        with open('run.cns', 'r') as in_fh:
            for line in in_fh.readlines():
                if line == '{===>} cpunumber_1=2;\n':
                    line = f"{{===>}} cpunumber_1={nproc};\n"
                # =========================================#
                # DEBUG ONLY, RUN A VERY SHORT SIMULATION
                if line == '{===>} structures_0=10000;\n':
                    line = '{===>} structures_0=2;\n'

                if line == '{===>} structures_1=400;\n':
                    line = '{===>} structures_1=2;\n'

                if line == '{===>} anastruc_1=400;\n':
                    line = '{===>} anastruc_1=2;\n'

                if line == '{===>} waterrefine=400;\n':
                    line = '{===>} waterrefine=2;\n'
                # =========================================#
                out_fh.write(line)

    shutil.copy('run.cns', 'run.cns.ori')
    shutil.copy('run.cns.edit', 'run.cns')

    logging.info(f'Simulation setup complete for {input_name}')

    logging.info('Running Haddock')
    logging.debug(f'current path is {os.getcwd()}')
    # FIXME: The singularity command might need to be tweaked
    singularity_cmd = [haddock_singularity_image]
    logging.debug(f'singularity command is {" ".join(singularity_cmd)}')
    # FIXME: Figure out a way to save stdout/stderr
    out = open(f'{run_dir}/haddock.out', 'w')
    err = open(f'{run_dir}/haddock.err', 'w')
    process = subprocess.call(singularity_cmd, stdout=out, stderr=err)
    if process == 0:
        # It can have exit signal 0 but still fail,
        #  make sure it worked by checking  for the final file of the simulation
        if not os.path.isfile(f'{run_dir}/structures/it1/water/file.list'):
            # FIXME: How should pycompss handle this?
            logging.error(f'Something went wrong with target {input_name}')
            exit()

        logging.info('Simulation complete :)')
        logging.info('Compressing the run directory')

        if not scratch_dir:
            file_name = f"{os.getenv('TMPDIR')}/{jobid}/{input_name}.tgz"
        else:
            file_name = f"{scratch_dir}/{input_name}.tgz"

        logging.info(f'Compressed filename {file_name}')
        if os.path.isfile(file_name):
            logging.warning('Compressed file found, it will be DELETED')
            os.remove(file_name)

        # TODO: Here we should also use multiprocessing compressing
        tar = tarfile.open(file_name, "w:gz")
        for name in os.listdir("."):
            tar.add(name)
        tar.close()

        logging.info('Compression done')
        logging.info(f'Target {input_name} complete')

        return True
    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    parser.add_argument('--log-level', default='INFO', choices=levels)
    parser.add_argument('--local', action='store_true', default=False)
    parser.add_argument('--nproc', default=48, type=int)
    parser.add_argument('--patch', default='ranair', type=str)

    parser.add_argument("bm5_path", help='')
    parser.add_argument("haddock_img", help='')

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level,
                        format='%(asctime)s %(funcName)s:%(lineno)d %(levelname)s - %(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S')

    logging.info('Initializing workflow runner')

    if not args.local:
        scratch_path = f"/gpfs/scratch/bsc19/bsc19275/{os.getenv('SLURM_JOB_ID')}"
        logging.info(f'Creating GPFS scratch dir at {scratch_path}')
        os.mkdir(scratch_path)
    else:
        logging.info('Running locally - use only for debug purposes')
        scratch_path = f'{str(pathlib.PurePath(os.path.abspath(__file__)).parent)}/scratch'
        logging.info(f'scratch dir is {scratch_path}')
        if not os.path.isdir(scratch_path):
            os.mkdir(scratch_path)

    patch_path = f'{args.bm5_path}/HADDOCK-ready/data'

    for pdb_dir in glob.glob(f'{args.bm5_path}/HADDOCK-ready/*/'):

        if pdb_dir in ['scripts', 'data', 'ana_scripts']:
            continue

        run_haddock(input_path=pdb_dir,
                    patch_dir=patch_path,
                    haddock_singularity_image=args.haddock_img,
                    scratch_dir=scratch_path,
                    patch=args.patch,
                    nproc=args.nproc)

    # compss_barrier(no_more_tasks=True)
    # file_name = "/gpfs/scratch/bsc19/bsc19275/" + jobid + "_runhaddock.tgz"
    # tar = tarfile.open(file_name, "w:gz")
    # os.chdir(gpfs_scratch)
    # for name in os.listdir("."):
    #     tar.add(name)
    # tar.close()
    # os.chdir("/gpfs/scratch/bsc19/bsc19275")
    # shutil.rmtree(gpfs_scratch, ignore_errors=True)
