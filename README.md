## Introduction

_pending_

## Instructions

Clone the repository with:

`git clone --recursive http://github.com/bioexcel/haddock_pycompss`

    $ python3 haddock_workflow.py -h
    usage: haddock_workflow.py [-h]
                               [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                               [--local] 
                               --nproc NPROC 
                               --patch {cm,ranair,ti,ti5,refb} 
                               --container-type {singularity,docker} 
                               --bm5-path BM5_PATH 
                               --image IMAGE

    optional arguments:
      -h, --help            show this help message and exit
      --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
      --local               Set the workflow to local, this is used solely for
                            debug purposes
      --nproc NPROC         Number of processors to be used, this value will be
                            given to HADDOCK
      --patch {cm,ranair,ti,ti5,refb}
                            Which benchmark patch should be applied
      --container-type {singularity,docker}
                            foo help
      --bm5-path BM5_PATH
      --image IMAGE

## Patches

These are edits to the `run.cns` for specific scenarios, located at `BM5-clean/HADDOCK-ready/data`

-   `cm` - center-of-mass restraints 
-   `ranair` - random restraints
-   `ti` - true interface
-   `ti5` - true interface 5A cutoff
-   `refb` -
