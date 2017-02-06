import time
from multiprocessing import Queue
from Adafruit_Thermal import *


class DummyDevice(object):

    def printImage(self, image):
        time.sleep(1)  # pretends to print the image
        print "Image printed!"

    def printText(self, text):
        time.sleep(.5)  # pretends to print the text
        print text

    def feed(self):
        pass


class PrintOrder(object):
    def __init__(self, f, *args):
        self.f = f
        self.args = args

    def execute(self):

        if self.args.__len__() == 0:
            self.f()
        else:
            self.f(self.args)


# device = DummyDevice()
device = Adafruit_Thermal("/dev/ttyAMA0", 9600, timeout=5)
queue = Queue()


def print_image(data):
  device.printImage(data[0], True)
  device.feed(7)