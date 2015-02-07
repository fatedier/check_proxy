#!/bin/env python

import sys, threading, socket
sys.path.append("../common/")
import global_data, task
from main_data import *

# the info of client connecting to server
class ClientInfo:
    start_acct_str = ""     # task start account string
    start_pwd_str = ""      # task start password string
    end_acct_str = ""       # task end account string
    end_pwd_str = ""        # task end password string
    ip = ""                 # ip address of client
    port = -1               # port of client
    sock = None             # socket fd
    client_status = global_data.CLIENT_STATUS_NONE      # client status
    offline_count = 0       # every few seconds, offline_count plus 1, if exceed a special value, close socket of client
    task_success_count = 0  # when client finish one task, plus one

    def is_this_one(this, start_acct_str, start_pwd_str):
        """
        If account and password are same with client's, return True, else False

        start_acct_str(string): the task start account string
        start_pwd_str(string): the task start password string
        """
        if this.start_acct_str == start_acct_str \
           and this.start_pwd_str == start_pwd_str:
            return True
        else:
            return False

    def assign_one_task(this, main_data):
        """
        Assign one task by MainData of process

        main_data(MainData): assign task by present account and password string of main_data, 
                             present account and password will change to next value

        result(bool): if assign task success, return True, else means task is all over, return False
        """
        main_data.lock()
        if main_data.is_task_over() == True:
            main_data.unlock()
            return False

        this.start_acct_str = "".join(main_data.now_acct_list)
        this.start_pwd_str = "".join(main_data.now_pwd_list)
        
        task.get_one_task(main_data.now_acct_list, main_data.now_pwd_list, 4, global_data.g_max_len) #inc 46656

        this.end_acct_str = "".join(main_data.now_acct_list)
        this.end_pwd_str = "".join(main_data.now_pwd_list)
        
        main_data.unlock()

        return True


# list to save every task of client
class AllClientData:
    client_infos = []
    max_client_count = 0
    all_client_mutex = threading.Lock()


    def init(this, max_client_count):
        this.max_client_count = max_client_count
    
    def lock(this):
        this.all_client_mutex.acquire()

    def unlock(this):
        this.all_client_mutex.release()

    def get_task_string(this, index):
        """
        Get a string format with start_acct_str + start_pwd_str + end_acct_str + end_pwd_str,
        every string is split by ":"
        """
        return this.client_infos[index].start_acct_str + ":" + this.client_infos[index].start_pwd_str + ":" \
               + this.client_infos[index].end_acct_str + ":" + this.client_infos[index].end_pwd_str
    
    def get_ip_port(this, index):
        """
        Get a string, ip:port
        """
        return this.client_infos[index].ip + ":" + str(this.client_infos[index].port)
    
    def get_new_client_data(this, sock, ip, port):
        """
        When a thread start, first get a new ClientInfo object.
        If there is an idle ClientInfo, choose this one, else create a new object.

        return(int): return the index of client_infos, if the count of client_infos 
                     exceed max_client_count, return -1
        """
        this.lock()
        for i in range(len(this.client_infos)):
            if this.client_infos[i].client_status == global_data.CLIENT_STATUS_NONE \
                or this.client_infos[i].client_status == global_data.CLIENT_STATUS_OFFLINE:
                this.client_infos[i].sock = sock
                this.client_infos[i].ip = ip
                this.client_infos[i].port = port
                this.client_infos[i].client_status = global_data.CLIENT_STATUS_INIT
                this.unlock()
                return i

        if len(this.client_infos) < this.max_client_count:
            this.client_infos.append(ClientInfo())
            i = len(this.client_infos) - 1
            this.client_infos[i].sock = sock
            this.client_infos[i].ip = ip
            this.client_infos[i].port = port
            this.client_infos[i].client_status = global_data.CLIENT_STATUS_INIT
            this.unlock()
            return i

        this.unlock()
        return -1

    def assign_one_task(this, index, main_data):
        """
        Assign one task to client.
        
        return(bool): True if assign task success, else False
        """
        result = False
        this.lock()
        # if there are undown task leave, choose one from global undown task list
        if len(global_data.g_undown_task_list) > 0:
            start_acct_str, start_pwd_str, end_acct_str, end_pwd_str = global_data.g_undown_task_list.pop(0)
            this.client_infos[index].start_acct_str = start_acct_str
            this.client_infos[index].start_pwd_str = start_pwd_str
            this.client_infos[index].end_acct_str = end_acct_str
            this.client_infos[index].end_pwd_str = end_pwd_str
            result = True
        # assign one task from global main data
        else:
            result = this.client_infos[index].assign_one_task(main_data)
        
        if result == True:
            global_data.g_running_task_list.append((this.client_infos[index].start_acct_str, \
                                                    this.client_infos[index].start_pwd_str, \
                                                    this.client_infos[index].end_acct_str, \
                                                    this.client_infos[index].end_pwd_str))

        this.unlock()
        return result

    def clear_offline_count(this, index):
        """
        Every time geting a message from client, change responding offline_count to zero.
        """
        this.lock()
        this.client_infos[index].offline_count = 0
        this.unlock()

    def inc_and_check_offline_count(this, index):
        """
        Let offline_count plus 1.

        return(bool): if this client's offline_count > g_max_offline_count, return True, else False.
        """
        this.client_infos[index].offline_count += 1
        if this.client_infos[index].offline_count > global_data.g_max_offline_count:
            return True
        else:
            return False

    def close_error_client(this, index, is_lock = True):
        """
        Close error client, close socket, change status.
        """
        if is_lock:
            this.lock()
        this.client_infos[index].sock.close()
        # if one client doesn't finish the task, put in the g_undown_task_list
        if this.client_infos[index].client_status == global_data.CLIENT_STATUS_RUN:
            auth = this.get_task_string(index).split(":")
            global_data.g_undown_task_list.append((auth[0], auth[1], auth[2], auth[3]))
            global_data.g_running_task_list.remove((auth[0], auth[1], auth[2], auth[3]))
        # change status to offline
        this.client_infos[index].client_status = global_data.CLIENT_STATUS_OFFLINE
        if is_lock:
            this.unlock()
