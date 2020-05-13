# Overview

IDentif.AI, a dynamic optimization AI-based platform, identifies the drug-dose parameter space by harnessing the quadratic relationship between biological responses to external perturbations, such as drug/dose inputs [1]. IDentif.AI analysis of the drug-dose parameter space identifies drug-drug interactions and ranks optimal drug-dosage combinations.

This package include the in vitro experimental data sets of the 12 drugs currently being explored in clinical trials to combat the COVID-19 disease *(see [manuscript](https://www.medrxiv.org/content/10.1101/2020.05.04.20088104v1))*. The Python and Matlab scripts were used to:
 - Normalise and calculate the raw experimental data into desired outputs: Vero E6, AC16 and THLE-2 %Cytotoxicity and viral activity %Inhibition (Vero E6) using the formula in [Supplementary Materials and Methods](https://www.medrxiv.org/content/10.1101/2020.05.04.20088104v1.supplementary-material).
 - Perform IDentif.AI second-order polynomial regression analysis on the resulting %Cytotoxicity and %Inhibition calculations, identify drug-drug interactions and rank optimal drug-dose combinations
 - Provide a set of graphical and statistical reports of IDentif.AI analysis


### Main structure:

check_dmso_effect/: contains input xlsx file and Python script

monotherapy/: contains input xlsx file, Python script and Graphpad PRISM template file. 

oacd/: contains input xlsx file, Python script and MATLAB scripts 

validation/: contains input xlsx file and Python script 


# System requirements

Python:[v3.7.7](https://www.python.org/downloads/release/python-377/)

Matlab: [2020a](https://www.mathworks.com/downloads/)

Graphpad Prism: [8.2](https://www.graphpad.com/scientific-software/prism/)


# Installation

Open the terminal, navigate to this folder, type:
>pip install --upgrade pip

>pip install -r -requirements.txt

The required Python modules are specified in requirements.txt. The installation process should only takes a few seconds.


# Instructions for use

## Monotherapy
#### Normalize and calculate raw data into %Inhibition and %Cytotoxicity
 - Open Terminal, navigate to folder *IDentifAI/monotherapy*, type to run Python script:
	>python3 monotherapy.py
	
 - Expected output: *Monotherapy_result.xlsx*
 

## OACD

#### Normalize and calculate raw data into %Inhibition and %Cytotoxicity
 - Open Terminal, navigate to *IDentifAI/oacd*, type to run Python script:
	>python3 oacd.py
	
	Expected output: *OACD_result.xlsx*, which is the input file for MATLAB codes (*OACD_part1.mlx* and *OACD_part2.mlx* files)

#### IDentif.AI regression analysis
- *allcomb.m* is a supporting function for the MATLAB codes [1]

- On MATLAB, run *OACD_part1.mlx*. 
	Expected output: *regr_final.mat*, regression output model file
	
- Run *OACD_part2.mlx*.
	Expected outputs: *regression* folder, containing 1) top 4/3/2-drug ranked drug combinations in *OACD_subsets.xlsx* and 2) subfolders *interaction_graphs* and *validation_graphs* with all drug-drug interaction graphs and validation graphs.


## Validation
#### Normalize and calculate raw data into %Inhibition and %Cytotoxicity. Present statistical and graphical analysis results.
 - Open Terminal, navigate to *IDentifAI/validation*, type to run Python script:
	>python3 validation.py > validation_stats.txt

	Expected output: 1) *Validation_result.xlsx*, 2) folder *barplots*, and 3) *validation_stats.txt*

## Additional: Verify DMSO non-cytotoxicity effect
- Open Terminal, navigate to *IDentifAI/check_dmso_effect*, type to run Python script:
	> python3 check_dmso.py > dmso_stats.txt

	Expected output: *dmso_stats.txt*


# References
[1] I. Al-Shyoukh _et al._, Systematic quantitative characterization of cellular responses induced by multiple signals. _BMC Syst Biol_ **5**, 88 (2011).

[2] Jos (10584) (2020). allcomb(varargin). *MATLAB Central File Exchange*. Available at: https://www.mathworks.com/matlabcentral/fileexchange/10064-allcomb-varargin. (Accessed: May 13, 2020).
