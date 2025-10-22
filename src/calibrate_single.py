import cv2
import numpy as np
import os

# 参数设置
square_size = 1.0  # 单位：厘米，根据实际情况调整
board_width = 11  # 棋盘格的宽度（角点数）
board_height = 8  # 棋盘格的高度（角点数）

# 准备对象点，即棋盘格上的角点在世界坐标系中的坐标（对于平面标定，所有角点z坐标相同）
objp = np.zeros((board_height * board_width, 3), np.float32)
objp[:, :2] = np.mgrid[0:board_width, 0:board_height].T.reshape(-1, 2) * square_size

# 存储所有图像的角点以及对应的对象点
objpoints = []  # 3d点在真实世界的坐标
imgpoints = []  # 2d点在图像中的坐标

# 定义 cornerSubPix 的迭代终止条件
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# 读取同路径下1_1_4_1_1文件夹的所有图片
folder_path = "./1_1_4_1_1/"  # 文件夹路径
camera_path = "RGB_1"
folder_path = folder_path + camera_path
images = []  # 用于存储图片

# 遍历文件夹中的所有文件
file_names = sorted(os.listdir(folder_path))  # 获取文件夹中的所有文件名，并排序
step = 10  # 每隔10张图片读取一张
for i in range(0, len(file_names), step):
    file_name = file_names[i]
    file_path = os.path.join(folder_path, file_name)  # 拼接完整的文件路径
    img = cv2.imread(file_path)  # 读取图片
    if img is not None:
        images.append(img)

# 检查是否成功读取图片
if not images:
    print("未找到任何图片，请检查文件夹路径和图片格式！")
else:
    print(f"成功读取 {len(images)} 张图片。")

# 读取图片并找到棋盘格角点
success_count = 0  # 用于统计成功检测到角点的图片数量
for img in images:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, (board_width, board_height), None)
    if ret:
        objpoints.append(objp)
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners2)
        success_count += 1  # 成功检测到角点的图片数量加1
        # 可选：在图像上绘制角点，便于检查标定质量
        cv2.drawChessboardCorners(img, (board_width, board_height), corners2, ret)
        cv2.imshow('Detected Corners', img)
        cv2.waitKey(500)
        cv2.destroyAllWindows()

# 打印成功检测到角点的图片数量
print(f"成功检测到角点的图片数量：{success_count} 张")

# 检查objpoints和imgpoints是否为空
if not objpoints or not imgpoints:
    print("没有成功检测到棋盘格角点，请检查棋盘格是否清晰可见，或者调整棋盘格参数！")
else:
    # 标定相机
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

    # 打印结果
    print("Camera matrix（相机矩阵）: \n")
    print(mtx)
    print("Distortion coefficients （畸变系数）: \n")
    print(dist)
    print("Rotation Vectors （旋转向量）: \n")
    print(rvecs)
    print("Translation Vectors （平移向量）: \n")
    print(tvecs)

    # 保存相机参数到文件
    save_dir = "./camera_parameter"  # 保存目录
    os.makedirs(save_dir, exist_ok=True)  # 创建保存目录（如果不存在）
    save_path = os.path.join(save_dir, f"{camera_path}.txt")  # 文件名以 camera_path 命名

    with open(save_path, "w") as f:
        f.write(f"Camera Parameters for {camera_path}:\n\n")
        f.write("Camera matrix:\n")
        f.write(str(mtx) + "\n\n")
        f.write("Distortion coefficients:\n")
        f.write(str(dist) + "\n\n")
        f.write("Rotation Vectors:\n")
        f.write(str(rvecs) + "\n\n")
        f.write("Translation Vectors:\n")
        f.write(str(tvecs) + "\n")

    print(f"相机参数已保存到 {save_path}")