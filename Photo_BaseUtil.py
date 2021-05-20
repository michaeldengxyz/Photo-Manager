#Pyhton 3.x
# -*- coding: UTF-8 -*-
#rev: beta 00.01.00

import sys 
import glob

import math
import numpy

import os
import time 
import re
import traceback
import base64 
import pickle
import zlib

import pynvml  #pip install nvidia-ml-py3;  #Python bindings to the NVIDIA Management Library
import psutil
import shutil

def ZipArray(a,isZip=True): 
    #压缩与解压数据   
    z = '' 
    try:  
        if isZip:        
            #z = base64.b64encode(zlib.compress(pickle.dumps(a)))
            #print("\nZip:\n",a,"\n\n",z) 
            z = base64.b64encode(zlib.compress(pickle.dumps(a)))
        else:
            '''
            print("\nfrom db:\n",type(a),a,'\n\n.decode(ascii):\n',type(a.decode('ascii')),a.decode('ascii'))             
            a = 'eJwtU38s1HEY/hyXrkNbm7biD7Is64+jrY2Z5VBTnVlEqRnHYcjhe+4YYd9wOz/W2J1Zas0lOeVnUq7CnXNx/RiSRRs5lXCZRS390dJ9n2/3xz1738/zPu/7Pu8d7SjJUUjzigSSXFmaQKrI' + \
                'lmcmy2TJRfwkWZokNydfLlNI5HyKsCx+Tir7SnFEREk5hHNSKEcVxY2hdvmKOCJaSTn9J6bKi/LS+NTueAdCSHogxRMREUdF7Ymh+L4ix3iOPRtMOUdFRZ3dsX/wJSJyyiWlOoxwCT6Xzz02' + \
                '2MHL+XtbiB3phGENg+KJpU7kPZrxbk04bmCQiH06EPOWjXgf1r5k+NYNNWLjt6FJJhY2SB8yMV2aOMagtqSkC+/NSTrkXYwW9KttfYP80YVB6F39+Aj6VY1NbP+mLoZH4taqwIu29TGxdjWg' + \
                'BfWydfC9PtW+Z1A4M98PXqEY82g9g+oxd37iJfR1vaaBfkvYHabei3IbBy8rEnW0NqQS+4zqdeg7HXgXeuZI+EC8ja9Q5yNm+34xTSDfFyND3v3XffhXZADPeoqYMW+lrR6+zJXeY9AYlGXG' + \
                'HMoFI/q0NrD+nS6/gTmW4gfB/yDpBn9t7Dr2nfxbjnyZCT5am0/CH2FExgh44gvQFRZ8vg291SkT9P1srO9+892oC50ZwN6WfdOoN+ueQ18vY+/c1mkCXzc3jPkXN6FLR4Q9g+6Auxr8oTLk' + \
                'xT8C4SNd8ecd6rmzuL9RvzkH/bp2+K3NXmH3lAf3IF5XYy5SWNwIve1Do/AxYRG+0T0FLdBdaWB9NXvjTuRodSH83To8gf16Q5/gHpE3bwGz94+jPrymBHWbmg7wTogqgIavSvh0Po/1O/pY' + \
                'O/hnMkbgS7RnP3jb1VrkYw2xwOWAGrz7F+MuWnUm+7t1+4l6ojddBGp+s/FB2wPc5XU69hP6OrHzW1Xwl/AVT6Er9LNgHgHvBfhXpuADqfPoBR54i/sI43zQlzjtDKC/f0Yb7umy3gqdWdUU' + \
                '+386QsPHDTF4xMKrAUq39PCNm14RQrnKqb0pgn+IFYEt'    
            print('\n.encode:\n',type(a.encode()),a.encode())
            z1 = base64.b64decode(a)
            z  = pickle.loads(zlib.decompress(z1))
            print('\nunzip result:\n',z)
            '''
            a = re.sub(r"^b\'|\'$",'',a.decode('utf-8'),re.I)
            #print(a,"\n",pickle.loads(zlib.decompress(base64.b64decode(a))))
            z = pickle.loads(zlib.decompress(base64.b64decode(a)))
    except:
        print(traceback.format_exc())

    return z   

def Progress(i, n, stime, x="",lastTime=0):                        
    if n > 0:
        leftt = ""        
        if i > 0 and n - i > 0:
            dt = 0
            if lastTime:
                dt = time.time() - lastTime
            else:
                dt = time.time() - stime
            left = dt / i * (n - i)
            leftt = ", est.left " + usedTime(0,left)

        print ("\r\t"+ x +"["+("."*int((i/n)*25))+(" "*(25 - int((i/n)*25)))+"] " + str(i) + "/" + str(n) + ", {:0>2.1f}".format(i/n*100) + "%, used " + usedTime(stime) + leftt, end='')  
        
def usedTime(stime,t=0):
    if not t:
        t = time.time() - stime

    tt={'h':'00','m':'00','s':'00'}
    
    if t > 3600:
        h = int(t/3600)
        tt['h'] = "{:0>2d}".format(h)
        t = t - h*3600
       
    if t > 60:
        m = int(t/60)
        tt['m'] = "{:0>2d}".format(m)
        t = t - m*60

    if t > 0:
        tt['s'] = "{:0>6.3f}".format(t)

    return tt['h'] + ':' + tt['m'] + ':' + tt['s'] 

def DictToDict(dict,keys):
    while len(keys):
       key = keys.pop(0)
       if key:
           if not dict.__contains__(key): 
              dict[key] = {}       
           dict = dict[key]

def IsKeyExist(dict,keys):  
    t = 1
    while len(keys):
        key = keys.pop(0)                             
        if not dict.__contains__(key): 
            t = 0
            break
        else:
            dict = dict[key]
            
    return t

def IsTrue(obj):
    #print(type(obj),obj)
    if(type(obj) == numpy.ndarray and obj.any()):
        return True
    elif(type(obj) == tuple and len(obj)):
        return True
    elif(type(obj) == list and len(obj)):
        return True
    elif(type(obj) == dict and len(obj.keys())):
        return True
    elif obj:
        return True    
    else: 
        return False

def del_file(path):
    try:
        ls = os.listdir(path)
        for i in ls:
            c_path = os.path.join(path, i)
            if os.path.isdir(c_path):
                del_file(c_path)
            else:
                os.remove(c_path)    
        shutil.rmtree(path)                     
    except:
        pass 

def checkNVIDIA_GPU(xself=None):
    try:
        pynvml.nvmlInit()
        xself.gpuNumber = pynvml.nvmlDeviceGetCount()  #显示有几块GPU
        for i in range(xself.gpuNumber):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i) # 这里的0是GPU id
            meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle)
            #print(meminfo.total) #显卡总的显存大小
            #print(meminfo.used)  #这里是字节bytes，所以要想得到以兆M为单位就需要除以1024**2
            #print(meminfo.free)  #显卡剩余显存大小
            m = int(meminfo.total*100/1024**2)/100

            xself.gpuInfo.append([i,m])
            if m >= 1:
                xself.gpuUsed = 1                
                if m >= 2:
                    xself.face_recognition_mode = 'cnn'

            if m > xself.gpuMaxMemory:
                xself.gpuMaxMemory = m
    except:
        print(traceback.format_exc())

    print("\ngpu number=",xself.gpuNumber,'\nMaxMemory(GB)=',xself.gpuMaxMemory,'\nface recognition mode=',xself.face_recognition_mode,'\ngpu Use Batch=',xself.gpuUseBatch,"\n")

def MemoryStatus():
    try:
        phymem = psutil.virtual_memory()
        line = "\t... RAM usage: %5s%% %6s/%s" %(
            phymem.percent,
            str(int(phymem.used/1024/1024))+"M",
            str(int(phymem.total/1024/1024))+"M"
            ) + ";  CPU usage: {:0>4.1f}".format(psutil.cpu_percent(1)) +"%"
        print(line)

        pynvml.nvmlInit()
        gpuNumber = pynvml.nvmlDeviceGetCount()  #显示有几块GPU
        for i in range(gpuNumber):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i) # 这里的0是GPU id
            meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle)
            #print(meminfo.total) #显卡总的显存大小
            #print(meminfo.used)  #这里是字节bytes，所以要想得到以兆M为单位就需要除以1024**2
            #print(meminfo.free)  #显卡剩余显存大小

            print('\t... GPU#'+ str(i) +': total memory',int(meminfo.total/1024**2),'M, used',int(meminfo.used/1024**2),'M ',int(meminfo.used/meminfo.total*10000)/100,'%, free',int(meminfo.free/1024**2),'M\n')
    except:
        pass
    
    