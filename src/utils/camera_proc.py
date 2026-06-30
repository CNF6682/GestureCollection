
import cv2
import time
import numpy as np
import multiprocessing
import threading
from PyQt5.QtCore import QThread, pyqtSignal,QMutex
import concurrent.futures as futures
import os

import utils.mvsdk as mvsdk

def setROI(hCamera,iWidth,iHeight,iHOffsetFOV,iVOffsetFOV):
    sRoiReslution = mvsdk.tSdkImageResolution()  # 实例化变量
    sRoiReslution.iIndex = 0xff  # 赋值
    sRoiReslution.iWidth = iWidth
    sRoiReslution.iWidthFOV = iWidth
    sRoiReslution.iHeight = iHeight
    sRoiReslution.iHeightFOV = iHeight
    sRoiReslution.iHOffsetFOV = iHOffsetFOV
    sRoiReslution.iVOffsetFOV = iVOffsetFOV
    mvsdk.CameraSetImageResolution(hCamera, sRoiReslution)

class camera_task:
    def __init__(self,DevInfo,NS,record_save,frameRates,ROI,save_status):
        self.DevInfo = DevInfo
        self.NS = NS
        self.record_save = record_save
        self.frameRates = frameRates
        self.ROI = ROI
        self.save_status = save_status
        # L1缓存: raw numpy frames
        self.imgs_buffer = []
        # L2缓存: encoded JPEG bytes
        self.l2_cache = []
        self.l2_path = ""
        self.l2_ready = threading.Event()
        self.l2_ready.set()  # 初始状态: L2空闲
        self.executor = futures.ThreadPoolExecutor(max_workers=1)

        # 打开相机
        self.hCamera = 0
        try:
            self.hCamera = mvsdk.CameraInit(DevInfo, -1, -1)
        except mvsdk.CameraException as e:
            print("CameraInit Failed({}): {}".format(e.error_code, e.message) )
            return
        
        # 获取相机特性描述
        cap = mvsdk.CameraGetCapability(self.hCamera)
        # 判断是黑白相机还是彩色相机
        monoCamera = (cap.sIspCapacity.bMonoSensor != 0)
        # 黑白相机让ISP直接输出MONO数据，而不是扩展成R=G=B的24位灰度
        if monoCamera:
            mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
        else:
            mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)

        # 相机模式切换成连续采集
        mvsdk.CameraSetTriggerMode(self.hCamera, 2)#2是外部触发
        # 手动曝光，曝光时间30ms
        mvsdk.CameraSetAeState(self.hCamera, 0)#0是手动曝光


        if self.DevInfo.GetSn() == "044011420148":  # 041182220233  044062320120
            # setROI(self.hCamera, 800, 800, 560, 112)
            mvsdk.CameraSetExposureTime(self.hCamera, 6 * 1000)  # 10是曝光时间（ms）
        else:
            mvsdk.CameraSetExposureTime(self.hCamera, 10 * 1000)
        # if self.DevInfo.GetSn() == "044030620196":  # 044062320105   042092320674
        #     setROI(self.hCamera, 800, 800, 240, 112)
        # elif self.DevInfo.GetSn() == "044062320120":
        #     setROI(self.hCamera, 800, 800, 240, 112)
        # else:
        #     setROI(self.hCamera, 800, 800, 240, 112)



        # if self.DevInfo.GetSn()=="044011420148":
        #     mvsdk.CameraSetGain(self.hCamera, iRGain=109, iGGain=100, iBGain=114)
        # else:
        #     mvsdk.CameraSetGain(self.hCamera, iRGain=140, iGGain=114, iBGain=100)
        # 让SDK内部取图线程开始工作
        mvsdk.CameraPlay(self.hCamera)
        # 计算RGB buffer所需的大小，这里直接按照相机的最大分辨率来分配
        FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)
        # 分配RGB buffer，用来存放ISP输出的图像
        # 备注：从相机传输到PC端的是RAW数据，在PC端通过软件ISP转为RGB数据（如果是黑白相机就不需要转换格式，但是ISP还有其它处理，所以也需要分配这个buffer）
        self.pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)
        self.setCrop()



    def _get_camera_name(self):
        sn_map = {
            "044011420148": "RGB_1",
            "044030620196": "RGB_2",
            "044062320120": "RGB_3",
            "044062320129": "RGB_4",
            "044030620195": "RGB_5",
            "043051920299": "inf",
            "044062320137": "RGB_6",
            "044062320105": "RGB_7",
            "042101120056": "RGB_8",
        }
        return sn_map.get(self.DevInfo.GetSn(), "unknown")

    def encode_to_l2(self):
        """L1 raw numpy → L2 JPEG bytes (CPU密集, 同步执行)"""
        self.l2_cache = []
        for img in self.template:
            ret, buf = cv2.imencode('.jpg', img)
            if ret:
                self.l2_cache.append(buf)
        self.template = []
        self.imgs_buffer = []
        # 提交后台落盘
        self.l2_ready.clear()
        self.executor.submit(self.flush_l2_to_disk)
        # 立即回报"采集完成"（数据已安全进入L2）
        print('{}采集完成，数据已进入L2缓存'.format(self._get_camera_name()))
        self.save_status[self.DevInfo.GetSn()] = True

    def flush_l2_to_disk(self):
        """L2 JPEG bytes → SATA HDD (I/O密集, 后台线程)"""
        try:
            camera = self._get_camera_name()
            path = self.l2_path
            sample_camera_path = os.path.join(path, camera)
            if not os.path.exists(sample_camera_path):
                os.mkdir(sample_camera_path)
            for index, buf in enumerate(self.l2_cache):
                if index >= 240:
                    break
                img_path = os.path.join(sample_camera_path, '%03d.jpg' % (index + 1))
                with open(img_path, 'wb') as f:
                    f.write(buf.tobytes())
            self.l2_cache = []
            print('{}落盘完成'.format(camera))
        finally:
            self.l2_ready.set()

    def setCrop(self):
        if self.DevInfo.GetSn()=="044011420148":   #041182220233  044062320120
            setROI(self.hCamera, 1024, 1024, 300, 112)
        elif self.DevInfo.GetSn()=="044030620196":  #044062320105   042092320674
            setROI(self.hCamera, 800, 800, 320, 112)
        elif self.DevInfo.GetSn()=="044062320120":
            setROI(self.hCamera, 800, 800, 100, 112)
        elif self.DevInfo.GetSn()=="044062320129":
            setROI(self.hCamera, 800, 800, 140, 100)
        elif self.DevInfo.GetSn()=="044030620195":
            setROI(self.hCamera, 800, 800, 240, 112)
        elif self.DevInfo.GetSn()=="043051920299":
            setROI(self.hCamera, 1024, 1024, 560, 140)
        elif self.DevInfo.GetSn()=="044062320137":
            setROI(self.hCamera, 800, 800, 100, 112)
        elif self.DevInfo.GetSn()=="044062320105":
            setROI(self.hCamera, 800, 800, 380, 200)
        elif self.DevInfo.GetSn()=="042101120056": #inf
            setROI(self.hCamera, 1024, 1024, 0, 0)


    def run(self,pipe,stop_event):
        num_frames = 0
        start_time = time.time()
        while not stop_event.is_set():
            try:

                pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 200)
                mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer, FrameHead)
                mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)
                # 计算帧率
                num_frames += 1
                elapsed_time = time.time() - start_time
                if elapsed_time > 0:
                    fps = num_frames / elapsed_time
                else:
                    fps = 0
                if num_frames>300:
                    num_frames=0
                    start_time=time.time()
                # print("fps:",fps)
                # print(self.NS)
                # print(self.record_save)
                # 此时图片已经存储在pFrameBuffer中，对于彩色相机pFrameBuffer=RGB数据，黑白相机pFrameBuffer=8位灰度数据
                # 把pFrameBuffer转换成opencv的图像格式以进行后续算法处理
                frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(self.pFrameBuffer)
                frame = np.frombuffer(frame_data, dtype=np.uint8)
                frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 1 if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3) )

                if self.DevInfo.GetSn() == "044011420148":
                    frame=cv2.flip(frame,0)

                elif self.DevInfo.GetSn() == "044030620196":  # 044062320105   042092320674
                    frame=cv2.flip(frame,1)
                    # pass
                elif self.DevInfo.GetSn() == "044062320120":
                    frame=cv2.flip(frame,0)
                    # pass
                elif self.DevInfo.GetSn() == "044062320129":
                    # pass
                    frame=cv2.rotate(frame,cv2.ROTATE_90_COUNTERCLOCKWISE)
                    frame=cv2.flip(frame,1)
                elif self.DevInfo.GetSn() == "044030620195":
                    frame=cv2.rotate(frame,cv2.ROTATE_90_CLOCKWISE)
                    frame=cv2.flip(frame,1)
                    # pas
                elif self.DevInfo.GetSn() == "044062320137":
                    frame=cv2.rotate(frame,cv2.ROTATE_90_CLOCKWISE)
                    frame=cv2.flip(frame,1)
                elif self.DevInfo.GetSn() == "044062320105":
                    frame=cv2.rotate(frame,cv2.ROTATE_90_COUNTERCLOCKWISE)
                    frame=cv2.flip(frame,1)
                    # pass
                elif self.DevInfo.GetSn() == "044030620196":
                    pass
                elif self.DevInfo.GetSn() == "043051920299":
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                    frame=cv2.flip(frame,1)
                elif self.DevInfo.GetSn() == "042101120056":
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                    frame=cv2.flip(frame,1)
                    # pass
                # frame = cv2.resize(frame, (640,480), interpolation = cv2.INTER_LINEAR)
                if num_frames % 10 == 0:
                    frame_show = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_show = cv2.resize(frame_show, (100,100))
                    pipe.send(frame_show)
                    self.frameRates[self.DevInfo.GetSn()] = fps

                if self.record_save.is_set():#self.record_save[self.DevInfo.GetSn()]==1:
                    self.imgs_buffer.append(frame)
                    # 记录采集进度
                    if self.DevInfo.GetSn() == "044011420148":
                        self.NS.sampled = len(self.imgs_buffer)/self.NS.sample_frame
                    if len(self.imgs_buffer) == 1:
                        start_time2 = time.time()
                    # print(len(self.imgs_buffer))
                    if len(self.imgs_buffer) == self.NS.sample_frame:
                        self.template=self.imgs_buffer[:self.NS.sample_frame]
                        self.l2_path = self.NS.save_id_path
                        self.record_save.clear()  # self.record_save[self.DevInfo.GetSn()]==0
                        end_time2 = time.time()
                        # 等待上一次L2落盘完成（防止覆盖）
                        self.l2_ready.wait()
                        # 同步编码到L2，然后异步落盘
                        self.encode_to_l2()



            except mvsdk.CameraException as e:
                if e.error_code != mvsdk.CAMERA_STATUS_TIME_OUT:
                    print("CameraGetImageBuffer failed({}): {}".format(e.error_code, e.message))


        mvsdk.CameraStopRecord(self.hCamera)
        # 关闭相机
        mvsdk.CameraUnInit(self.hCamera)
        # 释放帧缓存
        mvsdk.CameraAlignFree(self.pFrameBuffer)
        print("Camera stopped")
        
# def run_camera(index,pipe,stop_event):
#     camera = camera_task(index)
#     camera.run(pipe,stop_event)
# import setproctitle
# setproctitle.setproctitle(f"MindVision")
# import ctypes
def run_camera(devinfo,pipe,stop_event,NS,record_save,frameRates,ROI,save_status):
    # ctypes.windll.kernel32.SetConsoleTitleW(f"MindVision_{devinfo.GetSn()}")

    camera = camera_task(devinfo,NS,record_save,frameRates,ROI,save_status)
    camera.run(pipe,stop_event)
    
    
if __name__ == "__main__":
    p1 = multiprocessing.Process(target=run_camera, args=(0,))
    p2 = multiprocessing.Process(target=run_camera, args=(1,))
    
    # p1 = threading.Thread(target=run_camera, args=(0,))
    # p2 = threading.Thread(target=run_camera, args=(1,))    

    p1.start()
    p2.start()
    
    p1.join()
    p2.join()