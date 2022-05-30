import json, os, time, argparse
import pandas as pd, numpy as np
# from threading import Thread
# from typing import Dict, Callable
from datetime import datetime
import aiohttp, asyncio
# from functools import reduce

from helpers import datamodel, daemon_utils
from helpers import functions

labels_map = datamodel.get_label_map()

PATH_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = f"{PATH_DIR}/configs"

queries = []
responses = []
results = []

def getColumn(smartdata):
    df_raw = datamodel.smartdata_to_df(smartdata)
    # df_raw = datamodel.add_uuid_col(df_raw)
    df_raw.index = [i for i in range(len(df_raw))]  

    if len(df_raw) > 0:
        
        unit = df_raw["unit"][0]
        dev = df_raw["dev"][0]

        try:
            label = labels_map[(unit, dev)]
        except:
            label = f"undefined_{unit}_{dev}" 

        df_new = pd.DataFrame(df_raw["value"].values, columns=[label])

        df_new.index = pd.to_datetime(df_raw["t"], unit="ns")
        
        # df_new = df_new.ffill().bfill().resample("4ms").max().dropna()
        df_new = df_new.resample("5ms").max().dropna()
        
        return df_new

    return df_raw

async def get_data_iot():
    async with aiohttp.ClientSession() as session:
        tasks = functions.build_tasks(session, queries)
        responses = await asyncio.gather(*tasks)

        for response in responses:
            results.append(await response.text())
    

def main():

    start_process = int(time.time())

    #LOAD CONFIGS
    configs = functions.load_configs(CONFIG_FILE)

    domain = configs["domain"]
    username = configs["username"]
    password = configs["password"]
    version = configs["version"]

    EXPERIMENT_PATH = configs["experiment_path"]
    EXPORT_PATH = configs["export_path"]
    EXPORT_NAME = configs["export_name"]

    if EXPORT_PATH is None or len(EXPORT_PATH) == 0: 
        EXPORT_PATH = "./export/"
    if EXPORT_NAME is None or len(EXPORT_NAME) == 0: 
        EXPORT_NAME = ""

    if not os.path.exists(EXPERIMENT_PATH):
        print(f"Experiment file does not exists on {EXPERIMENT_PATH}.")
        return 0
    
    if not os.path.exists(EXPORT_PATH):
        print(f"Export path does not exists on {EXPORT_PATH}.")
        return 0

    with open(EXPERIMENT_PATH, "r") as f:
        experiment_variables = json.loads(f.read())

    vrs = []
    vrs_info = {}

    #LOAD VARIABLES + UNIT + DEV
    sig = experiment_variables["chassisId"][0]
    for var in experiment_variables["measurements"]:
        var_name = var["name"]
        var_unit = int(var["unit"],16)
        var_dev = int(var["dev"])
        var_source = var["source"]

        var_period = int(functions.source_period(var_source))

        vrs.append(var_name)
        vrs_info[var_name] = (var_unit, var_dev, var_period)

    #LOAD CONFIGS
    configs = functions.load_configs(CONFIG_FILE)

    domain = configs["domain"]
    username = configs["username"]
    password = configs["password"]
    version = configs["version"]

    if (len(sig[0]) == 0 or sig[0] is None or sig[0] == "") and version == 1.2:
        print("please verify if the tag <chassisId> on the experiment is informed.")
        return 0

    if len(domain) == 0 or len(username) == 0 or len(password) == 0 or len(configs["serv"]) == 0:
        print("please verify the configs file: domain, username, password or serv.")
        return 0

    wf = configs["wf"]
    error = configs["error"]
    trust = configs["trust"]
    type_query = configs["type"]

    x = configs["x"]
    y = configs["y"]
    z = configs["z"]
    r = configs["r"]

    method = "GET"

    print("Inform periods (microseconds/miliseconds/seconds):")
    t0 = int(input("t0: "))
    t1 = int(input("t1: "))
    # t0 = 1651074749 
    # t1 = 1651076122

    if t1 < t0:
        print("please inform t1 higher than t0.")
        return 0

    size_16 = len('1648708800000000')
    size_13 = len('1648708800000')
    size_10 = len('1648708800')

    if len(str(t0)) == size_10:
        t0 = t0 * (10 ** 6)
    
    if len(str(t1)) == size_10:
        t1 = t1 * (10 ** 6)

    if len(str(t0)) == size_13:
        t0 = t0 * (10 ** 3)
    
    if len(str(t1)) == size_13:
        t1 = t1 * (10 ** 3)

    if size_16 != len(str(t0)) or size_16 != len(str(t1)):
        print(f"please, inform t0 and t1 in epoch time length of {size_16} (microseconds), {size_13} (miliseconds) or {size_10} (seconds).")
        return 0
    else:
        search_from = str(datetime.fromtimestamp(t0/(10**6)))
        search_to = str(datetime.fromtimestamp(t1/(10**6)))

        print(f"searching on {configs['serv'].upper()} from {search_from} to {search_to}")

    for counter_step, var in enumerate(vrs):
        unit, dev, period = vrs_info[var]

        query_send = functions.build_query(version, t0, t1, unit, type_query, period, r, x, y, z, dev, sig, wf, domain, username, password)
        url_send = functions.build_url(method, configs)

        request_send = { "method": method, "url": url_send, "query": query_send, "var": var, "step": counter_step}
                    
        queries.append(request_send)
    
    print(f" sending {len(vrs)} requests...")

    now = time.time()
    asyncio.run(get_data_iot())
    print(f"  IOT Get Async Took: {int(time.time()-now)} seconds")
    
    df_list = []
    while True:
        if len(results) == len(vrs):
            print(" building dataframe(df)...")
            for res in results:
                # functions.write_log("TESTE.LOG", f"\n\n{time.time()}\n{res}")
                df_list.append(getColumn(json.loads(res)))
            break
    
    # if MERGE == 'YES':
    #     print(" merging results...")

    #     df = reduce(lambda  left,right: pd.merge(left,right,on=['t'], how='outer'), df_list).fillna('void')

    #     # df = df_list[0]
    #     # for i in range(1,len(df_list)):
    #     #     df = pd.merge(df, df_list[i], how="outer", left_index=True, right_index=True)
    # else:
    print(" concatenating results...")
    
    # df = pd.concat(df_list, axis=1,copy=False, ignore_index=True)
    # df = pd.concat(df_list, axis=1,copy=False)
    df = pd.concat(df_list, join='outer', axis=1).fillna(0)
    
    print(" exporting df...")

    EXTENTION = str(daemon_utils.get_currentTime())

    if len(EXPORT_NAME) == 0:
        search_from = search_from[len(search_from)-8:].replace(":","_")
        search_to = search_to[len(search_to)-8:].replace(":","_")
        NAME_EXPORT = f"IOT_EXP_{t0}_to_{t1}.parquet"
    else:
        NAME_EXPORT = f"{EXPORT_NAME}.parquet"

    if EXPORT_PATH[len(EXPORT_PATH)-1] == "/":
        EXPORT_PATH = f"{EXPORT_PATH}{NAME_EXPORT}"
    else:
        EXPORT_PATH = f"{EXPORT_PATH}/{NAME_EXPORT}"
    
    end_process = int(time.time())

    if len(df) == 0:
        print(f"No data in the period informed, took {end_process-start_process} seconds.")
        os.system(f'rm "{EXPORT_PATH}"')
    else:
        df.to_parquet(EXPORT_PATH, index=True) 

        print(f"Exported to file {EXPORT_PATH}, took {end_process-start_process} seconds.")

    
if __name__ == "__main__":
    main()
