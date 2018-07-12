import socket
import time
from random import *
from select import *
import sys

class Segment:  # Header and data
    def __init__(self, SYN=0, ACK=0, FIN=0, seq=0, acknowledgment=0, data=""):
        self.SYN, self.ACK, self.FIN = SYN, ACK, FIN
        self.acknowledgment = acknowledgment  # acknowledgment number
        self.seq = seq  # sequence number
        self.data = data
        self.seg = str(self.SYN) + str(self.ACK) + str(self.FIN) \
                       + "{0:06d}".format(self.seq) \
                       + "{0:06d}".format(self.acknowledgment) + data
        self.segment = self.seg.encode("UTF-8")  # segment in bit

def Chomp(data):
    message = data.decode("UTF-8")
    result = Segment(SYN=int(message[0]), ACK=int(message[1]), FIN=int(message[2]),
                     seq=int(message[3:9]), acknowledgment=int(message[9:15]), data=message[15:])
    return result

log = open("Receiver_log.txt", "w")
write_file = open("S.txt", "w")
seeds = 50
addr, port = '127.0.0.1', 3333
timeout = 1
seed(seeds)
address = (addr, int(port))

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(address)
print("Server started, waiting for connect.")

def handshake():
    server_seq = 200
    data, address = s.recvfrom(1024)
    msg = Chomp(data)
    log.writelines("rcv  %2.3f S %5d %3d %5d\n" % (time.time() % 100, msg.seq, len(msg.data), msg.acknowledgment))
    if msg.SYN == 1 and msg.ACK == 0:
        ack_num = msg.seq + 1
        handshake2 = Segment(SYN=1, ACK=1, seq=server_seq, acknowledgment=ack_num)
        s.sendto(handshake2.segment, address)
        log.writelines("snd  %2.3f SA%5d %3d %5d\n" % (time.time() % 100, server_seq, len(msg.data), ack_num))
    data, address = s.recvfrom(1024)
    msg = Chomp(data)
    if msg.SYN == 0 and msg.ACK == 1:
        log.writelines("rcv  %2.3f A %5d %3d %5d\n" % (time.time() % 100, msg.seq, len(msg.data), msg.acknowledgment))
        client_seq = msg.seq
        ack_num = msg.acknowledgment
        print("Connecting success!")
        return client_seq, ack_num
    else:
        s.close()
        print("Connecting fail.")

client_seq, ack_num = handshake()
amount = 0
duplicate_seq = 0
segment_received = 0


inputs = [s]
while True:
    state, outputs, message_queues = select(inputs, [], [], 0)
    if state:
        data, address = s.recvfrom(1024)
        msg = Chomp(data)
        if msg.FIN == 1:
            log.writelines(
                "rcv  %2.3f F %5d %3d %5d\n" % (time.time() % 100, msg.seq, len(msg.data), msg.acknowledgment))
            close_2 = Segment(FIN=1, ACK=1, seq=msg.acknowledgment, acknowledgment=msg.seq+1)
            s.sendto(close_2.segment, address)
            log.writelines("snd  %2.3f FA%5d %3d %5d\n" % (time.time() % 100, close_2.seq, len(close_2.data), close_2.acknowledgment))
            data, address = s.recvfrom(1024)
            msg = Chomp(data)
            log.writelines("rcv  %2.3f A %5d %3d %5d\n" % (time.time() % 100, msg.seq, len(msg.data), msg.acknowledgment))
            if msg.ACK == 1:
                s.close()
                print("Connection closed.")
                break
        log.writelines(
            "rcv  %2.3f D %5d %3d %5d\n" % (time.time() % 100, msg.seq, len(msg.data), msg.acknowledgment))
        if client_seq == msg.seq:
            client_seq += len(msg.data)
            amount += len(msg.data.encode("UTF-8"))
            write_file.write(msg.data)
        else:
            duplicate_seq += 1
        segment_received += 1
        Back = Segment(seq=msg.acknowledgment, acknowledgment=client_seq)
        s.sendto(Back.segment, address)
        log.writelines(
           "snd  %2.3f A %5d %3d %5d\n" % (time.time() % 100, Back.seq, len(Back.data), Back.acknowledgment))

log.writelines("Amount of Data Received:{}\n".format(amount))
log.writelines("Number of Data Segments Received:{}\n".format(segment_received))
log.writelines("Number of duplicate segments received:{}\n".format(duplicate_seq))