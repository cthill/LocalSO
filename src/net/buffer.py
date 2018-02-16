import struct
from rc4 import RC4

# this key is baked into the clinet and used for login onlyS
ENC_KEY = [ord(x) for x in "J+Akg5C7'8741649"]
def enc_dec_buffer(buff, key=ENC_KEY):
    keystream = RC4(key)
    for i in range(len(buff)):
        buff[i] ^= keystream.next()

def read_byte(buff, start):
    return struct.unpack('B', buff[start:start+1])[0]

def read_short(buff, start):
    return struct.unpack('h', buff[start:start+2])[0]

def read_ushort(buff, start):
    return struct.unpack('H', buff[start:start+2])[0]

def read_int(buff, start):
    return struct.unpack('i', buff[start:start+4])[0]

def read_uint(buff, start):
    return struct.unpack('I', buff[start:start+4])[0]

def read_float(buff, start):
    return struct.unpack('f', buff[start:start+4])[0]

def read_double(buff, start):
    return struct.unpack('d', buff[start:start+8])[0]

def read_string(buff, start):
    num_read = 0
    output = ''
    while True:
        if buff[start + num_read] == 0x00:
            break
        output += chr(buff[start + num_read])
        num_read += 1

    return output

def write_byte(buff, val):
    buff += struct.pack('B', val)

def write_short(buff, val):
    buff += struct.pack('h', val)

def write_ushort(buff, val):
    buff += struct.pack('H', val)

def write_int(buff, val):
    buff += struct.pack('i', val)

def write_uint(buff, val):
    buff += struct.pack('I', val)

def write_float(buff, val):
    buff += struct.pack('f', val)

def write_double(buff, val):
    buff += struct.pack('d', val)

def write_string(buff, string):
    for c in string:
        buff.append(ord(c))
    buff.append(0x00)
