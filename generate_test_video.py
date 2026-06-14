"""Generate synthetic CPR test video."""
import cv2, numpy as np, os

def gen(path, dur=15, fps=30, w=800, h=600):
    out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w,h))
    n = int(dur*fps); cpm = 110; freq = cpm/60.0
    t = np.arange(n)/fps
    cx, sy = w//2, h//3
    amp = 100; sig = amp*np.sin(2*np.pi*freq*t)
    cpf = int(30/freq*fps); rpf = int(2*fps)
    comp = np.zeros(n, dtype=bool)
    i = 0
    while i < n:
        e = min(i+cpf, n); comp[i:e] = True; i = e + rpf
    wy = sy+240 + sig*comp
    for fi in range(n):
        fr = np.ones((h,w,3),np.uint8)*240
        cv2.circle(fr,(cx,sy-80),40,(80,60,40),-1)
        cv2.line(fr,(cx,sy),(cx,sy+150),(200,150,100),8)
        cv2.line(fr,(cx-40,sy),(cx-60,sy+120),(180,200,220),6)
        cv2.line(fr,(cx+40,sy),(cx+60,sy+120),(180,200,220),6)
        cv2.line(fr,(cx-30,sy+120),(cx,int(wy[fi])),(200,220,240),6)
        cv2.line(fr,(cx+30,sy+120),(cx,int(wy[fi])),(200,220,240),6)
        cv2.circle(fr,(cx,int(wy[fi])),15,(255,200,150),-1)
        st = "COMPRESSING" if comp[fi] else "REST"
        cv2.putText(fr,st,(10,30),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,180,0) if comp[fi] else (0,0,255),2)
        out.write(fr)
    out.release(); print(f"Done: {path}")

if __name__=="__main__":
    gen(os.path.join(os.path.dirname(__file__),"cpr_test_video.mp4"))
