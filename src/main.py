# 华南理工大学
# 王熙来
# 开发时间：2024/4/16 16:13

import os
import sys
import time

from utils import mvsdk
#将当前工作目录修改为上级目录
sys.path.append("../")
sys.path.append("../../")

import shutil
import csv
#界面
from ui.UI import Ui_MAIN_WINDOW

#pyqt
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QCloseEvent, QPixmap, QImage, QMovie
from PyQt5.QtWidgets import QFileDialog, QMessageBox

import pandas as pd

from utils.utils import Utils
from utils.camera_proc import *
from utils.camera_proc_realsence import runRealsence
from utils.camera_proc_event import runEventCamera
from utils.camera_ZED import runZED

from utils.audio_proc import run_audio

from multiprocessing import Pipe,Event,Process,Manager

import pyrealsense2 as rs
import dv_processing as dv
import socket



class Main_Window(QtWidgets.QMainWindow):
    def __init__(self):
        super(Main_Window, self).__init__()
        self.ui = Ui_MAIN_WINDOW()
        self.ui.setupUi(self)
        self.init_UI()
        # 初始化摄像头进程和管道
        self.processes = []
        self.parent_conns = []
        self.stop_events = []
        self.show_windows = [] #self.ui.label_RGB,self.ui.label_RGB_2,self.ui.label_RGB_3,self.ui.label_RGB_4,self.ui.label_RGB_5
        self.frameRates_label = [] #记录各个相机的帧率
        self.NS=Manager().Namespace() #用于进程间通信Manager命名空间,所有全局变量都放在这里
        self.record_save = Manager().dict() #用于进程间通信Manager字典
        self.record_events = []#用event试试
        self.frameRates = Manager().dict() #用于进程间通信Manager字典,记录各个相机的帧率
        self.ROI=Manager().dict() #用于进程间通信Manager字典,记录各个相机的ROI


        #采样设置##################
        #采样帧数
        self.NS.sample_frame=240 #int(self.ui.lineEdit_sample_frame.text())

        # 采样进度百分比
        self.NS.sampled= 0

        # ZED保存标志
        self.NS.ZED_saved=False


        print('采样帧数为{}'.format(self.NS.sample_frame))
        #保存路径
        self.fpath = self.ui.lineEdit_sample_save_path.text()
        print('保存路径为{}'.format(self.fpath))
        #数据统计csv
        self.information_csv_path = os.path.join(self.fpath, 'user_info.csv')
        self.user_ids = []
        self.init_csv()

        #工具
        self.utils = Utils(self)


        self.timer_imshow=QtCore.QTimer(self)
        self.timer_imshow.timeout.connect(self.update_frames)
        self.timer_imshow.start(10)  # 每1ms检查一次新帧
        self.fakeTime=0 #理论系统时间

        self.timer_record=QtCore.QTimer(self)
        self.timer_record.timeout.connect(self.record_flag)

        self.timer_continue = QtCore.QTimer(self)
        self.timer_continue.timeout.connect(self.continue_record)
        
        # self.timer_fault=QtCore.QTimer(self)
        # self.timer_fault.timeout.connect(self.time_out)

        #控件##################
        self.name = self.ui.lineEdit_name.text()
        self.sex = self.ui.comboBox_sex.currentText()
        self.age = self.ui.lineEdit_age.text()
        self.ID = self.ui.lineEdit_ID.text()
        self.lr = self.ui.lineEdit_lr.text()
        self.session = self.ui.lineEdit_session.text()
        self.gesture_type = self.ui.lineEdit_gesture_type.text()
        self.sample_time = self.ui.lineEdit_NUM.text()
        self.fpath = self.ui.lineEdit_sample_save_path.text() #r"F:\dataset"
        # self.fpath = r"F:\dataset"
        self.fpath=r"E:\dataset"
        # self.fpath = r"C:\Users\Administrator.DESKTOP-ATGBNLB\Desktop\dataCollectionCode\GestureCollection\data"

        #帧数改变
        self.ui.lineEdit_sample_frame.textChanged.connect(self.sample_frame_changed)
        #路径选择
        self.ui.pushButton_select_path.clicked.connect(self.select_path)

        #ID改变
        self.ui.lineEdit_ID.textChanged.connect(self.ID_changed)
        #采样次数改变
        self.ui.lineEdit_NUM.textChanged.connect(self.sample_time_changed)
        #类别改变
        self.ui.lineEdit_gesture_type.textChanged.connect(self.gesture_type_changed)
        #场景改变
        self.ui.lineEdit_lr.textChanged.connect(self.lr_changed)
        #时期改变
        self.ui.lineEdit_session.textChanged.connect(self.session_changed)
        #性别改变
        self.ui.comboBox_sex.currentIndexChanged.connect(self.sex_changed)
        #年龄改变
        self.ui.lineEdit_age.textChanged.connect(self.age_changed)
        #姓名改变
        self.ui.lineEdit_name.textChanged.connect(self.name_changed)
        #注册
        self.ui.pushButton_regist.clicked.connect(self.regist)
        #删除
        self.ui.pushButton_del.clicked.connect(self.del_sample)
        #统计
        self.ui.pushButton_analyze.clicked.connect(self.analyze)
        # 是否连续采集
        self.ui.pushButton_continue.clicked.connect(self.continue_flag)
        self.continue_f=True



        #显示
        self.label_RGB_height = self.ui.label_RGB.geometry().height()  # 图像显示位置的高度
        self.label_RGB_width = self.ui.label_RGB.geometry().width()
        print("RGB Height: {}".format(self.label_RGB_height))
        print("RGB Width: {}".format(self.label_RGB_width))

        self.ui.progressBar.setValue(100)


        #相机##################
        #迈德威视相机
        self.DevList = mvsdk.CameraEnumerateDevice()
        # self.camera_objs = GlobalContainer()
        nDev = len(self.DevList)
        if nDev < 1:
            print("No camera was found!")
        print("Found %d 迈德 devices." % nDev)
        for i, DevInfo in enumerate(self.DevList):
            try:
                parent_conn, child_conn = Pipe()#设置管道
                stop_event = Event()#设置停止
                record_event = Event() # <--- [添加] 为这个相机创建一个专属的Event
                print("第{}个设备，编号{}".format(i, DevInfo.GetSn()))

                #记录每个设备的储存标志位 0显示 1缓存后保存
                self.record_save[DevInfo.GetSn()] = 0
                #每个相机的帧率
                self.frameRates[DevInfo.GetSn()] = 0
                # 每个相机的ROI
                self.ROI[DevInfo.GetSn()] = [0, 0]


                if DevInfo.GetSn() == "044011420148":  # 1  041182220233  044062320120
                    self.show_windows.append(self.ui.label_RGB)
                    self.frameRates_label.append(self.ui.label_frameRates_1)
                elif DevInfo.GetSn() == "044030620196":  # 2   042092320674  044062320105

                    self.show_windows.append(self.ui.label_RGB_2)
                    self.frameRates_label.append(self.ui.label_frameRates_2)

                elif DevInfo.GetSn() == "044062320120":  # 3  044062320129
                    self.show_windows.append(self.ui.label_RGB_3)
                    self.frameRates_label.append(self.ui.label_frameRates_3)

                elif DevInfo.GetSn() == "044062320129": #4 044062320137
                    self.show_windows.append(self.ui.label_RGB_4)
                    self.frameRates_label.append(self.ui.label_frameRates_4)

                elif DevInfo.GetSn() == "044030620195": #5 044011420148  042092320674静脉小
                    self.show_windows.append(self.ui.label_RGB_5)
                    self.frameRates_label.append(self.ui.label_frameRates_5)



                elif DevInfo.GetSn() == "044062320137": #6  044030620195
                    self.show_windows.append(self.ui.label_RGB_6)
                    self.frameRates_label.append(self.ui.label_frameRates_6)

                elif DevInfo.GetSn() == "044062320105":  # 7 042101120056
                    self.show_windows.append(self.ui.label_RGB_7)
                    self.frameRates_label.append(self.ui.label_frameRates_7)


                elif DevInfo.GetSn() == "042101120056": #inf 043051920299
                    self.show_windows.append(self.ui.label_infrared)
                    self.frameRates_label.append(self.ui.label_frameRates_inf)

                elif DevInfo.GetSn() == "043051920299": #8 044011420148
                    self.show_windows.append(self.ui.label_infrared)
                    self.frameRates_label.append(self.ui.label_frameRates_inf)


                process = Process(target=run_camera, args=(DevInfo,child_conn,stop_event,self.NS,record_event,self.frameRates,self.ROI))
                process.daemon = True  # <--- [添加] 设置为守护进程，确保主程序退出时子进程也退出
                process.start()
                self.parent_conns.append(parent_conn)
                self.stop_events.append(stop_event)
                self.record_events.append(record_event) # <--- [添加] 将Event存入列表
                self.processes.append(process)
                time.sleep(1)



            except mvsdk.CameraException as e:
                print("Camera {} Init Failed({}): {}".format(i,e.error_code, e.message))
                return


        # #realsence相机########################################################################################
        # try:
        #     # 创建context对象
        #     ctx = rs.context()
        #
        #     # 列出所有连接的设备
        #     devices = ctx.query_devices()
        #
        #     # 检查是否有连接的设备
        #     if len(devices) > 0:
        #         print("找到了RealSense设备。")
        #
        #         parent_conn, child_conn = Pipe()  # 设置管道
        #         parent_conn_2, child_conn_2 = Pipe()  # 设置管道
        #         stop_event = Event()  # 设置停止event
        #         print("realsence设备")
        #         # 记录每个设备的储存标志位 0显示 1缓存后保存
        #         self.record_save["realsence"] = 0
        #         # 每个相机的帧率
        #         self.frameRates["realsence"] = 0
        #         # self.frameRates["realsence_Depth"] = 0
        #
        #
        #
        #         process = Process(target=runRealsence,
        #                           args=(child_conn,child_conn_2, stop_event, self.NS, self.record_save, self.frameRates))
        #         process.start()
        #
        #         self.show_windows.append(self.ui.label_realsense_RGB)
        #         self.show_windows.append(self.ui.label_realsense_Depth)
        #         self.frameRates_label.append(self.ui.label_frameRates_realsnece_1)
        #         self.frameRates_label.append(self.ui.label_frameRates_realsnece_2)
        #
        #         self.parent_conns.append(parent_conn)
        #         self.parent_conns.append(parent_conn_2)
        #         self.stop_events.append(stop_event)
        #         self.processes.append(process)
        #
        # except Exception as e:
        #     print("Exception", e)
        #     print("Process realsence failed")
        # time.sleep(1)

        # print("parent_conns:", len(self.parent_conns))
        #事件相机########################################################################################
        try:
            cameras = dv.io.discoverDevices()
            if len(cameras) > 0:
                print("找到了事件相机设备。")
                parent_conn, child_conn = Pipe()  # 设置管道
                record_event = Event() # <--- [添加]
                stop_event = Event()  # 设置停止event
                print("事件相机")
                # 记录每个设备的储存标志位 0显示 1缓存后保存
                self.record_save["event"] = 0
                # 每个相机的帧率
                self.frameRates["event"] = 0

                process = Process(target=runEventCamera, args=(child_conn, stop_event, self.NS, record_event, self.frameRates))
                process.daemon = True  # <--- [添加] 设置为守护进程，确保主程序退出时子进程也退出
                process.start()

                self.show_windows.append(self.ui.label_event)
                self.frameRates_label.append(self.ui.label_frameRates_event)

                self.parent_conns.append(parent_conn)
                self.record_events.append(record_event) # <--- [添加]
                self.stop_events.append(stop_event)
                self.processes.append(process)

        except Exception as e:
            # print("Exception", e)
            print("Process event failed")

        # #ZED相机########################################################################################
        try:
            parent_conn, child_conn = Pipe()  # 设置管道
            parent_conn_2, child_conn_2 = Pipe()  # 设置管道
            record_event = Event() # <--- [添加]
            stop_event = Event()  # 设置停止event
            print("ZED设备")
            # 记录每个设备的储存标志位 0显示 1缓存后保存
            self.record_save["ZED"] = 0
            # 每个相机的帧率
            self.frameRates["ZED"] = 0

            process = Process(target=runZED, args=(child_conn, child_conn_2, stop_event, self.NS, record_event, self.frameRates))
            process.daemon = True  # <--- [添加] 设置为守护进程，确保主程序退出时子进程也退出
            process.start()

            self.show_windows.append(self.ui.label_Stereo)
            self.show_windows.append(self.ui.label_Depth)
            self.frameRates_label.append(self.ui.label_frameRates_Stereo)
            # self.frameRates_label.append(self.ui.label_frameRates_ZED_2)

            self.parent_conns.append(parent_conn)
            self.parent_conns.append(parent_conn_2)

            self.record_events.append(record_event) # <--- [添加]
            self.stop_events.append(stop_event)
            self.processes.append(process)

        except Exception as e:
            # print("Exception", e)
            print("Process ZED failed")

        #音频#################################################################################################
        self.NS_audio = Manager().Namespace()
        self.NS_audio.audio_start = False
        self.NS_audio.audio_stop = False
        self.NS_audio.audio_saved = False
        process = Process(target=run_audio,
                          args=(self.NS_audio,))
        process.start()



        self.sample_update(0)




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
            # print("user_ids:", self.user_ids)
    def init_UI(self):
        #初始化UI
        #图标        #自适应大小
        self.ui.label_scut.setPixmap(QPixmap("./sys_img/scut.jpg"))
        self.ui.label_BIP.setPixmap(QPixmap("./sys_img/biplab.jpg"))

    def sample_frame_changed(self):
        try:
            self.NS.sample_frame = int(self.ui.lineEdit_sample_frame.text())
            print('将采样帧数改成了{}'.format(self.NS.sample_frame))
        except:
            return

    def select_path(self):
        self.fpath = QFileDialog.getExistingDirectory(self, "选择保存视频的根目录", "../")
        if self.fpath == '':
            QMessageBox.warning(self, "Warning", "请选择需要保存的路径")
            return
        self.ui.lineEdit_sample_save_path.setText(self.fpath)
        print('保存路径为{}'.format(self.fpath))
        self.information_csv_path = os.path.join(self.fpath, 'user_info.csv')
        self.init_csv()

    def ID_changed(self):
        self.ID = self.ui.lineEdit_ID.text()
        print('ID为{}'.format(self.ID))

    def sample_time_changed(self):
        self.sample_time = self.ui.lineEdit_NUM.text()
        print('第{}次采样'.format(self.sample_time))

    def gesture_type_changed(self):
        self.gesture_type = self.ui.lineEdit_gesture_type.text()
        print('类别为{}'.format(self.gesture_type))

    def lr_changed(self):
        self.lr = self.ui.lineEdit_lr.text()
        print('左右为{}'.format(self.lr))

    def session_changed(self):
        self.session = self.ui.lineEdit_session.text()
        print('时期为{}'.format(self.session))

    def sex_changed(self):
        self.sex = self.ui.comboBox_sex.currentText()
        print('性别为{}'.format(self.sex))

    def age_changed(self):
        self.age = self.ui.lineEdit_age.text()
        print('年龄为{}'.format(self.age))

    def name_changed(self):
        # self.name = self.ui.lineEdit_name.text()
        print('姓名为{}'.format(self.name))

    def continue_flag(self):
        self.continue_f= not self.continue_f
        self.timer_continue.stop()
        if self.continue_f==False:
            self.ui.pushButton_continue.setText("当前是间断采集")
            self.ui.pushButton_regist.setEnabled(True)
        else:
            self.ui.pushButton_continue.setText("当前是连续采集")




    def update_frames(self):
        self.fakeTime+=1
        #从管道里面读取数据，初始化的时候管道和show_label是一一对应的
        # try:
        for i, parent_conn in enumerate(self.parent_conns):
            # print("i:", i)
            # print("parent_conn:", parent_conn.poll())
            if parent_conn.poll():
                # print("i:", i)

                frame = parent_conn.recv()
                # print("frame:", frame.shape)
                if i < len(self.show_windows):
                    frame = cv2.resize(frame, (self.show_windows[i].width(), self.show_windows[i].height()))

                    frame = QImage(frame, self.show_windows[i].width(),self.show_windows[i].height(),self.show_windows[i].width()*3, QImage.Format_RGB888)
                    img = QPixmap.fromImage(frame)
                    # if self.show_windows[i].width()>300:
                    #     print("show_windows[i].width():", self.show_windows[i].width())
                    self.show_windows[i].setPixmap(img)
                if i <len(self.DevList):
                    # print("帧率：{:.2f}".format(self.frameRates[self.DevList[i].GetSn()]))
                    self.frameRates_label[i].setText("帧率：{:.2f}".format(self.frameRates[self.DevList[i].GetSn()]))
                elif i<len(self.frameRates_label):
                    self.frameRates_label[i].setText("帧率：{:.2f}".format(self.frameRates["ZED"])) # 没理清楚pipe数量和label数量
                    pass


        # if self.fakeTime%500==0:
            # for i, DevInfo in enumerate(self.DevList):
            #     if self.record_save[DevInfo.GetSn()] == 0: # 不在记录
            #         self.ui.pushButton_regist.setEnabled(True)  # 启用注册按钮
            # else:
                # self.ui.pushButton_regist.setEnabled(False)  # 禁用注册按钮
        # print(self.fakeTime)
        if int(self.NS.sampled*100)%10==0 and int(self.NS.sampled*100)!=0 :
            # print("sampled:", int(self.NS.sampled*100))
            self.ui.progressBar.setValue(int(self.NS.sampled*100))
            if int(self.NS.sampled*100)==100:
                self.NS.sampled=0
                self.NS_audio.audio_stop=True


        if self.NS.ZED_saved== True:
            # QMessageBox.warning(self, "Warning", "本次采集完成")
            self.NS_audio.audio_saved=True
            self.ui.textBrowser_log.append("本次采集完成")
            self.NS.ZED_saved=False
            self.analyze()
            self.sample_update(1)


        # except Exception as e:
        #     print("Exception:", e)
        #     print("update_frames failed")
        #     pass

    #
    # def sync_client(self, host_b, port=65431, id_dir="1_0_999_0_0", num_frames=0):
    #     """向B电脑发送同步指令"""
    #     # 计算开始时间（当前时间 + 延迟）
    #     start_time = 0
    #     print("连接第一阶段")
    #     # 连接到B电脑
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #         print("连接第二阶段")
    #         s.connect((host_b, port))
    #         print(f"已连接到 {host_b}:{port}")
    #
    #         # 发送指令：id_dir,start_time,num_frames
    #         message = f"{id_dir},{start_time},{num_frames}"
    #         s.sendall(message.encode())
    #         print(f"已发送同步指令: {message}")


    def analyze(self):
        self.ui.textBrowser_log.clear()
        self.ui.textBrowser_log.append("以下为统计信息：")
        img_path = self.fpath + '/img'
        sample=self.session + "_" +  self.ID+ "_" + self.lr + "_" + self.gesture_type + "_" + self.sample_time
        # HOST_B = "192.168.1.119"  # B电脑的IP地址

        # print("开始发送目录")
        # self.sync_client(host_b=HOST_B, id_dir=sample)
        # print("发送完毕")

        self.ui.textBrowser_log.append(sample)
        self.save_id_path = img_path + '/' + sample

        if os.path.exists(self.save_id_path):
            # 统计id下对数据数量
            modalities = os.listdir(self.save_id_path)
            for modality in modalities:
                modality_path = self.save_id_path + "/" + modality
                imgs=os.listdir(modality_path)
                self.ui.textBrowser_log.append(modality+" : "+str(len(imgs)))

    # 定义排序的键函数
    def sort_key(self,sample_name):
        # 按照文件名的格式分割字符串
        parts = sample_name.split('_')
        # print(parts,"#####################################")
        # 提取文件名中的各个部分并转换为整数
        session = int(parts[0])
        lr = int(parts[2])
        ID = int(parts[1])
        gesture_type = int(parts[3])
        sample_time = int(parts[4])

        # 计算排序的键值
        key_value = (session + 1) * 1000000 + (ID + 1) * 100000 + (lr + 1) * 10000 + (gesture_type + 1) * 100 + (
                    sample_time + 1)
        return key_value

    def sample_update(self,flag):
        # self.session + "_" + self.lr + "_" + self.ID + "_" + self.gesture_type + "_" + self.sample_time
        if flag==0:
            img_path = self.fpath + '/img'
            samples=os.listdir(img_path)
            # 按照计算的键值进行降序排序
            samples.sort(key=self.sort_key, reverse=True)

            if len(samples)>0:

                sample_newest=samples[0]

                # 按照文件名的格式分割字符串
                parts = sample_newest.split('_')
                # 提取文件名中的各个部分并转换为整数
                session = parts[0]
                lr = parts[2]
                ID = parts[1]
                gesture_type = parts[3]
                sample_time = parts[4]

                self.ui.lineEdit_session.setText(session)
                self.ui.lineEdit_lr.setText(lr)
                self.ui.lineEdit_ID.setText(ID)
                self.ui.lineEdit_gesture_type.setText(gesture_type)
                self.ui.lineEdit_NUM.setText(sample_time)


                self.ID = self.ui.lineEdit_ID.text()
                self.lr = self.ui.lineEdit_lr.text()
                self.session = self.ui.lineEdit_session.text()
                self.gesture_type = self.ui.lineEdit_gesture_type.text()
                self.sample_time = self.ui.lineEdit_NUM.text()

        elif flag==1:

            print("######################################")
            if self.session=="1":
                if self.sample_time=="4":
                    self.sample_time="0"
                    self.ui.pushButton_regist.setEnabled(True)
                    if self.gesture_type=="10":
                        self.gesture_type="0"
                        if self.lr=="1":
                            self.lr="0"
                            self.ID = str(int(self.ID) + 1)

                        else:
                            self.lr="1"
                    else:
                        self.gesture_type=str(int(self.gesture_type)+1)
                else:
                    self.sample_time=str(int(self.sample_time)+1)
                    self.timer_continue.start(4000)
            elif self.session=="2" or self.session=="3":
                if self.gesture_type=="10":
                    self.gesture_type="0"
                    self.ui.pushButton_regist.setEnabled(True)
                    if self.sample_time == "5":
                        self.sample_time = "0"
                        if self.lr=="1":
                            self.lr="0"
                            self.ID = str(int(self.ID) + 1)

                        else:
                            self.lr="1"
                    else:
                        self.sample_time=str(int(self.sample_time)+1)
                else:
                    self.gesture_type=str(int(self.gesture_type)+1)
                    self.timer_continue.start(4000)


            # self.ui.lineEdit_session.setText(session)
            self.ui.lineEdit_lr.setText(self.lr)
            self.ui.lineEdit_ID.setText(self.ID)
            self.ui.lineEdit_gesture_type.setText(self.gesture_type)
            self.ui.lineEdit_NUM.setText(self.sample_time)




    def continue_record(self):
        self.timer_continue.stop()
        if self.continue_f==True:
            self.regist()






    def add_id(self):
        if self.ID in self.user_ids:
            return
        else:
            user_data = pd.read_csv(self.information_csv_path, dtype=str)
            new_item = {"name": self.name, "id": self.ID, "性别": self.sex, "年龄": self.age}
            new_item = pd.DataFrame(new_item,index=[0])
            user_data = pd.concat([user_data, new_item])
            user_data.to_csv(self.information_csv_path, index=None)
            self.user_ids.append(self.ID)


    # def sync_client_start(self, host_b, port=65432, id_dir="1_0_999_0_0", num_frames=120, delay=5.0):
    #     print("这是sync_client_start函数")
    #     """向B电脑发送同步指令"""
    #     # 计算开始时间（当前时间 + 延迟）
    #     start_time = time.time() + delay
    #
    #     # 连接到B电脑
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #         s.connect((host_b, port))
    #         print(f"已连接到 {host_b}:{port}")
    #
    #         # 发送指令：id_dir,start_time,num_frames
    #         message = f"{id_dir},{start_time},{num_frames}"
    #         s.sendall(message.encode())
    #         print(f"已发送同步指令: {message}")

        # 在此处添加A电脑自己的摄像头采集代码
        # 确保在相同的start_time开始采集
        # print(f"A电脑将在 {delay} 秒后开始采集...")


    def regist(self):
        #检查信息是否完整
        if self.name=='' or self.sex=='' or self.age=='' or self.ID=='' or self.lr=='' or self.session=='' or self.gesture_type=='' or self.sample_time=='':
            QMessageBox.warning(self, "Warning", "当前用户信息不全，请重新填写")
            return

        img_path = self.fpath + '/img'
        if not os.path.isdir(img_path):
            os.makedirs(img_path)

        #检查是否注册过
        self.save_id_path=img_path+'/'+self.session+"_"+self.ID+"_"+self.lr+"_"+self.gesture_type+"_"+self.sample_time
        if os.path.exists(self.save_id_path):
            del_or_not = QMessageBox.warning(self, "Warning", "已注册，点击确定将重新注册，是否继续？", QMessageBox.Yes | QMessageBox.No,
                                             QMessageBox.Yes)
            if del_or_not == QMessageBox.No:
                return

        self.ui.pushButton_regist.setEnabled(False) #暂时禁用注册按键

        self.NS_audio.audio_start=True
        # # 配置参数
        # HOST_B = "192.168.1.119"  # B电脑的IP地址
        # NUM_FRAMES = 120  # 采集帧数
        # DELAY = 3  # 延迟时间（秒）
        # print("开始发送采集!!!!!!!!")
        # self.sync_client_start(host_b=HOST_B, num_frames=NUM_FRAMES, delay=DELAY)

        if not os.path.isdir(self.save_id_path):
            os.makedirs(self.save_id_path)

        self.NS.save_id_path=self.save_id_path

        self.timer_record.start(3700) # 播音预计时长


        # if self.NS_audio.audio_start == False:

    def record_flag(self):
        #等待播音结束，开始采集
        self.ui.pushButton_regist.setEnabled(False)
        self.timer_record.stop()




        for devInfo in self.DevList:
            self.record_save[devInfo.GetSn()] = 1

        # self.ui.pushButton_regist.setEnabled(False) # 禁用注册按钮

        self.record_save["realsence"] = 1

        self.record_save["event"] = 1

        self.record_save["ZED"] = 1

        for event in self.record_events:
            event.set()

        # self.timer_fault.start(2000)
        # print("timer start")
        self.add_id()


    def del_sample(self):
        #检查信息是否完整
        if self.name=='' or self.sex=='' or self.age=='' or self.ID=='' or self.lr=='' or self.session=='' or self.gesture_type=='' or self.sample_time=='':
            QMessageBox.warning(self, "Warning", "信息不全，请重新填写")
            return

        img_path = self.fpath + '/img'
        sample=self.session+"_"+self.ID+"_"+self.lr+"_"+self.gesture_type+"_"+self.sample_time
        self.del_id_path=img_path+'/'+sample
        if os.path.exists(self.del_id_path):
            del_or_not = QMessageBox.warning(self, "Warning", "点击确定将删除样本“{}”，是否继续？".format(sample), QMessageBox.Yes | QMessageBox.No,
                                             QMessageBox.Yes)
            if del_or_not == QMessageBox.No:
                return
            else:
                shutil.rmtree(self.del_id_path)

                print("删除样本成功")
                self.sample_update(0)

                # #检查是否还有该ID的样本,没有则删除ID信息
                # id_left= False
                # samples= os.listdir(img_path)
                # for sample in samples:
                #     if sample.split('_')[1]==self.ID:
                #         id_left=True
                #         break

                # if id_left==False:
                #     df = pd.read_csv(self.information_csv_path, dtype=str)
                #     for i in range(df.shape[0]):
                #         if df.values[i, 1] == self.ID:
                #             df.drop(df.index[i], inplace=True)
                #             df.to_csv(self.information_csv_path, index=False)

                QMessageBox.information(self, "Information", "删除成功")

        else:
            QMessageBox.warning(self, "Warning", "未注册，请检查信息是否正确")
            return

    #
    # def time_out(self):
    #     print("time out")
    #     for thread in self.threads:
    #         thread.save = 1
    #     self.timer_fault.stop()

    # def show_frame(self, lst):
    #     frame = lst[0]
    #     label = lst[1]
    #     frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #     frame = cv2.resize(frame, (self.label_RGB_height, self.label_RGB_width))
    #     frame = QImage(frame, self.label_RGB_height, self.label_RGB_width, QImage.Format_RGB888)
    #     img = QPixmap.fromImage(frame)
    #     label.setPixmap(img)

    def closeEvent(self, event):
        self.timer_imshow.stop()
        self.timer_record.stop()
        self.timer_continue.stop()
        # print("close")
        for stop_event in self.stop_events:
            if stop_event is not None:#<-- new
            stop_event.set()
        time.sleep(0.5)
        #关闭管道，防止卡死
        for parent_conns in self.parent_conns:
            if parent_conns is not None:
            try:
                parent_conns.close()
            except:
                pass
        # time.sleep(5)
        # print("close")

        # for process in self.processes:
        #     process.join()
        #     print("close")
        # 尝试优雅地终止进程，但设置超时
        for i, process in enumerate(self.processes):
            if process is not None and process.is_alive():
                try:
                    process.join(timeout=1.0)
                    if process.is_alive():
                        self.ui.textBrowser_log.append(f"强制终止进程 {i}")
                        process.terminate()
                except:
                    pass
        # 最后再检查是否有任何进程仍然活着
        time.sleep(0.5)
        for process in self.processes:
            if process is not None and process.is_alive():
                process.kill()  # 最后的手段
        event.accept()
        # print("close")



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Main_Window()
    window.show()
    sys.exit(app.exec_())