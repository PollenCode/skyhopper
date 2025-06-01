import os
import random
import sys
import time
import cv2
import threading
import crypt
import hashlib
import struct
import socket

# image = cv2.imread("image.jpg")

# cv2.imshow('image',image)
# cv2.waitKey(0)

# LOCALHOST = "127.0.0.1"
# PORTS = [3456, 7689, 10023, 33332]


class SkyHopperDevice:
    current_freq: int
    key: bytes
    channel_count: int
    interval: float

    time_offset: float | None = None

    current_port = 0

    

    # 2.4 WiFi
    # 2.4 Bluetooth
    # LoRa

    def __init__(self, key: bytes, is_sender: bool, remote: str):
        self.key = key
        self.channel_count = 1000
        self.current_freq = 0
        self.interval = 1
        self.sock = None
        self.is_sender = is_sender
        self.remote = remote
        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.update_current_port()

        if is_sender:
            self.stream = cv2.VideoCapture(0)

    def get_freq_idx(self):
        frame_idx = self.get_time() // self.interval
        hashed = hashlib.sha1(self.key + bytearray(struct.pack("f", frame_idx)))
        return hashed.digest()[0] % self.channel_count
    
    def sync_time(self):
        self.time_offset = time.time()

    def get_time(self):
        if self.time_offset is None:
            return 0
        return time.time() - self.time_offset

    # def _update_freq(self):
    #     freq_idx = self.get_freq_idx()
    #     self.current_freq = freq_idx
        # freq =  ["WiFi", "Bt", "LoRa"][freq_idx]

        # print(int(self.get_time()), ": Channel updated:", freq)

    # def receive_message(self) -> bytes:
    #     buf = bytes(64) # TODO: receive payload from the receiver/transmitter

    #     return buf

    def set_socket_port(self, port: int):
        if self.current_port == port:
            return
        
        print("Change port", port)
        
        if self.sock is not None:
            self.sock.close()
            self.sock = None

        # if not self.is_sender:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('',port))
        self.sock.setblocking(False)

        self.current_port = port

    def receive_data(self) -> bytes | None:
        try:
            data, address = self.sock.recvfrom(10000)
            return data
        except socket.error as ex:
            # print("Receive error: ", type(ex), ex)
            return None
        
    def handle_message(self, message: bytes):
        if message[0] == 99:
            print("Sync time")
            self.sync_time()
        else:
            print("Received unknown message", message)

    def simple_sync_remote(self):
        self.sock.sendto(bytes([99]), (self.remote, self.current_port))
        self.sync_time()

    def update_current_port(self):
        port = self.get_freq_idx() + 4000
        # print("Freq", port)
        self.set_socket_port(port)

    def loop(self):
        
        i = 0
        while True:
            self.update_current_port()
            
            # if not self.is_sender:
            data = self.receive_data()
            if data is not None:
                self.handle_message(data)

            i += 1
            if i % 20 == 2 and self.sock is not None and self.is_sender:
                message = "message" + str(random.randint(100, 999))
                ret, frame = self.stream.read()
                print("Frame", ret, frame)
                        

                print("Send", message)
                self.sock.sendto(message.encode(), (self.remote, self.current_port))

            # print("data", data)

            time.sleep(0.01)



inst = SkyHopperDevice(bytes([1,2,3]), is_sender=(sys.argv[1] == "sender"), remote="172.31.70.33")
# inst.sync_time()
if inst.is_sender:
    inst.simple_sync_remote()
inst.loop()


# while True:
#     # print("time", inst.get_time(), "-> freq", inst.get_freq_idx())
#     inst._update_freq()
#     time.sleep(1)






# if sys.argv[1] == "recv":
#     print("receiver starting")

#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     sock.bind(('',8888))
#     sock.setblocking(False)

#     while True:
#         try:
#             data, address = sock.recvfrom(10000)
#             print("received:", bytes(data).decode())
#         except socket.error as ex:
#             # print("Receive error: ", type(ex), ex)
#             pass
#         # else: 
#         #     print("recv:", data[0],"times",len(data))
#         time.sleep(1)
# else:
#     print("sending")

#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
#     while True:
#         sock.sendto("hallo".encode(), ("127.0.0.1", 8888))
#         time.sleep(1.5)