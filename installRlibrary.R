# run from top dir as: Rscript installRlibrary.R
if (!require("pacman")) install.packages("pacman")
suppressMessages(library(pacman))
pacman::p_load(devtools, roxygen2)
setwd('CrimeBBprocessR')
document()
setwd('..')
install('CrimeBBprocessR')
