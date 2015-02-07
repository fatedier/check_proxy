#!/bin/env python

import os, socket, time, sys, threading, base64, signal
sys.path.append("./common/")
sys.path.append("./server/")
import global_data
from client_info import *
from assign_task_thread import *

if __name__ == "__main__":
    # create data file, if exist, read data and initial
    global_data.g_task_file = open(global_data.TASK_FILE, "r+", 0)
    start_auth = global_data.g_task_file.readline()
    start_auth = start_auth.rstrip("\n")
    global_data.g_result_file = open(global_data.RESULT_FILE, "a", 0)

    global_data.g_main_data = MainData()    # init g_main_data

    if start_auth == "":
        global_data.g_main_data.init(global_data.START_ACCT_STR, global_data.START_PWD_STR, \
                                     global_data.END_ACCT_STR, global_data.END_PWD_STR)
    else:
        start_auth_split = start_auth.split(":")
        global_data.g_main_data.init(start_auth_split[0], start_auth_split[1], \
                                     global_data.END_ACCT_STR, global_data.END_PWD_STR)

    global_data.g_all_client_data = AllClientData() # init all client data
    global_data.g_all_client_data.init(global_data.g_max_clients)

    try:
        listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_sock.bind(("0.0.0.0", global_data.g_server_port))
        listen_sock.listen(20)
    except:
        print("Init socket server error!")
        sys.exit(-1)
    
    # create heart beat thread
    t = threading.Thread(target = heart_beat_thread_entrance)
    t.setDaemon(True)
    t.start()

    while True:
        try:
            con_fd, addr = listen_sock.accept()
            t = threading.Thread(target = work_thread_entrance, args = (con_fd, addr[0], addr[1]))
            t.setDaemon(True)
            t.start()
        except socket.error:
            print("Socket accept error!")
            sys.exit(-1)
        except KeyboardInterrupt:
            sys.exit(-1)
        except:
            print("Get one connect from " + addr[0] + ", but create thread error!Close this socket.")
            con_fd.close()
            continue
