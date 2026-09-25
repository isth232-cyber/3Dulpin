import cv2
import glob
import os

video_dir = r"C:\Users\Nihaal S\OneDrive\Documents\3D"
videos = glob.glob(os.path.join(video_dir, "*.mp4"))

total_sec = 0
for f in videos:
    v = cv2.VideoCapture(f)
    frames = v.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = v.get(cv2.CAP_PROP_FPS)
    if fps > 0:
        total_sec += frames / fps
    v.release()

print(f"Total Videos: {len(videos)}")
print(f"Total Seconds: {total_sec}")
