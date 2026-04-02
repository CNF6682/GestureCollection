import os
import re
import cv2
import numpy as np
from time import time


def check_folders():
    base_dir = r"E:\dataset\img"
    # base_dir = r"F:\dataset\img"

    # 定义预期的子文件夹及其文件数量
    SUBFOLDERS_REQUIREMENTS = {
        "events": 1,
        "inf": 240,
        "RGB_1": 240,
        "RGB_2": 240,
        "RGB_3": 240,
        "RGB_4": 240,
        "RGB_5": 240,
        "RGB_6": 240,
        "RGB_7": 240,
        "ZED_Depth": 120,
        "ZED_RGB": 120
    }

    # 需要检查重复图片的文件夹
    DUPLICATE_CHECK_FOLDERS = [
        "inf", "RGB_1", "RGB_2", "RGB_3", "RGB_4", "RGB_5", "RGB_6", "RGB_7","ZED_RGB"
    ]

    print("🎯 文件夹完整性检查程序")
    print(f"📁 检查目录: {base_dir}")
    print("🔍 格式: t_id_hand_gesture_num")
    print("📂 子文件夹要求:", ", ".join([f"{k}({v}文件)" for k, v in SUBFOLDERS_REQUIREMENTS.items()]))
    print("🔄 重复图片检查: 对比中间两张图片的中心100x100区域")
    print("💡 输入 'quit' 退出程序")
    print("=" * 70)

    while True:
        try:
            # 获取用户输入
            t_input = input("\n🟢 请输入 t (1、2或3): ")
            if t_input.lower() == 'quit':
                print("👋 再见！")
                break

            id_input = input("🟢 请输入 id: ")
            if id_input.lower() == 'quit':
                print("👋 再见！")
                break

            t1=time()
            t = int(t_input)
            id_val = int(id_input)

            # 定义预期的文件夹数量
            if t == 1:
                expected_num_range = range(0, 5)  # 0-4
                num_info = "0-4"
            elif t == 2 or t == 3:
                expected_num_range = range(0, 6)  # 0-5
                num_info = "0-5"
            else:
                print(f"❌ 错误：t的值只能是1或2，当前输入为 {t}")
                continue

            expected_hand_range = [0, 1]
            expected_gesture_range = range(0, 11)  # 0-10

            # 查找所有相关的文件夹
            pattern = re.compile(rf"^{t}_{id_val}_(\d+)_(\d+)_(\d+)$")
            found_folders = []
            naming_errors = []
            valid_folders = []
            subfolder_issues = []  # 存储子文件夹问题
            duplicate_issues = []  # 存储重复图片问题

            # 检查目录是否存在
            if not os.path.exists(base_dir):
                print(f"❌ 错误：目录 {base_dir} 不存在")
                continue

            print(f"\n🔍 正在检查 t={t}, id={id_val} 的文件夹...")

            for folder_name in os.listdir(base_dir):
                folder_path = os.path.join(base_dir, folder_name)
                if os.path.isdir(folder_path):
                    match = pattern.match(folder_name)
                    if match:
                        hand, gesture, num = map(int, match.groups())

                        # 检查命名规则
                        errors = []
                        if hand not in expected_hand_range:
                            errors.append(f"hand应为0或1，实际为{hand}")
                        if gesture not in expected_gesture_range:
                            errors.append(f"gesture应为0-10，实际为{gesture}")
                        if num not in expected_num_range:
                            errors.append(f"num应为{num_info}，实际为{num}")

                        if errors:
                            naming_errors.append(f"{folder_name} ({'; '.join(errors)})")
                        else:
                            # 检查子文件夹
                            subfolder_problems = check_subfolders(folder_path, SUBFOLDERS_REQUIREMENTS)

                            # 检查重复图片
                            duplicate_problems = check_duplicate_images(folder_path, DUPLICATE_CHECK_FOLDERS)

                            if subfolder_problems or duplicate_problems:
                                if subfolder_problems:
                                    subfolder_issues.append({
                                        'folder': folder_name,
                                        'problems': subfolder_problems
                                    })
                                if duplicate_problems:
                                    duplicate_issues.append({
                                        'folder': folder_name,
                                        'problems': duplicate_problems
                                    })

                            valid_folders.append(folder_name)
                            found_folders.append((hand, gesture, num))

            # 检查缺失的文件夹
            missing_folders = []
            for hand in expected_hand_range:
                for gesture in expected_gesture_range:
                    for num in expected_num_range:
                        if (hand, gesture, num) not in found_folders:
                            missing_folders.append(f"{t}_{id_val}_{hand}_{gesture}_{num}")

            # 输出结果
            print("\n" + "=" * 70)
            print(f"📊 检查结果: t={t}, id={id_val}")
            print(f"📋 预期格式: {t}_{id_val}_[0-1]_[0-10]_[{num_info}]")
            print("=" * 70)

            # 统计信息
            total_expected = len(expected_hand_range) * len(expected_gesture_range) * len(expected_num_range)
            total_found = len(valid_folders)

            print(f"✅ 找到的有效文件夹: {total_found}/{total_expected}")
            print(f"❌ 命名错误的文件夹: {len(naming_errors)}个")
            print(f"⚠️  缺失的文件夹: {len(missing_folders)}个")
            print(f"🔍 子文件夹有问题的: {len(subfolder_issues)}个")
            print(f"🔄 有重复图片的: {len(duplicate_issues)}个")
            print("-" * 50)

            if naming_errors:
                print("📛 命名规则错误的文件夹:")
                for error in naming_errors:
                    print(f"   🔸 {error}")

            if subfolder_issues:
                print(f"\n🔧 子文件夹有问题的文件夹 ({len(subfolder_issues)}个):")
                for issue in subfolder_issues:
                    print(f"   📂 {issue['folder']}:")
                    for problem in issue['problems']:
                        print(f"      ❗ {problem}")

            if duplicate_issues:
                print(f"\n🔄 有重复图片的文件夹 ({len(duplicate_issues)}个):")
                for issue in duplicate_issues:
                    print(f"   📂 {issue['folder']}:")
                    for problem in issue['problems']:
                        print(f"      🔄 {problem}")

            if missing_folders:
                print(f"\n❓ 缺失的文件夹 ({len(missing_folders)}个):")
                # 分组显示缺失的文件夹
                missing_by_hand = {}
                for folder in missing_folders:
                    parts = folder.split('_')
                    hand = parts[2]
                    if hand not in missing_by_hand:
                        missing_by_hand[hand] = []
                    missing_by_hand[hand].append(folder)

                for hand, folders in missing_by_hand.items():
                    print(f"   🖐️  hand={hand}: {len(folders)}个缺失")
                    # 每行显示5个，避免输出太长
                    for i in range(0, len(folders), 5):
                        print(f"      {', '.join(folders[i:i + 5])}")

            if not naming_errors and not missing_folders and not subfolder_issues and not duplicate_issues:
                print("\n🎉 完美！所有文件夹命名正确、完整且子文件夹齐全，无重复图片！")

            print("=" * 70)
            t2 = time()
            print("所花时间：{}s".format(round(t2 - t1, 2)))

        except ValueError:
            print("❌ 错误：请输入有效的数字")
        except KeyboardInterrupt:
            print("\n👋 程序已退出")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")


def check_subfolders(folder_path, subfolder_requirements):
    """检查指定文件夹的子文件夹是否符合要求"""
    problems = []

    for subfolder, expected_count in subfolder_requirements.items():
        subfolder_path = os.path.join(folder_path, subfolder)

        if not os.path.exists(subfolder_path):
            problems.append(f"缺失子文件夹: {subfolder}")
            continue

        if not os.path.isdir(subfolder_path):
            problems.append(f"{subfolder} 不是文件夹")
            continue

        # 计算子文件夹中的文件数量（排除子文件夹）
        try:
            file_count = 0
            for item in os.listdir(subfolder_path):
                item_path = os.path.join(subfolder_path, item)
                if os.path.isfile(item_path):
                    file_count += 1

            if file_count != expected_count:
                problems.append(f"{subfolder}: 预期 {expected_count} 文件，实际 {file_count} 文件")

        except PermissionError:
            problems.append(f"{subfolder}: 无权限访问")
        except Exception as e:
            problems.append(f"{subfolder}: 检查错误 - {str(e)}")

    return problems


def check_duplicate_images(folder_path, check_folders):
    """检查指定文件夹中是否有重复图片"""
    problems = []

    for subfolder in check_folders:
        subfolder_path = os.path.join(folder_path, subfolder)

        if not os.path.exists(subfolder_path) or not os.path.isdir(subfolder_path):
            continue

        # 获取所有图片文件
        image_files = []
        for file in os.listdir(subfolder_path):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                image_files.append(file)

        # 按文件名排序
        image_files.sort()

        # 检查是否有足够的图片
        if len(image_files) < 2:
            problems.append(f"{subfolder}: 图片数量不足，无法检查重复")
            continue

        # 取中间两张图片的索引
        mid_index = len(image_files) // 2
        img1_path = os.path.join(subfolder_path, image_files[mid_index - 1])
        img2_path = os.path.join(subfolder_path, image_files[mid_index])

        try:
            # 读取图片
            img1 = cv2.imread(img1_path)
            img2 = cv2.imread(img2_path)

            if img1 is None or img2 is None:
                problems.append(f"{subfolder}: 无法读取图片 {image_files[mid_index - 1]} 或 {image_files[mid_index]}")
                continue

            # 获取图片尺寸
            h1, w1 = img1.shape[:2]
            h2, w2 = img2.shape[:2]

            # 计算中心区域
            center_x1, center_y1 = w1 // 2, h1 // 2
            center_x2, center_y2 = w2 // 2, h2 // 2

            # # 提取中心100x100区域
            center_region1 = img1[center_y1 - 50:center_y1 + 50, center_x1 - 50:center_x1 + 50]
            center_region2 = img2[center_y2 - 50:center_y2 + 50, center_x2 -50:center_x2 + 50]



            # 检查区域尺寸是否一致
            if center_region1.shape != center_region2.shape:
                problems.append(f"{subfolder}: 中心区域尺寸不匹配")
                continue

            # 计算区域总和
            sum1 = np.sum(center_region1)
            sum2 = np.sum(center_region2)

            # 检查是否相同
            if sum1 == sum2:
                problems.append(
                    f"{subfolder}: 图片 {image_files[mid_index - 1]} 和 {image_files[mid_index]} 可能重复 (中心5x5区域总和相同: {sum1})")

        except Exception as e:
            problems.append(f"{subfolder}: 检查重复图片时出错 - {str(e)}")

    return problems


if __name__ == "__main__":
    check_folders()