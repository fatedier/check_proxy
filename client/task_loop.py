#!/bin/env python

import sys, time, threading, socket, thread, os
sys.path.append("../common/")
import global_data
from thread_data import *
from message import *
from work_thread import *
from main_data import *

threads = []        # threads objects

def task_loop(sock):
    msg_header = MsgHeader()
    body = ""
    
    send_get_one_task(sock)

    while True:
        try:
            str_head = sock.recv(g_head_size)
            if str_head == "":
                print("Connection is closed by server, program will exit now...")
                sock.close()
                os._exit(-1)

            msg_header.pack(str_head)
            if int(msg_header.body_length) != 0:
                body = sock.recv(int(msg_header.body_length))
        except socket.error:
            print("Recv message error, program will exit now...")
            sock.close()
            os._exit(-1)
        except KeyboardInterrupt:
            os._exit(-1)

        cmd = msg_header.cmd
        if cmd == global_data.TASK_CMD_RESPONSE:
            deal_response(sock, body)
        elif cmd == global_data.TASK_CMD_STOPCLIENT:
            deal_stop_client(sock, body)
        elif cmd == global_data.TASK_CMD_HEARTBEAT:
            deal_heart_beat(sock, body)
        else:
            # error cmd, ignore
            pass


def father_task_thread_entrance(sock):
    """
    When client get response for TASK_CMD_RESPONSE, this thread should create 
    some child thread to deal task and join for threads end.
    Then send TASK_CMD_FINISHTASK message to server and sleep for a while.
    FInally send TASK_CMD_GETTASK to continue.
    """
    for i in range(global_data.g_thread_count):
        global_data.g_thread_data.append(WorkThreadData())
        t = threading.Thread(target = work_thread_entrance, args=(i,))
        t.setDaemon(True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("All task from server is finished, send task result to server and sleep for " \
            + str(global_data.g_finish_sleep_time) + " seconds...\n")
    # send task result to server
    send_finish_one_task(sock)

    time.sleep(global_data.g_finish_sleep_time)

    # get next task from server
    send_get_one_task(sock)

def send_get_one_task(sock):
    """
    Send Task_CMD_GETTASK to server to get one task.
    """
    print("Sending message to server for one task...")
    msg_header = MsgHeader()
    msg_header.cmd = global_data.TASK_CMD_GETTASK
    msg_header.body_length = "0000"
    try:
        sock.sendall(msg_header.unpack())
    except:
        print("Send message error, program will exit now...")
        sock.close()
        os._exit(-1)

def send_finish_one_task(sock):
    """
    Client finish one task, send result to server.

    Body format is account1:password1~account2:password2, etc...
    """
    msg_header = MsgHeader()
    msg_header.cmd = global_data.TASK_CMD_FINISHTASK
    body = ""
    for auth in global_data.g_find_auth_list:
        # auth is tuple (account, password)
        body += auth[0]
        body += ":"
        body += auth[1]
        body += "~"
    body = body.rstrip("~")
    msg_header.body_length = "%04d" % len(body)

    del(global_data.g_find_auth_list[:])

    try:
        sock.sendall(msg_header.unpack() + body)
    except:
        print("Send message error, program will exit now...")
        sock.close()
        os._exit(-1)

def deal_response(sock, body):
    """
    Get TASK_CMD_RESPONSE cmd from server.
    """
    if body[0:2] == global_data.TASK_CMD_GETTASK:
        task_auth = body[2:].split(":")
        if len(task_auth) != 4:
            # message error, ignore
            return

        global_data.g_main_data.init(task_auth[0], task_auth[1], task_auth[2], task_auth[3])
        
        print("Get one task from server...")
        print("---- from " + task_auth[0] + ":" + task_auth[1])
        print("---- to   " + task_auth[2] + ":" + task_auth[3])

        t = threading.Thread(target = father_task_thread_entrance, args = (sock,))
        t.setDaemon(True)
        t.start()
    else:
        # error cmd, ignore
        pass


def deal_stop_client(sock, body):
    """
    Get TASK_CMD_STOPCLIENT cmd from server.
    """
    print("Get TASK_CMD_STOPCLIENT from server, close now...")
    os._exit(-1)


def deal_heart_beat(sock, body):
    """
    Get TASK_CMD_HEARTBEAT cmd from server, return the TASK_CMD_RESPONSE with no data.
    """
    msg_header = MsgHeader()
    msg_header.cmd = global_data.TASK_CMD_RESPONSE
    body = global_data.TASK_CMD_HEARTBEAT
    msg_header.body_length = "%04d" % len(body)
    try:
        sock.sendall(msg_header.unpack() + body)
    except:
        print("Send message error, program will exit now...")
        sock.close()
        os._exit(-1)
