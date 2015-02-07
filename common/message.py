#!/bin/env python

g_head_size = 6     # all head string size

class MsgHeader:
    cmd = ""            # 2 bytes
    body_length = ""    # 4 bytes

    def pack(this, str_header):
        """
        from string to object
        """

        this.cmd = str_header[0:2]
        this.body_length = str_header[2:6]

    def unpack(this):
        """
        from object to string
        """

        return this.cmd + this.body_length
