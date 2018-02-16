import logging

from net.buffer import enc_dec_buffer

def tcp_write(conn, data, enc=False):
    data_enc = bytearray(data)
    if enc:
        enc_dec_buffer(data_enc)

    # prepend the length as a short
    data_len_short = [len(data_enc) & 0xff, (len(data_enc) & 0xff00) >> 8]
    payload = bytearray(data_len_short) + data_enc

    # convert to string and write
    payload_str = ''.join(chr(x) for x in payload)
    conn.send(payload_str)
    # logging.info("TCP wrote (enc=%s) %s" % (enc, buff_to_str(data)))

def tcp_write_multiple(conn, data, enc=False):
    for d in data:
        tcp_write(conn, d, enc)


def udp_write(sock, addr, data, enc=False):
    data_enc = bytearray(data)
    if enc:
        enc_dec_buffer(data_enc)

    # prepend the length as a short
    data_len_short = [len(data_enc) & 0xff, (len(data_enc) & 0xff00) >> 8]
    payload = bytearray(data_len_short) + data_enc

    # convert to string and write
    payload_str = ''.join(chr(x) for x in payload)
    sock.sendto(payload_str, addr)
    # logging.info("UDP wrote (enc=%s) %s" % (enc, buff_to_str(data)))
