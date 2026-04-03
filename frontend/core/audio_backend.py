from abc import ABC, abstractmethod


class AudioBackend(ABC):
    """音频后端抽象，便于后续替换为其它实现（如 VLC / QtMultimedia）。"""

    @abstractmethod
    def play(self, file_path, start_position=0):
        raise NotImplementedError

    @abstractmethod
    def pause(self):
        raise NotImplementedError

    @abstractmethod
    def resume(self):
        raise NotImplementedError

    @abstractmethod
    def stop(self):
        raise NotImplementedError

    @abstractmethod
    def set_volume(self, volume):
        raise NotImplementedError

    @abstractmethod
    def get_duration(self, file_path):
        raise NotImplementedError

    @abstractmethod
    def get_position(self):
        raise NotImplementedError

    @abstractmethod
    def seek(self, position_seconds):
        raise NotImplementedError

