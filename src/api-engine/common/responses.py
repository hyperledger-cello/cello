def ok(data):
    return {"data": data, "msg": None, "status": "successful"}


def err(msg):
    return {"data": None, "msg": msg, "status": "fail"}
