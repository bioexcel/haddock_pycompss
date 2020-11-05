## Introduction

_pending_

## Instructions

Clone the repository with:

`git clone --recursive http://github.com/bioexcel/haddock_pycompss`

```
$ python3 haddock_workflow.py -h
usage: haddock_workflow.py [-h] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--local] [--nproc NPROC] [--patch PATCH] bm5_path haddock_img

usage: haddock_workflow.py [-h] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--local] [--nproc NPROC] [--patch {cm,ranair,ti,ti5,refb}] bm5_path haddock_img

positional arguments:
  bm5_path
  haddock_img

optional arguments:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
  --local               Set the workflow to local, this is used solely for debug purposes
  --nproc NPROC         Number of processors to be used, this value will be given to HADDOCK
  --patch {cm,ranair,ti,ti5,refb}
                        Which benchmark patch should be applied

$ python3 haddock_workflow.py --nproc 48 --patch ranair `pwd`/BM5-clean haddock_v2.4-2020.09
```

### Patches
These are edits to the `run.cns` for specific scenarios, located at `BM5-clean/HADDOCK-ready/data`
* `cm` - center-of-mass restraints 
* `ranair` - random restraints
* `ti` - true interface
* `ti5` - true interface 5A cutoff
* `refb` -