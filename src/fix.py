
import os
from tqdm import tqdm


folder_path=r"F:\dataset\img"
samples=os.listdir(folder_path)


# 遍历每个项目
for sample in tqdm(samples):
    # 检查是否是文件夹
    sample_path = os.path.join(folder_path, sample)
    if os.path.isdir(sample_path):
        # 分割文件夹名称
        parts = sample.split('_')
        if len(parts) == 5:  # 确保文件夹名称符合 x_y_z_l_m 的格式
            # 交换 y 和 z 的位置
            # 并重新组合成新的名称

            new_sample_name = f"{parts[0]}_{parts[2]}_{parts[1]}_{parts[3]}_{parts[4]}"
            new_sample_path = os.path.join(folder_path, new_sample_name)
            # 重命名文件夹
            os.rename(sample_path, new_sample_path)
            print(f"Renamed folder '{sample}' to '{new_sample_name}'")
        else:
            print(f"Skipped folder '{sample}' as it does not match the expected format.")
    else:
        print(f"Skipped item '{sample}' as it is not a folder.")