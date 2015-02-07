#!/bin/env python

import os, socket, time, sys, threading, base64
sys.path.append("./common/")
sys.path.append("./client/")
import global_data
from work_thread import *
from main_data import *
from task_loop import *

if __name__ == "__main__":
    global_data.g_main_data = MainData()    # init g_main_data

    # connect to server
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((global_data.g_server_ip, global_data.g_server_port))
    except:
        print("connect server error!")
        sys.exit(-1)
    
    task_loop(s)
