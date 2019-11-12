#### AVONA over RQA Metrics ####

install.packages('anova')


det_anova = aov(DET ~ condition)

meanL_anova = aov(L ~ condition)
