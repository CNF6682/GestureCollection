# 华南理工大学
# 王熙来
# 开发时间：2024/4/17 16:03


import cv2
# import numpy as np
# import mvsdk
# import platform
import os
import csv
import pandas as pd
import datetime


# class Camera(object):
#     def __init__(self, DevInfo):
#         super(Camera, self).__init__()
#         self.DevInfo = DevInfo
#         self.hCamera = 0
#         self.cap = None
#         self.pFrameBuffer = 0
#
#         self.open()
#         pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 200)
#         mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer, FrameHead)
#         mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)
#         self.img_width = FrameHead.iWidth
#         self.img_height = FrameHead.iHeight
#
#         temp=int((self.img_width-self.img_height)/2)
#         self.crop = [temp, 0, temp + self.img_height, self.img_height]
#
#
#     def open(self):
#         if self.hCamera > 0:
#             return True
#
#         # 打开相机
#         try:
#             self.hCamera = mvsdk.CameraInit(self.DevInfo, -1, -1)
#         except mvsdk.CameraException as e:
#             print("CameraInit Failed({}): {}".format(e.error_code, e.message))
#             return False
#
#         # 获取相机特性描述
#         cap = mvsdk.CameraGetCapability(self.hCamera)
#
#         # 判断是黑白相机还是彩色相机
#         monoCamera = (cap.sIspCapacity.bMonoSensor != 0)
#
#         # 黑白相机让ISP直接输出MONO数据，而不是扩展成R=G=B的24位灰度
#         if monoCamera:
#             mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
#         else:
#             mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)
#
#         # 计算RGB buffer所需的大小，这里直接按照相机的最大分辨率来分配
#         FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)
#
#         # 分配RGB buffer，用来存放ISP输出的图像
#         # 备注：从相机传输到PC端的是RAW数据，在PC端通过软件ISP转为RGB数据（如果是黑白相机就不需要转换格式，但是ISP还有其它处理，所以也需要分配这个buffer）
#         pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)
#
#         # 相机模式切换成连续采集
#         mvsdk.CameraSetTriggerMode(self.hCamera, 0)
#         print("set trigger mode to hardware mode")
#         mvsdk.CameraSetExtTrigSignalType(self.hCamera, 0)
#
#         # 手动曝光，曝光时间30ms
#         mvsdk.CameraSetAeState(self.hCamera, 0)
#         mvsdk.CameraSetExposureTime(self.hCamera, 4 * 1000)
#
#         # 让SDK内部取图线程开始工作
#         mvsdk.CameraPlay(self.hCamera)
#
#
#         self.pFrameBuffer = pFrameBuffer
#         self.cap = cap
#         print("open camera success")
#         return True
#
#     def close(self):
#         if self.hCamera > 0:
#             mvsdk.CameraUnInit(self.hCamera)
#             self.hCamera = 0
#
#         mvsdk.CameraAlignFree(self.pFrameBuffer)
#         self.pFrameBuffer = 0
#
#     def grab(self):
#         # 从相机取一帧图片
#         hCamera = self.hCamera
#         pFrameBuffer = self.pFrameBuffer
#         try:
#             pRawData, FrameHead = mvsdk.CameraGetImageBuffer(hCamera, 200)
#             mvsdk.CameraImageProcess(hCamera, pRawData, pFrameBuffer, FrameHead)
#             mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)
#
#             # windows下取到的图像数据是上下颠倒的，以BMP格式存放。转换成opencv则需要上下翻转成正的
#             # linux下直接输出正的，不需要上下翻转
#             if platform.system() == "Windows":
#                 mvsdk.CameraFlipFrameBuffer(pFrameBuffer, FrameHead, 1)
#
#             # 此时图片已经存储在pFrameBuffer中，对于彩色相机pFrameBuffer=RGB数据，黑白相机pFrameBuffer=8位灰度数据
#             # 把pFrameBuffer转换成opencv的图像格式以进行后续算法处理
#             frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(pFrameBuffer)
#             frame = np.frombuffer(frame_data, dtype=np.uint8)
#             frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth,
#                                    1 if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3))
#
#             #裁剪为正方形
#             # frame = frame[self.crop[1]:self.crop[3], self.crop[0]:self.crop[2], :]
#
#
#             # frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_LINEAR)
#             return frame,True
#         except mvsdk.CameraException as e:
#             if e.error_code != mvsdk.CAMERA_STATUS_TIME_OUT:
#                 print("CameraGetImageBuffer failed({}): {}".format(e.error_code, e.message))
#             return None,False
#
#


class Utils():
    def __init__(self, win):
        self.win = win
        self.information_csv_path = win.information_csv_path
        self.user_ids = []
        self.init_csv()

    def init_csv(self):
        # 检插特征库里和csv里是否一样
        if not os.path.exists(self.information_csv_path):
            headers = ['name', 'id', '性别', '年龄']
            with open(self.information_csv_path, 'w',  encoding='utf-8-sig')as f:
                f_csv = csv.writer(f)
                f_csv.writerow(headers)

        # 读csv
        with open(self.information_csv_path,  encoding='utf-8-sig') as f:
            f_csv = csv.reader(f)

            for i, row in enumerate(f_csv):
                if i == 0: continue
                try:
                    id = row[1]
                    self.user_ids.append(id)
                except:
                    break
            print("user_ids:", self.user_ids)

    def save_video(self,path,camera, imgs):

        sample_camera_path = os.path.join(path, camera)
        if not os.path.exists(sample_camera_path):
            os.mkdir(sample_camera_path)

        for index, img in enumerate(imgs):
            img_path = os.path.join(sample_camera_path, '%03d.jpg' % (index + 1))
            # cv2.imshow("{}".format(camera), img)
            # cv2.waitKey(1)
            cv2.imwrite(img_path, img)

        # cv2.destroyAllWindows()

    # def save_picture(self, camera, img):
    #     sample_path = os.path.join(self.conf.root_path, "calibration_pic", camera)
    #     if not os.path.exists(sample_path):
    #         os.mkdir(sample_path)
    #     img_path = os.path.join(sample_path, "{}.jpg".format(datetime.datetime.now().strftime('%m_%d_%H_%M_%S')))
    #     cv2.imwrite(img_path, img)

    def add_id(self):
        if self.win.ID in self.user_ids:
            return
        else:
            user_data = pd.read_csv(self.information_csv_path, dtype=str)
            new_item = {"name": self.win.name, "id": self.win.ID, "性别": self.win.sex, "年龄": self.win.age}
            new_item = pd.DataFrame(new_item,index=[0])
            user_data = pd.concat([user_data, new_item])
        user_data.to_csv(self.information_csv_path, index=None)
        self.user_ids.append(self.win.ID)


# if __name__ == "__main__":
#     DevList = mvsdk.CameraEnumerateDevice()
#     nDev = len(DevList)
#     if nDev < 1:
#         print("No camera was found!")
#         exit()
#
#     print("Found %d devices." % nDev)