import sys, time; sys.path.insert(0,'.')
import cv2, numpy as np
from allow.fx import finish, rgb
from allow.kit import lyric
W,H=3840,2160
def save(img,name,t):
    out=finish(img,t,grain=0.028)
    cv2.imwrite(f'stills/{name}.jpg', cv2.cvtColor(out,cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(name, flush=True)
from allow.master import Master
M=Master(W,H)
fx,fy=M.P(982,585)
t=23.6
fa,fc=M.glass.frost_word('Allow','CormorantGaramond-MediumItalic.ttf',64*M.s,fx,fy,0.9,t,rgb(1.0,0.72,0.45)*0.45, opacity=0.7)
save(M.render(t,dict(warm=1.0,phone=0.25,frost=(fa,fc))),'1_warm_bedroom_0m23s',t)
t=91.0
fa,fc=M.glass.frost_word('Allow','CormorantGaramond-MediumItalic.ttf',64*M.s,fx,fy,1.0,t,rgb(0.25,0.55,1.0)*0.75, opacity=0.8)
save(M.render(t,dict(warm=0.5,warm_near=0.75,warm_far=0.24,night=0.75,phone=0.9,phone_fill=0.6,pulse=0.3,lean=0.4,frost=(fa,fc))),'3_first_blue_1m31s',t)
del M
from allow.shoulder import Shoulder
S=Shoulder(W,H); t=33.2
img=S.render(t,dict(warm=1.0,phone=1.0,presence=1.0,closeness=0.3))
save(lyric(img,"He's got manners, he's got a velvet voice",W,H),'2_his_presence_0m33s',t); del S
from allow.others import Mirror, Sister, City
Mi=Mirror(W,H); t=122.5; save(Mi.render(t,dict(warm=0.75,cold=0.6,phone=1.2)),'4_mirror_2m02s',t); del Mi
Si=Sister(W,H); t=191.6; save(Si.render(t,dict(hand=1.0,rise=1.0,write=1.0,tips=1.0)),'5_sisters_window_3m11s',t); del Si
C=City(W,H); t=227.6
img=C.render(t,dict(spread=0.85,last_on=1.0))
save(lyric(img,"Next door, a light comes on…",W,H,italic=True),'6_neighborhood_3m47s',t)
