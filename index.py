import os
import random
import sys
import time
import cv2
import threading
import hashlib
import struct
import socket
from picamera2 import Picamera2
import numpy as np

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
            self.picam2 = Picamera2()
            self.picam2.configure(self.picam2.create_preview_configuration(main={"format": 'RGB888', "size": (128,128)}))
            self.picam2.start()

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
        
        print("Change frequency", port)
        
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
            data, address = self.sock.recvfrom(50000)
            return data
        except socket.error as ex:
            # print("Receive error: ", type(ex), ex)
            return None
        
    def handle_message(self, message: bytes):
        if message[0] == 99:
            print("Sync time")
            self.sync_time()
        else:
            if not self.is_sender:
                colors = list(message)
                # print("Received pixels", len(colors))

                # color = np.random.randint(0, 256, size=(64*64*3), dtype=np.uint8)
                img_rgb = np.array(colors, dtype=np.uint8).reshape((128, 128, 3))

                # print(colors)

                # Convert RGB to BGR for OpenCV
                img_rgb = cv2.resize(img_rgb, (1000, 1000), interpolation=cv2.INTER_NEAREST)

                # img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
                img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)


                img_rgb = cv2.rotate(img_rgb, cv2.ROTATE_90_CLOCKWISE)

                # img_rgb = np.array(colors).reshape((64, 64, 3))
                cv2.imshow("Picamera2 Frame", img_rgb)
                cv2.waitKey(1) 
                
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
            if i % 50 == 2 and self.sock is not None and self.is_sender:
                frame = self.picam2.capture_array()
                print("Frame", frame.shape)
                frame = frame.flatten()
                buffer = bytes(frame)

                # buffer = ("message" + str(random.randint(100, 999))).encode()
                # buffer = bytes([0] * 1000)
                print("Send data", len(buffer))


                self.sock.sendto(buffer, (self.remote, self.current_port))

            


            # print("data", data)

            time.sleep(0.01)



inst = SkyHopperDevice(bytes([1,2,3]), is_sender=(sys.argv[1] == "sender"), remote="192.168.50.98")
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