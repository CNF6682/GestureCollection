import cv2
import numpy as np


def estimate_depth(left_img, right_img, output_path=None):
    """
    从左右相机图像估计深度图

    参数:
        left_img: 左相机图像 (RGB)
        right_img: 右相机图像 (RGB)
        output_path: 深度图保存路径 (可选)

    返回:
        depth_map: 估计的深度图
    """
    # 转换为灰度图像
    left_gray = cv2.cvtColor(left_img, cv2.COLOR_BGR2GRAY)
    right_gray = cv2.cvtColor(right_img, cv2.COLOR_BGR2GRAY)

    # 立体匹配参数设置
    window_size = 5
    min_disp = 0
    num_disp = 64 - min_disp

    # 创建StereoSGBM对象
    stereo = cv2.StereoSGBM_create(
        minDisparity=min_disp,
        numDisparities=num_disp,
        blockSize=window_size,
        P1=8 * 3 * window_size ** 2,
        P2=32 * 3 * window_size ** 2,
        disp12MaxDiff=1,
        uniquenessRatio=10,
        speckleWindowSize=100,
        speckleRange=32
    )

    # 计算视差图
    disparity = stereo.compute(left_gray, right_gray).astype(np.float32) / 16.0

    # 将视差转换为深度
    # 假设的相机参数 (实际应用中应该通过标定得到)
    f = 0.95 #0.8 * left_img.shape[1]  # 假设焦距为图像宽度的80%
    b = 0.12 # 0.1 * left_img.shape[1]  # 假设基线距离为图像宽度的10%

    # 避免除以零
    disparity[disparity == 0] = 0.1

    # 计算深度
    depth_map = (f * b) / disparity

    # 归一化深度图用于显示
    depth_map_normalized = cv2.normalize(depth_map, None, 0, 255, cv2.NORM_MINMAX)
    depth_map_normalized = np.uint8(depth_map_normalized)

    # 应用颜色映射
    depth_colormap = cv2.applyColorMap(depth_map_normalized, cv2.COLORMAP_JET)

    # 保存结果
    if output_path:
        cv2.imwrite(output_path, depth_colormap)

    return depth_colormap


def split_and_process(image_path, output_path=None):
    """
    处理包含左右图像的单个图像文件

    参数:
        image_path: 包含左右图像的单个图像文件路径
        output_path: 深度图保存路径 (可选)

    返回:
        depth_map: 估计的深度图(彩色)
    """
    # 读取图像
    combined_img = cv2.imread(image_path)
    if combined_img is None:
        raise ValueError("无法加载图像，请检查路径是否正确")

    # 分割左右图像
    height, width = combined_img.shape[:2]
    left_img = combined_img[:, :width // 2]
    right_img = combined_img[:, width // 2:]

    # 估计深度
    depth_colormap = estimate_depth(left_img, right_img, output_path)

    # 调整图像大小以便显示
    display_width = 800
    scale = display_width / width
    display_height = int(height * scale)

    # 调整图像大小
    left_display = cv2.resize(left_img, (display_width // 2, display_height))
    right_display = cv2.resize(right_img, (display_width // 2, display_height))
    depth_display = cv2.resize(depth_colormap, (display_width // 2, display_height))

    # 创建组合图像
    top_row = np.hstack((left_display, right_display))
    bottom_row = np.hstack((depth_display, np.zeros_like(depth_display)))
    combined_display = np.vstack((top_row, bottom_row))

    # 添加文字说明
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(combined_display, "Left Image", (10, 30), font, 0.7, (255, 255, 255), 2)
    cv2.putText(combined_display, "Right Image", (display_width // 2 + 10, 30), font, 0.7, (255, 255, 255), 2)
    cv2.putText(combined_display, "Depth Map", (10, display_height + 30), font, 0.7, (255, 255, 255), 2)

    # 显示结果
    cv2.imshow("Stereo Depth Estimation", combined_display)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return depth_colormap


# 使用示例
if __name__ == "__main__":
    # 替换为你的图像路径
    input_image = f"data/img/1_1_1_1_1/ZED_RGB/001.jpg"
    output_depth = "depth_map.png"

    # 处理图像
    depth_map = split_and_process(input_image, output_depth)