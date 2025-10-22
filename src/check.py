import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed


def check_folders():
    base_dir = r"E:\dataset\img"

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
    print("📁 检查目录: E:\\dataset\\img")
    print("🔍 格式: t_id_hand_gesture_num")
    print("📂 子文件夹要求:", ", ".join([f"{k}({v}文件)" for k, v in SUBFOLDERS_REQUIREMENTS.items()]))
    print("⚡ 使用多线程加速检查")
    print("💡 输入 'quit' 退出程序")
    print("=" * 70)

    while True:
        try:
            # 获取用户输入
            t_input = input("\n🟢 请输入 t (1或2): ")
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
            elif t == 2:
                expected_num_range = range(0, 6)  # 0-5
                num_info = "0-5"
            else:
                print(f"❌ 错误：t的值只能是1或2，当前输入为 {t}")
                continue

            expected_hand_range = [0, 1]
            expected_gesture_range = range(0, 11)  # 0-10

            # 检查目录是否存在
            if not os.path.exists(base_dir):
                print(f"❌ 错误：目录 {base_dir} 不存在")
                continue

            print(f"\n🔍 正在快速检查 t={t}, id={id_val} 的文件夹...")

            # 使用多线程并行处理文件夹检查
            pattern = re.compile(rf"^{t}_{id_val}_(\d+)_(\d+)_(\d+)$")
            naming_errors = []
            valid_folders_info = []  # 存储有效文件夹信息
            all_folders_to_check = []  # 存储需要检查的文件夹路径

            # 第一遍快速扫描：只检查文件夹命名
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
                            all_folders_to_check.append((folder_name, folder_path))

            # 使用多线程并行检查子文件夹
            subfolder_issues = []
            valid_folders = []

            if all_folders_to_check:
                print(f"⚡ 使用多线程检查 {len(all_folders_to_check)} 个文件夹的子文件夹...")

                with ThreadPoolExecutor(max_workers=8) as executor:
                    # 提交所有检查任务
                    future_to_folder = {
                        executor.submit(fast_check_subfolders, folder_path, SUBFOLDERS_REQUIREMENTS,
                                        folder_name): folder_name
                        for folder_name, folder_path in all_folders_to_check
                    }

                    # 收集结果
                    for future in as_completed(future_to_folder):
                        folder_name = future_to_folder[future]
                        try:
                            problems = future.result()
                            if problems:
                                subfolder_issues.append({
                                    'folder': folder_name,
                                    'problems': problems
                                })
                            else:
                                valid_folders.append(folder_name)
                        except Exception as e:
                            subfolder_issues.append({
                                'folder': folder_name,
                                'problems': [f"检查错误: {str(e)}"]
                            })

            # 构建找到的文件夹列表用于缺失检查
            found_folders = []
            for folder_name, _ in all_folders_to_check:
                parts = folder_name.split('_')
                if len(parts) >= 5:
                    try:
                        hand = int(parts[2])
                        gesture = int(parts[3])
                        num = int(parts[4])
                        found_folders.append((hand, gesture, num))
                    except:
                        pass

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
            total_found = len(all_folders_to_check)

            print(f"✅ 找到的文件夹: {total_found}/{total_expected}")
            print(f"❌ 命名错误的文件夹: {len(naming_errors)}个")
            print(f"⚠️  缺失的文件夹: {len(missing_folders)}个")
            print(f"🔍 子文件夹有问题的: {len(subfolder_issues)}个")
            print(f"✓ 完全正确的文件夹: {len(valid_folders)}个")
            print("-" * 50)

            if naming_errors:
                print("📛 命名规则错误的文件夹:")
                for error in naming_errors:
                    print(f"   🔸 {error}")

            if subfolder_issues:
                print(f"\n🔧 子文件夹有问题的文件夹 ({len(subfolder_issues)}个):")
                for issue in subfolder_issues[:5]:  # 只显示前5个问题
                    print(f"   📂 {issue['folder']}:")
                    for problem in issue['problems'][:3]:  # 只显示前3个问题
                        print(f"      ❗ {problem}")
                    if len(issue['problems']) > 3:
                        print(f"      ... 还有 {len(issue['problems']) - 3} 个问题")
                if len(subfolder_issues) > 5:
                    print(f"   ... 还有 {len(subfolder_issues) - 5} 个有问题的文件夹")

            if missing_folders:
                print(f"\n❓ 缺失的文件夹 ({len(missing_folders)}个):")
                # 只显示前10个缺失的文件夹
                for i, folder in enumerate(missing_folders[:10]):
                    print(f"   🔸 {folder}")
                if len(missing_folders) > 10:
                    print(f"   ... 还有 {len(missing_folders) - 10} 个缺失文件夹")

            # if valid_folders:
            #     print(f"\n✅ 完全正确的文件夹 ({len(valid_folders)}个):")
            #     for i, folder in enumerate(valid_folders[:5]):
            #         print(f"   ✓ {folder}")
            #     if len(valid_folders) > 5:
            #         print(f"   ... 还有 {len(valid_folders) - 5} 个正确文件夹")

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


def fast_check_subfolders(folder_path, subfolder_requirements, folder_name):
    """快速检查子文件夹 - 优化版本"""
    problems = []

    # 先快速检查所有子文件夹是否存在
    existing_subfolders = set()
    try:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                existing_subfolders.add(item)
    except Exception as e:
        return [f"无法读取文件夹: {str(e)}"]

    # 检查每个要求的子文件夹
    for subfolder, expected_count in subfolder_requirements.items():
        if subfolder not in existing_subfolders:
            problems.append(f"缺失: {subfolder}")
            continue

        subfolder_path = os.path.join(folder_path, subfolder)

        # 快速文件计数（不遍历所有文件，使用更高效的方法）
        try:
            # 使用listdir + isfile的快速计数
            file_count = 0
            for item in os.listdir(subfolder_path):
                if os.path.isfile(os.path.join(subfolder_path, item)):
                    file_count += 1
                    # 如果已经超过预期数量，提前退出
                    if file_count > expected_count:
                        break

            if file_count != expected_count:
                problems.append(f"{subfolder}: 需要{expected_count}个文件, 现有{file_count}个文件")

        except PermissionError:
            problems.append(f"{subfolder}: 无权限")
        except Exception as e:
            problems.append(f"{subfolder}: 错误 - {str(e)}")

    return problems


if __name__ == "__main__":
    check_folders()