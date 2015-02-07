#!/bin/env python

import sys, time, threading, socket, thread
sys.path.append("../common/")
import global_data
from thread_data import *

def work_thread_entrance(no):
    """
    thread main function

    no(int): the number of thread
    """

    while True:
        if global_data.g_thread_data[no].get_one_thread_task(global_data.g_main_data) == False:
            print("Thread " + str(no) + " find no task, exit!")
            thread.exit_thread()

        print("Thread " + str(no) + " get one task" + \
              " from " + "".join(global_data.g_thread_data[no].start_acct_list) + ":" + \
              "".join(global_data.g_thread_data[no].start_pwd_list) + \
              " to " + "".join(global_data.g_thread_data[no].end_acct_list) + ":" + \
              "".join(global_data.g_thread_data[no].end_pwd_list))

        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((global_data.g_proxy_ip, global_data.g_proxy_port))
            except:
                print("Thread " + str(no) + " connect to proxy error!Wait for " + str(global_data.g_error_sleep_time) + " second and try again...")
                time.sleep(global_data.g_error_sleep_time)
                s.close()
                continue

            try:
                s.send( global_data.g_thread_data[no].get_send_msg(global_data.g_msg) )
                response = s.recv(4096)
            except:
                print("Send or recv data from proxy server error!Wait for " + str(global_data.g_error_sleep_time) + " second and try again...")
                time.sleep(global_data.g_error_sleep_time)
                s.close()
                continue
            
            s.close()

            if "".join(response[9:12]) == "200":
                print("find! " + "".join(global_data.g_thread_data[no].now_acct_list) + ":" + "".join(global_data.g_thread_data[no].now_pwd_list))
                global_data.g_main_data.lock()
                global_data.g_find_auth_list.append(("".join(global_data.g_thread_data[no].now_acct_list), "".join(global_data.g_thread_data[no].now_pwd_list)))
                global_data.g_main_data.unlock()
            elif "".join(response[9:12]) != "407":
                print("may be! " + "".join(global_data.g_thread_data[no].now_acct_list) + ":" + "".join(global_data.g_thread_data[no].now_pwd_list))
                global_data.g_main_data.lock()
                global_data.g_find_auth_list.append(("".join(global_data.g_thread_data[no].now_acct_list), "".join(global_data.g_thread_data[no].now_pwd_list)))
                global_data.g_main_data.unlock()
            else:
                pass

            if global_data.g_thread_data[no].get_next_try_data() == True:
                print("Thread " + str(no) + " complete one small task! continue...")
                break
