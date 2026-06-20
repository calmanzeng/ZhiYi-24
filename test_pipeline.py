"""
ZhiYi24AI Test Pipeline
Generates synthetic test video, runs scoring with all 24 skills
"""

import cv2
import numpy as np
import os, yaml, importlib.util

OUTPUT_DIR = "C:/Users/Administrator/Desktop/zhiyi_tests"
os.makedirs(OUTPUT_DIR, exist_ok=True)
SKILLS_DIR = "C:/Users/Administrator/.hermes/scripts/cpr_ai_scorer/skills"

print("=" * 60)
print("ZhiYi24AI Test Pipeline")
print("=" * 60)

# Step 1: Generate synthetic test videos
print("\n[Step 1] Generating synthetic test videos...")

def draw_body(frame, offset=0):
    h, w = frame.shape[:2]
    nose = (w//2, int(h*0.10))
    ls = (int(w*0.35), int(h*0.28))
    rs = (int(w*0.65), int(h*0.28))
    lh = (int(w*0.38), int(h*0.52))
    rh = (int(w*0.62), int(h*0.52))
    lw = (int(w*0.32), int(h*0.52) + offset)
    rw = (int(w*0.68), int(h*0.52) + offset)
    le = (int(w*0.30), int(h*0.38))
    re = (int(w*0.70), int(h*0.38))
    lk = (int(w*0.40), int(h*0.70))
    rk = (int(w*0.60), int(h*0.70))
    col = (0, 255, 0); thick = 3
    cv2.line(frame, ls, rs, (0,200,0), 4)
    cv2.line(frame, ls, lh, col, 3); cv2.line(frame, rs, rh, col, 3)
    cv2.line(frame, lh, rh, (0,200,0), 4)
    cv2.line(frame, ls, le, col, 3); cv2.line(frame, rs, re, col, 3)
    cv2.line(frame, le, lw, col, 3); cv2.line(frame, re, rw, col, 3)
    cv2.line(frame, lh, lk, col, 3); cv2.line(frame, rh, rk, col, 3)
    cv2.circle(frame, nose, int(h*0.04), (0,200,0), -1)
    for pt in [nose, ls, rs, le, re, lw, rw, lh, rh, lk, rk]:
        cv2.circle(frame, pt, 5, (0,255,255), -1)

def gen_video(path, frames=300, fps=30, motion_type="cpr"):
    h, w = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(path, fourcc, fps, (w, h))
    avi_path = path.replace(".mp4", ".avi")
    out_avi = cv2.VideoWriter(avi_path, cv2.VideoWriter_fourcc(*"MJPG"), fps, (w, h))
    
    for t in range(frames):
        frame = np.ones((h, w, 3), dtype=np.uint8) * 45
        if motion_type == "cpr":
            offset = int(25 * np.sin(t * 2 * np.pi * 110 / 60 / fps))
            draw_body(frame, offset)
            cv2.putText(frame, f"CPR Test | CPM:{110 + 15*np.sin(t*0.02):.0f}", (10,25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 1)
        elif motion_type == "suturing":
            offset = int(10 * np.sin(t * 2 * np.pi * 0.5))
            draw_body(frame, offset)
            cv2.putText(frame, f"Suturing Test | Fine motor", (10,25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 1)
        elif motion_type == "percussion":
            offset = int(15 * np.sin(t * 2 * np.pi * 3))
            draw_body(frame, offset)
            cv2.putText(frame, f"Percussion Test | Rhythm", (10,25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 1)
        cv2.putText(frame, f"Frame {t}/{frames} | ZhiYi24AI", (w//2-100, h-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)
        out.write(frame); out_avi.write(frame)
    out.release(); out_avi.release()
    size = os.path.getsize(path)/1024
    print(f"  {os.path.basename(path)}: {size:.0f}KB, {frames}frames/{fps}fps = {frames/fps:.0f}s")
    return avi_path

tests = [
    ("test_cpr.mp4", 300, "cpr"),
    ("test_suturing.mp4", 200, "suturing"),
    ("test_percussion.mp4", 200, "percussion"),
]

paths = []
for name, frames, mtype in tests:
    p = os.path.join(OUTPUT_DIR, name)
    gen_video(p, frames, motion_type=mtype)
    paths.append(p)

print(f"\nVideos saved to: {OUTPUT_DIR}")

# Step 2: Test all scorers with simulated landmarks
print("\n[Step 2] Testing all 24 scorers with simulated data...")

np.random.seed(42)
base = {
    "nose": (0.5,0.1,0,0.99), "left_ear": (0.43,0.15,0.05,0.97), "right_ear": (0.57,0.15,-0.05,0.97),
    "left_shoulder": (0.35,0.28,0.05,0.99), "right_shoulder": (0.65,0.28,-0.05,0.99),
    "left_elbow": (0.30,0.40,0.03,0.98), "right_elbow": (0.70,0.40,-0.03,0.98),
    "left_wrist": (0.32,0.52,0.02,0.98), "right_wrist": (0.68,0.52,-0.02,0.98),
    "left_hip": (0.38,0.55,0.03,0.99), "right_hip": (0.62,0.55,-0.03,0.99),
    "left_knee": (0.40,0.72,0.02,0.98), "right_knee": (0.60,0.72,-0.02,0.98),
    "left_index": (0.31,0.54,0.03,0.90), "right_index": (0.69,0.54,-0.03,0.90),
    "left_thumb": (0.30,0.53,0.04,0.90), "right_thumb": (0.70,0.53,-0.04,0.90),
    "left_ankle": (0.42,0.88,0.01,0.97), "right_ankle": (0.58,0.88,-0.01,0.97),
}

# Generate 90 frames with rhythmic motion (simulates all skills)
frames = []
for t in range(90):
    p = t/90
    frame = {}
    for k, v in base.items():
        x, y, z, vis = v
        dx = 0.03*np.sin(p*18*np.pi); dy = 0.03*np.cos(p*20*np.pi+1)
        frame[k] = (x+dx, y+dy, z, vis)
    frames.append(frame)

d = os.listdir(SKILLS_DIR)
passed, failed = 0, 0
for skill_name in sorted(d):
    dp = os.path.join(SKILLS_DIR, skill_name)
    if not os.path.isdir(dp): continue
    sp = os.path.join(dp, "scoring.py"); yp = os.path.join(dp, "skill.yaml")
    if not os.path.exists(sp): continue
    try:
        spec = importlib.util.spec_from_file_location(f"t_{skill_name}", sp)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        s = mod.SkillScorer(); s.reset()
        for f in frames: s.extract_features(f)
        feat = s.feature_cache; met = s.compute_metrics(feat)
        fb = s.get_feedback(met, feat)
        ov = sum(m*0.25 for m in met.values()) if met else 0
        with open(yp) as f: cfg = yaml.safe_load(f)
        print(f"  [{passed+1:02d}] {cfg['display_name']:<40} ov={ov:.0f} feat={len(feat)} met={len(met)} | {fb[0]['message'][:20]}")
        passed += 1
    except Exception as e:
        print(f"  [ERR] {skill_name}: {str(e)[:60]}")
        failed += 1

print(f"\n{'='*60}")
print(f"Results: {passed} passed, {failed} failed | {OUTPUT_DIR}")
print(f"{'='*60}")
print(f"\nTo run with camera: python mvp.py")
print(f"To test video:      python mvp.py --video {OUTPUT_DIR}/test_cpr.mp4")
print(f"Test all videos:    python test_pipeline.py")
