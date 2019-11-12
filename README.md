# SA Analysis

A series of functions to clean and prepare data for analysis for
the dyscord lab's SA study.

## Structure

This code weaves together output from the data collection protocol generated
in the [SA Stimulus](https://github.com/dyscord-lab/SA_Stimulus) repository.

## Running

To run, raw data should be saved in a directory called `data` and in a
subdirectory in that directory called `raw`. The `data` directory should be
put in the top-level directory of this repo.

Open a Terminal window and navigate to the `SA_Analysis` directory. From there,
type `python run-sorting.py` and return.

Data will be output in two new subdirectories within the `data` directory:
`processed` (which includes a `gaze_df.csv` and a `survey_df.csv` file for
each participant) and `analysis` (which includes an `analysis_df.csv` file for
each participant).

## To do
1. Make the timestamps of the `gaze_positions` match up with the
  `.log` file
   - This will help account for disruptions
2. For the `exports` folder, use the most recently updated one instead
  of highest number
3. Make the file searching interactive in command prompt
