# ########################################################################
# #
# # Copyright (c) 2022, STEREOLABS.
# #
# # All rights reserved.
# #
# # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# # "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# # LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# # A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# # OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# # SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# # LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# # DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# # THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# # (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# # OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# #
# ########################################################################
#
# """
#     This sample demonstrates how to apply an exclusion ROI to all ZED SDK measures
#     This can be very useful to avoid noise from a vehicle bonnet or drone propellers for instance
# """
#
# import sys
# import pyzed.sl as sl
# import argparse
# import cv2
# import time
#
#
# def parse_args(init):
#     if len(opt.input_svo_file)>0 and opt.input_svo_file.endswith(".svo"):
#         init.set_from_svo_file(opt.input_svo_file)
#         print("[Sample] Using SVO File input: {0}".format(opt.input_svo_file))
#     elif len(opt.ip_address)>0 :
#         ip_str = opt.ip_address
#         if ip_str.replace(':','').replace('.','').isdigit() and len(ip_str.split('.'))==4 and len(ip_str.split(':'))==2:
#             init.set_from_stream(ip_str.split(':')[0],int(ip_str.split(':')[1]))
#             print("[Sample] Using Stream input, IP : ",ip_str)
#         elif ip_str.replace(':','').replace('.','').isdigit() and len(ip_str.split('.'))==4:
#             init.set_from_stream(ip_str)
#             print("[Sample] Using Stream input, IP : ",ip_str)
#         else :
#             print("Unvalid IP format. Using live stream")
#     if ("HD2K" in opt.resolution):
#         init.camera_resolution = sl.RESOLUTION.HD2K
#         print("[Sample] Using Camera in resolution HD2K")
#     elif ("HD1200" in opt.resolution):
#         init.camera_resolution = sl.RESOLUTION.HD1200
#         print("[Sample] Using Camera in resolution HD1200")
#     elif ("HD1080" in opt.resolution):
#         init.camera_resolution = sl.RESOLUTION.HD1080
#         print("[Sample] Using Camera in resolution HD1080")
#     elif ("HD720" in opt.resolution):
#         init.camera_resolution = sl.RESOLUTION.HD720
#         print("[Sample] Using Camera in resolution HD720")
#     elif ("SVGA" in opt.resolution):
#         init.camera_resolution = sl.RESOLUTION.SVGA
#         print("[Sample] Using Camera in resolution SVGA")
#     elif ("VGA" in opt.resolution):
#         init.camera_resolution = sl.RESOLUTION.VGA
#         print("[Sample] Using Camera in resolution VGA")
#     elif len(opt.resolution)>0:
#         print("[Sample] No valid resolution entered. Using default")
#     else :
#         print("[Sample] Using default resolution")
#
#
# def main():
#     # Create a ZED Camera object
#     zed = sl.Camera()
#
#     init_parameters = sl.InitParameters()
#     init_parameters.camera_resolution = sl.RESOLUTION.HD720 # 相机分辨率设置
#     init_parameters.depth_mode = sl.DEPTH_MODE.NEURAL # ULTRA  PERFORMANCE NEURAL
#     init_parameters.coordinate_units = sl.UNIT.MILLIMETER
#     # parse_args(init_parameters)
#     # 设置相机帧率
#     init_parameters.camera_fps = 60
#     # 设置曝光模式为手动
#     zed.set_camera_settings(sl.VIDEO_SETTINGS.EXPOSURE, 50)
#
#     init_parameters.coordinate_units = sl.UNIT.METER
#     init_parameters.depth_minimum_distance = 0.2
#
#     init_parameters.depth_maximum_distance = 4
#
#     # Open the camera
#     returned_state = zed.open(init_parameters)
#     if returned_state != sl.ERROR_CODE.SUCCESS:
#         print("Camera Open", returned_state, "Exit program.")
#         exit()
#     else:
#         print("Camera Opened Successfully")
#
#     # imWndName = "Image"
#     # depthWndName = "Depth"
#     # ROIWndName = "ROI"
#     # cv2.namedWindow(imWndName, cv2.WINDOW_NORMAL)
#     # cv2.namedWindow(ROIWndName, cv2.WINDOW_NORMAL)
#     # cv2.namedWindow(depthWndName, cv2.WINDOW_NORMAL)
#
#     # print("Press 'a' to apply the ROI")
#     # print("Press 'r' to reset the ROI")
#     # print("Press 's' to save the ROI as image file to reload it later")
#     # print("Press 'l' to load the ROI from an image file")
#
#     resolution = zed.get_camera_information().camera_configuration.resolution
#
#     # Create a Mat to store images
#     zed_image = sl.Mat(resolution.width, resolution.height, sl.MAT_TYPE.U8_C4, sl.MEM.CPU)
#     zed_depth_image = sl.Mat(resolution.width, resolution.height, sl.MAT_TYPE.U8_C4, sl.MEM.CPU)
#
#     # mask_name = "Mask.png"
#     # mask_roi = sl.Mat(resolution.width, resolution.height, sl.MAT_TYPE.U8_C1, sl.MEM.CPU)
#
#     # roi_running = True
#     # roi_param = sl.RegionOfInterestParameters()
#     # # roi_param.auto_apply = True
#     # roi_param.depth_far_threshold_meters = 2.5 # fareset distance to consider
#     # roi_param.image_height_ratio_cutoff = 0.5  # ratio of the image height to consider
#     # zed.start_region_of_interest_auto_detection(roi_param)
#
#     # Capture new images until 'q' is pressed
#     key = ' '
#     num_frames = 0
#     start_time = time.time()
#     while key != 'q' and key != 27:
#         # Check that a new image is successfully acquired
#         returned_state = zed.grab()
#         if returned_state == sl.ERROR_CODE.SUCCESS:
#             num_frames += 1
#             elapsed_time = time.time() - start_time
#             if elapsed_time > 0:
#                 fps = num_frames / elapsed_time
#             else:
#                 fps = 0
#             if num_frames > 60:
#                 num_frames = 0
#                 start_time = time.time()
#
#             print("fps:", fps)
#             # Retrieve left image
#             zed.retrieve_image(zed_image, sl.VIEW.SIDE_BY_SIDE) # SIDE_BY_SIDE, LEFT, RIGHT
#             zed.retrieve_image(zed_depth_image, sl.VIEW.DEPTH)
#
#             # status = zed.get_region_of_interest_auto_detection_status()
#             # if roi_running:
#             #     text = "Region of interest auto detection is running\r"
#             #     if status == sl.REGION_OF_INTEREST_AUTO_DETECTION_STATE.READY:
#             #         print(text, "Region of interest auto detection is done!   ")
#             #         zed.getRegionOfInterest(mask_roi)
#             #         cvMaskROI = mask_roi.get_data()
#             #         cv2.imshow("roi", cvMaskROI)
#
#             # roi_running = (status == sl.REGION_OF_INTEREST_AUTO_DETECTION_STATE.RUNNING)
#
#             cvImage = zed_image.get_data()
#             cvDepthImage = zed_depth_image.get_data()
#
#             # 清空缓存
#
#
#
#             cvImage=cv2.resize(cvImage,(0,0),fx=0.5,fy=0.5)
#             cvDepthImage=cv2.resize(cvDepthImage,(0,0),fx=0.5,fy=0.5)
#
#             cv2.imshow("rgb", cvImage)
#             cv2.imshow("depth", cvDepthImage)
#
#         key = cv2.waitKey(1)
#
#         # # Apply Current ROI
#         # if key == 'r': #Reset ROI
#         #     if not roi_running:
#         #         emptyROI = sl.Mat()
#         #         zed.setRegionOfInterest(emptyROI)
#         #     print("Resetting Auto ROI detection")
#         #     zed.startRegionOfInterestAutoDetection(roi_param)
#         # elif key == 's' and mask_roi.is_init():
#         #     print("Saving ROI to", mask_name)
#         #     mask_roi.write(mask_name)
#         # elif key == 'l':
#         #     # Load the mask from a previously saved file
#         #     tmp = cv2.imread(mask_name, cv2.IMREAD_GRAYSCALE)
#         #     if not tmp.empty():
#         #         slROI = sl.Mat(sl.Resolution(tmp.cols, tmp.rows), sl.MAT_TYPE.U8_C1, tmp.data, tmp.step)
#         #         zed.set_region_of_interest(slROI)
#         #     print(mask_name, "could not be found")
#
#     # Exit
#     zed.close()
#     exit()
#
#
# if __name__ == "__main__":
#     # parser = argparse.ArgumentParser()
#     # parser.add_argument('--input_svo_file', type=str, help='Path to an .svo file, if you want to replay it',default = '')
#     # parser.add_argument('--ip_address', type=str, help='IP Adress, in format a.b.c.d:port or a.b.c.d, if you have a streaming setup', default = '')
#     # parser.add_argument('--resolution', type=str, help='Resolution, can be either HD2K, HD1200, HD1080, HD720, SVGA or VGA', default = '')
#     # opt = parser.parse_args()
#     # if len(opt.input_svo_file)>0 and len(opt.ip_address)>0:
#     #     print("Specify only input_svo_file or ip_address, or none to use wired camera, not both. Exit program")
#     #     exit()
#     main()


########################################################################
#
# Copyright (c) 2022, STEREOLABS.
#
# All rights reserved.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
########################################################################

"""
    Live camera sample showing the camera information and video in real time and allows to control the different
    settings.
"""

import cv2
import pyzed.sl as sl
import time

# Global variable
camera_settings = sl.VIDEO_SETTINGS.BRIGHTNESS
str_camera_settings = "BRIGHTNESS"
step_camera_settings = 1
led_on = True
selection_rect = sl.Rect()
select_in_progress = False
origin_rect = (-1, -1)


# Function that handles mouse events when interacting with the OpenCV window.
def on_mouse(event, x, y, flags, param):
    global select_in_progress, selection_rect, origin_rect
    if event == cv2.EVENT_LBUTTONDOWN:
        origin_rect = (x, y)
        select_in_progress = True
    elif event == cv2.EVENT_LBUTTONUP:
        select_in_progress = False
    elif event == cv2.EVENT_RBUTTONDOWN:
        select_in_progress = False
        selection_rect = sl.Rect(0, 0, 0, 0)

    if select_in_progress:
        selection_rect.x = min(x, origin_rect[0])
        selection_rect.y = min(y, origin_rect[1])
        selection_rect.width = abs(x - origin_rect[0]) + 1
        selection_rect.height = abs(y - origin_rect[1]) + 1


def main():
    init = sl.InitParameters()
    init.depth_mode = sl.DEPTH_MODE.NEURAL # PERFORMANCE NEURAL
    cam = sl.Camera()
    status = cam.open(init)
    if status != sl.ERROR_CODE.SUCCESS:
        print("Camera Open : " + repr(status) + ". Exit program.")
        exit()

    runtime = sl.RuntimeParameters()

    mat = sl.Mat()
    win_name = "Camera Control"
    cv2.namedWindow(win_name)
    cv2.setMouseCallback(win_name, on_mouse)
    print_camera_information(cam)
    print_help()
    switch_camera_settings()
    key = ''
    num_frames = 0
    start_time = time.time()
    while key != 113:  # for 'q' key
        err = cam.grab(runtime)
        if err == sl.ERROR_CODE.SUCCESS:  # Check that a new image is successfully acquired
            num_frames += 1
            cam.retrieve_image(mat, sl.VIEW.LEFT)  # Retrieve left image
            # cam.retrieve_image(mat, sl.VIEW.DEPTH)
            cvImage = mat.get_data()  # Convert sl.Mat to cv2.Mat

            # Display FPS
            if num_frames > 600:
                num_frames = 0
                start_time = time.time()
            cv2.putText(cvImage, "FPS: " + str(int(num_frames / (time.time() - start_time+0.00001))), (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)


            if (not selection_rect.is_empty() and selection_rect.is_contained(sl.Rect(0, 0, cvImage.shape[1],
                                                                                      cvImage.shape[
                                                                                          0]))):  # Check if selection rectangle is valid and draw it on the image
                cv2.rectangle(cvImage, (selection_rect.x, selection_rect.y),
                              (selection_rect.width + selection_rect.x, selection_rect.height + selection_rect.y),
                              (220, 180, 20), 2)
            cv2.imshow(win_name, cvImage)  # Display image
        else:
            print("Error during capture : ", err)
            break

        key = cv2.waitKey(5)
        # Change camera settings with keyboard
        update_camera_settings(key, cam, runtime, mat)
    cv2.destroyAllWindows()

    cam.close()


# Display camera information
def print_camera_information(cam):
    cam_info = cam.get_camera_information()
    print("ZED Model                 : {0}".format(cam_info.camera_model))
    print("ZED Serial Number         : {0}".format(cam_info.serial_number))
    print("ZED Camera Firmware       : {0}/{1}".format(cam_info.camera_configuration.firmware_version,
                                                       cam_info.sensors_configuration.firmware_version))
    print("ZED Camera Resolution     : {0}x{1}".format(round(cam_info.camera_configuration.resolution.width, 2),
                                                       cam.get_camera_information().camera_configuration.resolution.height))
    print("ZED Camera FPS            : {0}".format(int(cam_info.camera_configuration.fps)))


# Print help
def print_help():
    print("\n\nCamera controls hotkeys:")
    print("* Increase camera settings value:  '+'")
    print("* Decrease camera settings value:  '-'")
    print("* Toggle camera settings:          's'")
    print("* Toggle camera LED:               'l' (lower L)")
    print("* Reset all parameters:            'r'")
    print("* Reset exposure ROI to full image 'f'")
    print("* Use mouse to select an image area to apply exposure (press 'a')")
    print("* Exit :                           'q'\n")


# update camera setting on key press
def update_camera_settings(key, cam, runtime, mat):
    global led_on
    if key == 115:  # for 's' key
        # Switch camera settings
        switch_camera_settings()
    elif key == 43:  # for '+' key
        # Increase camera settings value.
        current_value = cam.get_camera_settings(camera_settings)[1]
        cam.set_camera_settings(camera_settings, current_value + step_camera_settings)
        print(str_camera_settings + ": " + str(current_value + step_camera_settings))
    elif key == 45:  # for '-' key
        # Decrease camera settings value.
        current_value = cam.get_camera_settings(camera_settings)[1]
        if current_value >= 1:
            cam.set_camera_settings(camera_settings, current_value - step_camera_settings)
            print(str_camera_settings + ": " + str(current_value - step_camera_settings))
    elif key == 114:  # for 'r' key
        # Reset all camera settings to default.
        cam.set_camera_settings(sl.VIDEO_SETTINGS.BRIGHTNESS, -1)
        cam.set_camera_settings(sl.VIDEO_SETTINGS.CONTRAST, -1)
        cam.set_camera_settings(sl.VIDEO_SETTINGS.HUE, -1)
        cam.set_camera_settings(sl.VIDEO_SETTINGS.SATURATION, -1)
        cam.set_camera_settings(sl.VIDEO_SETTINGS.SHARPNESS, -1)
        cam.set_camera_settings(sl.VIDEO_SETTINGS.GAIN, -1)
        cam.set_camera_settings(sl.VIDEO_SETTINGS.EXPOSURE, -1)
        cam.set_camera_settings(sl.VIDEO_SETTINGS.WHITEBALANCE_TEMPERATURE, -1)
        print("[Sample] Reset all settings to default")
    elif key == 108:  # for 'l' key
        # Turn on or off camera LED.
        led_on = not led_on
        cam.set_camera_settings(sl.VIDEO_SETTINGS.LED_STATUS, led_on)
    elif key == 97:  # for 'a' key
        # Set exposure region of interest (ROI) on a target area.
        print("[Sample] set AEC_AGC_ROI on target [", selection_rect.x, ",", selection_rect.y, ",",
              selection_rect.width, ",", selection_rect.height, "]")
        cam.set_camera_settings_roi(sl.VIDEO_SETTINGS.AEC_AGC_ROI, selection_rect, sl.SIDE.BOTH)
    elif key == 102:  # for 'f' key
        # Reset exposure ROI to full resolution.
        print("[Sample] reset AEC_AGC_ROI to full res")
        cam.set_camera_settings_roi(sl.VIDEO_SETTINGS.AEC_AGC_ROI, selection_rect, sl.SIDE.BOTH, True)


# Function to switch between different camera settings (brightness, contrast, etc.).
def switch_camera_settings():
    global camera_settings
    global str_camera_settings
    if camera_settings == sl.VIDEO_SETTINGS.BRIGHTNESS:
        camera_settings = sl.VIDEO_SETTINGS.CONTRAST
        str_camera_settings = "Contrast"
        print("[Sample] Switch to camera settings: CONTRAST")
    elif camera_settings == sl.VIDEO_SETTINGS.CONTRAST:
        camera_settings = sl.VIDEO_SETTINGS.HUE
        str_camera_settings = "Hue"
        print("[Sample] Switch to camera settings: HUE")
    elif camera_settings == sl.VIDEO_SETTINGS.HUE:
        camera_settings = sl.VIDEO_SETTINGS.SATURATION
        str_camera_settings = "Saturation"
        print("[Sample] Switch to camera settings: SATURATION")
    elif camera_settings == sl.VIDEO_SETTINGS.SATURATION:
        camera_settings = sl.VIDEO_SETTINGS.SHARPNESS
        str_camera_settings = "Sharpness"
        print("[Sample] Switch to camera settings: Sharpness")
    elif camera_settings == sl.VIDEO_SETTINGS.SHARPNESS:
        camera_settings = sl.VIDEO_SETTINGS.GAIN
        str_camera_settings = "Gain"
        print("[Sample] Switch to camera settings: GAIN")
    elif camera_settings == sl.VIDEO_SETTINGS.GAIN:
        camera_settings = sl.VIDEO_SETTINGS.EXPOSURE
        str_camera_settings = "Exposure"
        print("[Sample] Switch to camera settings: EXPOSURE")
    elif camera_settings == sl.VIDEO_SETTINGS.EXPOSURE:
        camera_settings = sl.VIDEO_SETTINGS.WHITEBALANCE_TEMPERATURE
        str_camera_settings = "White Balance"
        print("[Sample] Switch to camera settings: WHITEBALANCE")
    elif camera_settings == sl.VIDEO_SETTINGS.WHITEBALANCE_TEMPERATURE:
        camera_settings = sl.VIDEO_SETTINGS.BRIGHTNESS
        str_camera_settings = "Brightness"
        print("[Sample] Switch to camera settings: BRIGHTNESS")


if __name__ == "__main__":
    main()
