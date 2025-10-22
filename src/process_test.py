# # 华南理工大学
# # 王熙来
# # 开发时间：2024/7/26 16:33
#
# import multiprocessing
# import time
#
# from multiprocessing import Manager
# def child_process(container):
#     while True:
#         time.sleep(0.5)
#         if container.flag == 1:
#             print("子进程运行程序A")
#             # 运行程序A的具体逻辑
#         elif container.flag == 2:
#             print("子进程运行程序B")
#             # 运行程序B的具体逻辑
#         else:
#             print("未知的标志位，无法确定运行的程序")
#
#
#
# if __name__ == "__main__":
#     manager = multiprocessing.Manager()
#     container1 = manager.Namespace()
#     container1.flag = 1
#
#     p = multiprocessing.Process(target=child_process, args=(container1,))
#     p.start()
#
#     # 在主进程中改变标志位，让子进程运行不同的程序
#     time.sleep(2)  # 模拟一些操作后改变标志位
#     container1.flag = 2  # 改变标志位为2
#     print("标志位已经改变")
#     time.sleep(2)  # 模拟一些操作后改变标志位
#
#     p.terminate()  # 结束子进程
#     p.join()

from multiprocessing import Manager, Process
import time


class GlobalContainer:
    def __init__(self):
        manager = Manager()
        self.shared_data = manager.dict()

    def set_data(self, key, value):
        self.shared_data[key] = value
        # print(self.shared_data.keys())
        print(f"Data set: {key} = {value}")

    def get_data(self, key):
        value = self.shared_data.get(key, None)
        print("get_data:", key, value)
        return value



def child_process(container):
    while True:
        time.sleep(0.5)
        if container.flag == 1:
            print("子进程运行程序A")
            # 运行程序A的具体逻辑
        elif container.flag == 2:
            print("子进程运行程序B")
            # 运行程序B的具体逻辑
        else:
            print("未知的标志位，无法确定运行的程序")

if __name__ == "__main__":
    container1 = GlobalContainer()
    for i in range(10):
        container1.set_data("flag{}".format(i), 1)

    container1.shared_data["flag2"] = 2
    print(container1.get_data("flag2"))
    # p = Process(target=child_process, args=(container1,))
    # p.start()

    # time.sleep(2)  # 模拟一些操作后改变标志位
