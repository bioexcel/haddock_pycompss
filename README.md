# benchmark-tools

## Configuration

To execute the benchmark tools you need a configuration file as below:

```toml
# ==============================
# This general section is obligatory and must contain the following keys
[ general ]
# Location of HADDOCK
haddock_path = '/Users/rodrigo/repos/haddock'

# Since HADDOCK runs on python2, we also need to point out its location
python2 = '/usr/bin/python2'

# Location of your prepared dataset
dataset_path = '/Users/rodrigo/repos/BM5-clean/HADDOCK-ready'

# We will automatically detect what is the receptor and the ligand
#  inside your dataset folder, but they need the match the suffixes below
receptor_suffix = '_r_u.pdb'
ligand_suffix = '_l_u.pdb'
# ==============================

# Here you will define the scenarios to benchmark,
#  each section must be named scenario_N
# Each parameter inside the scenario corresponds to
#  a parameter inside run.cns, except run_name and ambig_tbl
#  that are used to setup the run
[ scenario_1 ]
run_name = 'true-interface'
ambig_tbl = 'ambig.tbl'
noecv = true

[ scenario_2 ]
run_name = 'CM'
noecv = true
cmrest = true
cmtight = true
# ==============================
```

Create this file with whatever editor you prefer and save it in the location of your benchmark as benchmark_config.toml

## Execution example


    $ conda activate benchmark-tools
    (benchmark-tools) $ cd benchmark-tools/example
    (benchmark-tools) $ python ../run_benchmark.py scenarios.toml
