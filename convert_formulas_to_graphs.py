from pysmt.smtlib.parser import SmtLibParser
from six.moves import cStringIO

import networkx as nx
import os
from tqdm import tqdm
from networkx.drawing.nx_agraph import write_dot
from pathlib import Path
import pickle
import pandas as pd
import gc
from custom_smt_printer import CustomSmtPrinter

import pysmt.environment
import argparse
import time
from pysmt.smtlib.printers import SmtPrinter


def check_graph(G, treshold):
    # checks if the graph is in the correct form (DAG) and its number of vertices is smaller then the threshold
    roots = [n for n, d in G.in_degree() if d == 0]
    num_comp = len(list(nx.weakly_connected_components(G)))
    if len(roots) == 1 and num_comp == 1 and G.number_of_nodes() <= treshold and nx.is_directed_acyclic_graph(G):
        return True
    else:
        return False

def parse_formulas_and_convert(data_folder,logic_to_parse,output_folder):

    rootdir = f"{data_folder}/{logic_to_parse}"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # just to extract names of files we have data for so these are not processed and saved as graphs
    #timetable = pd.read_pickle(f"time_table_{logic_to_parse}.pickle")
    # to skip a file in case there are is no information about solvers for it
    #graphs_with_data = list(timetable.index)

    failed_formulas = 0
    cnt = 0

    # if the script fails on some graph, we can load the graphs parsed thus far and continue
    if os.path.exists(f"processed_graphs_{logic_to_parse}.pickle"):
        with open(f"processed_graphs_{logic_to_parse}.pickle", 'rb') as f:
            processed_graphs = pickle.load(f)
    else:
        processed_graphs = []

    # to later make 1 hot embeddings for the GCN, we store the set of all symbols which appeared in the parsed formulas
    if os.path.exists(f"symbols_{logic_to_parse}.pickle"):
        with open(f"symbols_{logic_to_parse}.pickle", 'rb') as f:
            all_symbols = pickle.load(f)
    else:
        all_symbols = set()

    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            filepath = subdir + os.sep + file
            # filter smt2 files with size less than 3.5MB
            if filepath.endswith(".smt2") and os.path.getsize(filepath) < 3500000:
                with open(filepath, 'r') as f:
                    # windows: makes filepath in format so it can be compared to entries in time table (removing data/)
                    #if str(Path(filepath)).replace("\\", "/")[5:] not in graphs_with_data:
                    #    continue
                    # check if the dot file already exists, this and next check is for the case this script runs multiple times
                    filepath = filepath.split(data_folder)[1]
                    if os.path.exists(str(Path(output_folder, str(Path(*Path(filepath).parts[1:]))[:-5] + ".dot"))):
                        continue
                    if filepath in processed_graphs:
                        continue

                    print(filepath)

                    content = f.read()
                    parser = SmtLibParser()
                    c = cStringIO()
                    pr = CustomSmtPrinter(c)

                    script = parser.get_script(cStringIO(content))

                    f = script.get_strict_formula()

                    e, n = pr.walk(f)

                    # reindex nodes to start from 0, e_new and n_new are node dict and edge list after re-indexing
                    order = sorted(n.keys())
                    n_new = {order.index(k): v for k, v in n.items()}
                    e_new = [(order.index(e1), order.index(e2)) for e1, e2 in e]

                    G = nx.DiGraph()
                    G.add_edges_from(e_new)

                    nx.set_node_attributes(G, n_new, "symbol")
                    # checks if the graph is in the correct format and it is not too big in terms of number of nodes
                    if check_graph(G, 10000):
                        Path(output_folder, Path(
                            *Path(filepath).parts[1:])).parent.mkdir(parents=True, exist_ok=True)
                        write_dot(G, str(Path(output_folder, str(
                            Path(*Path(filepath).parts[1:]))[:-5] + ".dot")))
                        all_symbols = all_symbols.union(set(list(n_new.values())))

                        with open(f'symbols_{logic_to_parse}.pickle', 'wb') as handle:
                            pickle.dump(all_symbols, handle,
                                        protocol=pickle.HIGHEST_PROTOCOL)
                        print("Graph_saved", cnt)
                        cnt += 1
                    else:
                        failed_formulas += 1
                        if failed_formulas % 200 == 0:
                            print("Failed: ", failed_formulas)
                    processed_graphs.append(filepath)
                    with open(f"processed_graphs_{logic_to_parse}.pickle", 'wb') as handle:
                        pickle.dump(processed_graphs, handle,
                                    protocol=pickle.HIGHEST_PROTOCOL)

                    # this will reset enviroment variables in pysmt, some logics contained variables of different types and same name which caused a problem
                    pysmt.environment.reset_env()
                    gc.collect()


if __name__ == '__main__':
        parser = argparse.ArgumentParser(description = 'Convert formulas to graphs')
        parser.add_argument('rootdir', help='the root folder which contains folders for different logics')
        parser.add_argument('logic', help='the name of the folder of a given logic')
        parser.add_argument('outdir', help='the path to the output dir')
        
        args = parser.parse_args()

        parse_formulas_and_convert(args.rootdir,args.logic,args.outdir)