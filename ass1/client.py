import socket
import time
from random import *


'''addr, port = args[0], args[1]
filename = args[2]
MWS_bit = int(args[3])
MSS = int(args[4])
MWS = MWS_bit // MSS
timeout= int(args[5])
pdrop = float(args[6])
seeds = int(args[7])'''


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

def Chomp(data):  # make data easier to operate
    message = data.decode("UTF-8")
    result = Segment(SYN=int(message[0]), ACK=int(message[1]), FIN=int(message[2]),
                     seq=int(message[3:9]), acknowledgment=int(message[9:15]), data=message[15:])
    return result

file = open("test1.txt")
log = open("Sender_log.txt", "w")
MSS = 50
MWS = 500
default_window = int(MWS/MSS)
seeds = 300
timeout = 0.2
seed(seeds)
address = ('127.0.0.1', 3333)
pdrop = 0.3

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(timeout)


def handshake():
    client_seq = 100  # set a sequence number for sender
    handshake1 = Segment(SYN=1, seq=client_seq)
    s.sendto(handshake1.segment, address)
    log.writelines("snd  %2.3f S %5d %3d %5d\n" % (time.time() % 100, client_seq, len(handshake1.data), 0))
    data, ADDR = s.recvfrom(1024)
    msg = Chomp(data)
    log.writelines("rcv  %2.3f SA%5d %3d %5d\n"
                   % (time.time() % 100, msg.seq, len(msg.data), msg.acknowledgment))
    if msg.SYN == 1 and msg.ACK == 1:
        client_seq += 1
        server_seq = msg.seq
        handshake3 = Segment(ACK=1, seq=client_seq, acknowledgment=server_seq+1)
        s.sendto(handshake3.segment, ADDR)
        log.writelines("snd  %2.3f A %5d %3d %5d\n"
                       % (time.time() % 100, handshake3.seq, len(handshake3.data), handshake3.acknowledgment))
        print("Connecting success!")
        return handshake3.seq, handshake3.acknowledgment
    else:
        s.close()
        print("Connecting fail.")

def close(SEQ, ACK):
    close_1 = Segment(FIN=1, seq=SEQ, acknowledgment=ACK)
    s.sendto(close_1.segment, address)
    log.writelines("snd  %2.3f F %5d %3d %5d\n" % (time.time() % 100, close_1.seq, len(close_1.data), close_1.acknowledgment))
    data_close, ADDR_close = s.recvfrom(1024)
    msg = Chomp(data_close)
    log.writelines("rcv  %2.3f FA%5d %3d %5d\n" % (time.time() % 100, msg.seq, len(msg.data), msg.acknowledgment))
    if msg.FIN == 1 and msg.ACK == 1:
        close_3 = Segment(ACK=1, seq=msg.acknowledgment, acknowledgment=msg.seq+1)
        s.sendto(close_3.segment, address)
        log.writelines("snd  %2.3f A %5d %3d %5d\n"
                       % (time.time() % 100, close_3.seq, len(close_3.data), close_3.acknowledgment))
        s.close()
        print("Connection closed.")
    else:
        print("Fail to close connection")

def PLD(package):
    global pack_num
    global pack_drop
    global amount
    global segment_sent
    global segment_drop
    drop_probability = random() + pdrop
    if drop_probability < 1:
        s.sendto(package.segment, address)
        pack_num += 1
        segment_sent += 1
        log.writelines("snd  %2.3f D %5d %3d %5d\n" %
                       (time.time() % 100, package.seq, len(package.data), package.acknowledgment))
    else:
        pack_drop += 1
        segment_drop += 1
        log.writelines("drop %2.3f D %5d %3d %5d\n" %
                       (time.time() % 100, package.seq, len(package.data), package.acknowledgment))
    amount += len(package.data.encode("utf-8"))

def window():
    global data_to_send
    global seq_0
    global ack_0
    global data1
    while len(data_to_send) < default_window and data1:
        data_to_send.append(Segment(seq=seq_0, acknowledgment=ack_0, data=data1))
        seq_0 += len(data1)
        data1 = file.read(MSS)

def receive():
    global last_ack
    global data_to_send
    global count
    global duplicated
    try:
        data, ADDR = s.recvfrom(1024)
        msg = Chomp(data)
        log.writelines("rcv  %2.3f A %5d %3d %5d\n" %
                       (time.time() % 100, msg.seq, len(msg.data), msg.acknowledgment))
        if msg.acknowledgment == last_ack:
            count += 1
            duplicated += 1
            if count >= 3:
                count = 0
                for j in range(0, len(data_to_send)):
                    if data_to_send[j].seq == last_ack:
                        data_to_send = data_to_send[j:]
                        window()
                return "Fast"
        else:
            count = 0
            T = 0
            last_ack = msg.acknowledgment
            return "OK"
    except socket.timeout:
        for j in range(0, len(data_to_send)):
            if data_to_send[j].seq == last_ack:
                data_to_send = data_to_send[j:]
                window()
        return "Timeout"



seq_0, ack_0 = handshake()
pack_num = 0
pack_drop = 0
data1 = file.read(MSS)
data_to_send = []
window()
last_ack = ack_0
count, amount, segment_sent, segment_drop, duplicated = 0, 0, 0, 0, 0
retransmitted = 0

while data_to_send:
    num = 0
    for unsent in data_to_send:
        PLD(unsent)
    for i in range(0, len(data_to_send)):
        inf = receive()
        if inf == "OK":
            data_to_send.pop(0)
        elif inf == "Fast":
            while True:
                try:
                    A, B = s.recvfrom(1024)
                except socket.timeout:
                    break
            retransmitted += len(data_to_send)
            break
        elif inf == "Timeout":
            retransmitted += len(data_to_send)
            break
    if not data_to_send:
        window()
    else:
        continue




close(seq_0, ack_0)

log.writelines("Amount of Data Transferred:{}\n".format(amount))
log.writelines("Number of Data Segments Sent:{}\n".format(segment_sent))
log.writelines("Number of Packets Dropped:{}\n".format(segment_drop))
log.writelines("Number of Retransmitted Segments:{}\n".format(retransmitted))
log.writelines("Number of Duplicate Acknowledgements received:{}\n".format(duplicated))


'''T += 1
if len(data_to_send) <= 2:
    window()
    return "Timeout"
elif count:
    window()
    return "Timeout"
elif T > 3:
    window()
    return "Timeout"
else:
    data_to_send = data_to_send[len(data_to_send) - 3:]
    window()
    return "Timeout"'''