#!/bin/env python

import sys, socket, thread, time
sys.path.append("../common/")
import global_data, task
from client_info import *
from message import *

def heart_beat_thread_entrance():
    """
    Send heartbeat packet to all clients interval of g_interval_time.
    """
    msg_header = MsgHeader()
    msg_header.cmd = global_data.TASK_CMD_HEARTBEAT
    msg_header.body_length = "0000"

    while True:
        time.sleep(global_data.g_interval_time)
        
        sock_list = []  # save sockets of active clients
        first_undown_auth = ""      # if g_running_task_list is not empty, just find the min one

        global_data.g_all_client_data.lock()

        index = 0
        for client in global_data.g_all_client_data.client_infos:
            if client.client_status == global_data.CLIENT_STATUS_INIT \
                    or client.client_status == global_data.CLIENT_STATUS_RUN \
                    or client.client_status == global_data.CLIENT_STATUS_DOWN:
                # if this client doesn't response for special time, close it
                if global_data.g_all_client_data.inc_and_check_offline_count(index) == True:
                    print(client.ip + ":" + str(client.port) + \
                          " doesn't response for a long time, change to offline!")
                    global_data.g_all_client_data.close_error_client(index, is_lock = False)
                # else save the sockets which will be sent heart beat package soon
                else:
                    sock_list.append(client.sock)
            index += 1

        if len(global_data.g_running_task_list) != 0:
            min_auth = global_data.g_running_task_list[0]
            for auth in global_data.g_running_task_list[1:]:
                if task.compare_auth(list(min_auth[0]), list(min_auth[1]), \
                        list(auth[0]), list(auth[1])) == 1:
                    min_auth = auth
            first_undown_auth = min_auth[0] + ":" + min_auth[1]

        global_data.g_all_client_data.unlock()

        # unlock first, then send heart beat package to clients
        for client_sock in sock_list:
            try:
                client_sock.sendall(msg_header.unpack())
            except:
                continue
        # write first undown task to task file
        if first_undown_auth != "":
            global_data.g_task_file.seek(0, 0)
            global_data.g_task_file.truncate()
            global_data.g_task_file.write(first_undown_auth)

def work_thread_entrance(sock, ip, port):
    """
    one connect to client one thread

    sock(int): socket fd of client
    ip(string): client ip
    port(int): client port
    """
    index = global_data.g_all_client_data.get_new_client_data(sock, ip, port)
    if index == -1:
        print(ip + ":" + str(port) + " is trying to connect but exceed max_client_count, close it.")
        send_stop_cmd(sock, "Error, exceed server's max_client_count!")
        global_data.g_all_client_data.close_error_client(index)
        thread.exit_thread()

    while True:
        try:
            str_head = sock.recv(g_head_size)
            # connection is closed by peer
            if str_head == "":
                print("Connection is closed by " + global_data.g_all_client_data.get_ip_port(index))
                global_data.g_all_client_data.close_error_client(index)
                break   # exit this thread

            body = ""
            msg_header = MsgHeader()
            msg_header.pack(str_head)
            
            if int(msg_header.body_length) != 0:
                body = sock.recv(int(msg_header.body_length))

            is_send, send_msg, is_close = deal_task(index, msg_header.cmd, body)

            if is_send == True:
                sock.sendall(send_msg)
            if is_close == True:
                sock.close()
                thread.exit_thread()
        except socket.error:
            print("Connection with " + global_data.g_all_client_data.get_ip_port(index) + " error, socket will be closed.")
            global_data.g_all_client_data.close_error_client(index)
            thread.exit_thread()
        except SystemExit:
            break   # exit this thread
        except:
            pass


def deal_task(index, cmd, body):
    """
    Deal message sent by client.

    return (is_send, send_msg, is_close)
    """
    is_send = False
    send_msg = ""
    is_close = False

    if cmd == global_data.TASK_CMD_GETTASK:
        is_send, send_msg, is_close = deal_cmd_get_task(index, body)
    elif cmd == global_data.TASK_CMD_FINISHTASK:
        is_send, send_msg, is_close = deal_cmd_finish_task(index, body)
    elif cmd == global_data.TASK_CMD_RESPONSE:
        is_send, send_msg, is_close = deal_cmd_response(index, body)
    else:
        # wrong cmd, ignore
        pass
        
    return (is_send, send_msg, is_close)

def send_stop_cmd(sock, msg_body):
    """
    Server send stop cmd to client.
    """
    head = MsgHeader()
    head.cmd = global_data.TASK_CMD_STOPCLIENT
    head.body_length = "%04d" % len(msg_body)

def deal_cmd_get_task(index, body):
    """
    Client want to get one task from server.

    return (is_send, send_msg, is_close)
    """
    msg_header = MsgHeader()
    global_data.g_all_client_data.lock()
    status = global_data.g_all_client_data.client_infos[index].client_status

    if status != global_data.CLIENT_STATUS_INIT and status != global_data.CLIENT_STATUS_DOWN:
        # status error, ignore this message
        global_data.g_all_client_data.unlock()
        return (False, "", False)
    
    global_data.g_all_client_data.unlock()
    
    # Task is over, fail to get one task
    if global_data.g_all_client_data.assign_one_task(index, global_data.g_main_data) == False:
        msg_header.cmd = global_data.TASK_CMD_STOPCLIENT
        body = "All task is over!"
        msg_header.body_length = "%04d" % len(body)
        send_msg = msg_header.unpack() + body
        is_send = True
        is_close = True

        # change status to CLIENT_STATUS_OFFLINE
        global_data.g_all_client_data.lock()
        global_data.g_all_client_data.client_infos[index].client_status = global_data.CLIENT_STATUS_OFFLINE
        global_data.g_all_client_data.unlock()
        return (is_send, send_msg, is_close)
    # success
    else:
        msg_header.cmd = global_data.TASK_CMD_RESPONSE
        body = global_data.TASK_CMD_GETTASK + global_data.g_all_client_data.get_task_string(index)
        msg_header.body_length = "%04d" % len(body)
        is_send = True
        send_msg = msg_header.unpack() + body
        is_close = False
        
        str_auth = global_data.g_all_client_data.get_task_string(index)
        auth_list = str_auth.split(":")
        print(global_data.g_all_client_data.get_ip_port(index) + " get one task...")
        print("---- from " + auth_list[0] + ":" + auth_list[1])
        print("---- to   " + auth_list[2] + ":" + auth_list[3])

        # change status to CLIENT_STATUS_RUN
        global_data.g_all_client_data.lock()
        global_data.g_all_client_data.client_infos[index].client_status = global_data.CLIENT_STATUS_RUN
        global_data.g_all_client_data.unlock()
        return (is_send, send_msg, is_close)


def deal_cmd_finish_task(index, body):
    """
    Get a TASK_CMD_FINISHTASK message from client.
    """
    print(global_data.g_all_client_data.get_ip_port(index) + " finish one task...")
    is_send = False
    send_msg = ""
    is_close = False
    # no auth found by client
    if len(body) == 0:
        # just ignore
        print("Nothing find.")
    else:
        result_auth_list = body.split("~")
        for auth in result_auth_list:
            print("Find! " + auth)
            # write auth found by client to result file
            global_data.g_result_file.write(auth + "\n")

    # change status to CLIENT_STATUS_DOWN
    global_data.g_all_client_data.lock()
    auth = global_data.g_all_client_data.get_task_string(index).split(":")
    global_data.g_running_task_list.remove((auth[0], auth[1], auth[2], auth[3]))
    global_data.g_all_client_data.client_infos[index].client_status = global_data.CLIENT_STATUS_DOWN
    global_data.g_all_client_data.unlock()

    return (is_send, send_msg, is_close)

def deal_cmd_response(index, body):
    """
    Get a TASK_CMD_RESPONSE message from client.
    The body's first 2 bytes is defined to what command.
    """
    
    response_to_what = body[0:2]
    if response_to_what == global_data.TASK_CMD_HEARTBEAT:
        # get a heart beat response from client, change this client's offline_count to zero
        global_data.g_all_client_data.clear_offline_count(index)
    else:
        # ignore
        pass

    return (False, "", False)
