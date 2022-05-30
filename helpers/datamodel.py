from os.path import exists as file_exists
from pathlib import Path
from typing import Dict, Callable
import pandas as pd
import numpy as np
import json

HELPERS = Path(__file__).absolute().parent
MODEL_CSV = HELPERS / "iase-ia" / "SmartData Model - AllVariables.csv"

dtype_map = {
    "t0": "float64",
    "unit": "int64",
    "error": "float64",
    "confidence": "float64",
    "r": "float64",
    "x": "float64",
    "y": "float64",
    "z": "float64",
    "period": "float64",
}


def read_model_from_csv(fpath=None) -> pd.DataFrame:
    fpath = fpath if fpath is not None else MODEL_CSV
    with open(fpath, "r") as f:
        df = pd.read_csv(f)

    return df


def model_to_label_map(model_df: pd.DataFrame) -> Dict:
    model_df["Unit"] = model_df["Unit"].apply(int, base=16)
    keys = (
        model_df[["Unit", "Dev"]]
        .to_records(index=False, column_dtypes="int64")
        .tolist()
    )
    values = model_df["Label"].values
    return dict(zip(keys, values))


def get_label_map() -> Dict:
    return model_to_label_map(read_model_from_csv())

def write_log(log_file, text, break_line=True):
    with open(f"{log_file}", "a") as f:
        if break_line:
            text += "\n"
        f.write(text)

def smartdata_to_df(smartdata_all: Dict) -> pd.DataFrame:
    if "series" in smartdata_all:  # MultiValues
        smartdata_all = smartdata_all["series"]

    df_all = pd.DataFrame()

    for smartdata in smartdata_all:
        write_log("smart.log",json.dumps(smartdata)) 
        if "smartdata" in smartdata:  # single value
            if len(smartdata_all) > 0:
                smartdata = smartdata["smartdata"]
            else:
                smartdata = smartdata_all[smartdata]
            
            df = pd.DataFrame(smartdata, index=[0])

            if "timestamp" in smartdata:
                df["t"] = df["timestamp"]
            elif "t0" in smartdata:
                df["t"] = df["t0"]

        if "MultiValueSmartData" in smartdata:
            if len(smartdata_all) > 0:
                smartdata = smartdata["MultiValueSmartData"]
            else:
                smartdata = smartdata_all[0]

            df = pd.DataFrame(smartdata["datapoints"])
            for k in filter(lambda x: x != "datapoints", smartdata):
                df[k] = smartdata[k]

            if "offset" in df.columns:
                df["t"] = df["t0"] + df["offset"]
            elif "period" in df.columns:
                df["t"] = df["t0"] + df.index * df["period"]

        for t in dtype_map:
            if t in df:
                df[t] = df[t].astype(dtype_map[t])
        
        df_all = pd.concat([df_all, df])

    # if "signature" in df:
    #     df["signature"] = df["signature"].apply(lambda x: str(int(x)) if x else None)

    return df_all


def add_label_col(df: pd.DataFrame, map: Dict) -> pd.DataFrame:
    df["label"] = df.apply(lambda x: map.get((x["unit"], x["dev"])), axis=1)
    return df


def read_smartdata(smartdata_argv, filename):
    full_filename = filename + "_" + str(smartdata_argv)

    if file_exists(full_filename):
        with open(full_filename, "r") as f:
            smartdata = json.loads(f.read())
    else:
        smartdata = json.loads(smartdata_argv)

    return smartdata


def set_uuid_to_coords(row):
    row["uuid"] = f'{row["x"]}_{row["y"]}_{row["z"]}'
    return row


def add_uuid_col(df: pd.DataFrame) -> pd.DataFrame:
    if "signature" in df:
        df["uuid"] = df["signature"]
    else:
        uuid_nan = np.array([np.NaN] * len(df))
        df["uuid"] = uuid_nan.tolist()
        df = df[df["uuid"].isna()].apply(set_uuid_to_coords, axis=1)
    return df
