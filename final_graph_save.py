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

import time
from pysmt.smtlib.printers import SmtPrinter


logic_to_parse = "QF_NRA"

def check_graph(Netx_graph, treshold):
    # check if the graph is in the correct form (DAG) and its number of vertices
    roots = [n for n, d in Netx_graph.in_degree() if d == 0]
    num_comp = len(list(nx.weakly_connected_components(G)))
    if len(roots) == 1 and num_comp == 1 and G.number_of_nodes() <= treshold and nx.is_directed_acyclic_graph(G):
        return True
    else:
        return False

rootdir = f"data/{logic_to_parse}" # smt lib files
output_folder = "dot_processed" # here dot graphs will be saved

if os.path.exists(output_folder) == False:
    os.makedirs("dot_processed")

timetable = pd.read_pickle(f"time_table_{logic_to_parse}.pickle") # just to extract names of files we have data for so these are not processed and saved as graphs
graphs_with_data = list(timetable.index) #to skip a file in case there are is no information about solvers for it

failed_formulas = 0
cnt = 0

if os.path.exists(f"processed_graphs_{logic_to_parse}.pickle"): #in case the the program is interrupted so it does not have to start over we store parsed smt file names
    with open(f"processed_graphs_{logic_to_parse}.pickle", 'rb') as f:
        processed_graphs = pickle.load(f)
else:
    processed_graphs = []

if os.path.exists(f"symbols_{logic_to_parse}.pickle"): # to later make 1 hot embeddings we make set of all symbols appeared in the data
    with open(f"symbols_{logic_to_parse}.pickle", 'rb') as f:
        all_symbols = pickle.load(f)
else:
        all_symbols = set()

for subdir, dirs, files in os.walk(rootdir):
    for file in files:
        filepath = subdir + os.sep + file
        if filepath.endswith(".smt2") and os.path.getsize(filepath) < 3500000: #filter smt2 files with size less than 3.5MB
            with open(filepath, 'r') as f:
                if str(Path(filepath)).replace("\\", "/")[5:] not in graphs_with_data: #windows: makes filepath in format so it can be compared to entries in time table (removing data/)
                    continue
                if os.path.exists(str(Path(output_folder, str(Path(*Path(filepath).parts[1:]))[:-5] + ".dot"))): #check if the dot file already exists, this and next check is for the case this script runs multiple times
                        continue
                if filepath in processed_graphs:
                        continue

                print(filepath)

                start = time.time()

                content = f.read()
                parser = SmtLibParser()
                c = cStringIO()
                pr = CustomSmtPrinter(c)

                script = parser.get_script(cStringIO(content))


                f = script.get_strict_formula()


                e, n = pr.walk(f)



                order = sorted(n.keys()) #reindex nodes to start from 0, e_new and n_new are node dict and edge list after re-indexing
                n_new = {order.index(k): v for k, v in n.items()}
                e_new = [(order.index(e1), order.index(e2)) for e1, e2 in e]

                G = nx.DiGraph()
                G.add_edges_from(e_new)


                nx.set_node_attributes(G, n_new, "symbol")
                check = check_graph(G, 10000) #checks if the graph is correct and if it is not too big



                if check:
                    Path(output_folder, Path(*Path(filepath).parts[1:])).parent.mkdir(parents=True, exist_ok=True)
                    write_dot(G, str(Path(output_folder, str(Path(*Path(filepath).parts[1:]))[:-5] + ".dot") ) )
                    all_symbols = all_symbols.union(set(list(n_new.values())))

                    with open(f'symbols_{logic_to_parse}.pickle', 'wb') as handle:
                        pickle.dump(all_symbols, handle, protocol=pickle.HIGHEST_PROTOCOL)
                    print("Graph_saved", cnt)
                    cnt += 1
                else:
                    failed_formulas += 1
                    if failed_formulas % 200 == 0:
                        print("Failed: ", failed_formulas)
                processed_graphs.append(filepath)
                with open(f"processed_graphs_{logic_to_parse}.pickle", 'wb') as handle:
                    pickle.dump(processed_graphs, handle, protocol=pickle.HIGHEST_PROTOCOL)

                pysmt.environment.reset_env() #this will reset enviroment variables in pysmt, some logics contained variables of different types and same name which caused a problem
                gc.collect()