#!/bin/bash

#source env_pycompss.sh
enqueue_compss --num_nodes=50 --cpus_per_node=48 --cpus_per_task --exec_time=400 --master_working_dir=$PWD --worker_working_dir=scratch --base_log_dir=$PWD \
  --jvm_workers_opts="-Dcompss.worker.removeWD=true" -d --summary \
 /home/bsc19/bsc19275/haddock/code/run4/simple_wf_python.py 

