import os
import time


def format_time(seconds):
    """将秒数格式化为分:秒格式"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def ensure_directory(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            return True
        except Exception as e:
            print(f"创建目录失败: {str(e)}")
            return False
    return True


def get_file_extension(file_path):
    """获取文件扩展名"""
    return os.path.splitext(file_path)[1].lower()


def is_audio_file(file_path):
    """判断是否为音频文件"""
    audio_extensions = ['.wav', '.mp3', '.ogg', '.flac', '.aac', '.m4a']
    ext = get_file_extension(file_path)
    return ext in audio_extensions


def get_file_size(file_path):
    """获取文件大小（字节）"""
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0


def format_file_size(bytes_size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"
