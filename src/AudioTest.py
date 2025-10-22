# import pyttsx3
#
# enguine = pyttsx3.init("sapi5")
# enguine.setProperty('rate', 300)  # Set the speech rate
# enguine.setProperty('volume', 1)  # Set the volume (0.0 to 1.0)
# voice_id = enguine.getProperty('voices')[0].id  # Get the first voice
# enguine.setProperty('voice', voice_id)  # Set the voice
#
# def speak(text):
#     """
#     Function to convert text to speech.
#     :param text: The text to be spoken.
#     """
#     enguine.say(text)
#     enguine.runAndWait()
#
# def main():
#     # 讲中文
#     speak("你好，欢迎使用语音合成测试程序。")
#     # 讲英文
#     speak("Hello, welcome to the text-to-speech test program.")
#
#
# if __name__ == "__main__":
#     main()
#     # 结束语音引擎
#     enguine.stop()
#     print("语音合成测试完成。")
#
# #
# import vlc
# import time
#
# # 创建一个 VLC 媒体播放器实例
# player = vlc.MediaPlayer("star.mp3")
#
# # 播放音频
# player.play()
#
# # 等待音频播放完成（可以根据需要调整等待时间）
# time.sleep(1)  # 示例：等待 10 秒
#
#
# from pydub import AudioSegment
#
# # 加载 m4a 文件
# audio = AudioSegment.from_file("start.m4a")
#
# # 导出为 wav 文件
# audio.export("start.wav", format="wav")
#
#
# import pyaudio
# import wave
#
# # 打开 wav 文件
# wf = wave.open("start.wav", "rb")
#
# # 初始化 PyAudio
# p = pyaudio.PyAudio()
#
# # 打开音频流
# stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
#                 channels=wf.getnchannels(),
#                 rate=wf.getframerate(),
#                 output=True)
#
# # 读取数据并播放
# data = wf.readframes(1024)
# while data:
#     stream.write(data)
#     data = wf.readframes(1024)
#
# # 停止并关闭流
# stream.stop_stream()
# stream.close()
# p.terminate()

#
# from playsound import playsound
#
# # 播放 MP3 文件
# playsound("start.mp3")


import pygame
import time

# 初始化 pygame 模块
pygame.init()

# 加载 MP3 文件
pygame.mixer.music.load("start.mp3")

# 播放音频
pygame.mixer.music.play()

# 等待音频播放完成
while pygame.mixer.music.get_busy():
    time.sleep(1)

# 退出 pygame 模块
pygame.quit()