import os, json, time
from variables import vars as name_var
from dictionary import * 
from random import randint, random
import aiohttp, asyncio

def random_values(amount_values, var, ):
    radom_value = []
    radom_time = []

    for index in range(amount_values):
        # time.sleep(1)
        t = index
        t = t * (10 ** 6)

        if int(dic_max[var]) == dic_max[var]:
            vl = randint(int(dic_min[var]), int(dic_max[var])) 
        else:
            vl = random() * dic_max[var]

        radom_value.append(vl)
        radom_time.append(t)

    return radom_value, radom_time  

def valid_dictionary(var_id):
    for name_variable in name_var:
        if name_var[name_variable] == name[var_id]:
            return True
        else:
            pass
    
    return False

def get_currentTime():
    currentTime = int(time.time() * (10 ** 6))
    return currentTime

def operation_file(file_path, mode, message=""):
    if os.path.exists(file_path):
        if mode == "r":
            with open(f"{file_path}", mode) as f:
                return f.read()
        elif mode == "w" or mode == "a":
            with open(f"{file_path}", mode) as f:
                return f.write(message+"\n")
    else:
        if mode == "w" or mode == "a":
            with open(f"{file_path}", mode) as f:
                return f.write(message+"\n")
        else:
            return ""

def load_configs(file_configs):
    configs = operation_file(file_configs, "r")

    return json.loads(configs)

def get_url(configs, key):
    return configs["urls"][key].replace("<serv>", configs["serv"])

def url(method, mv, configs):
    if method == "GET":
        url_send = get_url(configs, "get")
    elif method == "PUT":
        if mv:
            url_send = get_url(configs, "mv_put")
        else:
            url_send = get_url(configs, "put")
    elif method == "FINISH":
        url_send = get_url(configs, "finish")
    elif method == "CREATE":
        url_send = get_url(configs, "create")
    elif method == "SEARCH":
        url_send = get_url(configs, "search")

    return url_send

def build_query(version, t0, t1, unit, type_query, period, r, x, y, z, dev, sig, wf, domain, username, password):
    result_json = {
        "series": {
            "version": version,
            "t0": t0,
            "t1": t1,
            "unit": unit,
            "type": type_query,
            "period": period,
            "r": r,
            "x": x,
            "y": y,
            "z": z,
            "dev": dev,
            "signature": sig,
            "workflow": wf
        },
        "credentials": {"domain": domain,  "username": username, "password": password},
    }

    return result_json

def build_url(method, configs):
    mv = configs["mv"]
    if method == "GET":
        url_send = get_url(configs, "get")
    elif method == "PUT":
        if mv:
            url_send = get_url(configs, "mv_put")
        else:
            url_send = get_url(configs, "put")
    elif method == "FINISH":
        url_send = get_url(configs, "finish")
    elif method == "CREATE":
        url_send = get_url(configs, "create")
    elif method == "SEARCH":
        url_send = get_url(configs, "search")
    
    return url_send

def source_period(id_source):
    if id_source == 30:
        period = 4000
    elif id_source == 31:
        period = 5000
    elif id_source == 32:
        period = 10000
    elif id_source == 33:
        period = 100000
    else:
        #verificar quando por cylindro qual periodo deve ser, segundo o Sergio o valor do periodo varia, porém aí dificulta a aquisição destes dados
        period = 0

    return period

def build_tasks(session, queries):
    tasks = []
    for request_json in queries:
        url_send = request_json['url']
        query_send = request_json['query']
            
        #Query Send
        query_send_text = json.dumps(query_send)

        tasks.append(asyncio.create_task(session.post(url_send, data=query_send_text)))
    return tasks

def write_log(log_file, text, break_line=True):
    with open(f"{log_file}", "a") as f:
        if break_line:
            text += "\n"
        f.write(text)
   

def generate_xyz():
    x = randint(0, 255)
    y = randint(0, 255)
    z = randint(0, 255)

    return x, y, z
    

    