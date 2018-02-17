import math

def bytes_to_str(data):
    return " ".join("{:02x}".format(ord(c)) for c in data)

def buff_to_str(buff):
    return " ".join("{:02x}".format(b) for b in buff)

def ceildiv(a, b):
    return int(-(-a // b))

def dist(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
