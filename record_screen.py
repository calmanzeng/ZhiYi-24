"""
屏幕录制脚本 — 录制 MVP 运行窗口
"""
import cv2
import numpy as np
from PIL import ImageGrab
import time
import os

def record_screen(output_path, duration=35, fps=15):
    """Record screen at given fps for given duration"""
    print(f"Recording {duration}s @ {fps}fps...")
    print("Make sure mvp.py window is visible!")
    print("Recording in 3...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    print("1...")
    time.sleep(1)
    print("RECORDING! Do CPR now!")
    
    frames = []
    start = time.time()
    frame_interval = 1.0 / fps
    
    while time.time() - start < duration:
        loop_start = time.time()
        
        # Capture screen
        img = ImageGrab.grab()
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        frames.append(frame)
        
        # Wait to maintain fps
        elapsed = time.time() - loop_start
        sleep_time = max(0, frame_interval - elapsed)
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    # Save video
    if frames:
        h, w = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
        for f in frames:
            out.write(f)
        out.release()
        print(f"Saved: {output_path} ({len(frames)} frames, {os.path.getsize(output_path)/1024:.0f} KB)")
        return output_path
    return None

if __name__ == "__main__":
    output = os.path.join(os.path.dirname(__file__), "demo_screen_record.mp4")
    record_screen(output, duration=30)
