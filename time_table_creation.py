import pandas as pd
from collections import defaultdict, Counter


data_all = pd.read_csv("data/Single_Query_Track.csv")
data_all = data_all.iloc[:-1] #last line was empty in this case

data_all = data_all.set_index("benchmark")
logic_names = {"QF_NRA", "AUFLIA", "UFNIA", "QF_NIA", "UFLIA"}
for log in logic_names:
    logic_name = f"Competition - Single Query Track/{log}"
    data = data_all.loc[data_all.index.str.contains(f"{logic_name}/")]
    data = data.reset_index()


    data_dict = defaultdict(list)

    possibilities = {"expected" : set(data["expected"]), "status" : set(data["status"]), "result" : set(data["result"]), "solvers" : set(data["solver"])}
    used_solvers = possibilities["solvers"]

    for entry in data.iloc:
        data_dict["/".join(entry["benchmark"].split("/")[1:])].append([entry["solver"], entry["status"], entry["wallclock time"], entry["result"], entry["expected"]])

    final_dict = {}
    for problem, info in data_dict.items():
        final_dict[problem] = {r[0]: (r[1], r[2], r[3], r[4]) for r in info if r[0] in used_solvers}
    res = pd.DataFrame(final_dict).transpose()
    res.to_pickle(f"full_time_table_{log}.pickle")

    final_dict = {}
    for problem, info in data_dict.items():
        final_dict[problem] = {r[0] : r[2] for r in info if r[0] in used_solvers}
    res = pd.DataFrame(final_dict).transpose()
    res.to_pickle(f"time_table_{log}.pickle")



print("Done")