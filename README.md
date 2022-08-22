# SMT-GCN
Solver runtime prediction for SMT formulas based on graph representation with GCNs.

## Files:

* _custom_smt_printer.py_ Contains definition of a printer from pysmt with adjusted "walk" method, walk will return a node dictionary and an edgelist

* _final_graph_save.py_ An example of usage of the custom SMT printer. We iterate through all smt2 files in a directory and return the same directory structure with all formulas converted into dot graphs. Multiple checks are done (which could be omitted): if the smt2 file is small (we dont process too big formulas), if file is already processed and if there is data for a follow-up task of time prediction. Furthermore, final graph is checked before saving (we save graphs with less than 10 000 nodes).
