import winsound
import os
import time

# 测试winsound是否能正常工作
def test_winsound():
    print("测试winsound音频播放...")
    
    # 检查是否有wav文件
    wav_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.lower().endswith('.wav'):
                wav_files.append(os.path.join(root, file))
    
    if not wav_files:
        print("未找到WAV文件，请确保目录中有WAV格式的音频文件")
        return False
    
    print(f"找到{len(wav_files)}个WAV文件")
    
    # 测试播放第一个WAV文件
    test_file = wav_files[0]
    print(f"测试播放文件: {test_file}")
    
    try:
        # 播放音频
        print("开始播放...")
        winsound.PlaySound(test_file, winsound.SND_FILENAME | winsound.SND_NODEFAULT | winsound.SND_ASYNC)
        
        # 等待5秒
        time.sleep(5)
        
        # 停止播放
        print("停止播放...")
        winsound.PlaySound(None, winsound.SND_PURGE)
        
        print("测试成功!")
        return True
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    test_winsound()