#### Scipt for running ANOVAs on SA data ####

# set working directory
setwd("./SA_Analysis/")

# read in libraries and functions
source('./lib/functions_and_libraries-SA.R')

# load librariies
library(stats)
library(readr)

### Prep for analyses ###

# read in radius files and bind together
files <- list.files(path = "./data/crqa_results/radius_calculations", pattern = "*.csv", full.names = T)
tbl <- sapply(files, read_csv, simplify=FALSE) %>% 
  bind_rows()

# create empty dataframe for saving filtered data
#filtered = data.frame()

# filtering for radii with closest rr to .05
filtered = tbl %>% ungroup() %>%
  dplyr::group_by(chosen.participant) %>%
  dplyr::filter(from.target == min(from.target))
  
# write the whole thing to a dataframe
write.table(filtered,
            './data/crqa_results/best_radius_calculations.csv',
            sep=',',
            col.names = TRUE,
            row.names = FALSE)

### Getting condition back ###

# Read in old downsampled data to get condition back
gaze_data = read.table('./data/downsampled/all_participants-downsampled.csv',
                       sep=',',header=TRUE)

# get unique participant and condition combos
gaze_data_simplified = gaze_data %>% ungroup() %>%
  group_by(participant, condition) %>% slice(1)

# merge condition back into filtered data
filtered = cbind(gaze_data_simplified, filtered)

#### ANOVAs across RQA metrics and condition ####

### % Determinism (det) ###

  # run the anova
  det_anova <- aov(condition ~ det, data=filtered)
  
  # summarize results
  det_anova_results <- summary(det_anova)
  
  # save results to file
  capture.output(det_anova_results, file = './data/crqa_results/det_anova_results.txt')

### Mean Line (meanL) ###

  # run the anova
  meanL_anova <- aov(condition ~ meanL, data=filtered)
  
  # summarize results
  meanL_anova_results <- summary(meanL_anova)
  
  # save results to file
  capture.output(meanL_anova_results, file = './data/crqa_results/meanL_anova_results.txt')
  
### NRLINE ###
  
  # run the anova
  NRLINE_anova <- aov(condition ~ NRLINE, data=filtered)
  
  # summarize results
  NRLINE_anova_results <- summary(NRLINE_anova)
  
  # save results to file
  capture.output(NRLINE_anova_results, file = './data/crqa_results/NRLINE_anova_results.txt')
  
### maxL ###

  # run the anova
  maxL_anova <- aov(condition ~ maxL, data=filtered)
  
  # summarize results
  maxL_anova_results <- summary(maxL_anova)
  
  # save results to file
  capture.output(maxL_anova_results, file = './data/crqa_results/maxL_anova_results.txt')
  
### ENTR ###
  
  # run the anova
  ENTR_anova <- aov(condition ~ ENTR, data=filtered)
  
  # summarize results
  ENTR_anova_results <- summary(ENTR_anova)
  
  # save results to file
  capture.output(ENTR_anova_results, file = './data/crqa_results/ENTR_anova_results.txt')
  
### rENTR ###
  
  # run the anova
  rENTR_anova <- aov(condition ~ rENTR, data=filtered)
  
  # summarize results
  rENTR_anova_results <- summary(rENTR_anova)
  
  # save results to file
  capture.output(rENTR_anova_results, file = './data/crqa_results/rENTR_anova_results.txt')
  
### LAM ###
  
  # run the anova
  LAM_anova <- aov(condition ~ LAM, data=filtered)
  
  # summarize results
  LAM_anova_results <- summary(LAM_anova)
  
  # save results to file
  capture.output(LAM_anova_results, file = './data/crqa_results/LAM_anova_results.txt')
  
### TT ###

  # run the anova
  TT_anova <- aov(condition ~ TT, data=filtered)
  
  # summarize results
  TT_anova_results <- summary(TT_anova)
  
  # save results to file
  capture.output(TT_anova_results, file = './data/crqa_results/TT_anova_results.txt')
  