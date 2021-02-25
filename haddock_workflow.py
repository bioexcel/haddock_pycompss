#!/usr/bin/env python3
import argparse
import glob
import os
import subprocess
import shutil
import pathlib
# import tarfile
import logging
import shlex
import sys
# import traceback
# import fileinput
# import psutil
# from distutils.dir_util import copy_tree
# from pycompss.api.parameter import *
# from pycompss.api.constraint import constraint
# from pycompss.api.task import task
# from pycompss.api.api import compss_wait_on
# from pycompss.api.api import compss_barrier

SCRATCH_PATH = ''


# @constraint(computing_units="48")
# @task(on_failure = 'IGNORE')
def setup_haddock(input_path, scratch_dir, patch='ranair'):
    """
    Generate parameter input file for HADDOCK

    Step 1 - Copy target folder to working directory
    Step 2 - Create parameter file

    :param input_path: Directory of the simulation ex: /home/rodrigo/benchmark/1A2L
    :param scratch_dir: Scratch directory
    """
    logging.debug(f'Current pwd is {os.getcwd()}')

    # process = psutil.Process(os.getpid())
    # process_name = process.name()

    logging.info(f'Setting working directory as {scratch_dir}')

    # Get the target name and copy it to the working directory
    input_name = pathlib.PurePath(input_path).name
    target_path = f'{scratch_dir}/{input_name}'
    logging.info(f'Step 1 - Copying {input_name} to {scratch_dir}')
    if os.path.isdir(target_path):
        logging.warning(f'{input_name} already in {scratch_dir}, REMOVING')
        shutil.rmtree(target_path)
    shutil.copytree(input_path, target_path)

    # Each simulation needs its own run.param file, the code below will generate it
    #  and save it in the appropriate location
    logging.info(f'Step 2 - Creating parameter file for {input_name}')

    # check if target has hydrogen bond restraints
    hbond_rest_check = os.path.exists(os.path.join(target_path, 'hbonds.tbl'))
    if hbond_rest_check:
        logging.info('hydrogen-bond restraints found')

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

    return


def run_haddock(target_dir, patch_dir, patch, haddock_exec, nproc=48):
    """
    Executor function of HADDOCK.

    Step 1 - Initialize the docking run
    Step 2 - Apply the patch (run configuration)
    Step 3 - Tweak parameters in Haddock run
    Step 4 - Execute

    :param target_dir: Directory of the simulation ex: /home/rodrigo/benchmark/1A2L
    :param patch_dir: Location of the patch files ex: /home/rodrigo/benchmark/data
    :param exec: HADDOCK executable
    """

    # Haddock execution is a two-step process, first it will read the run.param generated before
    #  and create the appropriate folder structure
    logging.info('Step 1 - Initializing docking run')
    logging.debug(f'chdir into {target_dir}')
    os.chdir(target_dir)
    logging.debug(f'current path {os.getcwd()}')

    logging.debug(f'HADDOCK command is {exec}')
    logging.info('Executing HADDOCK')
    out = open(f'{target_dir}/haddock.out', 'w')
    err = open(f'{target_dir}/haddock.err', 'w')
    subprocess.call(shlex.split(haddock_exec), stdout=out, stderr=err)

    # We know if it worked if after this first execution there is a run1-patch directory
    run_dir = f'{target_dir}/run1-{patch}'
    if not os.path.isdir(run_dir):
        logging.error(f'run folder not found {run_dir}')
        logging.error(f'Setup failed check {target_dir}/haddock.err')

        # FIXME: How should pycompss handle this?
        sys.exit()

    # If there are specific ligand topologies and parameters, they need to be copied to the correct location
    # check if target has ligand topologies and parameters
    ligand_toppar = glob.glob(f'{target_dir}/../ligand*')
    if ligand_toppar:
        logging.info('ligand toppar found')
    if ligand_toppar:
        logging.info('Copying ligand toppar to run directory')
        for toppar in ligand_toppar:
            shutil.copy(toppar, f'{run_dir}/toppar/')

    # Each different patch represents a different set of parameters for the simulation
    #  these parameters are changed in the haddock's main configuration file run.cns
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

    # Here we are running Haddock in "node-mode" which means that it will spawn as many process
    #  as available cpunumbers, so here we change the cpunumber to our desired number
    logging.info('Step 5 - Parameter tweaking')
    logging.info(f'Changing parameter cpunumber_1 to {nproc}')
    with open('run.cns.edit', 'w') as out_fh:
        with open('run.cns', 'r') as in_fh:
            for line in in_fh.readlines():
                if line == '{===>} cpunumber_1=2;\n':
                    line = f"{{===>}} cpunumber_1={nproc};\n"

                # =========================================#
                #  DEBUG ONLY!! RUN A VERY SHORT SIMULATION
                # if line == '{===>} structures_0=10000;\n':
                #     line = '{===>} structures_0=2;\n'
                # if line == '{===>} structures_1=400;\n':
                #     line = '{===>} structures_1=2;\n'
                # if line == '{===>} anastruc_1=400;\n':
                #     line = '{===>} anastruc_1=2;\n'
                # if line == '{===>} waterrefine=400;\n':
                #     line = '{===>} waterrefine=2;\n'
                # =========================================#

                out_fh.write(line)

    shutil.copy('run.cns', 'run.cns.ori')
    shutil.copy('run.cns.edit', 'run.cns')

    # Setup complete! At this point the simulation is ready to be executed,
    #   no further configuration is needed
    logging.info(f'Simulation setup complete {target_dir}')

    # Proceed to the proper execution
    logging.info('Step 6 - Running Haddock')
    logging.debug(f'current path is {os.getcwd()}')

    logging.debug(f'HADDOCK command is {haddock_exec}')

    out = open(f'{run_dir}/haddock.out', 'w')
    err = open(f'{run_dir}/haddock.err', 'w')
    process = subprocess.call(shlex.split(haddock_exec), stdout=out, stderr=err)

    if process == 0:
        # It can have exit signal 0 but still fail,
        #  make sure it worked by checking for the final file of the simulation
        if not os.path.isfile(f'{run_dir}/structures/it1/water/file.list'):
            # FIXME: How should pycompss handle this?
            logging.error(f'Something went wrong check {run_dir}/haddock.err')
            sys.exit()

        # Simulation ended successfuly!
        logging.info('Simulation complete :)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    levels = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    available_patches = ('cm', 'ranair', 'ti', 'ti5', 'refb')
    available_containers = ('singularity', 'docker')
    parser.add_argument('--log-level', default='INFO', choices=levels)

    parser.add_argument('--local', action='store_true', default=False,
                        help='Set the workflow to local, this is used solely for debug purposes')

    parser.add_argument('--nproc', default=48, type=int, required=True,
                        help='Number of processors to be used, this value will be given to HADDOCK')

    parser.add_argument('--patch', default='ranair', type=str, choices=available_patches, required=True,
                        help='Which benchmark patch should be applied')

    parser.add_argument('--container-type', choices=available_containers, required=True,
                        help='foo help')

    parser.add_argument("--bm5-path", required=True, help='')

    parser.add_argument("--image", required=True, help='')

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level,
                        format='%(asctime)s %(funcName)s:%(lineno)d %(levelname)s - %(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S')

    logging.info('Initializing workflow runner')

    if args.container_type == 'singularity':
        if not os.path.isfile(args.image):
            logging.error(f'Singularity image {args.image} not found')
        else:
            haddock_cmd = args.image

    elif args.container_type == 'docker':
        cmd = f"docker inspect --type=image {args.image}"
        p = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode == 1:
            logging.error(f'Docker image {args.image} not found')
            sys.exit()
        else:
            # FIXME: How to make the docker image behave like the singularity? aka: as if it were an executable
            haddock_cmd = f'docker run -ti -v `pwd`:/runs {args.image}'

    if not args.local:
        # wd is the working directory, where the workflow will run

        # FIXME: Is this the right way of defining the directory where the simulation will run?
        wd = f"/gpfs/scratch/bsc19/bsc19275/{os.getenv('SLURM_JOB_ID')}"
        logging.info(f'Creating GPFS scratch dir at {wd}')
        os.mkdir(wd)

    else:
        logging.info('Running locally - use only for debug purposes')
        wd = f'{str(pathlib.PurePath(os.path.abspath(__file__)).parent)}/scratch'
        # wd = 'Users/rodrigo/projects/haddock_pycompss/runs
        logging.info(f'scratch dir is {wd}')
        if not os.path.isdir(wd):
            os.mkdir(wd)

    # location where the patches are located
    patch_path = f'{args.bm5_path}/HADDOCK-ready/data'

    # run haddock for each target in the BM5
    for pdb_dir in glob.glob(f'{args.bm5_path}/HADDOCK-ready/*/'):

        if pdb_dir in ['scripts', 'data', 'ana_scripts']:
            continue

        setup_haddock(input_path=pdb_dir,
                      scratch_dir=SCRATCH_PATH)

        run_haddock(target_dir=pdb_dir,
                    patch_dir=patch_path,
                    patch='ranair',
                    haddock_exec=haddock_cmd,
                    nproc=48)
