# SMT-GCN
Solver runtime prediction for SMT formulas based on graph representation with GCNs.

## Files:

* _custom_smt_printer.py_ Contains a modified printer from pysmt with the "walk" method adjusted to return a directed graph in the form of node dictionary and an edgelist

* _convert_formulas_to_graphs.py_ An example of usage of the custom SMT printer. We iterate through all smt2 files in a directory and convert them to dot graphs. The directory structure is retained. Multiple checks are done (which could be omitted if desired): checking whether the smt2 file is small (we don't process too big formulas) or if it was already processed (it may happen that the script fails and we need to run it again). Furthermore, final graph is checked before saving (we save graphs with less than 10 000 nodes).
The script expects 3 arguments: rootfolder which contains folders for different logics, the name of the folder for a given logic, and a path to an output folder.
