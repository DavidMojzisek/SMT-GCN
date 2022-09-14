from tqdm import tqdm
import pandas as pd
from networkx import nx_agraph
import pygraphviz
import pickle
import os
from torch_geometric.data import Data
import numpy as np
import torch
from pathlib import Path

import global_params


def assign_time(pd_frame_line, time_out, used_solvers):
    y = []
    for sol in used_solvers: #0 status  1 time 2 result 3 expected
        if pd_frame_line[sol][3] == pd_frame_line[sol][2]:
          time = float(pd_frame_line[sol][1])
        if pd_frame_line[sol][3] == "starexec-unknown" and pd_frame_line[sol][2] != "starexec-unknown":
          time = float(pd_frame_line[sol][1])
        if pd_frame_line[sol][3] == "starexec-unknown" and pd_frame_line[sol][2] == "starexec-unknown":
          time = 2*time_out
        if pd_frame_line[sol][3] == "sat" and pd_frame_line[sol][2] == "sat":
          time = float(pd_frame_line[sol][1])
        if pd_frame_line[sol][3] == "unsat" and pd_frame_line[sol][2] == "unsat":
          time = float(pd_frame_line[sol][1])
        if pd_frame_line[sol][0] != "complete":
          time = 2*time_out

        determine_interval = lambda t : int(np.floor(pow(t, np.log(global_params.number_of_intervals) / np.log(global_params.time_out)))) if t <= global_params.time_out else global_params.number_of_intervals

        y.append(determine_interval(time))

    return y


def create_data(logic_name):
    dot_graph_folder, time_table_path, symbol_set_path = f"dot_processed/{logic_name}", f"full_time_table_{logic_name}.pickle", f"symbols_{logic_name}.pickle"

    cnt = 0
    timetab = pd.read_pickle(time_table_path)
    used_solvers = list(timetab.columns)

    with open(symbol_set_path, 'rb') as f:
        symbol_set = pickle.load(f)
        symbol_set = list(symbol_set)

    if os.path.exists(f'processed_paths_PyG_{logic_name}.pickle'):
        with open(f'processed_paths_PyG_{logic_name}.pickle', 'rb') as f:
            processed_filepaths = pickle.load(f)
    else:
        processed_filepaths = []
        with open(f'processed_paths_PyG_{logic_name}.pickle', 'wb') as handle:
            pickle.dump(processed_filepaths, handle, protocol=pickle.HIGHEST_PROTOCOL)


    for subdir, dirs, files in tqdm(os.walk(dot_graph_folder)):
        for file in files:
            filepath = subdir + os.sep + file
            if filepath.endswith(".dot"):
                if filepath in processed_filepaths:
                    continue
                problem_name = "/".join(Path(filepath).parts[1:])[:-4] + ".smt2"
                if problem_name not in list(timetab.index):
                    continue
                pd_frame_line = timetab.loc[problem_name]
                gr = nx_agraph.from_agraph(pygraphviz.AGraph(filepath))
                edge_list = []
                for ed in list(gr.edges):
                    edge_list += [(int(ed[0]), int(ed[1])), (int(ed[1]), int(ed[0])) ]
                edge_index = list(zip(*list(edge_list)))
                edge_index = torch.tensor(edge_index, dtype=torch.long)

                x = []
                for i in range(len(gr.nodes)):
                    x.append(np.eye(len(symbol_set), dtype = int)[symbol_set.index(dict(gr.nodes.data())[str(i)]["symbol"])] )
                x = torch.tensor(np.array(x), dtype=torch.float)


                y = assign_time(pd_frame_line, global_params.time_out, used_solvers)

                datapoint = Data(x = x, edge_index = edge_index, y = torch.tensor(y, dtype=torch.long), problem_name = problem_name)

                cnt += 1

                if os.path.exists(f'{logic_name}_PyG_datalist.pickle'):
                    with open(f'{logic_name}_PyG_datalist.pickle', 'rb') as f:
                        old_data_list = pickle.load(f)
                        new_datalist = old_data_list + [datapoint]
                    with open(f'{logic_name}_PyG_datalist.pickle', 'wb') as handle:
                        pickle.dump(new_datalist, handle, protocol=pickle.HIGHEST_PROTOCOL)
                    del old_data_list, new_datalist
                else:
                    with open(f'{logic_name}_PyG_datalist.pickle', 'wb') as handle:
                        pickle.dump([datapoint], handle, protocol=pickle.HIGHEST_PROTOCOL)
                with open(f'processed_paths_PyG_{logic_name}.pickle', 'rb') as f:
                    processed_filepaths = pickle.load(f)
                    processed_filepaths.append(filepath)
                with open(f'processed_paths_PyG_{logic_name}.pickle', 'wb') as handle:
                    pickle.dump(processed_filepaths, handle, protocol=pickle.HIGHEST_PROTOCOL)
                print(f"Total Graph Processed {cnt}")
    return None

if __name__ == "__main__":

    logic_name = "QF_NRA"
    create_data(logic_name)
    print("DONE")