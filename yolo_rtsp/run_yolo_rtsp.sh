#!/bin/bash

# 设置工作目录
cd /yolo_rtsp

# 使用nohup在后台运行程序，将所有输出重定向到/dev/null
nohup /bin/conda run -n yolov8 --no-capture python /yolo_rtsp.py > /dev/null 2>&1 &
parent_pid=$!

# 等待一秒让子进程启动
sleep 1

# 获取Python进程的PID（conda run的子进程）
python_pid=$(pgrep -P $parent_pid)


echo "Parent process started with PID: $parent_pid"
echo "Python process started with PID: $python_pid"
