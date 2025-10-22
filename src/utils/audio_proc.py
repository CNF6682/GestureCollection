
import cv2
import time
import numpy as np
import multiprocessing
import threading
from PyQt5.QtCore import QThread, pyqtSignal,QMutex
import concurrent.futures as futures
import os


import pygame
import time

# 初始化 pygame 模块
pygame.init()


class audio_task:
    def __init__(self,NS):

        self.NS = NS
    def play(self,flag):
        #


        # 播放音频
        if flag =="start":
            pygame.mixer.music.load("openhand.mp3")
        elif flag=="stop":
            pygame.mixer.music.load("stop.mp3")
        # elif flag=="saved":
        #     pygame.mixer.music.load("saved.mp3")

        pygame.mixer.music.play()
        # 等待音频播放完成
        while pygame.mixer.music.get_busy():
            time.sleep(0.2)

        # 播放音频
        if flag =="start":
            pygame.mixer.music.load("start.mp3")
        elif flag=="stop":
            pygame.mixer.music.load("rest.mp3")
            print("rest")
        elif flag=="saved":
            pygame.mixer.music.load("saved.mp3")

        pygame.mixer.music.play()
        # 等待音频播放完成
        while pygame.mixer.music.get_busy():
            time.sleep(0.2)
        print(1)





    def run(self):

        while True:
            try:
                if self.NS.audio_start==True:
                    self.NS.audio_start = False
                    self.play("start")

                elif self.NS.audio_stop==True:
                    self.NS.audio_stop = False
                    self.play("stop")

                # elif self.NS.audio_saved == True:
                #     self.NS.audio_saved = False
                #     self.play("saved")


            except Exception as e:
                # print(e)
                pass

    
def run_audio(NS):
    camera = audio_task(NS)
    camera.run()
    
    
if __name__ == "__main__":
    p1 = multiprocessing.Process(target=run_camera, args=(0,))
    p2 = multiprocessing.Process(target=run_camera, args=(1,))
    
    # p1 = threading.Thread(target=run_camera, args=(0,))
    # p2 = threading.Thread(target=run_camera, args=(1,))    

    p1.start()
    p2.start()
    
    p1.join()
    p2.join()