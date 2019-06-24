# gcrmn-benthic-classification

## Goals

The Global Coral Reef Monitoring Network is preparing its 2020 report. The organization has global, but incomplete field data on coral cover and fish biomass. The availability of a simple map showing land, water, and reef (LWR) would greatly facilitate their monitoring and reporting efforts, but our Allen Coral Atlas partners do not have the bandwidth for preparing this map in addition to the current map priorities. Thus, we are exploring the feasibility of generating a global LWR from already-available Caribbean data. 

## Data

We have access to a global visual mosaic from Planet, split into quads. We also have LWR classifications for Belize, Dominican Republic, and US Virgin Islands. 

## Strategy

1. Train a model to predict LWR classifications using mosaic imagery from Belize, DR, and USVI.  
2. Predict LWR classifications in other Caribbean reefs using the trained model and mosaic imagery.  
3. Create new LWR classification maps for output and supplemented model training by manually cleaning the generated predictions.  
4.  Meet or exceed the accuracy of the World Conservation Monitoring Centre (WCMC) glocal coral layer. 

## Timeline

Initial analyses done by early September.

