
import random
import io
import os
import threading
import time
import logging
import sys
from datetime import datetime
from Queue import Queue, Empty
import grpc
from FeatureExtractionApi_pb2 import Image
import FeatureExtractionApi_pb2_grpc
import cv2
#from picamera import PiCamera
#from picamera.exc import PiCameraMMALError, PiCameraError
from configs import CONFIGS, CAMERA
from datetime import datetime

FPS = 5
SERVER_URL = '200.126.23.95:50052'
logger = logging.getLogger("Camera")
logger.setLevel(logging.DEBUG)
class VideoRecorder:

    def __init__(self, on_error):
        "docstring"
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            raise IOError("Error al reconocer la camara USB")
        # self.set_camera_params()
        # print self.camera.get(cv2.CAP_PROP_FRAME_WIDTH), self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
        # channel = grpc.insecure_channel('200.126.23.95:50052')
        # self.grpc_stub = FeatureExtractionApi_pb2_grpc.FeatureExtractionStub(channel)
        self.recording_stop = True
        self.image_queue = Queue()
        self.count = 0
        self.sent_count = 0
        self.grabbing = False
        self.on_error = on_error
        logger.debug("Camera started")

    def set_camera_params(self):
        self.camera.set(3,1296)
        self.camera.set(4,972)

    def capture_continuous(self, filename):
        logger.debug("capture continuous")
        self.count = 1
        self.grabbing = True
        while True:
            start = time.time()
            ret, frame = self.camera.read()
            #frame=cv2.flip(frame,0)
            bytesImg= cv2.imencode(".jpg",frame)[1].tostring()
            self.image_queue.put(Image(source=bytesImg,file_name=filename,timestamp=str(datetime.now())))
            if self.recording_stop:
                break
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            self.count += 1
            time.sleep(max(1./FPS - (time.time() - start), 0))
        self.grabbing = False

    def generate_videos_iterator(self):
        logger.debug("generate video iterator")
        self.sent_count = 0
        while not self.recording_stop or not self.image_queue.empty() or self.grabbing:
            try:
                yield self.image_queue.get(block=True, timeout=1)
                self.image_queue.task_done()
                #print "sent",self.sent_count, "of", self.count, "captured"
                self.sent_count += 1
            except Empty as ex:
                logger.error("No data in image queue")
        logger.debug("Done generating images")

    def start_recording(self, filename):
        logger.info("Start recording")
        try:
            channel = grpc.insecure_channel(SERVER_URL)
            if not self.ping(channel):
                raise
            self.grpc_stub = FeatureExtractionApi_pb2_grpc.FeatureExtractionStub(channel)
            threading.Thread(target=self.capture_continuous, args=(filename, )).start()
            videos_iterator = self.generate_videos_iterator()
            response = self.grpc_stub.processVideo(videos_iterator)
            logger.debug(response)
        except:
            logger.error("Murio grpc")
            self.on_error()

    def ping(self, channel=None):
        if channel is None:
            channel = grpc.insecure_channel(SERVER_URL)
        try:
            grpc.channel_ready_future(channel).result(timeout=1)
            logger.info("Ping")
            return True
        except grpc.FutureTimeoutError as e:
            logger.error("Couldnt connect to GRPC SERVER")
            return False


    def record(self):
        filename=CONFIGS["session"]
        self.recording_stop = False
        self.image_queue = Queue()
        threading.Thread(target=self.start_recording, args=(filename, )).start()

    def stop_record(self, callback=None):
        self.recording_stop = True
        time.sleep(5)
        self.image_queue.join()
        CONFIGS["session"] = '0'
        if callback:
            callback()

    def get_progress(self):
        try:
            return "{} %".format(int(self.sent_count * 100.0 / self.count))
        except:
            return "0 %"
        # return "{}/{}".format(self.sent_count, self.count)

    def clean(self):
        self.camera.release()
        logger.debug("Camera released")
        # self.camera.close()

    def convert_to_mp4(self):
        filename_mp4 = self.filename.split(".")[0]+".mp4"
        logger.info("file .h264 saved.. Transforming to mp4...")
        os.system("MP4Box -fps 30 -add "+ self.filename + " " + filename_mp4)
        logger.info("File converted to mp4")

if __name__ == "__main__":
    vid_recorder = VideoRecorder()
    print ("Set vid recorder")
    # vid_recorder.camera.wait_recording(5)
    time.sleep(2)
    start = datetime.now()
    print("Start" , start)
    print(start)
    vid_recorder.record()
    # vid_recorder.camera.wait_recording(2)
    # vid_recorder.camera.capture("foo.jpg", use_video_port=True)
    # print ("Pic taken")
    # vid_recorder.camera.wait_recording(30)
    time.sleep(30)
    vid_recorder.stop_record()

    vid_recorder.clean()
