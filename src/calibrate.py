import cv2

import numpy as np

# 参数设置

square_size = 1.0 # 单位：厘米，根据实际情况调整

board_width = 12 # 棋盘格的宽度（格子数）

board_height = 9 # 棋盘格的高度（格子数）

# 准备对象点，即棋盘格上的角点在世界坐标系中的坐标（对于平面标定，所有角点z坐标相同）

objp = np.zeros((board_height * board_width, 3), np.float32)

objp[:, :2] = np.mgrid[0:board_width, 0:board_height].T.reshape(-1, 2) * square_size

# 存储所有图像的角点以及对应的对象点

objpoints = [] # 3d点在真实世界的坐标

imgpoints = [] # 2d点在图像中的坐标

# 读取图片并找到棋盘格角点


for img in images:

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    ret, corners = cv2.findChessboardCorners(gray, (board_width, board_height), None)

    if ret:

        objpoints.append(objp)

        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

        imgpoints.append(corners2)

        # 可选：在图像上绘制角点，便于检查标定质量

        cv2.drawChessboardCorners(img, (board_width, board_height), corners2, ret)

        cv2.imshow('img', img)

        cv2.waitKey(500)

        cv2.destroyAllWindows()

# 标定相机

ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

# 打印结果

print("Camera matrix : \n")

print(mtx)

print("Distortion coefficients : \n")

print(dist)

print("Rotation Vectors : \n")

print(rvecs)

print("Translation Vectors : \n")

print(tvecs)