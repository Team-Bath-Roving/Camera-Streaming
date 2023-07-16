import socket
import time

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

class StreamServer:
    cam_list=None
    def __init__(self,model):
        # List available devices
        self.usb=False
        self.cam=None
        if StreamServer.cam_list is None: # first instantiation gets list of cameras
            StreamServer.scan()
        for idx,camera in enumerate(StreamServer.cam_list):
            # Find camera with corresponding model name
            print(camera["Model"])
            if model in camera["Model"]:
                if not "Active" in camera: # skip this one if it's already been claimed
                    # Determine if CSI or USB (YUV or YUYV/MJPEG)
                    if "usb" in camera["Id"]:
                        usb=True
                    # Initialise camera
                    self.cam=Picamera2(idx)
                    camera["Active"]=True # add key to show this has been claimed (allows multiple cams with same model)
        if self.cam is None:
            raise Exception(f"Failed to find camera with model name {model}")
    def scan():
        StreamServer.cam_list=Picamera2.global_camera_info()
    def configure(self,width,height,format=None):
        config={"size":(width,height)}
        if not format is None:
            config["format"]=format
        self.cam.configure(self.cam.create_video_configuration(config))
    def start(self,ip,port,multicast=True):
        if not self.usb:
            self.encoder=H264Encoder(100000,repeat=True,iperiod=5)
        if multicast:
            self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
        else:
            self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.sock.connect((ip, port))
        self.stream = self.sock.makefile("wb")
        self.cam.start_recording(self.encoder, FileOutput(self.stream))
    def stop(self):
        self.cam.stop_recording()
        self.sock.close()
    def set_bitrate(self,bitrate):
        self.encoder.bitrate=bitrate
        self.encoder.stop()
        self.encoder.start()
    def set_controls(self,controls_dict):
        self.cam.set_controls(controls_dict)
    def set_exposure(self,exposure):
        self.set_controls({"ExposureTime": exposure})
