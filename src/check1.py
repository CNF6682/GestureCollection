import os
import re


def check_folders():
    base_dir = r"E:\dataset\img"
    # base_dir = r"E:\datasettest\img"
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

            # # 显示完整的文件夹信息
            # if valid_folders and not subfolder_issues:
            #     print(f"\n✅ 完整的文件夹 ({len(valid_folders)}个):")
            #     valid_count = 0
            #     for folder in valid_folders:
            #         # 检查这个文件夹是否有子文件夹问题
            #         has_issue = any(issue['folder'] == folder for issue in subfolder_issues)
            #         if not has_issue:
            #             valid_count += 1
            #             if valid_count <= 10:  # 只显示前10个完整的文件夹
            #                 print(f"   ✓ {folder}")
            #     if valid_count > 10:
            #         print(f"   ... 还有 {valid_count - 10} 个完整文件夹")

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


if __name__ == "__main__":
    check_folders()