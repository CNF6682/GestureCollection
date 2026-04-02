# # 华南理工大学
# # 王熙来
# # 开发时间：9/1/2024 10:11 上午

# import datetime
# import time
# import dv_processing as dv
# import cv2 as cv
# import argparse
#
# parser = argparse.ArgumentParser(description='Show a preview of an iniVation event camera input.')
#
# args = parser.parse_args()
#
# # Open the camera
# camera = dv.io.CameraCapture()
#
# # Initialize visualizer instance which generates event data preview
# visualizer = dv.visualization.EventVisualizer(camera.getEventResolution())
#
# # Create the preview window
# cv.namedWindow("Preview", cv.WINDOW_NORMAL)
#
#
# def preview_events(event_slice):
#     cv.imshow("Preview", visualizer.generateImage(event_slice))
#     cv.waitKey(1)
#
#     end_time = time.time()
#     print("fps:",1/(end_time-start_time+0.00001))
#
#
# # Create an event slicer, this will only be used events only camera
# slicer = dv.EventStreamSlicer()
# slicer.doEveryTimeInterval(datetime.timedelta(milliseconds=20), preview_events)
#
# start_time = time.time()
#
# # start read loop
# while True:
#
#
#     # Get events
#     events = camera.getNextEventBatch()
#
#     # If no events arrived yet, continue reading
#     if events is not None:
#         slicer.accept(events)


import datetime
import time
import dv_processing as dv
import cv2
import argparse
import os
import concurrent.futures as futures

class EventCamera:
    def __init__(self,NS,record_save,frameRates,pipe,save_status,cache_duration_seconds=4.0):

        self.NS = NS
        self.record_save = record_save
        self.frameRates = frameRates
        self.pipe = pipe
        self.save_status = save_status
        self.cache_duration_seconds = cache_duration_seconds
        self.executor = futures.ThreadPoolExecutor(max_workers=1)


        self.camera = dv.io.CameraCapture()
        # self.writer = dv.io.MonoCameraWriter("mono_writer_sample.aedat4", self.camera)
        self.visualizer = dv.visualization.EventVisualizer(self.camera.getEventResolution())
        self.slicer = dv.EventStreamSlicer()
        self.slicer.doEveryTimeInterval(datetime.timedelta(milliseconds=33), self.preview_events)
        self.cameraCheck()


        #event camera在发现某处亮度变化时,就会马上输出一个事件,其响应特别快(~1us= HZ,比IMU还要快)，因此我们需要一个缓存机制来存储事件
        self.event_store = dv.EventStore()
        self.start_time = time.time()

        self.num_frames_show = 0

    def cameraCheck(self):
        # Check whether event stream is available
        if self.camera.isEventStreamAvailable():
            # Get the event stream resolution
            resolution = self.camera.getEventResolution()
            print("resolution",resolution)
            # Print the event stream capability with resolution value
            print(f"* Events at ({resolution[0]}x{resolution[1]}) resolution")
        # Check whether frame stream is available
        if self.camera.isFrameStreamAvailable():
            # Get the frame stream resolution
            resolution = self.camera.getFrameResolution()
            # Print the frame stream capability with resolution value
            print(f"* Frames at ({resolution[0]}x{resolution[1]}) resolution")
        # Check whether the IMU stream is available
        if self.camera.isImuStreamAvailable():
            # Print the imu data stream capability
            print("* IMU measurements")
        # Check whether the trigger stream is available
        if self.camera.isTriggerStreamAvailable():
            # Print the trigger stream capability
            print("* Triggers")


    def preview_events(self, event_slice):
        try:
            color_image=self.visualizer.generateImage(event_slice)
            # cv2.imshow("Preview", color_image)
            # cv2.waitKey(1)
            color_image = color_image[:, 0:480, :]
            frame_show = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
            frame_show = cv2.resize(frame_show, (160, 160))
            # frame_show = cv2.rotate(frame_show, cv2.ROTATE_180)
            # print("frame_show.shape",frame_show.shape)
            self.pipe.send(frame_show)

            # # 计算帧率
            # self.num_frames_show += 1
            # elapsed_time = time.time() - self.start_time
            # if elapsed_time > 0:
            #     fps = self.num_frames_show / elapsed_time
            # else:
            #     fps = 0
            # if self.num_frames_show > 60:
            #     self.num_frames_show = 0
            #     self.start_time = time.time()
            #
            # # print("fps:", fps)
            #
            # self.frameRates["event"] = fps
        except Exception as e:
            print("Failed to preview events: ", e)

        # end_time = time.time()
        # print("fps:", 1 / (end_time - self.start_time + 0.00001))

    # def run(self,pipe,stop_event):
    #     self.start_time = time.time()
    #
    #     while True:
    #         events = self.camera.getNextEventBatch()
    #         if events is not None:
    #             self.slicer.accept(events)
    #
    #             self.writer.writeEvents(events, streamName='events')
    def save_event(self):
        # try:
            print("Saving events...")


            path=self.NS.save_id_path
            sample_camera_path = os.path.join(path, "events")
            if not os.path.exists(sample_camera_path):
                os.mkdir(sample_camera_path)
            sample_camera_path = os.path.join(sample_camera_path, "event.aedat4")
            print("sample_camera_path",sample_camera_path)
            self.writer = dv.io.MonoCameraWriter(sample_camera_path, self.camera)
            self.writer.writeEvents(self.event_store, streamName='events')
            # Clear the event_store
            print("Events saved")
            # print(self.event_store.size())
            # self.event_store.erase(0, self.event_store.size())
            # print(self.event_store.size())
            #重新初始化event_store
            self.event_store = dv.EventStore()
            self.save_status["event"] = True
        #
        #
        # except Exception as e:
        #     print("Failed to save events: ", e)





    def run(self, stop_event):
        self.start_time = time.time()
        num_events = 0
        while True:
            # try:
            events = self.camera.getNextEventBatch()
            # print(num_events)
            if events is not None:


                # 切片展示
                self.slicer.accept(events)
                # print("events.shape",events)

                if self.record_save.is_set():#self.record_save["event"] == 1:
                    #触发事件存储
                    num_events += 1
                    #记录开始时间
                    if num_events == 1:
                        start_time = time.time()
                    self.event_store.add(events)
                    # print(len(self.event_store))

                    current_time = time.time()
                    # print(current_time - start_time)
                    if current_time - start_time >= self.cache_duration_seconds:
                        print("Saving events to disk...")
                        self.record_save.clear()  # self.record_save["event"] = 0
                        self.executor.submit(self.save_event)
                        num_events = 0
            # except Exception as e:
            #     print("Failed to run event camera: ", e)


        print("Event camera stopped")



# parser = argparse.ArgumentParser(description='Show a preview of an iniVation event camera input.')
#
# args = parser.parse_args()

def runEventCamera(pipe,stop_event,NS,record_save,frameRates,save_status):
    task = EventCamera(NS,record_save,frameRates,pipe,save_status)
    task.run(stop_event)


if __name__ == '__main__':
    # camera = dv.io.CameraCapture()
    visualizer = dv.visualization.EventVisualizer((640,480))
    reader = dv.io.MonoCameraRecording(r"C:\Users\Administrator.DESKTOP-ATGBNLB\Desktop\dataCollectionCode\GestureCollection\data\img\1_21_1_10_4\events\event.aedat4")

    cv2.namedWindow("Preview", cv2.WINDOW_NORMAL)
    # Run the loop while camera is still connected



    def preview_events(event_slice):
        global last_frame_time, frame_rate

        # Display the event image
        cv2.imshow("Preview", visualizer.generateImage(event_slice))

        # Calculate and display the frame rate
        # current_time = time.time()
        # frame_rate = 1.0 / (current_time - last_frame_time+0.0000001)
        # last_frame_time = current_time

        # print("fps:", frame_rate)

        # Show frame rate in the window
        # cv.displayOverlay("Preview", f"Frame Rate: {frame_rate:.2f} FPS", 1000)

        cv2.waitKey(0)


    # Create an event slicer, this will only be used events only camera
    slicer = dv.EventStreamSlicer()
    slicer.doEveryTimeInterval(datetime.timedelta(milliseconds=1), preview_events)

    while reader.isRunning():
        # Read batch of events
        events = reader.getNextEventBatch()
        if events is not None:
            slicer.accept(events)
        else:
            print("No events were received")


    # # Open the camera
    # camera = dv.io.CameraCapture()
    #
    # # Initialize visualizer instance which generates event data preview
    # visualizer = dv.visualization.EventVisualizer(camera.getEventResolution())
    #
    # # Create the preview window
    # # cv.namedWindow("Preview", cv.WINDOW_NORMAL)
    #
    # # Initialize timing variables
    # last_frame_time = time.time()
    # frame_rate = 0
    #
    #

    #
    #

    #
    # # Start read loop
    # while True:
    #     # Get events
    #     events = camera.getNextEventBatch()
    #
    #     # Get frame
    #     # frame = camera.getNextFrame()
    #
    #     # If no events arrived yet, continue reading
    #     if events is not None:
    #         slicer.accept(events)
    #     else:
    #         print("No events were received")
    #
    #     # if frame is not None:
    #     #     cv2.imshow("Preview", frame)
    #     #     cv2.waitKey(1)
    #     # else:
    #     #     print("No fames were received")


