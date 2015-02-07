#!/bin/env python

# defines

# client status
CLIENT_STATUS_NONE      = "0"   # initial status
CLIENT_STATUS_INIT      = "1"   # client first connect to server
CLIENT_STATUS_RUN       = "2"   # client is runing to finish task
CLIENT_STATUS_DOWN      = "3"   # client finish one task
CLIENT_STATUS_OFFLINE   = "4"   # client is offline

# task_command
TASK_CMD_HEARTBEAT      = "00"  # server to client, heart beat
TASK_CMD_GETTASK        = "01"  # client to server, get one task
TASK_CMD_FINISHTASK     = "02"  # client to server, finish one task
TASK_CMD_STOPCLIENT     = "03"  # server to client, find error, stop client
TASK_CMD_RESPONSE       = "04"  # response to cmd


g_main_data = None              # global account and password data
g_server_ip = "0.0.0.0"         # server ip
g_server_port = 9999            # server port
g_thread_data = []              # thread data, responding to the index of thread
g_thread_count = 10             # count of threads
g_proxy_ip = "0.0.0.0"          # proxy ip
g_proxy_port = 808              # proxy port
g_max_len = 8                   # account and password max length
g_error_sleep_time = 10         # unit:second, if meet an error, sleep for a while
g_finish_sleep_time = 10        # unit:second, when client finish one task, sleep for a while
g_find_auth_list = []           # the auth found by clinet in one task, value is tuple (account, password)

g_msg = """GET http://www.baidu.com/ HTTP/1.0
User-Agent: Wget/1.12 (linux-gnu)
Accept: */*
Host: www.baidu.com
Proxy-Authorization: Basic """  # http message header template


# server global info
# file name
TASK_FILE               = ".task.dat"       # task file to save first undown start auth string
RESULT_FILE             = ".result.dat"     # result file to save results found by clients

# task info
START_ACCT_STR          = "0"
START_PWD_STR           = "0"
END_ACCT_STR            = "ZZZZZZ"
END_PWD_STR             = "ZZZZZZ"

g_all_client_data = None        # all clients data
g_max_clients = 5               # max clients which can connect to server
g_interval_time = 10            # unit:second, every g_interval_time, offline_count plus 1
g_max_offline_count = 3         # when offline_count exceed this value, close socket
g_undown_task_list = []         # if one client is offline, put undown list in this list
                                # value is tuple (start_acct_str, start_pwd_str, end_acct_str, end_pwd_str)
g_running_task_list = []        # which tasks runing in clients, value is same as g_undown_task_list
g_task_file = None              # file object for TASK_FILE
g_result_file = None            # file object for RESULT_FILE
