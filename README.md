# SMT-GCN
Solver runtime prediction for SMT formulas based on graph representation with GCNs.

## Files:

* _custom_smt_printer.py_ Contains a modified printer from pysmt with the "walk" method adjusted to return a directed graph in the form of node dictionary and an edgelist

* _convert_formulas_to_graphs.py_ An example of usage of the custom SMT printer. We iterate through all smt2 files in a directory and convert them to dot graphs. The directory structure is retained. Multiple checks are done (which could be omitted if desired): checking whether the smt2 file is small (we don't process too big formulas) or if it was already processed (it may happen that the script fails and we need to run it again). Furthermore, final graph is checked before saving (we save graphs with less than 10 000 nodes).
The script expects 3 arguments: rootfolder which contains folders for different logics, the name of the folder for a given logic, and a path to an output folder.

* _time_table_creation,py_ Creates two pandas dataframes used for different purposes. 1) To create a target to train the NN with respect to. 2) To determine for which formuals result can be predicted so formulas with no data are not parsed (saves time). 3) To compare network predictions to GT. We add the the original file _Single_Query_Track.csv_ so user can run this script and how the resulted table looks like if she/he wants to use different data.

* _convert_formulas_to_graphs_ This file takes the folder with DOT graphs, full time table (the one with the information about solver result) and list of symbols. From those it creates PyG datalist which can be iterated as a dataset to train and eveluate GNN model.

## Workflow:

1) Create timetables.

2) Convert smt2 formuals to DOT graphs and save the list of symbols create symbol list.

3) Run the file to convert dot graphs to PyG datalist.