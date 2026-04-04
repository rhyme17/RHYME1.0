@echo off

rem ASR参数预设（方法2：写在启动脚本里）
set RHYME_ASR_DEVICE=cpu
set RHYME_ASR_COMPUTE_TYPE=float32
set RHYME_ASR_MODEL_SIZE=medium
set RHYME_ASR_BEAM_SIZE=8
set RHYME_ASR_VAD_FILTER=true
set RHYME_ASR_TO_SIMPLIFIED=true

rem 启动RHYME
echo 启动RHYME...
cd frontend\apps\desktop\windows
python app.py

pause
