#!/bin/env python

import threading, copy
import task

# the process global data
class MainData:
    start_acct_list = []
    end_acct_list = []
    now_acct_list = []
    start_pwd_list = []
    end_pwd_list = []
    now_pwd_list = []
    main_data_mutex = threading.Lock()
    

    def init(this, start_acct_str, start_pwd_str, end_acct_str, end_pwd_str):
        """
        initial data from string to list
        """

        this.start_acct_list = list(start_acct_str)
        this.end_acct_list = list(end_acct_str)
        this.start_pwd_list = list(start_pwd_str)
        this.end_pwd_list = list(end_pwd_str)
        this.now_acct_list = copy.deepcopy(this.start_acct_list)
        this.now_pwd_list = copy.deepcopy(this.start_pwd_list)

    def lock(this):
        this.main_data_mutex.acquire()

    def unlock(this):
        this.main_data_mutex.release()

    def is_task_over(this):
        result = task.compare_auth(this.now_acct_list, this.now_pwd_list, \
                              this.end_acct_list, this.end_pwd_list)
        if result == 0 or result == 1:
            return True
        else:
            return False
