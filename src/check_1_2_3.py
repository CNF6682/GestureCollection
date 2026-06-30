import os
import re
from PIL import Image
import hashlib


def check_folders():
    base_dir = r"H:\dataset\img"
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

    print("🎯 文件夹完整性检查程序")
    print(f"📁 检查目录: {base_dir}")
    print("🔍 格式: t_id_hand_gesture_num")
    print("📂 子文件夹要求:", ", ".join([f"{k}({v}文件)" for k, v in SUBFOLDERS_REQUIREMENTS.items()]))
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
                            if subfolder_problems:
                                subfolder_issues.append({
                                    'folder': folder_name,
                                    'problems': subfolder_problems
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

            # 执行图片一致性检查
            if valid_folders:
                print(f"\n🖼️  开始图片一致性检查...")
                image_consistency_issues = check_image_consistency(base_dir, valid_folders, SUBFOLDERS_REQUIREMENTS)

                if image_consistency_issues:
                    print(f"❌ 图片一致性检查发现 {len(image_consistency_issues)} 个问题:")
                    for issue in image_consistency_issues:
                        print(f"   🔸 {issue}")
                else:
                    print("✅ 图片一致性检查通过！")

            if not naming_errors and not missing_folders and not subfolder_issues:
                print("\n🎉 完美！所有文件夹命名正确、完整且子文件夹齐全！")

            print("=" * 70)

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


def check_image_consistency(base_dir, valid_folders, subfolder_requirements):
    """检查图片一致性，排除events文件夹"""
    issues = []

    # 排除events模态文件夹
    modalities_to_check = [modality for modality in subfolder_requirements.keys() if modality != "events"]

    for folder_name in valid_folders:
        folder_path = os.path.join(base_dir, folder_name)

        for modality in modalities_to_check:
            modality_path = os.path.join(folder_path, modality)

            if not os.path.exists(modality_path) or not os.path.isdir(modality_path):
                continue

            # 获取所有图片文件
            image_files = []
            for file in os.listdir(modality_path):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                    image_files.append(file)

            # 按数字排序（假设文件名包含数字）
            image_files.sort(key=lambda x: extract_number(x))

            if len(image_files) < 2:
                continue

            # 等间隔抽取5份
            total_images = len(image_files)
            sample_indices = []

            if total_images >= 10:
                # 如果图片足够多，等间隔抽取5个位置
                step = max(1, total_images // 5)
                sample_indices = [i * step for i in range(5)]
                sample_indices = sample_indices[:5]  # 确保不超过5个
            else:
                # 如果图片较少，从开始、中间、结束各取一些
                sample_indices = [0, total_images // 4, total_images // 2, 3 * total_images // 4, total_images - 2]
                sample_indices = [i for i in sample_indices if i < total_images - 1]
                sample_indices = sample_indices[:min(5, len(sample_indices))]

            # 检查每个抽样位置的连续两张图片
            for idx in sample_indices:
                if idx + 1 >= total_images:
                    continue

                img1_path = os.path.join(modality_path, image_files[idx])
                img2_path = os.path.join(modality_path, image_files[idx + 1])

                try:
                    if are_images_identical(img1_path, img2_path):
                        issue_msg = f"{folder_name}/{modality}: 图片 {image_files[idx]} 和 {image_files[idx + 1]} 相同"
                        issues.append(issue_msg)
                        print(f"   ⚠️  {issue_msg}")
                except Exception as e:
                    print(f"   💥 检查图片时出错 {folder_name}/{modality}/{image_files[idx]}: {e}")

    return issues


def extract_number(filename):
    """从文件名中提取数字用于排序"""
    numbers = re.findall(r'\d+', filename)
    return int(numbers[0]) if numbers else 0


def are_images_identical(img_path1, img_path2):
    """检查两张图片是否完全相同"""
    try:
        # 方法1: 文件哈希比较
        if get_file_hash(img_path1) == get_file_hash(img_path2):
            return True

        # 方法2: 图片内容比较
        with Image.open(img_path1) as img1, Image.open(img_path2) as img2:
            # 比较尺寸
            if img1.size != img2.size:
                return False

            # 比较像素数据
            return list(img1.getdata()) == list(img2.getdata())

    except Exception as e:
        print(f"   比较图片时出错: {img_path1} vs {img_path2} - {e}")
        return False


def get_file_hash(file_path):
    """计算文件的MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


if __name__ == "__main__":
    check_folders()