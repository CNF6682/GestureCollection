
import cv2
import time
import numpy as np
import multiprocessing
import threading
from PyQt5.QtCore import QThread, pyqtSignal,QMutex
import concurrent.futures as futures
import os

import utils.mvsdk as mvsdk
from utils.logger import setup_logger

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
    def __init__(self,DevInfo,NS,record_save,frameRates,ROI):
        self.DevInfo = DevInfo
        self.NS = NS
        self.record_save = record_save
        self.frameRates = frameRates
        self.ROI = ROI
        # 缓存
        self.imgs_buffer = []
        self.executor = futures.ThreadPoolExecutor(max_workers=1)
        
        # 初始化日志
        camera_name = f"Camera_{DevInfo.GetSn()}"
        self.logger = setup_logger(camera_name)
        self.logger.info(f"初始化相机: {DevInfo.GetSn()}")

        # 打开相机
        self.hCamera = 0
        try:
            self.hCamera = mvsdk.CameraInit(DevInfo, -1, -1)
            self.logger.info(f"相机初始化成功: {DevInfo.GetSn()}")
        except mvsdk.CameraException as e:
            self.logger.error(f"相机初始化失败({e.error_code}): {e.message}")
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



    def save_video(self):
        """保存视频，带错误处理"""
        camera = ""
        try:
            if self.DevInfo.GetSn() == "044011420148":   # 041182220233  044062320120
                camera = "RGB_1"
            elif self.DevInfo.GetSn() == "044030620196":  # 044062320105   042092320674
                camera = "RGB_2"
            elif self.DevInfo.GetSn() == "044062320120":
                camera = "RGB_3"
            elif self.DevInfo.GetSn() == "044062320129":
                camera = "RGB_4"
            elif self.DevInfo.GetSn() == "044030620195":
                camera = "RGB_5"
            elif self.DevInfo.GetSn() == "043051920299":
                camera = "inf"
            elif self.DevInfo.GetSn() == "044062320137":
                camera = "RGB_6"
            elif self.DevInfo.GetSn() == "044062320105":
                camera = "RGB_7"
            elif self.DevInfo.GetSn() == "042101120056":
                camera = "RGB_8"

            path = self.NS.save_id_path
            sample_camera_path = os.path.join(path, camera)
            
            try:
                if not os.path.exists(sample_camera_path):
                    os.makedirs(sample_camera_path)
            except OSError as e:
                self.logger.error(f"创建保存目录失败: {str(e)}")
                return
            
            self.logger.info(f"{camera} 开始保存视频，共 {len(self.imgs_buffer)} 帧")

            saved_count = 0
            for index, img in enumerate(self.imgs_buffer):
                try:
                    img_path = os.path.join(sample_camera_path, '%03d.jpg' % (index + 1))
                    cv2.imwrite(img_path, img)
                    saved_count += 1
                    if index >= 240:
                        break
                except Exception as e:
                    self.logger.error(f"保存第 {index+1} 帧时出错: {str(e)}")

            self.logger.info(f'{camera} 采集完成，已保存 {saved_count} 帧到 {sample_camera_path}')
            
        except Exception as e:
            self.logger.error(f"save_video方法出错: {str(e)}")
        finally:
            # 无论如何都清空缓存
            self.imgs_buffer = []

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


    def run(self, pipe, stop_event):
        """相机运行主循环，带完整错误处理"""
        self.logger.info(f"相机 {self.DevInfo.GetSn()} 开始运行")
        num_frames = 0
        start_time = time.time()
        pRawData = None
        
        try:
            while not stop_event.is_set():
                try:
                    # 获取图像缓冲区
                    try:
                        pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 200)
                    except mvsdk.CameraException as e:
                        if e.error_code != mvsdk.CAMERA_STATUS_TIME_OUT:
                            self.logger.error(f"CameraGetImageBuffer失败({e.error_code}): {e.message}")
                        continue
                    
                    try:
                        # 处理图像
                        mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer, FrameHead)
                    except Exception as e:
                        self.logger.error(f"图像处理失败: {str(e)}")
                        continue
                    finally:
                        # 无论如何都要释放图像缓冲区
                        if pRawData:
                            try:
                                mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)
                                pRawData = None
                            except Exception as e:
                                self.logger.warning(f"释放图像缓冲区失败: {str(e)}")
                    
                    # 计算帧率
                    num_frames += 1
                    elapsed_time = time.time() - start_time
                    fps = num_frames / elapsed_time if elapsed_time > 0 else 0
                    
                    if num_frames > 300:
                        num_frames = 0
                        start_time = time.time()
                        self.logger.debug(f"相机 {self.DevInfo.GetSn()} 当前帧率: {fps:.2f}")
                    
                    # 转换图像格式
                    try:
                        frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(self.pFrameBuffer)
                        frame = np.frombuffer(frame_data, dtype=np.uint8)
                        frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 
                                             1 if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3))
                    except Exception as e:
                        self.logger.error(f"图像格式转换失败: {str(e)}")
                        continue
                    
                    # 根据相机序列号进行图像变换
                    try:
                        frame = self._transform_frame(frame)
                    except Exception as e:
                        self.logger.warning(f"图像变换失败: {str(e)}")
                    
                    # 发送显示帧
                    if num_frames % 10 == 0:
                        try:
                            frame_show = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            frame_show = cv2.resize(frame_show, (160, 160))
                            if pipe and not pipe.closed:
                                pipe.send(frame_show)
                            self.frameRates[self.DevInfo.GetSn()] = fps
                        except Exception as e:
                            self.logger.warning(f"发送显示帧失败: {str(e)}")
                    
                    # 记录数据
                    if self.record_save.is_set():
                        try:
                            self.imgs_buffer.append(frame)
                            
                            # 记录采集进度
                            if self.DevInfo.GetSn() == "044011420148":
                                self.NS.sampled = len(self.imgs_buffer) / self.NS.sample_frame
                            
                            if len(self.imgs_buffer) == 1:
                                start_time2 = time.time()
                                self.logger.info(f"相机 {self.DevInfo.GetSn()} 开始记录数据")
                            
                            if len(self.imgs_buffer) >= self.NS.sample_frame:
                                self.record_save.clear()
                                end_time2 = time.time()
                                self.logger.info(f"相机 {self.DevInfo.GetSn()} 采集完成，耗时: {end_time2-start_time2:.2f}秒")
                                
                                # 提交保存任务
                                try:
                                    if self.executor:
                                        self.executor.submit(self.save_video)
                                except Exception as e:
                                    self.logger.error(f"提交保存任务失败: {str(e)}")
                        except Exception as e:
                            self.logger.error(f"记录数据时出错: {str(e)}")

                except Exception as e:
                    self.logger.error(f"处理帧时出错: {str(e)}")
                    # 继续运行，不中断循环
                    
        except Exception as e:
            self.logger.critical(f"相机运行主循环出现严重错误: {str(e)}")
        finally:
            # 确保资源被正确清理
            self.logger.info(f"相机 {self.DevInfo.GetSn()} 开始清理资源...")
            self.cleanup()
            self.logger.info(f"相机 {self.DevInfo.GetSn()} 已停止")

    def _transform_frame(self, frame):
        """根据相机序列号变换图像"""
        sn = self.DevInfo.GetSn()
        
        if sn == "044011420148":
            frame = cv2.flip(frame, 0)
        elif sn == "044030620196":
            frame = cv2.flip(frame, 1)
        elif sn == "044062320120":
            frame = cv2.flip(frame, 0)
        elif sn == "044062320129":
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            frame = cv2.flip(frame, 1)
        elif sn == "044030620195":
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            frame = cv2.flip(frame, 1)
        elif sn == "044062320137":
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            frame = cv2.flip(frame, 1)
        elif sn == "044062320105":
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            frame = cv2.flip(frame, 1)
        elif sn == "043051920299":
            frame = cv2.rotate(frame, cv2.ROTATE_180)
            frame = cv2.flip(frame, 1)
        elif sn == "042101120056":
            frame = cv2.rotate(frame, cv2.ROTATE_180)
            frame = cv2.flip(frame, 1)
            
        return frame
        
def run_camera(devinfo, pipe, stop_event, NS, record_save, frameRates, ROI):
    """运行相机的进程入口函数，带错误处理"""
    camera = None
    logger = setup_logger(f"run_camera_{devinfo.GetSn()}")
    
    try:
        logger.info(f"启动相机进程: {devinfo.GetSn()}")
        camera = camera_task(devinfo, NS, record_save, frameRates, ROI)
        camera.run(pipe, stop_event)
    except Exception as e:
        logger.critical(f"相机进程 {devinfo.GetSn()} 发生严重错误: {str(e)}")
        # 确保清理资源
        if camera:
            try:
                camera.cleanup()
            except:
                pass
    finally:
        logger.info(f"相机进程 {devinfo.GetSn()} 退出")
    
    
if __name__ == "__main__":
    p1 = multiprocessing.Process(target=run_camera, args=(0,))
    p2 = multiprocessing.Process(target=run_camera, args=(1,))
    
    # p1 = threading.Thread(target=run_camera, args=(0,))
    # p2 = threading.Thread(target=run_camera, args=(1,))    

    p1.start()
    p2.start()
    
    p1.join()
    p2.join()