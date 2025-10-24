import pygame
import time
from queue import Queue, Empty
from threading import Thread, Event
from utils.logger import setup_logger

class AudioPlayer:
    def __init__(self):
        self.command_queue = Queue()
        self.playlist = []
        self.is_playing = False
        self.stop_event = Event()
        pygame.init()
        
        # 初始化日志
        self.logger = setup_logger('AudioPlayer')
        self.logger.info("音频播放器初始化完成")
        
        # 启动播放线程
        self.play_thread = Thread(target=self._playback_loop, daemon=True)
        self.play_thread.start()
        
    def _playback_loop(self):
        """独立的播放线程"""
        SONG_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(SONG_END)
        clock = pygame.time.Clock()
        
        self.logger.info("音频播放线程启动")
        
        while not self.stop_event.is_set():
            try:
                # 处理播放结束事件
                for event in pygame.event.get():
                    if event.type == SONG_END:
                        self._play_next()
                
                clock.tick(30)
                
            except Exception as e:
                self.logger.error(f"播放线程错误: {e}")
    
    def _play_next(self):
        """播放下一个音频"""
        if self.playlist:
            audio_file = self.playlist.pop(0)
            try:
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                self.logger.info(f"播放音频: {audio_file}")
                self.is_playing = True
            except Exception as e:
                self.logger.error(f"音频加载失败 {audio_file}: {e}")
                self._play_next()
        else:
            self.is_playing = False
    
    def play_sequence(self, audio_files):
        """添加播放序列"""
        self.playlist.extend(audio_files)
        self.logger.debug(f"添加播放序列: {audio_files}")
        if not self.is_playing:
            self._play_next()
    
    def stop(self):
        """停止播放器"""
        self.logger.info("停止音频播放器")
        self.stop_event.set()
        pygame.mixer.music.stop()


class audio_task:
    def __init__(self, NS):
        self.NS = NS
        self.player = AudioPlayer()
        
        # 初始化日志
        self.logger = setup_logger('AudioTask_LYX')
        self.logger.info("音频任务(LYX版本)初始化完成")
        
        self.audio_map = {
            "start": ["openhand.mp3", "start.mp3"],
            "stop": ["stop.mp3", "rest.mp3"],
            "saved": ["saved.mp3"]
        }
    
    def run(self):
        """主循环 - 只检查标志位"""
        self.logger.info("音频任务主循环开始运行")
        
        while True:
            try:
                # 非阻塞检查标志位
                if self.NS.audio_start:
                    self.NS.audio_start = False
                    self.player.play_sequence(self.audio_map["start"])
                    self.logger.info("触发开始音频播放")
                
                if self.NS.audio_stop:
                    self.NS.audio_stop = False
                    self.player.play_sequence(self.audio_map["stop"])
                    self.logger.info("触发停止音频播放")
                
                if self.NS.audio_saved:
                    self.NS.audio_saved = False
                    self.player.play_sequence(self.audio_map["saved"])
                    self.logger.info("触发保存完成音频播放")
                
                time.sleep(0.05)  # 50ms检查一次
                
            except KeyboardInterrupt:
                self.logger.info("收到键盘中断，停止音频播放器")
                self.player.stop()
                break
            except Exception as e:
                self.logger.error(f"主循环错误: {e}", exc_info=True)

def run_audio(NS):
    task = audio_task(NS)
    task.run()