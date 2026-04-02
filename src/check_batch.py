import os
import re
from datetime import datetime

# ==================== 配置 ====================
# BASE_DIR = r"E:\dataset\img"
BASE_DIR = r"F:\dataset\img"

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

T_VALUES = [1, 2, 3]
ID_RANGE = range(1, 101)  # id: 1 ~ 100

OUTPUT_LOG_FILE = f"folder_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
# ==============================================


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

        try:
            file_count = sum(
                1 for item in os.listdir(subfolder_path)
                if os.path.isfile(os.path.join(subfolder_path, item))
            )

            if file_count != expected_count:
                problems.append(f"{subfolder}: 预期 {expected_count} 文件，实际 {file_count} 文件")

        except PermissionError:
            problems.append(f"{subfolder}: 无权限访问")
        except Exception as e:
            problems.append(f"{subfolder}: 检查错误 - {str(e)}")

    return problems


def check_folders_batch():
    """批量检查 t=1,2,3 和 id=1~100 的所有文件夹"""
    print("🚀 开始批量检查文件夹完整性...")
    print(f"📁 基础目录: {BASE_DIR}")
    print(f"📋 检查范围: t ∈ {T_VALUES}, id ∈ [{ID_RANGE.start}, {ID_RANGE.stop})")
    print(f"📝 报告将保存至: {OUTPUT_LOG_FILE}")

    if not os.path.exists(BASE_DIR):
        error_msg = f"❌ 错误：基础目录不存在: {BASE_DIR}"
        print(error_msg)
        with open(OUTPUT_LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(error_msg + "\n")
        return

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("📂 数据集文件夹完整性检查报告")
    report_lines.append(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"📁 检查路径: {BASE_DIR}")
    report_lines.append("=" * 80)
    report_lines.append("")

    total_combinations = len(T_VALUES) * len(ID_RANGE)
    processed = 0

    for t in T_VALUES:
        for id_val in ID_RANGE:
            processed += 1
            print(f"\r🔄 处理进度: {processed}/{total_combinations} (t={t}, id={id_val})...", end="", flush=True)

            # 确定 num 范围
            if t == 1:
                expected_num_range = range(0, 5)   # 0-4
                num_info = "0-4"
            else:  # t == 2 or t == 3
                expected_num_range = range(0, 6)   # 0-5
                num_info = "0-5"

            expected_hand_range = [0, 1]
            expected_gesture_range = range(0, 11)  # 0-10

            pattern = re.compile(rf"^{t}_{id_val}_(\d+)_(\d+)_(\d+)$")
            found_folders = []  # (hand, gesture, num)
            naming_errors = []
            subfolder_issues = []
            missing_folders = []

            folder_scan_root = BASE_DIR
            if not os.path.exists(folder_scan_root):
                report_lines.append(f"⚠️  t={t}, id={id_val} -> 目录 {folder_scan_root} 不存在")
                continue

            # 扫描匹配的文件夹
            for folder_name in os.listdir(folder_scan_root):
                folder_path = os.path.join(folder_scan_root, folder_name)
                if not os.path.isdir(folder_path):
                    continue

                match = pattern.match(folder_name)
                if match:
                    hand, gesture, num = map(int, match.groups())

                    # 命名验证
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
                        problems = check_subfolders(folder_path, SUBFOLDERS_REQUIREMENTS)
                        if problems:
                            subfolder_issues.append({
                                'folder': folder_name,
                                'problems': problems
                            })
                        found_folders.append((hand, gesture, num))

            # 检查缺失的组合
            for hand in expected_hand_range:
                for gesture in expected_gesture_range:
                    for num in expected_num_range:
                        if (hand, gesture, num) not in found_folders:
                            missing_folders.append(f"{t}_{id_val}_{hand}_{gesture}_{num}")

            # 收集当前 (t, id) 的结果
            total_expected = len(expected_hand_range) * len(expected_gesture_range) * len(expected_num_range)
            total_found = len(found_folders)
            missing_count = len(missing_folders)
            naming_error_count = len(naming_errors)
            subfolder_issue_count = len(subfolder_issues)

            has_problems = any([missing_count, naming_error_count, subfolder_issue_count])

            if not has_problems:
                continue  # 完美通过，不记录（可取消注释以记录全部）

            # 添加有问题的条目到报告
            section = []
            section.append(f"🔴 问题记录: t={t}, id={id_val}")
            section.append(f"   📋 格式: {t}_{id_val}_[0-1]_[0-10]_[{num_info}]")
            section.append(f"   ✅ 找到有效文件夹: {total_found}/{total_expected}")
            if naming_error_count:
                section.append(f"   ❌ 命名错误: {naming_error_count} 个")
                for err in naming_errors:
                    section.append(f"     🔹 {err}")
                # if len(naming_errors) > 5:
                #     section.append(f"     ... 还有 {len(naming_errors) - 5} 个命名错误")

            if subfolder_issue_count:
                section.append(f"   ⚠️  子文件夹问题: {subfolder_issue_count} 个")
                for issue in subfolder_issues:
                    section.append(f"     📂 {issue['folder']}:")
                    for problem in issue['problems']:
                        section.append(f"        ❗ {problem}")
                    # if len(issue['problems']) > 2:
                    #     section.append(f"        ... 还有 {len(issue['problems']) - 2} 个问题")
                # if len(subfolder_issues) > 3:
                #     section.append(f"     ... 还有 {len(subfolder_issues) - 3} 个有问题的文件夹")

            if missing_count:
                section.append(f"   ❗ 缺失文件夹: {missing_count} 个")
                # 分 hand 显示部分
                by_hand = {}
                for m in missing_folders:
                    hand = m.split('_')[2]
                    by_hand.setdefault(hand, []).append(m)
                for h, m_list in by_hand.items():
                    section.append(f"     🖐️  hand={h}: {len(m_list)} 个缺失")
                    # 列出最多前5个
                    for i in range(min(5, len(m_list))):
                        section.append(f"       {m_list[i]}")
                    if len(m_list) > 5:
                        section.append(f"       ... 还有 {len(m_list) - 5} 个未列出")

            section.append("")  # 空行分隔
            report_lines.extend(section)

    # 写入报告文件
    with open(OUTPUT_LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))

    print("\n✅ 所有检查完成！")
    print(f"📄 报告已保存至: {OUTPUT_LOG_FILE}")


if __name__ == "__main__":
    check_folders_batch()