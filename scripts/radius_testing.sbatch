#!/bin/bash

#SBATCH --job-name=sa_20191113-tw1         # Name of the job.
#SBATCH --exclusive                    # Request exclusive use of the node so that we can use more memory.
#SBATCH --output=slurm_output/sa_20191113-tw1-%A_%a.out       # Provide unique output files for each array task.
#SBATCH --error=slurm_output/sa_20191113-tw1-%A_%a.err        # Provide unique error files for each array task.
#SBATCH --array=1-96                 # Provide values that we'll translate to unique gridsearch parameters.
#SBATCH --ntasks=1                    # We've only got one script we're running.
#SBATCH --time=01:00:00               # Don't let it run forever.

# load modules
source /etc/profile.d/modules.sh
module load X11/7.7 gcc/9.2.0 r/3.6.1

# save our task ID as an environmental variable
export SLURM_ARRAY_TASK_ID

# print to output for confirmation that it's started
echo $SLURM_ARRAY_TASK_ID ": Running SLURM task"

# run the R script
Rscript $HOME/SA_Analysis/scripts/test_one_crqa_radius.R

# print to output for confirmation that it's ended
echo $SLURM_ARRAY_TASK_ID ": Job done"
