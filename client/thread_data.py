#!/bin/env python

import sys, copy, threading
sys.path.append("../common/")
import global_data, task, main_data

# the thread self data
class WorkThreadData:
    start_acct_list = []
    end_acct_list = []
    now_acct_list = []
    start_pwd_list = []
    end_pwd_list = []
    now_pwd_list = []

    def is_task_over(this):
        result = task.compare_auth(this.now_acct_list, this.now_pwd_list, \
                              this.end_acct_list, this.end_pwd_list)
        if result == 0 or result == 1:
            return True
        else:
            return False

    def get_one_thread_task(this, main_data):
        """
        get one task from MainData

        main_data(MainData): the golbal variable
        return(bool): if get task success, return True, else False
        """
        
        main_data.lock()
        if main_data.is_task_over() == True:
            main_data.unlock()
            return False

        this.start_acct_list = copy.deepcopy(main_data.now_acct_list)
        this.start_pwd_list = copy.deepcopy(main_data.now_pwd_list)
        
        task.get_one_task(main_data.now_acct_list, main_data.now_pwd_list, 3, global_data.g_max_len) #inc 1296

        this.end_acct_list = copy.deepcopy(main_data.now_acct_list)
        this.end_pwd_list = copy.deepcopy(main_data.now_pwd_list)
        main_data.unlock()

        this.now_acct_list = copy.deepcopy(this.start_acct_list)
        this.now_pwd_list = copy.deepcopy(this.start_pwd_list)
        return True
    
    def get_next_try_data(this):
        """
        change to next data to try
        
        return(bool): if complete one task, return True, else False
        """

        task.get_next_auth(this.now_acct_list, this.now_pwd_list, global_data.g_max_len)
        return this.is_task_over()

    def get_send_msg(this, msg):
        """
        pack this thread's now data to message which will be sent

        msg(string): http message header template
        return(string): the message to be sent
        """
        
        return task.get_send_msg(global_data.g_msg, this.now_acct_list, this.now_pwd_list)
