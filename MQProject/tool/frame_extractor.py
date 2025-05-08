import cv2
import os

def ensure_folder_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def calculate_end_frame(cap, end_time):
    if end_time is None:
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        end_time = frame_count / frame_rate
    return int(end_time * cap.get(cv2.CAP_PROP_FPS))

def extract_frames(video_path, output_folder, start_time=0, end_time=None):
    ensure_folder_exists(output_folder)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    start_frame = int(start_time * frame_rate)
    end_frame = calculate_end_frame(cap, end_time)

    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if count >= start_frame and count <= end_frame:
            if count % int(frame_rate) == 0:
                frame_path = os.path.join(output_folder, f"frame_{count}.jpg")
                cv2.imwrite(frame_path, frame)

        if count > end_frame:
            break

        count += 1

    cap.release()



if __name__ == "__main__":

    video_path = 'path/to/your/video.mp4'

    # 输出文件夹路径
    output_folder = 'path/to/output/folder'

    # 调用函数提取帧
    extract_frames(video_path, output_folder, start_time=10, end_time=20)