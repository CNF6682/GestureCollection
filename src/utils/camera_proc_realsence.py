# 华南理工大学
# 王熙来
# 开发时间：2024/8/17 16:52


import cv2
import numpy as np
import pyrealsense2 as rs
import time
import concurrent.futures as futures
import os

class RealSenceTask:
    def __init__(self,NS,record_save,frameRates):

        self.NS = NS
        self.record_save = record_save
        self.frameRates = frameRates

        self.executor = futures.ThreadPoolExecutor(max_workers=1)

        # 创建一个上下文对象。该对象拥有所有连接的Realsense设备的句柄
        self.pipeline = rs.pipeline()
        # 配置视频流
        self.config = rs.config()
        self.config.enable_stream(rs.stream.depth, 320, 240, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
        #设置min distance


        #开启视频流
        self.profile = self.pipeline.start(self.config)
        self.depth_scale = self.profile.get_device().first_depth_sensor().get_depth_scale()
        print("Depth Scale is: ", self.depth_scale)

        # Declare sensor object and set options
        depth_sensor = self.profile.get_device().first_depth_sensor()
        depth_sensor.set_option(rs.option.visual_preset, 5)  # 5 is short range, 3 is low ambient light
        depth_sensor.set_option(rs.option.min_distance, 0)
        depth_sensor.set_option(rs.option.confidence_threshold, 2)
        depth_sensor.set_option(rs.option.laser_power,0)
        depth_sensor.set_option(rs.option.pre_processing_sharpening,5)
        depth_sensor.set_option(rs.option.noise_filtering,6)

        # emitter = depth_sensor.get_option(rs.option.emitter_enabled)
        # print("emitter = ", emitter)
        # set_emitter = 0
        # depth_sensor.set_option(rs.option.emitter_enabled, set_emitter)
        # emitter1 = depth_sensor.get_option(rs.option.emitter_enabled)
        # print("new emitter = ", emitter1)

        # if depth_sensor.supports(rs.option.emitter_enabled):
        #     print("emitter_enabled")
        #     depth_sensor.set_option(rs.option.emitter_enabled, 0)
        # depth_sensor.set_option(rs.option.max_distance, 1)
        # depth_sensor.stop()

        # 相机RGB和深度图对齐
        self.align = rs.align(rs.stream.color)
        # # get camera intrinsics 获取相机内在函数
        # self.intr = self.profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
        # # 设置open3d中的针孔相机数据
        # self.pinhole_camera_intrinsic = o3d.camera.PinholeCameraIntrinsic(self.intr .width, self.intr .height, self.intr .fx, self.intr .fy,
        #                                                              self.intr .ppx, self.intr .ppy)

        self.recording = 0
        self.save = 0

    def grab(self):
        try:
            # 等待图像进来
            frames = self.pipeline.wait_for_frames()
            # 将RGBD对齐
            aligned_frames = self.align.process(frames)
            #获得深度图和彩色图，并转化为numpy数组
            depth_frame = aligned_frames.get_depth_frame()

            spatial = rs.spatial_filter()
            spatial.set_option(rs.option.filter_magnitude, 2)
            spatial.set_option(rs.option.filter_smooth_alpha, 1)
            spatial.set_option(rs.option.filter_smooth_delta, 10)
            spatial.set_option(rs.option.holes_fill, 5)
            #
            # hole_filling = rs.hole_filling_filter()
            #
            filtered_depth = spatial.process(depth_frame)
            # filtered_depth = hole_filling.process(depth_frame)

            color_frame = aligned_frames.get_color_frame()
            depth_image = np.asanyarray(filtered_depth.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            # print("depth_image: ", depth_image.shape)

            #640*480crop到480*480


            # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
            # >4m的与4m的颜色显示相同，那么alpha=255/(2*10^3)≈0.064
            depth_colormap = True # cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.14), cv2.COLORMAP_BONE)
            #取中心点的深度
            # dist=depth_frame.get_distance(320,240) #*self.depth_scale
            # dist2=depth_image[240,320]*self.depth_scale
            # dist, _, _, _ = cv2.mean(depth_image*self.depth_scale)
            # print("distance: ", dist, "m")
            # print("distance2: ", dist2, "m")
            depth_image = cv2.convertScaleAbs(depth_image, alpha=0.14)
            #像素值大于一定值的像素变为0
            depth_image[depth_image>245]=0
            #取中心点的像素值
            # uv=depth_image[240,320]
            # print("uv: ", uv)



            color_image = color_image[:, 80:560, :]
            depth_image = depth_image[:, 80:560]
            # depth_colormap = depth_colormap[:, 80:560, :]

            return depth_colormap,depth_image, color_image,True

        except Exception as e:
            print(e)
            return None, None,None,None,False


    def save_video(self):

        path=self.NS.save_id_path
        sample_camera_path_1 = os.path.join(path, "realsence_RGB")
        sample_camera_path_2 = os.path.join(path, "realsence_Depth")
        if not os.path.exists(sample_camera_path_1):
            os.mkdir(sample_camera_path_1)
        if not os.path.exists(sample_camera_path_2):
            os.mkdir(sample_camera_path_2)

        for index, img in enumerate(self.RGB_buffer):
            img_path = os.path.join(sample_camera_path_1, '%03d.jpg' % (index + 1))
            img_path2 = os.path.join(sample_camera_path_2, '%03d.jpg' % (index + 1))
            # cv2.imshow("{}".format(camera), img)
            # cv2.waitKey(1)
            # print("img_path:",img_path)
            cv2.imwrite(img_path, img)
            cv2.imwrite(img_path2, self.Depth_buffer[index])


        self.RGB_buffer = []
        self.Depth_buffer = []

        print('realsence采集完成')

    def run(self,pipe,pipe2,stop_event):
        num=0
        self.RGB_buffer = []
        self.Depth_buffer = []
        self.PCD_buffer = []
        num_frames = 0
        start_time = time.time()

        while not stop_event.is_set():
            try:
                # print(num_frames)

                depth_color_image,depth_image, color_image ,ret= self.grab()
                if ret:
                    # color_image = cv2.flip(color_image, 1)
                    # depth_image = cv2.flip(depth_image, 1)
                    # self.signal_changeFrame_RGB.emit([color_image, self.win.ui.label_realsense_RGB])
                    # self.signal_changeFrame_Depth.emit([depth_image, self.win.ui.label_realsense_Depth])

                    # 计算帧率
                    num_frames += 1
                    elapsed_time = time.time() - start_time
                    if elapsed_time > 0:
                        fps = num_frames / elapsed_time
                    else:
                        fps = 0
                    if num_frames>60:
                        num_frames=0
                        start_time=time.time()

                    # print("fps:",fps)
                    # print(num_frames)

                    if num_frames % 2 == 0:

                        frame_show = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
                        frame_show = cv2.resize(frame_show, (160,160))
                        pipe.send(frame_show)
                        frame_show_2=cv2.cvtColor(depth_image, cv2.COLOR_BGR2RGB)

                        frame_show_2= cv2.resize(frame_show_2, (160,160))
                        pipe2.send(frame_show_2)
                        self.frameRates["realsence"] = fps
                        # print("fps:", fps)


                    if self.record_save["realsence"] == 1:
                        num+=1
                        self.RGB_buffer.append(color_image.copy())
                        self.Depth_buffer.append(depth_image.copy())
                        # self.Depth_Color_buffer.append(depth_color_image.copy())
                        # self.PCD_buffer.append(pcd.copy())

                        # self.signal_changenum.emit(int(num / self.win.sample_frame * 100))

                        if len(self.RGB_buffer) == 1:
                            start_time2 = time.time()
                        # print(len(self.imgs_buffer))
                        if len(self.RGB_buffer) == self.NS.sample_frame:
                            end_time2 = time.time()
                            print("采集完成，耗时：",end_time2-start_time2)
                            self.executor.submit(self.save_video)

                            self.record_save["realsence"] = 0

                    end=time.time()
                    # print("time:",1/(end - start))
            except Exception as e:
                print(e)




        print("realsence stop")
        # # 停止管道数据传输
        # self.pipeline.stop()
        #
        # # 获取深度传感器的设备
        # depth_sensor = self.pipeline.get_active_profile().get_device().first_depth_sensor()
        # # 关闭深度传感器
        # depth_sensor.stop()




def runRealsence(pipe,pipe2,stop_event,NS,record_save,frameRates):
    task = RealSenceTask(NS,record_save,frameRates)
    task.run(pipe,pipe2,stop_event)