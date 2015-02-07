#!/bin/env python

import base64

def inc_str_num(str_list, max_len):
    """ 
    set str_list to next one, 9's next is A and Z's next is 0

    str_list(list): start_list, will increas one finally
    max_len(int): the max length of str_list
    return(bool): if len(str_list) > max_len, return True, else return False
    """

    isInc = False
    next_char = ""
    for i in range(len(str_list))[::-1]:
        isInc = False
        if str_list[i] == "9":
            next_char = "A"
        elif str_list[i] == "Z":
            next_char = "0"
            isInc = True
        else:
            # just add ascii
            next_char = chr(ord(str_list[i]) + 1)
        str_list[i] = next_char
        # normal char, just inc
        if isInc == False:
            break
        # if i is 0, add a new char in index 0
        if i == 0 and isInc == True:
            str_list.insert(0, "0")

    if len(str_list) > max_len:
        del(str_list[:])
        str_list += ["0"]
        return True
    else:
        return False


def get_next_auth(acct_list, pwd_list, max_len):
    """
    get the next account and password

    max_len(int): the max length of acct_list and pwd_list

    return(bool): if acct_list and pwd_list touch the end of all value, return True, else False
    """

    if inc_str_num(pwd_list, max_len) == True:
        return inc_str_num(acct_list, max_len)
    else:
        return False


def get_one_task(acct_list, pwd_list, last_index, max_len):
    """
    let the last_index character increase 1, the same as 46656 call for inc_str_num()

    last_index(int): the last index of pwd_list, inc this character
    max_len(int): the max length of acct_list and pwd_list

    notice: the value of acct_list and pwd_list may be changed, if len(pwd_list) < last_index(4), the value is "1000"
            if len(acct_list) touch the max_len, the value may like "ZZZZZZZ"
    """

    if len(pwd_list) < last_index:
        del(pwd_list[:])
        pwd_list += ["1"] + ["0"] * (last_index - 1)
        return
    
    # let pwd_list increase
    isInc = False
    next_char = ""
    for i in range(len(pwd_list) - (last_index - 1))[::-1]:
        isInc = False
        if pwd_list[i] == "9":
            next_char = "A"
        elif pwd_list[i] == "Z":
            next_char = "0"
            isInc = True
        else:
            # just add ascii 1
            next_char = chr(ord(pwd_list[i]) + 1)
        pwd_list[i] = next_char
        # normal char, just inc
        if isInc == False:
            break
        # if i is 0, add a new char in index 0
        if i == 0 and isInc == True:
            pwd_list.insert(0, "0")

    # if pwd_list exceed the max value
    if len(pwd_list) > max_len:
        del(pwd_list[:])
        pwd_list += ["0"]
        if inc_str_num(acct_list, max_len) == True:
            del(acct_list[:])
            del(pwd_list[:])
            acct_list += ["Z"] * max_len
            pwd_list += ["Z"] * max_len


def get_send_msg(msg, account, password):
    """
    pack send message

    msg(string): http header template
    account(list): account's string list
    password(list): password's string list

    return(string): the message to be sent
    """

    auth = base64.b64encode("".join(account) + ":" + "".join(password))
    return msg + auth + "\n\n"


def compare_str_num(left_str_list, right_str_list):
    """
    compare two string
    first compare the length of string list
    if length is equal, just compare the string

    return(int): 1 means greater, 0 means equal, -1 means less
    """

    if len(left_str_list) > len(right_str_list):
        return 1
    elif len(left_str_list) < len(right_str_list):
        return -1
    else:
        if "".join(left_str_list) == "".join(right_str_list):
            return 0
        elif "".join(left_str_list) > "".join(right_str_list):
            return 1
        else:
            return -1


def compare_auth(left_acct_list, left_pwd_list, right_acct_list, right_pwd_list):
    """
    compare by account and password list

    return(int): 1 means greater, 0 means equal, -1 means less
    """

    result = compare_str_num(left_acct_list, right_acct_list)
    if result != 0:
        return result
    return compare_str_num(left_pwd_list, right_pwd_list)

if __name__ == "__main__":
    a = list("123")
    b = list("123")
    print(compare_str_num(a, b))
