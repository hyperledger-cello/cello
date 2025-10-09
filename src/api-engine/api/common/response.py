#
# SPDX-License-Identifier: Apache-2.0
#
"""Class represents response format.
        {
            status, successful/fail
            data,  response
            msg, error messages
        }

    """


def ok(data):
    return {"data": data, "msg": None, "status": "successful"}


def err(msg):
    return {"data": None, "msg": msg, "status": "fail"}
