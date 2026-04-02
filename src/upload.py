import os
import paramiko
from stat import S_ISDIR
import sys
from datetime import datetime
import time

# ------------------------ 配置参数 ------------------------
# 本地目标目录 (Windows 路径)
LOCAL_BASE_DIR = r"F:\dataset\img"  # <-- 修改为你的本地目录路径

# 远程服务器信息
REMOTE_HOST = "202.38.209.227"  # <-- 修改为远程服务器 IP 或域名
REMOTE_PORT = 2222  # <-- 修改为 SSH 端口 (通常 22)
REMOTE_USERNAME = "ps"  # <-- 修改为远程用户名
# 选择一种认证方式：
# 方式 1: 使用密码
REMOTE_PASSWORD = "biplab6666"  # <-- 修改为远程用户密码 (如果使用密码)
# 方式 2: 使用私钥文件 (推荐更安全)
# REMOTE_PKEY_PATH = r"C:\path\to\your\private_key.ppk"  # <-- 修改为你的私钥文件路径 (.ppk 或 .pem)
# REMOTE_PKEY_PASSPHRASE = "your_passphrase"      # <-- 如果私钥有密码短语，请填写

# 远程目标目录 (Linux 路径)
REMOTE_BASE_DIR = "/NewData/dataPart1/"  # <-- 修改为远程服务器上的目标目录

# 可选: 是否在远程服务器上为每个上传的文件夹创建同名父目录
CREATE_REMOTE_PARENT_DIR = True

# 日志文件路径
LOG_FILE = "upload_log.txt"

# 进度条宽度
PROGRESS_BAR_WIDTH = 50


# --------------------------------------------------------

class UploadProgress:
    """上传进度显示类"""

    def __init__(self, filename, filesize):
        self.filename = filename
        self.filesize = filesize
        self.transferred = 0
        self.start_time = datetime.now()

    def callback(self, transferred, total):
        """进度回调函数"""
        self.transferred = transferred
        self._update_progress()

    def _update_progress(self):
        """更新进度条"""
        # 计算进度百分比
        percent = min(100, (self.transferred / self.filesize) * 100)

        # 计算进度条
        filled_length = int(PROGRESS_BAR_WIDTH * self.transferred // self.filesize)
        bar = '█' * filled_length + '-' * (PROGRESS_BAR_WIDTH - filled_length)

        # 计算传输速度
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        speed = self.transferred / elapsed_time if elapsed_time > 0 else 0

        # 格式化大小显示
        def format_size(size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f}{unit}"
                size /= 1024.0
            return f"{size:.1f}TB"

        # 清除当前行并重新打印
        sys.stdout.write('\r')
        sys.stdout.write(f'{self.filename} |{bar}| {percent:6.2f}% '
                         f'[{format_size(self.transferred)}/{format_size(self.filesize)}] '
                         f'{format_size(speed)}/s')
        sys.stdout.flush()

        # 当传输完成时换行
        if self.transferred >= self.filesize:
            sys.stdout.write('\n')
            sys.stdout.flush()


def create_remote_dir_if_not_exists(sftp, remote_path):
    """检查远程路径是否存在，如果不存在则创建目录（包括父目录）"""
    try:
        sftp.stat(remote_path)
    except FileNotFoundError:
        print(f"远程目录不存在，正在创建: {remote_path}")
        try:
            sftp.mkdir(remote_path, mode=0o777)
            print(f"成功创建远程目录: {remote_path}")
        except Exception as mkdir_e:
            # mkdir 可能无法创建多级目录，尝试逐级创建
            parts = remote_path.strip('/').split('/')
            current_path = ''
            for part in parts:
                if part:  # 避免空字符串
                    current_path += '/' + part
                    try:
                        sftp.stat(current_path)
                    except FileNotFoundError:
                        try:
                            sftp.mkdir(current_path, mode=0o777)
                            print(f"成功创建远程目录: {current_path}")
                        except Exception as e:
                            print(f"创建远程目录失败 {current_path}: {e}")
                            raise
                    except Exception as e:
                        print(f"检查远程目录状态失败 {current_path}: {e}")
                        raise
    except Exception as e:
        print(f"检查远程目录状态失败 {remote_path}: {e}")
        raise


def upload_file_with_progress(sftp, local_file_path, remote_file_path):
    """上传文件并显示进度"""
    try:
        # 判断远程文件是否已存在且大小相同

        try:
            remote_file_attr = sftp.stat(remote_file_path)
            remote_file_size = remote_file_attr.st_size
            local_file_size = os.path.getsize(local_file_path)
            if remote_file_size == local_file_size:
                print(f"  跳过已存在且大小相同的文件: {local_file_path}")
                return True
        except FileNotFoundError:
            # 远程文件不存在，继续上传
            pass
        # 获取文件大小
        file_size = os.path.getsize(local_file_path)

        # 创建进度显示对象
        progress = UploadProgress(os.path.basename(local_file_path), file_size)

        print(f"  上传文件: {local_file_path}")

        # 使用回调函数上传文件
        sftp.put(local_file_path, remote_file_path, callback=progress.callback)

        print(f"  ✅ 上传成功: {local_file_path}")

        return True

    except Exception as e:
        print(f"  ❌ 上传文件失败 {local_file_path}: {e}")
        # 写入日志
        with open(LOG_FILE, 'a', encoding='utf-8') as log:
            log.write(f"ERROR: 上传文件失败 {local_file_path} -> {remote_file_path}: {e}\n")
        return False


def upload_folder(sftp, local_folder_path, remote_folder_path):
    """递归上传整个文件夹到远程服务器"""
    print(f"开始上传文件夹: {local_folder_path} -> {remote_folder_path}")

    # 统计总文件数，设置为长整形
    total_files = 27939739
    # 遍历本地文件夹，统计文件总数

    # for root, dirs, files in os.walk(local_folder_path):
    #     for file in files:
    #         total_files += 1
    #         if total_files % 1000000 == 0:
    #             print(f"  已统计 {total_files} 个文件...")


    print(f"  包含 {total_files} 个文件")

    # 将total_files个文件分为1000份，range(0, total_files, total_files//1000)，每一次的数量为total_files//1000，这一次的数量是total_files//1000*n
    # times = 1
    # this_time_files = total_files // 10000 * times

    # 开始上传
    uploaded_files = 0

    for root, dirs, files in os.walk(local_folder_path):
        # print(root, ":", dirs, ":", files)
        # 计算相对路径
        rel_path = os.path.relpath(root, local_folder_path)
        print(f"  上传目录: {rel_path}")

        remote_root = remote_folder_path
        if rel_path != '.': # 如果不是根目录，则添加相对路径
            # 如果rel_path包含\，替换为/
            if '\\' in rel_path:
                sample,modality = rel_path.split('\\')[0], rel_path.split('\\')[1]
                remote_root = f"{remote_folder_path}/{modality}/{sample}/"
                try:
                    sftp.stat(f"{remote_folder_path}/{modality}")
                except FileNotFoundError:
                    sftp.mkdir(f"{remote_folder_path}/{modality}",mode=0o777)
                    print(f"  ✅ 创建远程目录: {remote_folder_path}/{modality}")
            else:
                remote_root = remote_folder_path

        # 创建远程目录
        try:
            sftp.stat(remote_root)
        except FileNotFoundError:
            try:
                sftp.mkdir(remote_root, mode=0o777)
                print(f"  ✅ 创建远程目录: {remote_root}")
            except Exception as e:
                print(f"  ⚠️  创建远程目录失败 {remote_root}: {e}")
                return False

        # 上传文件
        for file in files:
            local_file_path = os.path.join(root, file)
            remote_file_path = f"{remote_root}/{file}"
            # #
            # if uploaded_files >= this_time_files:
            #     break



            # if uploaded_files < 1951140:
            #     uploaded_files += 1
            #     print("  已上传文件数:", uploaded_files)
            #     continue

            if uploaded_files % 2000 == 0 and uploaded_files > 0:
                time.sleep(20)  # 每上传1000个文件，休息20秒，防止过快
                print("  休息5秒，防止过快...")

            if upload_file_with_progress(sftp, local_file_path, remote_file_path):
                uploaded_files += 1


                # 显示整体进度（可选）
                overall_percent = (uploaded_files / total_files) * 100
                sys.stdout.write(f'\r整体进度: [{uploaded_files}/{total_files}] 文件, {overall_percent:.1f}% 完成')
                sys.stdout.flush()

    if total_files > 0:
        sys.stdout.write('\n')  # 换行
        sys.stdout.flush()

    print(f"✅ 文件夹 '{os.path.basename(local_folder_path)}' 上传完成。")
    print(f"  成功上传 {uploaded_files} 个文件。")

    return True


def main():
    # 检查本地目录是否存在
    if not os.path.isdir(LOCAL_BASE_DIR):
        print(f"❌ 本地目录不存在: {LOCAL_BASE_DIR}")
        return

    # 获取本地目录下的所有子文件夹
    try:
        subfolders = [f for f in os.listdir(LOCAL_BASE_DIR) if os.path.isdir(os.path.join(LOCAL_BASE_DIR, f))]
    except Exception as e:
        print(f"❌ 读取本地目录失败: {e}")
        return

    if not subfolders:
        print(f"⚠️  在 {LOCAL_BASE_DIR} 中未找到任何子文件夹。")
        return

    print(f"找到 {len(subfolders)} 个子文件夹需要上传:")
    for folder in subfolders:
        print(f"  - {folder}")

    # 初始化 SSH 客户端
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # try:
    # 建立 SSH 连接
    print(f"\n正在连接到远程服务器 {REMOTE_HOST}:{REMOTE_PORT} ...")

    if 'REMOTE_PASSWORD' in globals() and REMOTE_PASSWORD:
        ssh_client.connect(
            hostname=REMOTE_HOST,
            port=REMOTE_PORT,
            username=REMOTE_USERNAME,
            password=REMOTE_PASSWORD
        )
        print("✅ SSH 连接成功 (密码认证)")
    elif 'REMOTE_PKEY_PATH' in globals() and REMOTE_PKEY_PATH:
        try:
            if REMOTE_PKEY_PATH.lower().endswith('.ppk'):
                private_key = paramiko.RSAKey.from_private_key_file(REMOTE_PKEY_PATH,
                                                                    password=REMOTE_PKEY_PASSPHRASE)
            else:
                private_key = paramiko.RSAKey.from_private_key_file(REMOTE_PKEY_PATH,
                                                                    password=REMOTE_PKEY_PASSPHRASE)
            ssh_client.connect(
                hostname=REMOTE_HOST,
                port=REMOTE_PORT,
                username=REMOTE_USERNAME,
                pkey=private_key
            )
            print("✅ SSH 连接成功 (密钥认证)")
        except Exception as e:
            print(f"❌ 加载私钥或连接失败: {e}")
            return
    else:
        print("❌ 未配置有效的认证方式 (密码或私钥)。")
        return

    # 打开 SFTP 会话
    sftp = ssh_client.open_sftp()
    print("✅ SFTP 会话已打开")

    # 确保远程基础目录存在
    create_remote_dir_if_not_exists(sftp, REMOTE_BASE_DIR)

    # 遍历并上传每个子文件夹
    successful_uploads = 0

    # try:
    if CREATE_REMOTE_PARENT_DIR:
        create_remote_dir_if_not_exists(sftp, REMOTE_BASE_DIR)

    if upload_folder(sftp, LOCAL_BASE_DIR, REMOTE_BASE_DIR):
        successful_uploads += 1
        with open(LOG_FILE, 'a', encoding='utf-8') as log:
            log.write(f"SUCCESS: 上传文件夹 {LOCAL_BASE_DIR} -> {REMOTE_BASE_DIR} 完成\n")
    else:
        with open(LOG_FILE, 'a', encoding='utf-8') as log:
            log.write(f"ERROR: 上传文件夹 {LOCAL_BASE_DIR} -> {REMOTE_BASE_DIR} 失败\n")


    sftp.close()
    print("✅ SFTP 会话已关闭")





if __name__ == "__main__":
    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write(f"文件传输日志 - 开始时间: {datetime.now()}\n")
        log.write("=" * 60 + "\n")
    main()