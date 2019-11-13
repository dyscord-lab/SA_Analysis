#### libraries_and_functions-SA.r ####
#
# This script loads libraries and creates a number of 
# additional functions to facilitate data prep and analysis.
#
#####################################################################################

#### Load necessary packages ####

# list of required packages
required_packages = c(
  'plyr',
  'dplyr',
  'stringr',
  'data.table',
  'lme4',
  'ggplot2',
  'pander',
  'grid',
  'gridExtra',
  'plotrix',
  'gtable',
  'viridis',
  'jsonlite',
  'tidyr',
  'tibble',
  'RCurl'
)

# load required packages
invisible(lapply(required_packages, require, character.only = TRUE))

#### Prevent scientific notation ####
options(scipen = 999)
options(digits=14)

#### Create global variables and useful global functions ####

# function to return p-values from t-values
pt = function(x) {return((1 - pnorm(abs(x))) * 2)}

# function to identify first local minimum (modified from https://stackoverflow.com/a/6836583)
first_local_minimum <- function(x){
  flm = as.numeric((which(diff(sign(diff(x)))==-2)+1)[1])
  if (is.na(flm)) { 
    flm_1 = as.numeric(which(diff(x)==max(diff(x))))-1 
    flm_2 = c(as.numeric(which(x<.001))-1)[1]
    flm = min(flm_1,flm_2)
  }
  return(flm)
}

# specify raw sampling rate
raw_sampling_rate = 124

# specify downsampled sampling rate
downsampled_sampling_rate = 20

# specify which variables will be factors
factor_variables = c('participant_id',
                     'condition')

#### Read in model output formatting functions from repo ####

# read in `pander_lme` at the correct commit
# thanks to https://github.com/opetchey/RREEBES/wiki/
pander_lme_url = "https://raw.githubusercontent.com/a-paxton/stats-tools/bee546f2c959cb6a5b9cad1f28d3afbae6e46c41/pander_lme.R"
pander_lme_file = getURL(pander_lme_url, ssl.verifypeer = FALSE)
eval(parse(text = pander_lme_file))