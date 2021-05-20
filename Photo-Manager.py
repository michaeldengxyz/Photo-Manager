#Pyhton 3.x
# -*- coding: UTF-8 -*-
#rev: beta 00.02.00

import shutil
import os
import sys 
import glob
import time,datetime
import traceback
import re

import pymysql
import base64 
import hashlib
import shutil
from urllib import parse as urlParse
import requests

import math
import numpy
import face_recognition
import zlib
import pickle
import pynvml  #pip install nvidia-ml-py3;  #Python bindings to the NVIDIA Management Library
import psutil
from bingmaps.apiservices.locations import LocationByPoint
import simplejson as json
import exifread

from tkinter import *
from tkinter import filedialog,messagebox,ttk,tix as Tix
import threading
import ctypes
from multiprocessing import Process

from PIL import Image, ImageDraw, ImageStat
from PIL.ExifTags import TAGS
import cv2

from Photo_BaseUtil import *

#from example.commons import Faker 
from pyecharts import options as pyOpts 
from pyecharts.charts import Geo, Map as pyMap
from pyecharts.globals import ChartType, SymbolType
import webbrowser

WindX  = {}
WindXX = {}
WindX['self_filepath'] = __file__
WindX['self_folder'] = re.sub(r'\\','/',os.path.abspath(os.path.dirname(__file__)))
print("\nroot:",WindX['self_folder'])  
sys.path.append(WindX['self_folder'])  
os.chdir(WindX['self_folder'])
WindX['pcName'] = os.environ['COMPUTERNAME']
print("getcwd:",os.getcwd() + "\nDevice Name:",WindX['pcName'])

WindX['main'] = None
WindX['mainPX'] = 0
WindX['mainPY'] = 0 
WindX['PhotoFolderStr'] = "H:/WE4"
WindX['FindLocationLastRequestTime'] = 0
WindX['WindowStatus'] = "normal"

def GUI():         
    WindX['main'] = Tix.Tk()
    WindX['main'].title("Photo Manager")
    WindX['main'].configure(bg='#A0A0A0')
    WindX['main'].geometry('+' + str(WindX['mainPX']) + '+' + str(WindX['mainPY']))
    WindX['main'].wm_attributes('-topmost',1) 
    #WindX['main'].overrideredirect(1)
    WindX['main'].protocol("WM_DELETE_WINDOW", WindExit)

    WindX['Frame1'] = Frame(WindX['main'],bg='#D0D0D0')
    WindX['Frame1'].grid(row=1,column=0,sticky=E+W+S+N,pady=1,padx=0)
    WindX['Frame2'] = Frame(WindX['main'],bg='#D0D0D0')
    WindX['Frame2'].grid(row=2,column=0,sticky=E+W+S+N,pady=0,padx=0)
        
    balstatus = Label(WindX['main'], justify=CENTER, relief=FLAT,pady=3,padx=3, bg='yellow',wraplength = 50)
    WindX['winBalloon'] = Tix.Balloon(WindX['main'], statusbar = balstatus)
    
    if WindX['Frame1']:
        row = 0
        Lfg = 'gray'
        Label(WindX['Frame1'], text='Photo Directory', justify=LEFT, relief=FLAT,pady=3,padx=3,fg=Lfg).grid(row=row,column=1,sticky=W+E+N+S)
        WindXX['PhotoFolder'] = StringVar()
        e=Entry(WindX['Frame1'], justify=LEFT, relief=FLAT, textvariable= WindXX['PhotoFolder'], width=25)
        e.grid(row=row,column=2,sticky=W+E+N+S,padx=1,pady=0)
        WindX['e_PhotoFolder'] = e
        if WindX['PhotoFolderStr']:
            e.insert(0,WindX['PhotoFolderStr'])
        elif WindX['self_folder']:
            e.insert(0,WindX['self_folder'])
        iButton(WindX['Frame1'],row,3,SetFolder,'...',None,tip='Select folder',width=8) 
        
        row += 1
        Label(WindX['Frame1'], text='Export Label', justify=LEFT, relief=FLAT,pady=3,padx=3,fg=Lfg).grid(row=row,column=1,sticky=W+E+N+S,pady=1)
        WindXX['b_ExportLabel'] = StringVar()
        b = ttk.Combobox(WindX['Frame1'], textvariable=WindXX['b_ExportLabel'], justify=CENTER, state="readonly")
        b.grid(row=row,column=2,sticky=W+E+N+S,padx=1,pady=1, columnspan=2) 
        WindX['b_ExportLabel'] = b        

    if WindX['Frame2']:
        button_bg = "#A0A0A0"
        row = 0
        iButton(WindX['Frame2'],row,0,lambda:main(None),        'RUN for List', width=25, bg=button_bg, tip='Run to get image / video list from the selected [Photo Directory]') 
        iSeparator(WindX['Frame2'],row,1,bg=button_bg)
        iButton(WindX['Frame2'],row,2,lambda:main("CheckRepeatedImages"), 'Check Repeated files', width=25, bg=button_bg, tip='Check repeated files and make mark in the  [file_list] table')
        
        row += 1
        iButton(WindX['Frame2'],row,0,lambda:main("FileListMD5Check"), 'Refresh MD5 FileList', width=25, bg=button_bg, tip='Check the field [md5_file] in the table [file_list], if null get md5 of the file and save') 
        iSeparator(WindX['Frame2'],row,1,bg=button_bg)
        iButton(WindX['Frame2'],row,2,lambda:main("FacesCleanUp"),     'Clean Up Faces',       width=25, bg=button_bg, tip='Delete faces are not having existing [file_id] in the [file_list] table')

        row += 1
        iButton(WindX['Frame2'],row,0,lambda:main("SyncFileID"),       'Sync File ID',     width=25, bg=button_bg, tip='Sync file id to faces table') 
        iSeparator(WindX['Frame2'],row,1,bg=button_bg)
        iButton(WindX['Frame2'],row,2,lambda:main("FileLocation_Map"), 'Map File Location',width=25, bg=button_bg, tip='Map / estimate file location by its date time v.s. other files which has location information')

        row += 1
        iButton(WindX['Frame2'],row,0,lambda:main("LocationFind"),      'Find Location (Bing map)',      width=25, bg=button_bg, tip='Find file location information (country, province, city, ...) \nby using its [latitude, longitude], \nusing MS Bing-map service') 
        iSeparator(WindX['Frame2'],row,1,bg=button_bg)
        iButton(WindX['Frame2'],row,2,lambda:main("LocationFind_BaiDU"),'Find Location (Baidu map)',      width=25, bg=button_bg, tip='Find file location information (country, province, city, ...) \nby using its [latitude, longitude], \nusing Baidu-map service') 
             
        row += 1
        iButton(WindX['Frame2'],row,0,lambda:main("ExportImagesByLabel"    ), 'Export By Label (raw)',  width=25, bg=button_bg, tip='Export images by the selected [Export Label] with raw image') 
        iSeparator(WindX['Frame2'],row,1,bg=button_bg)
        iButton(WindX['Frame2'],row,2,lambda:main("ExportImagesByLabel1080"), 'Export By Label (1080)', width=25, bg=button_bg, tip='Export images by the selected [Export Label] with 1080px image')

        row += 1
        iButton(WindX['Frame2'],row,0,lambda:main("FlightTrace"), 'Flight Trace',  width=25, bg=button_bg, tip='Flight trace according to file modified time and locations') 
        iSeparator(WindX['Frame2'],row,1,bg=button_bg)
        iButton(WindX['Frame2'],row,2,lambda:main("LocationToCoordinates"), 'Location To Lat&Lon', width=25, bg=button_bg, tip='Get latitude & longitude from a location')
        
        row += 1
        iButton(WindX['Frame2'],row,0,lambda:main("DELRepeatedFile"), 'Delete Repeated Files',  width=25, bg=button_bg, tip='Delete repeated files in the photo directory') 
        iSeparator(WindX['Frame2'],row,1,bg=button_bg)
        iButton(WindX['Frame2'],row,2,lambda:main("GPSInfoGet"),       'Get GPS Information',   width=25, bg=button_bg, tip='Get GPS information from the file inside')
        
           
    main("FacesLabelknownListGet")                                      
    mainloop()
    
def TDB(go=None):
    print("TBD")
    return

def EnableWidgets(wid=None, state="normal", act=1):
    WindX['WindowStatus'] = state
    
    if not wid:
        return
    try:
        for item in wid.winfo_children():
            #print("-"*act,item)
            if re.match(r'.*\!entry\d*$|.*button\d*$|.*combobox\d*$',str(item),re.I):
                if state=="normal" and re.match(r'.*button\d*$',str(item),re.I):
                    item.configure(state=state, relief=FLAT)
                else:
                    item.configure(state=state)

            if item.winfo_children() :
                EnableWidgets(item, state=state, act=act+1)
    except:
        pass
        
def SetFolder():
    fpath = filedialog.askdirectory(initialdir = WindX['self_folder'])
    if fpath:
        print(fpath)
        WindX['e_PhotoFolder'].delete(0,END)
        WindX['e_PhotoFolder'].insert(0,fpath)
        
def WindExit():
    WindX['main'].destroy()
    os._exit(0)        
        
    #sys.exit(0)  # This will cause the window error: Python has stopped working ...

def OpenNew():
    print("\n##### OpenNew:", "python.exe " + WindX['self_filepath'], "\n")
    os.system("python.exe " + WindX['self_filepath'])
    
def FindLocationStatus(thread1=None):
    print("\n##### FindLocationStatus ...", thread1, WindX['FindLocationLastRequestTime'], WindX['WindowStatus'])
    while True:        
        if WindX['FindLocationLastRequestTime'] and WindX['WindowStatus'] == "disabled":
            t = time.time() - WindX['FindLocationLastRequestTime']
            #print(t)
            if t > 60:
                messagebox.showwarning(title='Warning', message='Action to find location might hang up now, please check!')
            elif t > 120:
                p = Process(target=OpenNew,args=())
                p.start()
                
                print("\n##### Action to find location might hang up now, stop the action ...")
                for proc in psutil.process_iter():
                    if re.match(r'.*python', str(proc.name()), re.I):
                        #print(proc.name(), proc.cmdline())
                        if re.match(r'.*Photo\-Manager', str(proc.cmdline()), re.I):
                            proc.kill()                
                break

            time.sleep(10)
        else:
            break
        
def main(ToDo=""):
    WindX['WindowStatus'] = "disabled"
    WindX['FindLocationLastRequestTime'] = time.time()
    thread1 = threading.Thread(target=mainX, args=[ToDo])
    
    if ToDo == "LocationFind":
        thread2 = threading.Thread(target=FindLocationStatus, args=[thread1]) 
        thread2.start()
        
    thread1.start()

def mainX(ToDo=""):          
    photo_dir = WindXX['PhotoFolder'].get()   #给定存放照片的根文件夹，如果没有，默认为当前目录

    label = None
    if ToDo == "ExportImagesByLabel" or ToDo == "ExportImagesByLabel1080":
        label = WindXX['b_ExportLabel'].get()
        if not label:
            messagebox.showwarning(title='Warning', message='Please select a [Label] !')
            return
    
    p = Photo(photo_dir)
    p.run(ToDo=ToDo,label_correct=label)   
    
    if ToDo == "FacesLabelknownListGet":
        WindX['b_ExportLabel']['values'] = p.faceKnownlabelList
        WindX['b_ExportLabel'].current(0)
    
    #开始运行: 
    #选项: FileGetMD5 FileListMD5Check FacesCleanUp SyncFileID 
    #      FileLocation_Map LocationFind GPSInfoGet 
    #      CheckRepeatedImages ExportImagesByLabel
    
    #p.FaceRecognition2()
    #p.FaceRecognitionKnown()
    #p.FaceRecognitionKnownTopX() 

class Photo():
    def __init__(self,pdir=None):   
        self.dir       = pdir
        self.FacesPath = ""   #存放人脸图片的文件夹 H:/WE4/Faces
        self.refresh_all  = 0 #1 - 重新开始处理所有照片；0-保留上次已经处理的照片信息
        self.allPicQTY  = 0  #初始默认路径下的照片数量
        self.allFileQTY = 0  #初始默认路径下的文件数量
        self.picK      = 0  #已经遍历照片的数量
        self.formats   = ['BMP', 'TIFF', 'GIF', 'JPEG', 'PNG', 'JPG']  #照片格式   ,'HEIC'
        self.pixels    = [1080,500,350] #,250,100,50  #照片小图的分辨率

        self.faceKnown = {}    #存放 - 已知人脸照片的特征        
        self.faceKnown['encodings'] = []
        self.faceKnown['labels'] = []
        self.facesData = []    #存放 - 人脸照片数据
        self.lastLabelIndex = 0
        self.tolerance = 0.4

        self.db        = None  #连接数据库的句柄
        self.dbName    = 'we2' #数据库名称 
        self.username  = 'we2' #登录数据库的用户名
        self.password  = '12345$9876' #登录密码
        self.lastupdate= time.time()

        self.gpuMaxMemory = 0
        self.gpuInfo      = []
        self.gpuNumber    = 0
        self.gpuUseBatch  = 0 #使用批处理人脸识别
        self.gpuLastBsize = 2 #批处理人脸识别照片，每次处理的图片数量,必须是2的倍数！！！
        self.face_recognition_mode = 'hog'  #人脸识别，gpu可用时选cnn，只用CPU时选hog
        self.nott_upsample = 1 #人脸识别的参数number_of_times_to_upsample，大于等于0的整数，数值越大，辨识精度越高，消耗时间内存越大        

        self.face_rec_width =800  #像素值，人脸识别时，输入照片的最大宽度，如果self.gpuUseBatch=1时，照片的长宽都是self.face_rec_width；
        self.face_rec_height=600  #像素值，人脸识别时，输入照片的最大高度；照片越小，辨识速度越快，但是人脸辨识的精确度会降低很多。

        self.process_qty = 0 #已经处理的照片及视频的数量  
        self.faceKnownlabelList = []

        self.bingmaps_key = 'geCv96Y8QjpJl0Y3wX44~H72v79dH5L5IroJ0Irn-PA~As-Dp9ay0LByAZg6Ihaw8k-tKQmSY8ZxQaBCYpG86AwzTY8ZAvN8SR99JfDtdDDY'   #Bing map key, to get location, see help http://www.bingmap.cn
        self.LocationFind_use_bingmaps_service = 0
        
        self.baidu_maps_appkey = 'g5AfygI95PwX8HO7S9T4tlchKEfMaMNZ'
        self.baidu_maps_snkey  = 'RyTYGPPTqU58dYgiksBzb9Vub166GATd'
        self.LocationFind_use_baidu_service = 1        

        #checkNVIDIA_GPU(self) #check NVIDIA GPU only  # need to check this function for CNN mode ----- 
        print('gpuUseBatch=',self.gpuUseBatch,'\ngpuLastBsize=',self.gpuLastBsize,'\nface_recognition_mode=',self.face_recognition_mode,'\nnott_upsample=',self.nott_upsample,'\n')
       
    def run(self,ToDo=None,label_correct=None,topx=50):
        EnableWidgets(wid=WindX['main'], state="disabled")
        
        self.startTime= time.time()
        
        self.dir = re.sub(r'\\+','/',self.dir)
        self.dir = re.sub(r'\/*$','',self.dir)    
        print('start from this folder:',self.dir)

        if (not self.dir) or (not os.path.exists(self.dir)):
            #self.dir = re.sub(r'\\','/',os.path.abspath(os.path.dirname(__file__)))  #获取当前路径
            print("Please set a valid path where your photos were stored!!",'\n')
            EnableWidgets(wid=WindX['main'], state="normal")
            return

        self.ConnectDB()
        self.cursor = self.db.cursor()  #连接数据库的指针
        
        if ToDo == "FileGetMD5":            
            self.GetFileQTY(self.dir)  #获取当前目录及子目录下所有照片的数量
            self.FileGetMD5(self.dir)            
        elif ToDo == "FileListMD5Check":
            self.FileListMD5Check()           
        elif ToDo == "FacesCleanUp":
            self.Faces_CleanUp()        
        elif ToDo == "SyncFileID":
            self.SyncFileID()            
        elif ToDo == "LocationFind":
            self.LocationFind_use_bingmaps_service = 1
            self.LocationFind_use_baidu_service = 0 
            self.LocationFind()
        elif ToDo == "LocationFind_BaiDU":
            self.LocationFind_use_bingmaps_service = 0
            self.LocationFind_use_baidu_service = 1 
            self.LocationFind()
        elif ToDo == "CheckRepeatedImages":
            self.CheckRepeatedImages()
        elif ToDo == "ExportImagesByLabel1080":
            self.ExportImagesByLabel(label_correct,'1080')
        elif ToDo == "ExportImagesByLabel":
            self.ExportImagesByLabel(label_correct,'raw')
        elif ToDo == "GPSInfoGet":
            self.GPSInfoGet()
        elif ToDo == "FaceRecognitionKnownTopX":
            self.FaceRecognitionKnownTopX(topx)
        elif ToDo == "FacesLabelknownListGet":
            self.FacesLabelknownListGet()
        elif ToDo == "LocationToCoordinates":
            self.LocationToCoordinates()
        elif ToDo == "FlightTrace":
            self.FlightTrace()
        elif ToDo == "FileLocation_Map":
            self.FileLocation_Map()
        elif ToDo == "DELRepeatedFile":
            #获取以MD5为基准的文件列表
            self.GetFileQTY(self.dir)  #获取当前目录及子目录下所有照片的数量
            self.FileRepeatedGetList()
            self.FileRepeatedDelete(self.dir)
        else:            
            #获取当前目录及子目录下所有照片的数量
            self.GetFileQTY(self.dir)
            print (u"所有照片: ",self.allPicQTY,"\n")
        
            self.FacesLabelRefresh()
            #'''
            self.FacesLabelGet()

            #创建存放人脸图片的文件夹
            if not self.FacesPath:
                self.FacesPath = self.dir + '/Faces'
            if not os.path.exists(self.dir + '/Faces'):  
                os.makedirs(self.dir + '/Faces') 
            
            #获取以MD5为基准的文件列表
            self.FileRepeatedGetList()
            
            #开始扫描照片：获取照片EXIF，人脸等信息，并创建照片的小图
            self.MakeThumbs(self.dir)
            print ('\nTotal processed image&video:',self.process_qty,'/',self.allPicQTY,'\nAll done, Total used:',usedTime(self.startTime),'\n')      

            self.SyncFileID()
            self.SyncfaceImageID()
            self.LocationFind()
            self.FileLocation_Map()
            print("\n")       
            #'''
            
        if self.db:  
            try: 
                self.cursor.close()
                self.db.close() 
            except:
                pass
            
        EnableWidgets(wid=WindX['main'], state="normal")

    def ConnectDB(self):
        #连接到数据库
        self.db = None
        
        config={
            "host":"127.0.0.1",
            'port':3306,
            "user":self.username,
            "password":self.password,
            "database":self.dbName,
            'charset':'utf8mb4',
        }
        
        try:
            self.db = pymysql.connect(**config)
        except:
            print("\n.... Failed to connect database:\n",traceback.format_exc())
            
        if not self.db:                                             
            sys.exit(0)             
    
    def GetUsecondFromName(self,name=""):    
        #name must be the format:  YYYYMMDD-HHMMSS
        if not name:
            return 1
        
        strName = re.sub(r'[^0-9]','',name)
        year = int(strName[0:4])
        month= int(strName[4:6])
        dayx = int(strName[6:8])
        hour = int(strName[8:10])
        minx = int(strName[10:12])
        secx = int(strName[12:14])            
        
        if year > 0 and month > 0 and dayx > 0:
            t = datetime.datetime(year, month, dayx, hour, minx, secx)
            return int(time.mktime(t.timetuple()))
        else:
            return 1
        
    def FlightTrace(self):
        print("Flight trace according to file modified time and locations ...")
        cmap = {
            '中华人民共和国': "China", 
            '越南': "Vietnam", 
            '马来西亚': "Malaysia", 
            '美国': "United States"
        }
        
        self.traces = {
            "country":[],
            "quantity":[]
        }
        
        self.locations = {}
        
        nmax = 10
        try:
            self.startTime= time.time()
            #get files which has location information
            self.cursor.execute("SELECT `mtime`,`id`,`latitude`,`longitude`, `countryRegion`, `adminDistrict`, `adminDistrict2`, `locality` FROM `filelist` " + \
                                   "where (`latitude` IS not null and `latitude`<>'') and (`longitude` IS not null and `longitude`<>'') and `countryRegionIso2`='CN' and (`is_repeated`=0 or `is_repeated` is null or `is_repeated`='') order by `mtime` limit 100")  
            results = self.cursor.fetchall() 
            n = len(results)
            print(".. get location records: ",n)
            
            self.localsNum = {}
            self.localsCords = {}
            
            lastLoc  = ""
            for p in results:                
                loc = str(p[4]) + "__" + str(p[5]) + "__" + str(p[6]) + "__" + str(p[7])   #`countryRegion`, `adminDistrict`, `adminDistrict2`, `locality`
                loc = str(base64.b64encode(loc.encode(encoding='utf-8')),'utf-8')
                locNun = 0
                if self.localsNum.__contains__(loc):
                    locNun = self.localsNum[loc]
                else:
                    num = len(self.localsNum.keys())
                    self.localsNum[loc] = num + 1
                    locNun = num + 1
                
                if self.localsCords.__contains__(locNun):
                    self.localsCords[locNun][0] = (self.localsCords[locNun][0] + float(p[2]))/2
                    self.localsCords[locNun][1] = (self.localsCords[locNun][1] + float(p[3]))/2
                else:
                    self.localsCords[locNun] = [float(p[2]), float(p[3])] #[`latitude`,`longitude`]
                        
                if not loc == lastLoc:  
                    mt = re.sub(r'\.\d+$','',p[0])
                    if not self.locations.__contains__(mt):
                        self.locations[mt] = {}
                        
                    self.locations[mt][locNun] = 1  #[`mtime`][`id`] = 1
                    
                lastLoc = loc
                
            #{'adminDistrict': '四川省', 'adminDistrict2': '甘孜藏族自治州', 'countryRegion': '中华人民共和国', 'formattedAddress': '四川省甘孜藏族自治州新龙县', 'locality': '新龙县', 'countryRegionIso2': 'CN'}
            self.cursor.execute("SELECT `countryRegion`, count(`id`) as countid FROM `filelist` where (`countryRegion` IS not null and `countryRegion`<>'') and (`is_repeated`=0 or `is_repeated` is null or `is_repeated`='') group by `countryRegion` ")   
            results2 = self.cursor.fetchall() 
            n = len(results2)
            print(".. get country records: ",n)
            
            for p in results2:
                self.traces["country" ].append(cmap[p[0]])
                self.traces["quantity"].append(p[1])
                if p[1] > nmax:
                    nmax = p[1]       
        except:
            print(traceback.format_exc())
        
        print(self.traces)
        c = (
            pyMap(init_opts=pyOpts.InitOpts(width="2500px", height="1200px"))
            .add("Trace World by Country", [list(z) for z in zip(self.traces["country" ], self.traces["quantity"])], "world")
            .set_series_opts(label_opts = pyOpts.LabelOpts(is_show=False))
            .set_global_opts(
                title_opts    = pyOpts.TitleOpts(title="Trace World"),
                visualmap_opts= pyOpts.VisualMapOpts(max_=nmax),
            )
        )

        result = c.render(WindX['self_folder'] + "/FlightTraceByCountry.html")
        webbrowser.open_new_tab(result)
        
        #display locations ion the map
        g = Geo(init_opts=pyOpts.InitOpts(width="2500px", height="1200px"))
        data_pair = []
        lines = []
        lastid = 0  
        for mt in sorted(self.locations.keys()):
            for locNun in sorted(self.locations[mt].keys()):
                g.add_coordinate(locNun, self.localsCords[locNun][1], self.localsCords[locNun][0])
                data_pair.append((locNun,1))
                if lastid:
                    lines.append((lastid,locNun))
                lastid = locNun
            
        g.add_schema(maptype="china")
        g.add(
            "",
            data_pair,
            type_=ChartType.EFFECT_SCATTER,
            color="green",
        )
        g.add(
            "Flight Trace",
            lines,
            type_=ChartType.LINES,
            #effect_opts=pyOpts.EffectOpts(symbol=SymbolType.ARROW, symbol_size=6, color="blue"),
            linestyle_opts=pyOpts.LineStyleOpts(curve=0.2),
        )
        g.set_series_opts(label_opts=pyOpts.LabelOpts(is_show=False))
        g.set_global_opts(title_opts=pyOpts.TitleOpts(title="Trace World"))

        result = g.render(WindX['self_folder'] + "/FlightTraceLines.html")
        webbrowser.open_new_tab(result)
        
    def FileLocation_Map(self):
        print("map/estimate file location by date time ...")
        #check file md5_file, if null get md5 and save
        try:
            self.startTime= time.time()
            #get files which has location information
            self.cursor.execute("SELECT `id`,`name`,`dir_id` from `filelist` where countryRegion IS NOT NULL")  
            
            results = self.cursor.fetchall() 
            n = len(results)
            print(".. get file without location records: ",n)

            LocList = {}
            LocListDir = {}
            k = 0
            pnum = int(n / 10)
            if pnum < 100:
                pnum = 100
            for p in results:
                k +=1
                if k==1 or k % pnum == 0:
                    speed = (time.time() - self.startTime)/k
                    print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))             

                file_time = self.GetUsecondFromName(p[1])
                LocList[file_time] = p[0]
                
                DictToDict(LocListDir,[p[2],file_time])
                LocListDir[p[2]][file_time] = p[0]
                
            if n:
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))  
        
            #get files which has not location information
            self.startTime= time.time()
            self.cursor.execute("SELECT `id`,`name`,`dir_id` from `filelist` where `map_location_id`=0 and (`countryRegion` IS NULL OR `adminDistrict` IS NULL) ")  
            
            results = self.cursor.fetchall() 
            n = len(results)
            print("\n.. get file without location records: ",n)

            filelist = {}
            k = 0
            pnum = int(n / 20)
            if pnum < 100:
                pnum = 100
            nx = 0
            for p in results:
                k +=1
                if k==1 or k % pnum == 0:
                    speed = (time.time() - self.startTime)/k
                    print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))

                file_time = self.GetUsecondFromName(p[1])
                mint = 4000
                mapid = 0
                
                if LocListDir.__contains__(p[2]):
                    for t in range(file_time - 3600, file_time + 3600):
                        if LocListDir[p[2]].__contains__(t):
                            if abs(t - file_time) < mint:
                                mint = t - file_time
                                mapid = LocList[t]                    
                
                if not mapid:
                    mint = 4000
                    for t in range(file_time - 3600, file_time + 3600):
                        if LocList.__contains__(t):
                            if abs(t - file_time) < mint:
                                mint = t - file_time
                                mapid = LocList[t]
                            
                if mapid:
                    filelist[p[0]] = mapid
                    nx +=1                           
                
            if n:
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))
                
            print("\n.. get mapped location id: ",nx)
            if nx:
                print(".. save mapped location: ")
                self.startTime= time.time()
                k = 0
                n = nx
                pnum = int(nx / 20)
                if pnum < 100:
                    pnum = 100
                for id in filelist:
                    try:
                        k +=1
                        if k %pnum == 0:
                            self.db.commit()
                            
                            speed = (time.time() - self.startTime)/k
                            print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))                            

                        self.cursor.execute('UPDATE `filelist` SET `map_location_id`="{}" WHERE `id`="{}" '.format(filelist[id], id))                   
                    except:
                        print(traceback.format_exc())

                    #break
                self.db.commit()  
                
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))               
        except:
            print(traceback.format_exc())
        
    def FileListMD5Check(self):
        print("Check file MD5 ...")
        #check file md5_file, if null get md5 and save
        try:
            self.startTime= time.time()
            #get file list and map md5 string
            self.cursor.execute("SELECT `filelist`.`id`,`filelist`.`name`,`dirlist`.`path`, `filelist`.`dir_id` from `filelist` join `dirlist` where (`dirlist`.`id` = `filelist`.`dir_id`) and `filelist`.`md5_file` is null ORDER BY `filelist`.`dir_id` ")  
            
            results = self.cursor.fetchall() 
            n = len(results)
            print(".. get file records: ",n)

            filelist = {}
            k = 0
            pnum = int(n / 50)
            if pnum < 100:
                pnum = 100

            nx = 0
            for p in results:
                k +=1
                if k==1 or k % pnum == 0:
                    speed = (time.time() - self.startTime)/k
                    print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))

                filepath = p[2] + '/' + p[1]
                if os.path.exists(filepath):
                    try:
                        md5str,fsize = self.FileGetMD5_String(filepath)              
                        if md5str:
                            nx +=1
                            filelist[p[0]] = md5str                            
                    except:
                        print(traceback.format_exc())
                    

            if n:
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))            

            print(".. get file md5 string: ",nx)
            if nx:
                print(".. save file md5 string: ")
                self.startTime= time.time()
                k = 0
                pnum = int(nx / 20)
                if pnum < 100:
                    pnum = 100
                for id in filelist:
                    try:
                        k +=1
                        if k %pnum == 0:
                            self.db.commit()
                            
                            speed = (time.time() - self.startTime)/k
                            print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))                            

                        self.cursor.execute('UPDATE `filelist` SET `md5_file`="{}" WHERE `id`="{}" '.format(pymysql.escape_string(filelist[id]), id))                   
                    except:
                        print(traceback.format_exc())

                self.db.commit()  
                
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))               
            
        except:
            print(traceback.format_exc())          
        
    def FileGetMD5_Sync2Filelist(self):
        print("\nSync dm5 string to Filelist ... ...")
        self.startTime= time.time()

        self.ConnectDB()
        self.cursor = self.db.cursor()  #连接数据库的指针
        self.repeated = {}
        try:
            #get file md5 string
            self.cursor.execute("SELECT `filelist_md5`.`id`,`filelist_md5`.`md5`,`filelist_md5`.`name`,`dirlist`.`path`, `filelist_md5`.`dir_id`, `filelist_md5`.`filesize` " + \
                                       " from `filelist_md5` join `dirlist` where (`dirlist`.`id` = `filelist_md5`.`dir_id`) ORDER BY `md5`,`dir_id`,`name`")  
            
            results = self.cursor.fetchall() 
            n = len(results)
            print(".. get md5 records: ",n)

            fileMD5list = {}
            k = 0
            pnum = int(n / 10)
            if pnum < 100:
                pnum = 100

            for p in results:
                k +=1
                if k==1 or k % pnum == 0:
                    speed = (time.time() - self.startTime)/k
                    print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))

                fdir = re.sub(r'^H\:|^I\:','',p[3])
                if fdir:
                    DictToDict(fileMD5list,[fdir,p[2]])
                    fileMD5list[fdir][p[2]]['md5']  = p[1]
                    fileMD5list[fdir][p[2]]['size'] = p[5]

            if n:
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))


            #get file list and map md5 string
            self.cursor.execute("SELECT `filelist`.`id`,`filelist`.`size`,`filelist`.`name`,`dirlist`.`path`, `filelist`.`dir_id` " + \
                                       " from `filelist` join `dirlist` where (`dirlist`.`id` = `filelist`.`dir_id`) ORDER BY `name` ")  
            
            results = self.cursor.fetchall() 
            n = len(results)
            print(".. get file records: ",n)

            filelist = {}
            k = 0
            pnum = int(n / 10)
            if pnum < 100:
                pnum = 100

            nx = 0
            for p in results:
                k +=1
                if k==1 or k % pnum == 0:
                    speed = (time.time() - self.startTime)/k
                    print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))

                fdir = re.sub(r'^H\:|^I:','',p[3])
                if fileMD5list.__contains__(fdir) and fileMD5list[fdir].__contains__(p[2]) and fileMD5list[fdir][p[2]]['size'] == p[1]:
                    filelist[p[0]] = fileMD5list[fdir][p[2]]['md5']
                    nx +=1

            if n:
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))            

            print(".. get file md5 string: ",nx)
            if nx:
                print(".. save file md5 string: ")
                self.startTime= time.time()
                k = 0
                pnum = int(nx / 20)
                if pnum < 100:
                    pnum = 100
                for id in filelist:
                    try:
                        k +=1
                        if k %pnum == 0:
                            self.db.commit()
                            
                            speed = (time.time() - self.startTime)/k
                            print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))                            

                        self.cursor.execute('UPDATE `filelist` SET `md5_file`="{}" WHERE `id`="{}" '.format(pymysql.escape_string(filelist[id]), id))                   
                    except:
                        print(traceback.format_exc())

                self.db.commit()  
                
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))               
            
        except:
            print(traceback.format_exc())  

        if self.db:   
            self.cursor.close()
            self.db.close()         
    
    def FileGetMD5_String(self, filepath):
        md5str = "" 
        fsize  = ""
        try:
            myhash = hashlib.md5()                    
            fsize = str(os.stat(filepath).st_size)                                                     
            fhandle = open(filepath,'rb')
            rn = 0
            while True:
                b = fhandle.read(8096)
                if not b :
                    break
                rn +=1
                myhash.update(b)
            fhandle.close()
            
            if rn:
                myhash.update(fsize.encode(encoding='utf-8'))
                md5str = (myhash.hexdigest()).upper()
                
        except:
            print(traceback.format_exc())
            
        return md5str,fsize
                                
    def FileGetMD5(self, curDir=""):       
        print ('Total used:',usedTime(self.startTime),"\n\n",curDir + " ... \n------------------------")    
        os.chdir(curDir)
        
        self.ifiles = {}        
        self.filesDone = {}
        self.FileGetMD5_Done(curDir)      
        dirs = []
        fileNum = 0
                   
        for f in sorted(glob.glob("*")): 
            if (f == '.') or (f == '..') or (f == 'Faces') or (f == '_git') or (f == 'ThumbABC'):
                continue     
            
            if os.path.isdir(f):
                dirs.append(curDir + '/' + f)
                            
            elif os.path.isfile(f):
                self.process_qty +=1
                try:
                    md5str,fsize = self.FileGetMD5_String(curDir + '/' + f)    
                    #print(f,md5str,fsize)                
                    if md5str:
                        if not (self.filesDone.__contains__(f) and self.filesDone[f] == md5str):                                
                            fileNum +=1
                            self.ifiles[fileNum] = {'name':f, 'md5': md5str, 'fsize': fsize}
                        
                except:
                    print(traceback.format_exc())

        if fileNum:
            self.FileGetMD5_Save(curDir)

        if self.allFileQTY:  
            print("\n*******************************************************************") 
            print(curDir)
            if self.process_qty > 0:
                speed = int((time.time() - self.startTime)/self.process_qty*1000)/1000
                print(".. Avg processing speed: {} seconds/image".format(speed),', estimated left time:',usedTime(self.startTime,speed*(self.allFileQTY-self.process_qty)))
            print("-- Total processed files: " + str(self.process_qty) + "/" + str(self.allFileQTY) + " {:0>2.1f}".format(self.process_qty/self.allFileQTY*100) + "% done, used time so far:",usedTime(self.startTime))
            print("*******************************************************************\n")

        if len(dirs):
            for dirx in sorted(dirs):
                self.FileGetMD5(dirx)
                
    def FileGetMD5_Save(self, curDir=""):
        dir_id = self.DirGetID(curDir)
        if not dir_id:
            return   

        ck = 0
        for fn in self.ifiles:
            try:
                #print("\t",id,':',GPS[id])
                ck +=1
                if ck %1000 == 0:
                    self.db.commit()

                self.cursor.execute('INSERT INTO `filelist_md5` (`name`, `dir_id`, `md5`, `filesize`) VALUES ("{}", "{}", "{}", "{}") '.format(
                        pymysql.escape_string(self.ifiles[fn]["name"]), 
                        dir_id, 
                        pymysql.escape_string(self.ifiles[fn]["md5"]),
                        pymysql.escape_string(self.ifiles[fn]["fsize"])
                        ))                    
            except:
                print(traceback.format_exc())

        self.db.commit() 
            
    def FileGetMD5_Done(self, curDir=""):
        try:
            dir_id = self.DirGetID(curDir)
            if not dir_id:
                return               
            
            self.cursor.execute("SELECT `name`,`md5` from `filelist_md5` where `dir_id`='"+ dir_id +"' ")  
            results = self.cursor.fetchall() 
            n = len(results)
            print(".. get files done: ",n)

            for p in results:
                self.filesDone[p[0]] = p[1]

        except:
            print(traceback.format_exc())
    
    def ExportImagesByLabel(self,label_correct=None,act='raw'):
        if not label_correct:
            return

        topath = WindX['self_folder'] + '/Export'
        if not os.path.exists(topath):
            os.mkdir(topath)
            
        os.chdir(topath)
        if not os.path.exists(label_correct):
            os.mkdir(label_correct)

        if not os.path.exists(label_correct):
            print('failed to make path: ',topath + '/' + str(label_correct))
            return
        
        os.chdir(label_correct)
        print("\ncheck images of "+ str(label_correct) +" ... ...")
        self.startTime= time.time()

        try:
            self.cursor.execute("SELECT `filelist`.`name`,`dirlist`.`path`" + \
                                " from `faces` join `filelist` join `dirlist` " + \
                                "where (`faces`.`label_correct`='"+label_correct+"' and `faces`.`file_id`= `filelist`.`id` and `dirlist`.`id` = `filelist`.`dir_id` and `type`='image') ORDER BY `dirlist`.`path`")  
            results = self.cursor.fetchall() 
            n = len(results)
            print(".. get faces: ",n)

            k = 0
            pnum = 100

            for p in results:
                k +=1
                if k==1 or k % pnum == 0:
                    speed = (time.time() - self.startTime)/k
                    print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))

                filepath = p[1] + '/' + p[0]
                if os.path.exists(filepath):
                    folder = re.sub(r'\_+','_',re.sub(r'\/+|\\+|\s+|\:+|\(+|\)+','_',re.sub(r'^.*WE4\/PHOTO\/*','',p[1])))
                    '''
                    if folder:                        
                        if not os.path.exists(folder):
                            os.mkdir(folder)
                        if os.path.exists(folder):
                            if os.path.exists(p[1] + '/ThumbABC/W1080/' + p[0]):
                                filepath = p[1] + '/ThumbABC/W1080/' + p[0]

                            #print('copy image:',filepath,'to',folder,'/',p[0])
                            shutil.copy(filepath,folder + '/' + p[0])
                    '''
                    folder = re.sub(r'^.*年\_*|^.*以前\_|^X\_Z9999其他照片\_','',folder,re.I)
                    suffix = act
                    if act == '1080':
                        if os.path.exists(p[1] + '/ThumbABC/W1080/' + p[0]):
                            filepath = p[1] + '/ThumbABC/W1080/' + p[0]
                            suffix = '1080p'
                    shutil.copy(filepath, folder + ' ' + suffix + " " + p[0])
            if n:
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))

                print('\nExport to path: ',topath + '/' + str(label_correct))
        except:
            print(traceback.format_exc()) 

    def CheckRepeatedImages(self):
        #check repeated images and mark them as is_repeated = 1
        print("\ncheck repeated images ... ...")
        self.startTime= time.time()
        self.repeated = {}
        try:
            self.cursor.execute("SELECT `filelist`.`id`,`filelist`.`md5_file`,`filelist`.`name`,`filelist`.`dir_id`, `dirlist`.`path` from `filelist` join `dirlist` where `filelist`.`dir_id`=`dirlist`.`id` and `filelist`.`md5_file` is not null")  
            results = self.cursor.fetchall() 
            n = len(results)
            print(".. get records: ",n)

            filelist = {}
            k = 0
            pnum = int(n / 10)
            if pnum < 100:
                pnum = 100

            for p in results:
                k +=1
                if k==1 or k % pnum == 0:
                    speed = (time.time() - self.startTime)/k
                    print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))
                
                rank = 'R1'
                if re.match(r'PHOTOX',p[4],re.I):
                    rank = 'R2'
                        
                DictToDict(filelist,[p[1],"data",rank,p[0]])
                filelist[p[1]]["data"][rank][p[0]] = p[2]   #filelist - md5 - data - rank - id = name
                
                if filelist[p[1]].__contains__('number'):
                    filelist[p[1]]['number'] +=1
                else:
                    filelist[p[1]]['number'] = 1    
                 
            if n:
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))

            print("\t..All done! md5: ",len(filelist.keys()),'/',n,'\n')
            rn = 0
            rnn = 0
            nx  = 0
            updateList = {}
            for md5 in filelist:
                if filelist[md5]['number'] > 1:
                    rn +=1
                    rnn += filelist[md5]['number']
                    
                    keyid = 0  
                    keyname = "" 
                    keyrank = ''                 
                    if filelist[md5]["data"].__contains__('R1'):
                        keyrank = 'R1'
                        minLength = 10000
                        for id in filelist[md5]["data"]['R1']:
                            if len(filelist[md5]["data"]['R1'][id]) < minLength:
                                minLength = len(filelist[md5]["data"]['R1'][id])
                                keyid = id
                                keyname = filelist[md5]["data"]['R1'][id]
                    
                    elif filelist[md5]["data"].__contains__('R2'):
                        keyrank = 'R2'
                        minLength = 10000
                        for id in filelist[md5]["data"]['R2']:
                            if len(filelist[md5]["data"]['R2'][id]) < minLength:
                                minLength = len(filelist[md5]["data"]['R2'][id])
                                keyid = id  
                                keyname = filelist[md5]["data"]['R2'][id]
                    
                    #print(md5,keyrank, "keyid=",keyid,keyname," --- ", end="") 
                    updateList[keyid] = 0 
                    nx += 1         
                    for rank in filelist[md5]["data"]:
                        for id in filelist[md5]["data"][rank]:
                            if not id == keyid:
                                updateList[id] = 1
                                nx += 1
                                #print(id,filelist[md5]["data"][rank][id],", ", end="") 
                    #print(filelist[md5]['number'])                                                                   
                    
            print('\n----- repeated QTY (groupds, images)', rn, rnn)
            
            if nx:
                print(".. update to records: ",nx)
                self.startTime= time.time()
                k = 0
                n = nx
                pnum = int(nx / 20)
                if pnum < 100:
                    pnum = 100
                for id in updateList:
                    try:
                        k +=1
                        if k %pnum == 0:
                            self.db.commit()
                            
                            speed = (time.time() - self.startTime)/k
                            print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))                            

                        self.cursor.execute('UPDATE `filelist` SET `is_repeated`="{}" WHERE `id`="{}" '.format(updateList[id], id))                   
                    except:
                        print(traceback.format_exc())

                self.db.commit()  
                
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))  
        except:
            print(traceback.format_exc())

    def GPSInfoGet2(self): #seond way to get GPS information
        print("\nGPSInfoGet2 ... ...")
        self.startTime= time.time()

        self.ConnectDB()
        self.cursor = self.db.cursor()  #连接数据库的指针
        self.gps_saved = {}
        try:
            self.cursor.execute("SELECT `filelist`.`id`, `filelist`.`name`, `dirlist`.`path` FROM `filelist` join `dirlist` " + \
                                    " where `filelist`.`dir_id` = `dirlist`.`id` and (`filelist`.`exif_make` is not null AND `filelist`.`exif_make` LIKE '%Apple%') and " + \
                                        " (`filelist`.`latitude` IS NULL or `filelist`.`latitude`='') and " + \
                                            " (`filelist`.`longitude` IS null or `filelist`.`longitude`='') order by `filelist`.`id` DESC ")  
            results = self.cursor.fetchall() 
            n = len(results)
            print(".. get files: ",n)

            GPS={}
            nk = 0
            k = 0
            pnum = 100

            for p in results:
                k +=1
                if k==1 or k % pnum == 0:
                    speed = (time.time() - self.startTime)/k
                    print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))
                    #if k > 1:
                    #    self.GPSInfoToDB(GPS,nk)

                filepath = p[2] + '/' + p[1]  #'H:/WE4/_git/IMG_7368.JPG'
                if os.path.exists(filepath):
                    #print("\t    ",p[0],filepath)
                    gps_n = []
                    with open(filepath,'rb') as f:
                        try:
                            tags = exifread.process_file(f)
                            for tag in tags:  
                                #if not re.match(r'.*JPEGThumbnail|.*MakerNote',tag,re.I):          
                                #    print("\t\t",tag,":",tags[tag])
                                if re.match(r'.*GPS',tag,re.I):          
                                    gps_n.append("\t\t" + tag + ":" + str(tags[tag]))

                        except:
                            print("\t",traceback.format_exc()) 

                    if len(gps_n):
                        print("\t    ",p[0],filepath)
                        print('\n'.join(gps_n))
                        print('')

                else:
                    print('\tNot existing:',p[0],filepath)
                #GPSInfo = {1: 'N', 2: ((31, 1), (14, 1), (3392, 100)), 3: 'E', 4: ((121, 1), (29, 1), (5162, 100)), 5: b'\x00', 6: (58253, 3066), 7: ((3, 1), (27, 1), (20, 1)), 12: 'K', 13: (0, 1), 16: 'M', 17: (254201, 3812), 23: 'M', 24: (254201, 3812), 29: '2019:06:15', 31: (165, 1)}

            if n:
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))

            #self.GPSInfoToDB2(GPS,nk)
            print("\nAll done! Got GPS info: ",len(self.gps_saved.keys()),'/',n,'\n')

        except:
            print(traceback.format_exc())  

        if self.db:   
            self.cursor.close()
            self.db.close() 

    def GPS_Value_jsondumps(self,value,act=1):              
        try:
            jstr = json.dumps(value)
            #print("json.dumps(value)=",jstr)
            self.gpsinfo2 = jstr
        except:
            #print("\n#" + str(act), value)
            #print(traceback.format_exc())
            if act < 3:
                gps = {}
                for s in value:
                    #print(s,"=",value[s],":",str(type(value[s])))
                    gps[s] = [str(value[s]), str(type(value[s]))]
                    '''
                    if re.match(r'.*IFDRational|.*bytes',str(type(value[s])),re.I):
                        gps[s] = str(value[s])
                        #print(s,gps[s],":",str(type(gps[s])))
                    else:
                        gps[s] = value[s]
                    '''    
                    #print(s,"=",gps[s],":",str(type(gps[s])))
                #print(gps)                   
                self.GPS_Value_jsondumps(gps,act+1)   
                     
    def GPSInfoParse(self,gv,filepath="",model=""):
        #print("\nGPSInfoParse ... ...")
        gps = {
            'altitude': '', #海拔高度
            'GPSLongitude': '',  #经度 
            'GPSLatitude' : '',   #纬度
            'GPSLongitudeRef': "", #东西半球标识
            'GPSLatitudeRef' : ""  #南北半球标识
        }
        
        #          {1: 'N', 2: ((31, 1), (14, 1), (3392, 100)), 3: 'E', 4: ((121, 1), (29, 1), (5162, 100)), 5: b'\x00', 6: (58253, 3066), 7: ((3, 1), (27, 1), (20, 1)), 12: 'K', 13: (0, 1), 16: 'M', 17: (254201, 3812), 23: 'M', 24: (254201, 3812), 29: '2019:06:15', 31: (165, 1)}
        
        #iPhone XR {1: 'N', 2: (22.0, 40.0, 53.97), 3: 'E', 4: (109.0, 15.0, 20.98), 5: b'\x00', 6: 60.927385892116185, 12: 'K', 13: 0.028920661671765373, 16: 'T', 17: 205.55809399477806, 23: 'T', 24: 25.55809402671102,                   31: 16.774588142448454}
        #iPhone 12 {1: 'N', 2: (22.0, 50.0, 37.25), 3: 'E', 4: (108.0, 24.0, 40.87), 5: b'\x00', 6: 100.07397827211588, 12: 'K', 13: 9.8299999236915,      16: 'T', 17: 264.0360107421875,  23: 'T', 24: 264.0360107421875, 29: '2021:01:01', 31: 76.81722617836554}
        
        #{1: 'N', 2: (31.0, 22.0, 45.93), 3: 'E', 4: (121.0, 1.0, 21.13),  5: b'\x00', 6: 5.478824619011535, 7: (12.0, 19.0, 39.42), 12: 'K', 13: 0.0,               29: '2019:10:27', 31: 65.0, 'filePath': 'H:/WE4/PHOTO/NINGIP6S/ITOOLS PHOTOS/20191027-201947.JPG'}      
        #{1: 'N', 2: (22.0, 45.0, 37.68), 3: 'E', 4: (108.0, 17.0, 44.21), 5: b'\x00', 6: 0.0,               7: (10.0, 13.0, 0.0),   27: 'ASCII\x00\x00\x00NETWORK', 29: '2019:08:03',           'filePath': 'H:/WE4/PHOTO/NINGIP6S/ITOOLS PHOTOS/20190803-181301.JPG'}  
        #{1: 'N', 2: (31.0, 9.0, 21.01),  3: 'E', 4: (121.0, 20.0, 44.75),                                   7: (3.0, 48.0, 38.9),   12: 'K', 13: 0.0, 16: 'T', 17: 266.10513296227583, 23: 'T', 24: 266.10513296227583, 29: '2019:06:30', 31: 3.2821891101517893, 'filePath': 'H:/WE4/PHOTO/NINGIP6S/ITOOLS PHOTOS/20190630-114840.JPG'}
        
        if gv.__contains__(1) and re.match(r'[a-z]',gv[1],re.I) and \
           gv.__contains__(3) and re.match(r'[a-z]',gv[3],re.I) and \
           gv.__contains__(2) and isinstance(gv[2], tuple) and len(gv[2])==3 and \
           gv.__contains__(4) and isinstance(gv[4], tuple) and len(gv[4])==3:
           #gv.__contains__(12) and re.match(r'[a-z]',gv[12],re.I) and \
           #gv.__contains__(16) and re.match(r'[a-z]',gv[16],re.I) and \
           #gv.__contains__(23) and re.match(r'[a-z]',gv[23],re.I) and \           
           #gv.__contains__(5) and isinstance(gv[5], bytes) and \
           #gv.__contains__(6):
           
           try:
                if gv.__contains__(6):    
                    altitudeRef = 1 #Above Sea Level
                    if gv.__contains__(5):
                        if not re.match(r'.*x00', str(gv[5]), re.I):
                            altitudeRef = -1
                    gps['altitude'] = int(float(gv[6])*altitudeRef + 0.5)
                
                gps['GPSLatitudeRef']  = gv[1]
                gps['GPSLatitude']     = self.LocationConvertToDecimal(str(gv[2][0]), str(gv[2][1]), str(gv[2][2]), gps['GPSLatitudeRef']) #deg, minu, sec, GPS LatitudeRef
                
                gps['GPSLongitudeRef'] = gv[3]
                gps['GPSLongitude'] = self.LocationConvertToDecimal(str(gv[4][0]), str(gv[4][1]), str(gv[4][2]), gps['GPSLongitudeRef']) #对特殊的经纬度格式进行处理 deg, minu, sec, GPS LongitudeRef        
           except:
               pass
           
           if not (gps['GPSLatitude'] and gps['GPSLongitude']):
               gps['GPSLongitude'] = ""
               gps['GPSLatitude']  = ""
           
        else:
            #print("\n---- unkown GPS format ---\n",gv,"\n")
            try:
                isExist = 0
                gvv = {}
                for key in gv:
                    gvv[key] = re.sub(r'\d+','d+',str(gv[key]))
                    
                for mdx in self.unknownGPSformats:
                    isMatch = 1
                    for key in gv:
                        if not (self.unknownGPSformats[mdx]["mode"].__contains__(key) and gvv[key] == self.unknownGPSformats[mdx]["mode"][key]):
                            isMatch = 0
                            break
                            
                    if isMatch:
                        isExist = 1
                        self.unknownGPSformats[mdx]["qty"] +=1
                        break
                    
                if not isExist:
                    n = len(self.unknownGPSformats.keys()) + 1
                    if self.gpsinfo2:
                        try:
                            gv['filePath'] = filepath
                            gv['model'] = model
                            
                            self.unknownGPSformats[n] = {}
                            self.unknownGPSformats[n]["mode"]  = gvv    
                            self.unknownGPSformats[n]["value"] = gv 
                            self.unknownGPSformats[n]["qty"]   = 1
                        except:
                            print(traceback.format_exc())
            except:
                pass
                
        return gps        
        
    def GPSInfoGet(self):
        print("\nGPSInfoGet ... ...")
        self.startTime= time.time()
        self.gps_saved = {}
        try:
            self.cursor.execute("SELECT `filelist`.`id`, `filelist`.`name`, `dirlist`.`path`,`filelist`.`exif_model` FROM `filelist` join `dirlist` " + \
                                    " where `filelist`.`dir_id` = `dirlist`.`id` and (`filelist`.`exif_make` is not null) and (`filelist`.`exif_model` not like 'NIKON%')  and (`no_gps_info`=0 or `no_gps_info` is null) and " + \
                                        " ((`exif_gpsinfo2` IS null OR `exif_gpsinfo2`='') OR (`exif_gps_altitude` IS null OR `exif_gps_altitude`='') OR " + \
                                          "(`latitude` IS null      OR `latitude`=''     ) OR (`longitude` IS null         OR `longitude`=''        )) order by `filelist`.`id` DESC") 
            results = self.cursor.fetchall() 
            n = len(results)
            print(".. get files: ",n)
                    
            GPS={}
            nk = 0
            k = 0
            pnum = int(n / 20)
            if pnum < 100:
                pnum = 100

            self.unknownGPSformats = {}
            self.no_gps_info = []
            for p in results:
                k +=1
                if k==1 or k % pnum == 0:
                    speed = (time.time() - self.startTime)/k
                    print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))
                    if k > 1:
                        self.GPSInfoToDB(GPS,nk)

                filepath = p[2] + '/' + p[1]  #'H:/WE4/_git/IMG_7368.JPG'
                #filepath = 'G:/Work/OneDrive - Jabil/Pictures/Camera Roll/2021/20210101_050141615_iOS.jpg'
                if os.path.exists(filepath):
                    #print("\t",filepath)
                    with Image.open(filepath) as im:
                        info = im._getexif()
                        if info:
                            try:      
                                isget = 0  
                                for (tag, value) in info.items():                
                                    ikey = TAGS.get(tag, tag) #.lower()
                                    if type(ikey) != str:
                                        ikey = str(ikey)

                                    if ikey == 'GPSInfo':
                                        #print('\t\t',ikey,':', p[3],value)                                        
                                        isget = 1
                                        self.gpsinfo2 = ""
                                        self.GPS_Value_jsondumps(value)                                            
                                        gps = self.GPSInfoParse(value,filepath,p[3]) 
                                        #print("\n",self.gpsinfo2, "\n", gps)
                                        if self.gpsinfo2 and (not gps['altitude'] == ''):
                                            nk +=1                                            
                                            GPS[p[0]] = {}   
                                                                         
                                            GPS[p[0]]['gpsinfo2']  = self.gpsinfo2  
                                            GPS[p[0]]['altitude']  = gps['altitude']   
                                            GPS[p[0]]['latitude']  = gps['GPSLatitude']   
                                            GPS[p[0]]['longitude'] = gps['GPSLongitude']   
                                                                          
                                    elif re.match(r'.*gps',ikey,re.I):
                                        print("\t",p[0],filepath,'\n\t\t',ikey,':',value)
                                        
                                if isget == 0:
                                    self.no_gps_info.append(p[0])
                                #    print('\tNot get GPSInfo',filepath)                                     
                            except:
                                print("\t",traceback.format_exc()) 
                        else:
                            print('\tNot get exif info:',p[0],filepath)

                        #print(GPS)
                else:
                    print('\tNot existing:',p[0],filepath)
             

            if n:
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))

            self.GPSInfoToDB(GPS,nk)
            print("\nAll done! Got GPS info: ",len(self.gps_saved.keys()),'/',n,'\n')
            print("\nunknown GPS formats:") 
            for k in self.unknownGPSformats:
                print("\t", self.unknownGPSformats[k])

        except:
            print(traceback.format_exc())

    def GPSInfoToDB(self,GPS,nk):
        #return
    
        if nk:
            print("\t.. save GPS info to db: ",nk,"\n")
            ck = 0
            for id in GPS:
                if not self.gps_saved.__contains__(id):
                    try:
                        #print("\t",id,':',GPS[id])
                        ck +=1
                        if ck %1000 == 0:
                            self.db.commit()

                        self.cursor.execute('UPDATE `filelist` SET `lastupdate`="{}", `latitude`="{}", `longitude`="{}", `exif_gpsinfo2`="{}", `exif_gps_altitude`="{}" where `id`="{}" '.format(
                                                self.lastupdate,
                                                GPS[id]['latitude'],
                                                GPS[id]['longitude'],
                                                pymysql.escape_string(GPS[id]['gpsinfo2']),
                                                GPS[id]['altitude'],
                                                id
                                            ))                    
                        self.gps_saved[id] = 1
                    except:
                        print(traceback.format_exc())
            self.db.commit()
        
        if len(self.no_gps_info):
            print("\t.. save no GPS info to db: ",len(self.no_gps_info),"\n")
            ck = 0
            for id in self.no_gps_info:
                    try:
                        ck +=1
                        if ck %1000 == 0:
                            self.db.commit()
                        self.cursor.execute('UPDATE `filelist` SET `no_gps_info`="{}" where `id`="{}" '.format(1,id))
                    except:
                        print(traceback.format_exc())
            self.db.commit() 
            self.no_gps_info = []        

    def LocationToCoordinates(self):
        #按照地点查询经纬度 latitude longitude # 通过地址获取经纬度
        print("\nLocationToCoordinates ... ...")        
        self.baidu_maps_appkey = "g5AfygI95PwX8HO7S9T4tlchKEfMaMNZ"
        self.baidu_maps_snkey  = 'RyTYGPPTqU58dYgiksBzb9Vub166GATd'
        try:
            self.cursor.execute("SELECT `id`,`latitude`, `longitude`, `countryRegion`,`adminDistrict`, `adminDistrict2`, `locality`,`formattedAddress` " +\
                                "FROM `filelist` " + \
                                "where  ((`countryRegion` IS not null and `countryRegion`<>'') and (`adminDistrict` IS not null and `adminDistrict`<>'') and " +\
                                         "(`locality` IS not null and `locality`<>''))")            
                               #((`latitude` IS null OR `latitude`='') OR (`longitude` IS null OR `longitude`='')) and
                               #{'adminDistrict': '四川省', 'adminDistrict2': '甘孜藏族自治州', 'countryRegion': '中华人民共和国', 'formattedAddress': '四川省甘孜藏族自治州新龙县', 'locality': '新龙县'}
            
            results = self.cursor.fetchall()
            n = len(results)
            print("\n.. get locations information: ",n)
            
            self.knowns = {}
            self.unknowns = {}
            nx = 0
            for p in results:
                address = p[7]
                if (not address) or (address == "NA"):
                    address = p[3] + p[4] + p[5] + p[6]
                address = re.sub(r'\s+','',re.sub(r'(NA)+','',re.sub(r'\-+','',re.sub(r'\s+','',address,re.I))))
                
                city = p[5]
                if not city:
                    city = p[3] + p[4]
                else:                    
                    city = p[3] + p[4] + p[5]
                city = re.sub(r'(NA)+','',re.sub(r'\-+','',re.sub(r'\s+','',city,re.I)))
                #print(city, "-----", address)   
                                 
                ikey = str(base64.b64encode((city + ' ' + address).encode(encoding='utf-8')),'utf-8')

                if re.match(r'\-*\d+\.*\d*', str(p[1])) and re.match(r'\-*\d+\.*\d*', str(p[2])):
                    if not self.knowns.__contains__(ikey):
                        self.knowns[ikey] = []
                    self.knowns[ikey].append(p)                    
                else:
                    if not self.unknowns.__contains__(ikey):
                        self.unknowns[ikey] = []
                    self.unknowns[ikey].append([p, city, address]) 
                    nx += 1                
            
            print(".. get locations with unknown Coordinates: ",nx)
            self.startTime= time.time()
            self.getCoords = []
                
            n = nx
            k = 0
            pnum = 1000
            coords_get = 0
            for ikey in self.unknowns.keys():
                for px in self.unknowns[ikey]:
                    k +=1
                    if k==1 or k % pnum == 0:
                        speed = (time.time() - self.startTime)/k                    
                        print("\n\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}, got coords {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k)), coords_get))
                        if k > 1:
                            self.LocationToCoordinatesToDB(coords_get)
                        #print("\t",end="")  
                    address = px[2] #"广西横县横州镇西城路173号"
                    city    = px[1] #"广西南宁市"  
                    if self.knowns.__contains__(ikey):
                        coords_get +=1
                        if self.knowns[ikey][0][0]:
                            self.getCoords.append([px[0][0], self.knowns[ikey][0][1], self.knowns[ikey][0][2], 'from known id=' + str(self.knowns[ikey][0][0]), city, address])
                        else:
                            self.getCoords.append([px[0][0], self.knowns[ikey][0][1], self.knowns[ikey][0][2], 'from BaiDu M', city, address])
                            
                    else:    
                        try: 
                            if address:
                                # 以get请求为例http://api.map.baidu.com/geocoder/v2/?address=百度大厦&output=json&ak=你的ak
                                queryStr = '/geocoding/v3/?address={}&city={}&output=json&ak={}'.format(address, city, self.baidu_maps_appkey)
                                # 对queryStr进行转码，safe内的保留字符不转换
                                encodedStr = urlParse.quote(queryStr, safe="/:=&?#+!$,;'@()*[]") 
                                # 在最后直接追加上yoursk
                                rawStr = encodedStr + self.baidu_maps_snkey
                                #计算sn
                                sn = hashlib.md5(urlParse.quote_plus(rawStr).encode("utf8")).hexdigest()
                                #由于URL里面含有中文，所以需要用parse.quote进行处理，然后返回最终可调用的url
                                url = urlParse.quote("http://api.map.baidu.com"+queryStr+"&sn="+sn, safe="/:=&?#+!$,;'@()*[]")
                                
                                response = requests.get(url)
                                answer = response.json()
                                data = {}
                                if (answer['status'] == 0):
                                    data = {
                                        'lng': answer['result']['location']["lng"], # 经度
                                        'lat': answer['result']['location']["lat"]  # 纬度
                                    }
                                    coords_get +=1
                                    self.getCoords.append([px[0][0], data['lat'], data['lng'], 'from BaiDu', city, address])
                                    
                                    if not self.knowns.__contains__(ikey):
                                        self.knowns[ikey] = []
                                    self.knowns[ikey].append([0, data['lat'], data['lng']])
                                    
                                #print("\t\t", address,"\n\t\t",answer,"\n\t\t", data)
                                #{"status":0,"result":{"location":{"lng":116.50104690641698,"lat":39.79092147361288},"precise":1,"confidence":80,"level":"地产小区"}}
                        except:
                            print(traceback.format_exc())
            
            if n:
                self.LocationToCoordinatesToDB(coords_get)
                speed = (time.time() - self.startTime)/k
                print("\n\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, got coords {}".format(k,n,k/n*100,usedTime(self.startTime),speed, coords_get))
          
            print("\nAll done! Got coordinates: ",coords_get,'/',n,'\n')
            #for px in self.getCoords:
            #    print(px)

        except:
            print(traceback.format_exc()) 
            
    def LocationToCoordinatesToDB(self,nk):
        print("\t.. save locations to db total: ",nk)
        #return
        ck = 0
        try:
            for p in self.getCoords:
                try:
                    #print("\t",p)
                    ck +=1
                    if ck %500 == 0:
                        self.db.commit(), 

                    self.cursor.execute('UPDATE `filelist` SET `lastupdate`="{}", `latitude`="{}", `longitude`="{}", `coords_from`="{}" where `id`="{}" '.format(self.lastupdate, p[1], p[2], p[3], p[0]))     
                except:
                    print(traceback.format_exc())

            self.db.commit() 
        except:
            print(traceback.format_exc())
        
        self.getCoords = []
    
    def LocationConvertToDecimal(self,*gps): #将经纬度转换为小数形式
        #度
        gps_d = 0 
        gps_m = 0 
        gps_s = 0
        
        if '/' in gps[0]:
            deg = gps[0].split('/')
            if deg[0] == '0' or deg[1] == '0':
                gps_d = 0
            else:
                gps_d = float(deg[0]) / float(deg[1])
        else:
            gps_d = float(gps[0])
            
        #分
        if '/' in gps[1]:
            minu = gps[1].split('/')
            if minu[0] == '0' or minu[1] == '0':
                gps_m = 0
            else:
                gps_m = (float(minu[0]) / float(minu[1])) / 60
        else:
            gps_m = float(gps[1]) / 60
            
        #秒
        if '/' in gps[2]:
            sec = gps[2].split('/')
            if sec[0] == '0' or sec[1] == '0':
                gps_s = 0
            else:
                gps_s = (float(sec[0]) / float(sec[1])) / 3600
        else:
            gps_s = float(gps[2]) / 3600

        decimal_gps = gps_d + gps_m + gps_s
        
        #如果是南半球或是西半球
        if gps[3] == 'W' or gps[3] == 'S' or gps[3] == "83" or gps[3] == "87":
            decimal_gps = decimal_gps * -1

        return "{:.010f}".format(decimal_gps)
        

    def LocationFind(self):
        print("\nLocationFind ... ...")
        self.startTime= time.time()
        self.location_saved = {}
        
        self.loc_exist = {}
        try: 
            print(".. get existing mapped locations ... ...")
            self.cursor.execute("SELECT `id`,`latitude`,`longitude`, `adminDistrict`, `adminDistrict2`, `countryRegion`, `formattedAddress`, `locality`, `countryRegionIso2`, `addressLine` " + \
                                "FROM `filelist` where (`latitude` IS not null and `latitude`<>'') and (`longitude` IS not null and `longitude`<>'') and " + \
                                        " (`countryRegion` IS not null and `countryRegion`<>'') and (`addressLine` IS not null and `addressLine`<>'') and `map_location_id`= 0")  
            results = self.cursor.fetchall()  
            print("\t.. get mapped locations: ", len(results))          
            for p in results:
                #print("{:.010f}".format(float(p[1])) + ' ' + "{:.010f}".format(float(p[2])))
                igps = str(base64.b64encode(("{:.010f}".format(float(p[1])) + ' ' + "{:.010f}".format(float(p[2]))).encode(encoding='utf-8')),'utf-8')
                self.loc_exist[igps] = {
                    'latitude' : p[1],
                    'longitude': p[2],
                    'adminDistrict':     p[3],
                    'adminDistrict2':    p[4],
                    'countryRegion':     p[5],
                    'formattedAddress':  p[6],
                    'locality':          p[7],
                    'countryRegionIso2': p[8],
                    'addressLine':       p[9]                    
                }  
                
                #print(igps,self.loc_done[igps])          
        except:
            print(traceback.format_exc())

        try:
            self.cursor.execute("SELECT `id`,`latitude`,`longitude` FROM `filelist` where (`latitude` IS not null and `latitude`<>'') and (`longitude` IS not null and `longitude`<>'') and " + \
                                    "((`countryRegion` IS null OR `countryRegion`='') ) ") #OR `map_location_id`<> 0
            results = self.cursor.fetchall()
            n = len(results)
            print("\n.. get gps information: ",n)
            
            GPS={}
            nk = 0
            nx = 0
            k = 0
            loc_not_exist = []
            for p in results:
                igps = str(base64.b64encode(("{:.010f}".format(float(p[1])) + ' ' + "{:.010f}".format(float(p[2]))).encode(encoding='utf-8')),'utf-8')
                if self.loc_exist.__contains__(igps):
                   GPS[p[0]] = self.loc_exist[igps]
                   nk +=1 
                   k +=1
                else:
                   loc_not_exist.append([p[0], p[1], p[2], igps])  
                   nx +=1
            if nk:
                self.LocationToDB(GPS,nk)
            
            if not nx:
                return
            
            #print(loc_not_exist)
            #return
            
            pnum = 100
            checkdone = {}            
            loc_no_return = 0
            for p in loc_not_exist:
                k +=1
                if k==1 or k % pnum == 0:
                    speed = (time.time() - self.startTime)/k                    
                    print("\n\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}, no return total {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k)), loc_no_return))
                    if k > 1:
                        self.LocationToDB(GPS,nk) 
                    print("\t",end="")                   

                try:
                    #igps = str(base64.b64encode(("{:.010f}".format(float(p[1])) + ' ' + "{:.010f}".format(float(p[2]))).encode(encoding='utf-8')),'utf-8')
                    igps = p[3]
                    if checkdone.__contains__(igps):
                        GPS[p[0]] = GPS[checkdone[igps]]
                        nk +=1
                    elif self.loc_exist.__contains__(igps):
                        print("*",end="",flush=True)
                        GPS[p[0]] = self.loc_exist[igps]
                        nk +=1
                    else: 
                        if p[1] and p[2]:
                            isGood = 0
                            res = {
                                'latitude' : p[1],
                                'longitude': p[2],
                                'adminDistrict':'',
                                'adminDistrict2':'',
                                'countryRegion':'',
                                'formattedAddress':'',
                                'locality': '',
                                'countryRegionIso2': '',
                                'addressLine':''
                            }  

                            if self.LocationFind_use_bingmaps_service:
                                data = {
                                    'point': p[1] + ',' + p[2],  #A point on the Earth specified by a latitude and longitude
                                    'includeEntityTypes': 'Address', #A comma separated list of entity types selected from the following options:
                                    'c': 'zh-Hans',  #A string specifying the culture parameter
                                    'o': '',  #If empty, default output would be a JSON data string, If given xml, the output would be an xml data string
                                    'includeNeighborhood': 1,
                                    'key': self.bingmaps_key                                    
                                }
                                                            
                                for i in range(3):
                                    if isGood:
                                        break

                                    try:
                                        print(".",end="",flush=True)
                                        WindX['FindLocationLastRequestTime'] = time.time()
                                        
                                        loc_by_point = LocationByPoint(data,'http')      
                                        #print(iGPS,'\nstatus_code:',loc_by_point.status_code)                      
                                        if loc_by_point.status_code == 200:                                         
                                            nn = 0     
                                            for addr in loc_by_point.get_address:
                                                for key in addr:
                                                    nn +=1
                                                    #print('\t',key,'=',addr[key])  
                                                    res[key] = addr[key]     #{'adminDistrict': '四川省', 'adminDistrict2': '甘孜藏族自治州', 'countryRegion': '中华人民共和国', 'formattedAddress': '四川省甘孜藏族自治州新龙县', 'locality': '新龙县', 'countryRegionIso2': 'CN'}
                                                break

                                            if nn:                                    
                                                #print('\t',res)
                                                nk +=1
                                                GPS[p[0]] = res
                                                checkdone[igps] = p[0]
                                            else:
                                                loc_no_return +=1
                                                #print('\tLocationByPoint, no return (#'+str(i)+', '+ str(k) +'):',iGPS)
                                            
                                            isGood = 1
                                        else:
                                            print('\terror:',loc_by_point.status_code)                                     
                                    except:
                                        print(traceback.format_exc())
                                        print("\twait for 3 seconds ...")
                                        time.sleep(3)

                            elif self.LocationFind_use_baidu_service: 
                                try:                              
                                    # 以get请求为例http://api.map.baidu.com/geocoder/v2/?address=百度大厦&output=json&ak=你的ak
                                    queryStr = '/reverse_geocoding/v3/?ak={}&output=json&coordtype=wgs84ll&location={},{}'.format(self.baidu_maps_appkey, p[1], p[2])   #`latitude`,`longitude`
                                    # 对queryStr进行转码，safe内的保留字符不转换
                                    encodedStr = urlParse.quote(queryStr, safe="/:=&?#+!$,;'@()*[]") 
                                    # 在最后直接追加上yoursk
                                    rawStr = encodedStr + self.baidu_maps_snkey
                                    #计算sn
                                    sn = hashlib.md5(urlParse.quote_plus(rawStr).encode("utf8")).hexdigest()
                                    #由于URL里面含有中文，所以需要用parse.quote进行处理，然后返回最终可调用的url
                                    url = urlParse.quote("http://api.map.baidu.com"+queryStr+"&sn="+sn, safe="/:=&?#+!$,;'@()*[]")
                                    response = requests.get(url)
                                    answer = response.json()                                    
                                    
                                    if answer['status'] == 0 and answer['result']['formatted_address']:
                                        country = answer['result']['addressComponent']['country']
                                        if answer['result']['addressComponent']['country_code_iso2'] == 'CN':
                                            country = '中华人民共和国'
                                            
                                        res = {
                                            'latitude' : p[1],
                                            'longitude': p[2],
                                            'adminDistrict':     answer['result']['addressComponent']['province'],
                                            'adminDistrict2':    answer['result']['addressComponent']['city'],
                                            'countryRegion':     country,
                                            'formattedAddress':  answer['result']['formatted_address'],
                                            'locality':          answer['result']['addressComponent']['district'],
                                            'countryRegionIso2': answer['result']['addressComponent']['country_code_iso2'],
                                            'addressLine':       answer['result']['addressComponent']['street']
                                        } 
                                        
                                        nk +=1
                                        GPS[p[0]] = res
                                        checkdone[igps] = p[0]
                                        isGood = 1
                                        
                                        #print(res)
                                    else:
                                        loc_no_return +=1
                                        
                                    '''
                                    print(answer)                      
                                    {'status': 0, 
                                    'result': {
                                        'location': {'lng': 106.72190409324523, 'lat': 21.9756233028995}, 
                                        'formatted_address': '广西壮族自治区崇左市凭祥市', 
                                        'business': '', 
                                        'addressComponent': {
                                            'country': '中国', 
                                            'country_code': 0, 
                                            'country_code_iso': 'CHN', 
                                            'country_code_iso2': 'CN', 
                                            'province': '广西壮族自治区', 
                                            'city': '崇左市', 
                                            'city_level': 2, 
                                            'district': '凭祥市', 
                                            'town': '', 
                                            'town_code': '', 
                                            'adcode': '451481', 
                                            'street': '', 
                                            'street_number': '',
                                            'direction': '', 
                                            'distance': ''
                                            }, 
                                        'pois': [], 
                                        'roads': [], 
                                        'poiRegions': [], 
                                        'sematic_description': '', 
                                        'cityCode': 144}
                                    }
                                    '''
                                except:
                                    print(traceback.format_exc())
                                    
                            #if not GPS.__contains__(p[0]):
                            #    GPS[p[0]] = res
                            #    nk +=1

                except:
                    print(traceback.format_exc())
            if n:
                speed = (time.time() - self.startTime)/k
                print("\n\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, no return total {}".format(k,n,k/n*100,usedTime(self.startTime),speed, loc_no_return))

            self.LocationToDB(GPS,nk)            
            print("\nAll done! Got locations: ",len(self.location_saved.keys()),'/',n,'\n')

        except:
            print(traceback.format_exc()) 

    def LocationToDB(self,GPS,nk):
        print("\t.. save locations to db total: ",nk)
        #return
        ck = 0
        try:
            for id in GPS:
                if not self.location_saved.__contains__(id):
                    try:
                        #print("\t",id,':',GPS[id])
                        ck +=1
                        if ck %1000 == 0:
                            self.db.commit()

                        self.cursor.execute('UPDATE `filelist` SET `lastupdate`="{}", `adminDistrict`="{}", `adminDistrict2`="{}", `countryRegion`="{}", `formattedAddress`="{}", `locality`="{}", `countryRegionIso2`="{}",`addressLine`="{}" where `id`="{}" '.format(
                                        self.lastupdate,               
                                        GPS[id]['adminDistrict'],
                                        GPS[id]['adminDistrict2'],
                                        GPS[id]['countryRegion'],
                                        GPS[id]['formattedAddress'],
                                        GPS[id]['locality'],
                                        GPS[id]['countryRegionIso2'],
                                        GPS[id]['addressLine'],
                                        id
                                    ))     
                        
                        self.location_saved[id] = 1
                    except:
                        print(traceback.format_exc())

            self.db.commit() 
        except:
            print(traceback.format_exc())
                            
    def LocationFind2(self):
        print("\nLocationFind ... ...")
        self.startTime= time.time()

        self.ConnectDB()
        self.cursor = self.db.cursor()  #连接数据库的指针
        self.location_saved = {}
        try:
            self.cursor.execute("SELECT `id`,`exif_gpsinfo`,`exif_model` FROM `filelist` where (exif_gpsinfo IS NOT NULL) AND (latitude IS NULL OR latitude='') ")  
            results = self.cursor.fetchall()
            n = len(results)
            print(".. get gps information: ",n)
            GPS={}
            nk = 0
            k = 0
            pnum = 100
            checkdone = {}

            for p in results:
                k +=1
                if k==1 or k % pnum == 0:
                    speed = (time.time() - self.startTime)/k
                    print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))
                    if k > 1:
                        self.LocationToDB(GPS,nk)

                try:
                    igps = str(base64.b64encode(p[1].encode(encoding='utf-8')),'utf-8')
                    if checkdone.__contains__(igps):
                        GPS[p[0]] = GPS[checkdone[igps]]
                        nk +=1
                    else:
                        value = re.split(r'\s+',re.sub(r'\(|\)|\,',' ',p[1]))   
                        #Apple XR: N(31, 1)(22, 1)(4540, 100) E(121, 1)(1, 1)(2160, 100) 
                        #print('\t',p[0],p[1],p[2])     #Iphone4: N(31, 1)(252, 100)(0, 1) E(121, 1)(1263, 100)(0, 1)      Apple XR: N(31, 1)(22, 1)(4540, 100) E(121, 1)(1, 1)(2160, 100)
                        #print('\t',value)    #['N', '31', '1', '252', '100', '0', '1', 'E', '121', '1', '1263', '100', '0', '1', '']
                                              #  0    1     2    3      4      5    6    7    8      9    10      11    12   13   
                        
                        if len(value) >= 13:
                            iGPS = {}
                            #南北半球标识
                            if value[0] and re.match(r'[a-z]',value[0],re.I):
                                iGPS['GPSLatitudeRef'] = str(value[0])
                            else:
                                iGPS['GPSLatitudeRef'] = 'N' #缺省设置为北半球

                            
                            #东西半球标识
                            if value[7] and re.match(r'[a-z]',value[7],re.I):
                                iGPS['GPSLongitudeRef'] = str(value[7])
                            else:
                                iGPS['GPSLongitudeRef'] = 'E' #缺省设置为东半球
                            
                            #获取纬度                                                   
                            deg = str(value[1])
                            minu = '0'
                            sec  = '0'
                            if value[5] == '0':
                                minu = str(int(value[3])) + '/' + str(int(value[4]))
                            else:
                                minu = str(value[3])
                                sec  = str(int(value[5]) / 4) + '/' + str(int(value[6])/4)
                            #将纬度转换为小数形式
                            iGPS['GPSLatitude'] = self.LocationConvertToDecimal(deg, minu, sec, iGPS['GPSLatitudeRef'])
                            
                            #获取经度                    
                            deg = str(value[8]) 
                            minu = '0'
                            sec  = '0'
                            if value[12] == '0':
                                minu  = str(int(value[10]) / 5) + '/' + str(int(value[11])/5)
                            else:
                                minu = str(value[10])
                                sec  = str(int(value[12]) / 2) + '/' + str(int(value[13])/2)
                            #将经度转换为小数形式
                            iGPS['GPSLongitude'] = self.LocationConvertToDecimal(deg, minu, sec, iGPS['GPSLongitudeRef'])#对特殊的经纬度格式进行处理

                            if iGPS['GPSLatitude'] and iGPS['GPSLongitude']:
                                data = {
                                    'point': iGPS['GPSLatitude'] + ',' + iGPS['GPSLongitude'],  #A point on the Earth specified by a latitude and longitude
                                    'includeEntityTypes': 'Address', #A comma separated list of entity types selected from the following options:
                                    'c': 'zh-Hans',  #A string specifying the culture parameter
                                    'o': '',  #If empty, default output would be a JSON data string, If given xml, the output would be an xml data string
                                    'includeNeighborhood': 1,
                                    'key': self.bingmaps_key                                    
                                }
                        

                                isGood = 0
                                res = {
                                    'latitude': iGPS['GPSLatitude'],
                                    'longitude': iGPS['GPSLongitude'],
                                    'adminDistrict':'',
                                    'adminDistrict2':'',
                                    'countryRegion':'',
                                    'formattedAddress':'',
                                    'locality': '',
                                    'countryRegionIso2': '',
                                    'addressLine':''
                                }  

                                for i in range(3):
                                    if isGood:
                                        break

                                    try:
                                        loc_by_point = LocationByPoint(data,'http')      
                                        #print(iGPS,'\nstatus_code:',loc_by_point.status_code)                      
                                        if loc_by_point.status_code == 200:                                         
                                            nn = 0     
                                            for addr in loc_by_point.get_address:
                                                for key in addr:
                                                    nn +=1
                                                    #print('\t',key,'=',addr[key])  
                                                    res[key] = addr[key]     #{'adminDistrict': '四川省', 'adminDistrict2': '甘孜藏族自治州', 'countryRegion': '中华人民共和国', 'formattedAddress': '四川省甘孜藏族自治州新龙县', 'locality': '新龙县', 'countryRegionIso2': 'CN'}
                                                break

                                            if nn:                                    
                                                #print('\t',res)
                                                nk +=1
                                                GPS[p[0]] = res
                                                checkdone[igps] = p[0]
                                            else:
                                                print('\tLocationByPoint, no return:',iGPS,'\n\t',p[0],p[1],p[2],'\n\t',value,'\n')
                                            
                                            isGood = 1
                                        else:
                                            print('\terror:',loc_by_point.status_code)                                     
                                    except:
                                        print(traceback.format_exc())
                                        print("\twait for 3 seconds ...")
                                        time.sleep(3)

                                if not GPS.__contains__(p[0]):
                                    GPS[p[0]] = res
                                    nk +=1

                except:
                    print(traceback.format_exc())
            if n:
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))


            self.LocationToDB(GPS,nk)
            print("\nAll done! Got locations: ",len(self.location_saved.keys()),'/',n,'\n')

        except:
            print(traceback.format_exc())  

        #if self.db:   
            #self.cursor.close()
            #self.db.close() 

    def LocationToDB2(self,GPS,nk):
        print("\t.. save locations to db: ",nk)
        ck = 0
        for id in GPS:
            if not self.location_saved.__contains__(id):
                try:
                    #print("\t",id,':',GPS[id])
                    ck +=1
                    if ck %1000 == 0:
                        self.db.commit()

                    self.cursor.execute('UPDATE `filelist` SET `latitude`="{}",`longitude`="{}",`adminDistrict`="{}", `adminDistrict2`="{}", `countryRegion`="{}", `formattedAddress`="{}", `locality`="{}", `countryRegionIso2`="{}",`addressLine`="{}" where `id`="{}" '.format(
                                    GPS[id]['latitude'],
                                    GPS[id]['longitude'],                
                                    GPS[id]['adminDistrict'],
                                    GPS[id]['adminDistrict2'],
                                    GPS[id]['countryRegion'],
                                    GPS[id]['formattedAddress'],
                                    GPS[id]['locality'],
                                    GPS[id]['countryRegionIso2'],
                                    GPS[id]['addressLine'],
                                    id
                                ))     
                    
                    self.location_saved[id] = 1
                except:
                    print(traceback.format_exc())

        self.db.commit() 

    def SyncFileID(self):
        print("\nsync file id to faces table ... ...")
        self.startTime= time.time()

        try:
            self.cursor.execute("SELECT `id`,`face_idx`,`is_repeated` FROM `filelist` where `face_idx` is not null")
            results = self.cursor.fetchall()
            n = len(results)
            print(".. get face_idx from filelist table:",n)
            filelist={}
            for p in results:
                filelist[p[1]] = [p[0],p[2]]

            self.cursor.execute("SELECT `id`,`idx` FROM `faces` where `idx` is not null and (`file_id` is null or `file_id`='') ") 
            results = self.cursor.fetchall()
            n = len(results)
            print(".. get idx from faces table:",n)
            if not n:
                return
            
            facelist={}
            for p in results:
                facelist[p[0]] = p[1]   #id -- idx            

            print(".. map face_idx to face idx ... ")
            for id in facelist:
                if filelist.__contains__(facelist[id]):
                    facelist[id] = filelist[facelist[id]]  #id --  [file_id,is_repeated]
                else:
                    facelist[id] = []

            print(".. save file id to faces table ... ")
            k = 0
            pnum = 1000
            for id in facelist:
                k +=1
                if k==1 or k % pnum == 0:
                    if k > 1:
                        self.db.commit()
                    speed = (time.time() - self.startTime)/k
                    print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))

                if not len(facelist[id]):
                    continue

                try:                       
                    self.cursor.execute('UPDATE `faces` SET `file_id`="{}", `is_repeated`="{}" where `id`="{}" '.format(facelist[id][0], facelist[id][1], id))                         
                except:
                    print(traceback.format_exc())

            self.db.commit() 
            if n:
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))

        except:
            print(traceback.format_exc())  
                
    def SyncfaceImageID(self):
        print("\nsync image id to faces table ... ...")
        self.startTime= time.time()
        try:
            self.cursor.execute("SELECT `id`,`path` FROM `faces_image` where `path` is not null and `path`<>'' ")
            results = self.cursor.fetchall()
            n = len(results)
            print(".. get records from `faces_image` table:",n)
            filelist={}
            for p in results:  
                x = str(base64.b64encode(p[1].encode(encoding='utf-8')),'utf-8')                               
                filelist[x] = p[0]            


            self.cursor.execute("SELECT `id`,`path` FROM `faces` where `path` is not null and `path`<>''")
            results = self.cursor.fetchall()
            n = len(results)
            print(".. get records from faces table:",n)
            facelist={}
            n = 0
            for p in results:
                x = str(base64.b64encode(p[1].encode(encoding='utf-8')),'utf-8') 
                if filelist.__contains__(x):
                    facelist[p[0]] = filelist[x] 
                    n +=1

            print(".. image id to faces table ... ",n)
            k = 0
            pnum = 500
            for id in facelist:
                k +=1
                if k==1 or k % pnum == 0:
                    speed = (time.time() - self.startTime)/k
                    print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))

                try:
                    self.cursor.execute("UPDATE `faces` SET `image_id`='"+ str(facelist[id]) +"' where `id`='"+ str(id) +"' ")                          
                except:
                    print(traceback.format_exc())

            self.db.commit() 
            if n:
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))

        except:
            print(traceback.format_exc()) 

    def GetFileQTY(self,curDir):
        #获取当前文件夹及其子文件夹里所有照片的数量
        os.chdir(curDir)

        qty = 0
        exfms=[]
        xstr = ""
        for formati in self.formats:
            qx = glob.glob("*." + formati)   
            qty += len(qx)
            if len(qx) > 0:
                xstr += curDir + ": " + str(len(qx)) + " " + formati + u" 照片\n"
                exfms.append(formati) 
        
        self.allPicQTY += qty
        
        print(xstr + curDir + ": TOTAL "+ str(qty) + " " + "/".join(exfms) + u" 照片\n")
        
        dirs = []
        for f in glob.glob("*"): 
            if (f == '.') or (f == '..') or (str(f).upper() == "THUMBABC") or (f=='Faces') or (f=='_git'):
                continue
                                        
            if os.path.isdir(curDir + "/" + f):
                dirs.append(curDir + "/" + f)    
            
            elif os.path.isfile(curDir + "/" + f):
                self.allFileQTY +=1                
                
        if len(dirs):
            for dirx in sorted(dirs):
                self.GetFileQTY(dirx)
    
    def FileRepeatedDelete(self,curDir):
        print("\n.... FileRepeatedDelete - checking:",curDir)
        os.chdir(curDir)        
        
        for f in glob.glob("*"): 
            if (f == '.') or (f == '..') or (str(f).upper() == "THUMBABC") or (f=='Faces') or (f=='_git'):
                continue
            
        dirs = []
        for f in glob.glob("*"): 
            if (f == '.') or (f == '..') or (str(f).upper() == "THUMBABC") or (f=='Faces') or (f=='_git'):
                continue
            
            fpath = curDir + "/" + f                           
            if os.path.isdir(fpath):
                dirs.append(fpath)    
            
            elif os.path.isfile(fpath):
                self.process_qty +=1
                if self.allFileQTY and (self.process_qty == 1 or self.process_qty % 100 == 0):
                    p = int(self.process_qty / self.allFileQTY * 10000)/100
                    print("\t.... completed:",str(p) + "%")
                
                md5str = self.FileGetMD5_String(fpath)
                if self.FileRepeatedCheck(md5str,fpath):
                    print("\t.... repeated, to be deleted:",fpath)
                
        if len(dirs):
            for dirx in sorted(dirs):
                self.FileRepeatedDelete(dirx)        
                
    def FileRepeatedGetList(self):
        #获取以MD5为基准的文件列表
        print(".... Get repeated file list ...")
        self.filesRepeated = {} #filesRepeated -- md5str = [[id1 path ext], [id2 path ext],...]
        try:
            self.cursor.execute("SELECT FLIST.`id`, FLIST.`dir_id`, FLIST.`name`, FLIST.`md5_file`, DLIST.`path` FROM `filelist` AS FLIST LEFT JOIN (SELECT * FROM `dirlist`) AS DLIST ON DLIST.`id` = FLIST.`dir_id` WHERE FLIST.`md5_file` is not null")            
            results = self.cursor.fetchall()
            n = len(results)
            print("\t.. get records:",n)

            for p in results:
                arr = os.path.splitext(p[2])
                ext = str(arr[len(arr) - 1].replace(".","")).upper()
                
                if not self.filesRepeated.__contains__(p[3]):
                    self.filesRepeated[p[3]] = []
                    
                self.filesRepeated[p[3]].append([p[0], p[4] + "/" + p[2], ext])        
                        
            print("\t.. done")            
        except:
            print(traceback.format_exc())
                   
    def FileRepeatedCheck(self,md5str,filepath):   
        r = False
        arr = os.path.splitext(filepath)
        ext = str(arr[len(arr) - 1].replace(".","")).upper()  
        
        if IsKeyExist(self.filesRepeated,[md5str]):  #filesRepeated -- md5str = [[id1 path ext], [id2 path ext],...]
            try:
                for pic in self.filesRepeated[md5str]:
                    #print(pic)
                    if os.path.exists(pic[1]) and ext == pic[2]:
                        r = True
                        #os.unlink(filepath)
                        break                                           
            except:
                print(traceback.format_exc())
        
        if not r:
            if not self.filesRepeated.__contains__(md5str):
                self.filesRepeated[md5str] = []
            self.filesRepeated[md5str].append([0, filepath, ext]) 
        #print(self.filesRepeated)
            
        return r
            
        
    def MakeThumbs(self,curDir):   
        #遍历文件夹，找出照片与视频  
        #sstime = time.time()

        print ('Total used:',usedTime(self.startTime),"\n\n",curDir + " ... \n------------------------")    
        os.chdir(curDir)

        self.ifiles = {}
        self.fields = {'name':1,'type':1,'dir_id':1,'mtime':1,'size':1}
        self.ik = 0

        filesDoneQTY = 0
        qtyxx = [] #所有图片列表
        #获取文件夹curDir下面所有包含在数组self.formats里格式的照片
        for format in self.formats:        
            qtyxx += glob.glob("*." + format)    

        self.filesDone = {'image':{},'video':{}}
        if self.refresh_all == 0:
            self.DirsGetFilesDone(curDir)
            print('\t',curDir,', image done:',len(self.filesDone['image'].keys()),'/',len(qtyxx))
            
            del_id = []
            for f in self.filesDone['image'].keys():
                try:
                    qtyxx.index(f)
                except:
                    del_id.append(self.filesDone['image'][f])
            if len(del_id):
                print('\tdelete image record from filelist:',del_id)
                try:
                    for id in del_id:
                        self.cursor.execute("DELETE from `filelist` WHERE `id`='"+ str(id) +"' ")
                    self.db.commit()  
                except:
                    print(traceback.format_exc()) 
        
        video_img = []   #所有的照片名称列表
        processed_image = 0 #已经处理的图片数量
        if len(qtyxx):            
            #新建小图文件夹
            if not os.path.exists(curDir + '/ThumbABC'):  
                os.makedirs(curDir + '/ThumbABC')       

            #按照小图像素大小，新建小图文件夹
            for p in self.pixels:
                if not os.path.exists(curDir + '/ThumbABC/W' + str(p)):  
                    os.makedirs(curDir + '/ThumbABC/W' + str(p))
        
            self.pixels.sort(reverse = True)            
            self.curImgAll = [] #保存当前文件夹里的Image.open(file)进来的照片数据
            
            done_img = []
            skip_img = 0
            for f in qtyxx:
                self.curFilepath = ""
                self.curImg = None  #Image.open(file)进来的照片数据                

                self.picK +=1
                #跳过视频文件的封面照片
                if re.match(r'.*\.(MP3|MP4|MOV|AVI|RM|RMVB|MTV|FLV|MKV|3GP|RMVB)\.jpg',f,re.I):
                    video_img.append(f)
                    skip_img +=1
                    continue    
               
                if self.refresh_all == 0:
                    if IsKeyExist(self.filesDone['image'],[f]):
                        filesDoneQTY +=1
                        done_img.append(f)
                        skip_img +=1
                        continue              
                
                processed_image +=1
                self.ik +=1
                DictToDict(self.ifiles,[self.ik])
                self.curFilepath = curDir + '/' + f

                #照片重新命名,并获取照片的EXIF信息  
                fname = self.FileRename(f,0)

                self.ifiles[self.ik]['name'] = fname
                self.ifiles[self.ik]['type'] = 'image'               
                self.ifiles[self.ik]['mtime']= str(os.stat(curDir + '/' + fname).st_mtime)
                self.ifiles[self.ik]['size'] = str(os.stat(curDir + '/' + fname).st_size)
                
                md5str,fsize = self.FileGetMD5_String(curDir + '/' + fname)
                self.ifiles[self.ik]['md5_file'] = md5str
                if self.FileRepeatedCheck(md5str, curDir + '/' + fname):
                    self.ifiles[self.ik]['is_repeated'] = 1
                else:
                    self.ifiles[self.ik]['is_repeated'] = 0                
                
                self.curFilepath = curDir + '/' + fname
                done_img.append(fname)

                #创建照片的小图
                for p in self.pixels:
                    self.ImageResize(curDir,fname,p)

                if self.gpuUseBatch:
                    #缩小图片,保持所有图片大小一致FixSize=1，再保存
                    im = self.FacePrepareIm(FixSize=1)
                    self.curImgAll.append([self.ik,fname,self.curFilepath,self.picK,im])
                    #每保存500张照片检查内存使用率, 如果使用率大于80%, 去批量获取照片里面的人脸，并释放内存
                    if self.ik%500==0:
                        if MemoryStatus() >= 80:
                            #批量获取照片里面的人脸，并释放内存 
                            self.FacesGet_batch()
                else:
                    #MemoryStatus()
                    #获取单张照片里面的人脸                     
                    self.ifiles[self.ik]['faces'] = []                                        
                    self.FacesGet() 
                    #MemoryStatus()

                self.curImg = None
            
            #清理小图标
            #print(done_img)
            if len(done_img):
                for p in self.pixels:
                    if os.path.exists(curDir + '/ThumbABC/W' + str(p)):  
                        os.chdir(curDir + '/ThumbABC/W' + str(p))
                        for f in sorted(glob.glob("*.*")): 
                            if (f == '.') or (f == '..') or (f == 'Faces') or (f == '_git'):
                                continue
                            try:
                                done_img.index(f)
                            except:
                                print('\t.... delete: ',curDir + '/ThumbABC/W' + str(p) + '/' + f)
                                os.unlink(f)                       
            else:
                #文件夹内没有照片，就删除ThumbABC小图标文件夹及其文件
                if os.path.exists(curDir + '/ThumbABC'):
                    print('\t.... delete folder:',curDir + '/ThumbABC')
                    del_file(curDir + '/ThumbABC')

            os.chdir(curDir)

            #self.process_qty += processed_image
            print('\tprocessed image',processed_image,', skipped images',skip_img,', all images',len(qtyxx),"\n")

            if len(self.curImgAll):
                #批量获取照片里面的人脸，并释放内存 
                self.FacesGet_batch()

        processed_video = 0 #已经处理的视频数量
        dirs = []  #文件夹地址列表
        videos=[]  #视频名字列表
        videosImg = []  #视频的封面照片列表
        for f in sorted(glob.glob("*")): 
            if (f == '.') or (f == '..') or (f == 'Faces') or (f == '_git'):
                continue
            
            #删除文件夹THUMBABC下面所有EXIF文件
            if str(f).upper() == "THUMBABC":
                del_file(curDir + "/" + f + '/EXIF')            
                continue
                    
            if os.path.isdir(curDir + "/" + f) and (f != 'ThumbABC'): 
                dirs.append(curDir + "/" + f)             
            
            #删除文件FileList.php .picasa.ini
            elif f == 'FileList.php' or f == '.picasa.ini':
                os.unlink(curDir + "/" + f)
      
            #如果是视频文件， 抽取视频的封面照片
            elif re.match(r'.*\.(MP3|MP4|MOV|AVI|RM|RMVB|MTV|FLV|MKV|3GP|RMVB)$',f,re.I):
                if self.refresh_all == 0:
                    if IsKeyExist(self.filesDone['video'],[f]):                        
                        videos.append(f)
                        if os.path.exists(f + '.jpg'):
                            videosImg.append(f + '.jpg')
                            filesDoneQTY +=1
                        else:
                            os.chdir(curDir)
                            vf = self.GetVideoFirstFrame(curDir,f)
                            if vf:
                                videosImg.append(vf)
                            processed_video +=1
                        continue

                processed_video +=1
                self.ik +=1
                DictToDict(self.ifiles,[self.ik])
                
                os.chdir(curDir)   
                if os.path.exists(f + '.jpg'):
                    os.remove(f + '.jpg')
                            
                ifname = self.FileRename(f,1)
                self.ifiles[self.ik]['name'] = ifname
                self.ifiles[self.ik]['type'] = 'video'
                self.ifiles[self.ik]['mtime']= str(os.stat(curDir + '/' + ifname).st_mtime)
                self.ifiles[self.ik]['size'] = str(os.stat(curDir + '/' + ifname).st_size)   
                
                md5str,fsize = self.FileGetMD5_String(curDir + '/' + ifname)  
                self.ifiles[self.ik]['md5_file'] = md5str
                if self.FileRepeatedCheck(md5str, curDir + '/' + ifname):
                    self.ifiles[self.ik]['is_repeated'] = 1
                else:
                    self.ifiles[self.ik]['is_repeated'] = 0 
                             
                videos.append(ifname)                
                
                os.chdir(curDir)
                vf = self.GetVideoFirstFrame(curDir,ifname)
                if vf:
                    videosImg.append(vf)
        
        self.process_qty += processed_video + processed_image

        #从数据库里删除不存在视频文件的记录
        del_id = []
        for f in self.filesDone['video'].keys():
            try:
                videos.index(f)
            except:
                del_id.append(self.filesDone['video'][f])
        if len(del_id):
            print('\tdelete video record from filelist:',del_id)
            try:
                for id in del_id:
                    self.cursor.execute("DELETE from `filelist` WHERE `id`='"+ str(id) +"' ")
                self.db.commit()  
            except:
                print(traceback.format_exc()) 

        #删除没有视频的视频封面图片
        if len(video_img):
            os.chdir(curDir)
            for f in video_img:
                try:
                    videosImg.index(f)
                except:
                    try:
                        os.remove(f)
                    except:
                        pass

        if self.ik:
            self.File2DB(curDir)

        if self.allPicQTY:  
            print("\n*******************************************************************") 
            print(curDir)           
            print(".. skipped as done before: ",filesDoneQTY,', processed images:',processed_image,', processed video:',processed_video,', total image+video in the folder:',str(filesDoneQTY + processed_image + processed_video))
            if self.picK > 0:
                speed = int((time.time() - self.startTime)/self.picK*1000)/1000
                print(".. Avg processing speed: {} seconds/image".format(speed),', estimated left time:',usedTime(self.startTime,speed*(self.allPicQTY-self.picK)))
            print("-- Total processed Image: " + str(self.picK) + "/" + str(self.allPicQTY) + " {:0>2.1f}".format(self.picK/self.allPicQTY*100) + "% done, used time so far:",usedTime(self.startTime))
            print("*******************************************************************\n")

        if len(dirs):
            #threads = []
            for dirx in sorted(dirs):
                self.MakeThumbs(dirx)
                #threads.append(threading.Timer(1,self.MakeThumbs,args=[dirx]))                
            
            #for t in threads:
            #    t.start()              

    def DirsGetFilesDone(self,idir):
        idir = idir.upper()
        self.filesDone = {'image':{},'video':{}}
        k = 0
        try:
            #cursor = self.cursor()
            try:
                self.dirs = {}
                self.DirsGet()

                idirc = str(base64.b64encode(idir.encode(encoding='utf-8')),'utf-8')
                if IsKeyExist(self.dirs,[idirc]):  
                    #print('.... dir existing:',idir,'; dir_id=',self.dirs[idirc])              
                    try:
                        #print('\t',"SELECT `name`,`id` FROM `filelist` where `dir_id`='"+str(self.dirs[idirc])+"'")
                        self.cursor.execute("SELECT `name`,`id`,`TYPE` FROM `filelist` where `dir_id`='"+str(self.dirs[idirc])+"'") #AND `size` > '0' AND (`face_idx is not null)
                        results = self.cursor.fetchall()
                        for p in results:
                            k +=1
                            self.filesDone[p[2]][p[0]] = p[1]
                    except:
                        print(traceback.format_exc())         
            except:
                print(traceback.format_exc())

            #try:  
            #    cursor.close()
            #except:
            #    pass
        except:
            pass
        
        print("\n\t",k,"files have been done in the folder: ",idir)

    def DirsGet(self):
        #cursor = self.db.cursor()
        try:            
            self.cursor.execute("SELECT `id`,`path` FROM `dirlist`")
            results = self.cursor.fetchall()
            for p in results:                
                x = str(base64.b64encode(p[1].encode(encoding='utf-8')),'utf-8')                
                self.dirs[x] = str(p[0])     

        except:
            print(traceback.format_exc())

        #try:  
        #    cursor.close()
        #except:
        #    pass           
    def DirGetID(self, cdir=""):
        dir_id = ""
        cdir = cdir.upper()

        self.dirs = {}
        self.DirsGet()           
        self.DirsCheck(cdir)
        
        idir = str(base64.b64encode(cdir.encode(encoding='utf-8')),'utf-8')
        if IsKeyExist(self.dirs,[idir]) and self.dirs[idir]:
            dir_id = self.dirs[idir]
            
        return dir_id
    
    def DirsCheck(self,idir):    
        idirc = str(base64.b64encode(idir.encode(encoding='utf-8')),'utf-8')
        if IsKeyExist(self.dirs,[idirc]):
            return
        print("\n",idir)    
        try:
            #cursor = self.db.cursor()
            self.cursor.execute("INSERT INTO `dirlist` (`path`,`base64`) VALUES ('"+ pymysql.escape_string(idir) +"','"+ idirc +"')")
            self.db.commit()
            self.DirsGet()              
        except:
            print(traceback.format_exc())

    def DBColumnCheck(self):
        try:
            self.cursor.execute("select column_name from information_schema.columns where table_schema ='"+ self.dbName +"' and table_name = 'filelist'")
            results = self.cursor.fetchall()
            #print(results)
            for fd in self.fields.keys():
                e = 0
                for p in results:
                    if p[0] == fd.lower():
                        e = 1
                        break
                if e == 0:
                    print('Add new field: '+ fd.lower())
                    self.cursor.execute("ALTER TABLE `filelist` ADD COLUMN `"+ fd.lower() +"` TEXT NULL")
                    self.db.commit()              
        except:
            print(traceback.format_exc())
                    
    def File2DB(self,cdir):  
        #cursor = self.db.cursor()
        dir_id = ""
        cdir = cdir.upper()
        try:    
            self.fields['md5_file'] = 1
            self.fields['is_repeated']  = 1
            
            self.dirs = {}
            self.DirsGet()           
            self.DBColumnCheck()
            
            self.fields['lastupdate']   = 1
            self.fields['dir_id']   = 1
            self.DirsCheck(cdir)
            
            idir = str(base64.b64encode(cdir.encode(encoding='utf-8')),'utf-8')
            if IsKeyExist(self.dirs,[idir]) and self.dirs[idir]:
                dir_id = self.dirs[idir]

                #如果是重新处理，删除在数据库里的当前文件夹的信息
                if self.refresh_all:
                    self.cursor.execute("DELETE FROM `filelist` WHERE `dir_id`='" + dir_id + "'")
                    self.cursor.execute("DELETE FROM `faces`    WHERE `dir_id`='" + dir_id + "'")
                    self.cursor.execute("DELETE FROM `faces_image`    WHERE `dir_id`='" + dir_id + "'")
                    self.db.commit()  
            
            for n in self.ifiles:
                self.ifiles[n]['lastupdate']  = self.lastupdate
                self.ifiles[n]['dir_id']  = dir_id

                info = str(self.ifiles[n]['size']) #+ self.ifiles[n]['name'] + str(self.ifiles[n]['mtime'])
                for xkey in ['exif_ResolutionUnit','exif_Model','exif_LensMake','exif_XResolution',
                             'exif_ExifImageWidth','exif_ExifImageHeight','exif_ISOSpeedRatings','exif_ExposureTime']:
                    if IsKeyExist(self.ifiles[n],[xkey]) and self.ifiles[n][xkey]:
                        info += self.ifiles[n][xkey]                              
                self.ifiles[n]['md5'] = str(hashlib.md5(info.encode(encoding='utf-8')).hexdigest()).upper()
                self.fields['md5'] = 1
                self.fields['face_idx'] = 1

                fs = []
                vals=[]
                arg =[]

                for fd in self.fields.keys():
                    if IsKeyExist(self.ifiles[n],[fd]):
                        #print(fd.lower(),": ",self.ifiles[n][fd])
                        fs.append("`" + fd.lower() + "`")
                        vals.append('%s')
                        arg.append(pymysql.escape_string(str(self.ifiles[n][fd])))
                    
                self.cursor.execute("INSERT INTO `filelist` ("+','.join(fs)+") VALUES("+",".join(vals)+")", arg)
            
            self.db.commit()                         
        except:
            print("\t.. Save to db error: \n\t\t",traceback.format_exc())
            self.db.rollback()  
        
        self.FacesLabelToDB()
        self.FacesInfoToDB(dir_id)
        #try:
        #    cursor.close()
        #except:
        #    pass                       

    def GetEXIF(self,info):
        #print(self.curFilepath)
        mtime = ""
        try:        
            for (tag, value) in info.items():                
                ikey = TAGS.get(tag, tag) #.lower()
                if type(ikey) != str:
                    ikey = str(ikey)
                    
                if ikey != 'MakerNote':
                    #print(ikey,":",type(value),":\n\t",value)
                    try:
                        if re.match(r'DateTime|DateTimeOriginal',ikey,re.I):                                 
                            if type(value) != str: 
                                value = str(value)     #2019:04:04 16:40:11
                                #print('\t-- datetime in exif:',value) 
                            if re.match(r'',value):                             
                                mtime = re.sub(r':','',re.sub(r'\s+','-',value)) 
 
                        valuestr = ""
                        ikey = 'exif_' + ikey
                        if type(value) == str: 
                            valuestr = value                    
                        elif type(value) == int:
                            valuestr = str(value)                          
                        elif type(value) == list:
                            valuestr = ','.join(map(str,value)) 
                        elif type(value) == tuple:
                            valuestr = '/'.join(map(str,value))                           
                        elif type(value) == dict: 
                            if ikey == 'exif_GPSInfo':  
                                valuestr = value[1] + ''.join(map(str,value[2])) + ' ' + value[3] + ''.join(map(str,value[4]))

                                self.gpsinfo2 = ""
                                self.GPS_Value_jsondumps(value)
                                self.ifiles[self.ik]['exif_gpsinfo2'] = self.gpsinfo2
                                self.fields['exif_gpsinfo2'] = 1
                                          
                                gps = self.GPSInfoParse(value) 
                                self.ifiles[self.ik]['exif_gps_altitude'] = gps['altitude']  #获取海拔高度
                                self.fields['exif_gps_altitude'] = 1
                                
                                self.ifiles[self.ik]['latitude'] = gps['GPSLatitude']  
                                self.fields['latitude'] = 1
                                
                                self.ifiles[self.ik]['longitude'] = gps['GPSLongitude']
                                self.fields['longitude'] = 1

                        elif type(value) == bytes: 
                            valuestr = str(value, encoding='utf-8')      
                        
                        if len(valuestr):
                            self.ifiles[self.ik][ikey] = valuestr
                            self.fields[ikey] = 1    
                    except:
                        pass
        except:
            print(".. " + self.curFilepath,"\n",traceback.format_exc()) 
        
        return mtime

    def FileRename(self,file,NotCheckThumbABC=0):
        #if re.match(r'^\d\d\d\d\d\d\d\d|^\d\d\d\d\-\d\d\-\d\d',file,re.I):
        #    return file     
        #print('.... FileRename ... NotCheckThumbABC=',NotCheckThumbABC)
        mtime = ""
        try:        
            #获取照片exif里面的拍摄时间
            if NotCheckThumbABC == 0:
                with Image.open(file) as im:                    
                    if im:
                        try:                                                        
                            info = im._getexif()
                            if info:
                                mtime = self.GetEXIF(info)     
                                #print('\t--datetime in exif:',mtime)                           
                        except:
                            pass
                            print('\t',self.curFilepath,': failed to getexif!')    
                        self.curImg = im.copy() 

                        self.ifiles[self.ik]['width'] = str(im.size[0])
                        self.fields['width'] = 1   
                        self.ifiles[self.ik]['height'] = str(im.size[1])
                        self.fields['height'] = 1                                    
        except:
            pass
        
        if not mtime:        
            try:
                #如果照片exif里面没有拍摄时间，获取照片文件的修改时间
                mtime = time.strftime("%Y%m%d-%H%M%S",time.localtime(os.stat(file).st_mtime)) 
            except:
                print(traceback.format_exc())
                return file   
                
        ftype = file.split('.')    
        n = 0
        name = mtime + '.' + ftype[-1] 
        #print('\n\tfile.upper() != name.upper??',file.upper(),',',name.upper())
        if file.upper() != name.upper():         
            while os.path.exists(name):    
                n +=1
                name = mtime + '_' + str(n) + '.' + ftype[-1] 
        
        xname = mtime
        if n >0:
            name  = mtime + '_' + str(n) + '.' + str(ftype[-1]).upper()  
            xname = mtime + '_' + str(n)      
        else:
            name = mtime + '.' + str(ftype[-1]).upper() 
        
        print("\t\tRename: from ",file,"to",name)
        os.rename(file,name) 
        if os.path.exists(name):
            fn = re.sub(r'\.(\w+)$','', file)
            if os.path.exists(fn + '.AAE'):
                os.rename(fn + '.AAE', xname + '.AAE')   
                    
        if not NotCheckThumbABC:   
            if os.path.exists(name):    
                for p in self.pixels:
                    if os.path.exists('ThumbABC/W'+str(p)+'/' + file):
                        os.rename('ThumbABC/W'+str(p)+'/' + file,'ThumbABC/W'+str(p)+'/' + name) 
            else:
                name = file            
                
        return name

    def ImageResize(self,fdir,fname,lsize):    
        newfile = "ThumbABC/W" + str(lsize) + "/" + str(fname).upper()
        if os.path.exists(newfile): 
            return

        size  = os.stat(fname).st_size / 1024
        if size < 800 and lsize > 500:
            return
        
        self.pixels.sort(reverse = False)
        for p in self.pixels:
            if p<= lsize:
                continue
                
            if os.path.exists("ThumbABC/W" + str(p) + "/" + str(fname).upper()): 
                print("\t\tCompress(" + str(lsize)+" px): read image from "+ "ThumbABC/W" + str(p) + "/" + str(fname).upper())
                os.chdir("ThumbABC/W" + str(p))
                break
        try:
            im = self.curImg.copy()   
            os.chdir(fdir)
            iw, ih = im.size
            if iw and ih:
                w = lsize
                h = 0
                
                if iw>ih:
                    h= lsize*ih/iw
                else:
                    h= lsize
                    w= lsize*iw/ih
        
                im.thumbnail((w, h))  #can use: im.thumbnail((lsize, lsize))
                im.save(newfile)
                
                if lsize == 1080: 
                    print("\n\t文件夹: " + fdir)             
        
                print("\t\tCompress ("+ str(lsize) + " px): "+ fname +" done; Total "+ str(int(self.picK/self.allPicQTY*10000)/100) + "%("+str(self.picK)+"/"+ str(self.allPicQTY)+") done")
                        
            else:            
                print(traceback.format_exc())
                if lsize == self.pixels[-1]: 
                    print("")
        
        except:
            print("    Compress ("+ str(lsize) + " px): $fname failed!\n",traceback.format_exc())            

    def GetVideoFirstFrame(self,idir,filename):
        vf = ''
        print("\tGet first frame of the video:",idir + '/' + filename) 
        try:
            vc = cv2.VideoCapture(filename) #读入视频文件
            if vc.isOpened():  # 判断是否正常打开
                rval, frame = vc.read()
                print("\tfirst frame:",filename + '.jpg')
                if os.path.exists(filename + '.jpg'):
                    os.unlink(filename + '.jpg')    
                cv2.imwrite(filename + '.jpg', frame) 
                if os.path.exists(filename + '.jpg'):
                    vf = filename + '.jgp'
            else:
                print("\tFailed to open the video!")    
            vc.release()
        except:
            print("\t",traceback.format_exc()) 
        print("")     

        return vf                     
    
    def FaceRecognitionKnownTopX(self,topX=50): #已知人物的人脸数量前topX，在未知人脸B，C，D，E，F，...中找出是他们的人脸
        print("\nFaces recognition for the known faces top "+ str(topX) +" ... ...")

        try:
            self.cursor.execute("SELECT label_correct, COUNT(label_correct) AS icount FROM faces WHERE (label_correct is not null and label_correct<>'') GROUP BY label_correct ORDER BY icount DESC LIMIT " + str(topX)) 
            results = self.cursor.fetchall()
            n = len(results)
            k = 0
            for p in results:
                if p[0]:
                    k +=1
                    print("\nFaces recognition for the known faces top {}/{}: {} ...".format(k,n,p[0]))
                    self.FaceRecognitionKnown(faceA=p[0])

        except:
            print(traceback.format_exc())

    def Faces_CleanUp(self):
        #Delete faces are not having existing file_id in the filelist table
        print("Faces_CleanUp ...")
        try:
            self.startTime= time.time()
            #get file list and map md5 string
            
            print(".. get file ids ... ")
            filelist = {}
            self.cursor.execute("SELECT `id` from `filelist` ")
            results = self.cursor.fetchall() 
            for p in results:
                filelist[p[0]] = 1
            
            print(".. get clean-up list ... ")
            delList = {}  
            n = 0  
            self.cursor.execute("SELECT `id`, `file_id`, `image_id` from `faces` ")  
            results = self.cursor.fetchall() 
            for p in results:
                if not filelist.__contains__(p[1]):
                    delList[p[0]] = p[2]        
                    n += 1  

            print(".. clean up: ",n)
            if n:
                print(".. save file md5 string: ")
                self.startTime= time.time()
                k = 0
                pnum = int(n / 20)
                if pnum < 100:
                    pnum = 100
                for id in delList:
                    try:
                        k +=1
                        if k %pnum == 0:
                            self.db.commit()
                            
                            speed = (time.time() - self.startTime)/k
                            print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record, 预计还需工时: {}".format(k,n,k/n*100,usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))                            

                        self.cursor.execute('DELETE from `faces` WHERE `id`="{}" '.format(id))
                        self.cursor.execute('DELETE from `faces_image` WHERE `id`="{}" '.format(delList[id]))                                           
                    except:
                        print(traceback.format_exc())

                self.db.commit()  
                
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/record".format(k,n,k/n*100,usedTime(self.startTime),speed))               
            
        except:
            print(traceback.format_exc())  
            
    def FaceRecognitionKnown(self,faceA=None): #已知人物A的人脸，在未知人脸B，C，D，E，F，...中找出是A的人脸
        #faceA = '陆绍凤'
        if faceA:
            print("\nFaces recognition for the known faces ["+ faceA +"] ... ...")
            self.tolerance = 0.34
        else:
            print("\nFaces recognition for known faces ... ...")

        self.startTime= time.time()

        if not faceA:
            self.ConnectDB()
            self.cursor = self.db.cursor()  #连接数据库的指针

        print("\tget known faces labels ... ")
        self.faceKnown = {}
        self.faceKnown['encodings'] = []
        self.faceKnown['labels'] = []
        self.faceKnown['encodings_known'] = []
        self.faceKnown['labels_known'] = []
        self.lastLabelIndex = 0
        #cursor = self.db.cursor()
        try:
            sqlStr = "SELECT `faces`.`id`,`faces`.`label`,`faces`.`label_correct`,`faces_image`.`encodings` FROM `faces` join `faces_image` WHERE `faces`.`fixed`=1 and (`label_correct` is not null and `label_correct`<>'') and `faces_image`.`id` = `faces`.`image_id` "
            if faceA:
                self.cursor.execute("UPDATE `faces` SET `label_correct`='' WHERE `label_correct`='"+ str(faceA) +"' and `fixed`=0 ")
                self.db.commit() 
                sqlStr = "SELECT `faces`.`id`,`faces`.`label`,`faces`.`label_correct`,`faces_image`.`encodings` FROM `faces` join `faces_image` WHERE `faces`.`fixed`=1 and `label_correct`='"+str(faceA)+"' and `faces_image`.`id` = `faces`.`image_id` "

            self.cursor.execute(sqlStr) 
            results = self.cursor.fetchall()
            n = len(results)
            for p in results:
                self.faceKnown['labels_known'].append([p[0],p[1],'',p[2]])            
                self.faceKnown['encodings_known'].append(ZipArray(p[3],isZip=False))      

            print("\tgot faces labels:total",n,'\n')
        except:
            print(traceback.format_exc())

        try:                 
            print("\tget unconfirmed faces ...")
            self.cursor.execute("SELECT `faces`.`id`,`faces_image`.`encodings` FROM  `faces` join `faces_image` WHERE `faces`.`fixed`=0 and `faces_image`.`id` = `faces`.`image_id` ") #and (`label_correct` is null or `label_correct`='')  #fixed=0，表示该人脸还没有被标识为已知的人物
            results = self.cursor.fetchall()
            n = len(results)
            print("\trecognizing unlabel faces:", n, "耗工时: {}".format(usedTime(self.startTime)))
            pnum = 500
            k = 0
            facesNew = []
            for p in results:
                k +=1
                if k==1 or k % pnum == 0:
                    speed = (time.time() - self.startTime)/k
                    print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 目标[{}], 给定误差{}, 找到目标{:0>6d}, 共耗工时: {}, 速度 {:.3f} s/image, 预计还需工时: {}".format(k,n,k/n*100,faceA,self.tolerance,len(facesNew),usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))
                
                label,name = self.FaceRecognition(unkown_encodings=ZipArray(p[1],isZip=False),imgZ=None,knownOnly=1)
                if label and name:
                    facesNew.append([p[0],label,name])
                    #break

            if n:
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/image".format(k,n,k/n*100,usedTime(self.startTime),speed))

            print("\tUpdate recognition result to faces table:", len(facesNew), '/', n)
            for p in facesNew:
                self.cursor.execute("UPDATE `faces` SET `label`='"+ str(p[1]) +"',`label_correct`='"+ str(p[2]) +"' WHERE `id`='"+ str(p[0]) +"' ")
            self.db.commit() 

            print("\t.. 已处理完成, 共耗工时: {}".format(usedTime(self.startTime)),'\n')
        except:
            print(traceback.format_exc())

        if not faceA:
            if self.db:   
                self.cursor.close()
                self.db.close() 
        print("")

    def FaceRecognition2(self):   #对数据库里面的人脸再次独立做人脸识别，包括已知的人脸与未知的人脸
        self.startTime= time.time()

        self.ConnectDB()
        self.cursor = self.db.cursor()  #连接数据库的指针

        self.FacesLabelRefresh()
        self.FacesLabelGet()
        try:
            print("\nFaces recognition again ... ...")
            
            print("\tget unlabel faces ...")
            self.cursor.execute("SELECT `faces`.`id`,`faces_image`.`encodings`,`faces_image`.`image` FROM  `faces` join `faces_image` WHERE `faces`.`fixed`=0 and (`label_correct` is null or `label_correct`='') and `faces_image`.`id` = `faces`.`image_id` ")   #fixed=0，表示该人脸还没有被标识为已知的人物
            results = self.cursor.fetchall()
            n = len(results)
            print("\trecognizing unlabel faces:", n, "耗工时: {}".format(usedTime(self.startTime)))
            pnum = 500
            k = 0
            facesNew = []
            for p in results:
                k +=1
                if k==1 or k % pnum == 0:
                    speed = (time.time() - self.startTime)/k
                    print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 给定误差{}, 找到目标{:0>6d}, 共耗工时: {}, 速度 {:.3f} s/image, 预计还需工时: {}".format(k,n,k/n*100,self.tolerance,len(facesNew),usedTime(self.startTime),speed,usedTime(self.startTime,speed*(n-k))))
                
                imgz = ZipArray(ZipArray(p[2],isZip=False))
                label,name = self.FaceRecognition(unkown_encodings=ZipArray(p[1],isZip=False),imgZ=imgz)
                facesNew.append([p[0],label,name])

            if n:
                speed = (time.time() - self.startTime)/k
                print("\t.. 已处理: {:0>9d}/{} {:0>2.1f}%, 共耗工时: {}, 速度 {:.3f} s/image".format(k,n,k/n*100,usedTime(self.startTime),speed))

            print("\tUpdate recognition result to faces table:", len(facesNew), '/', n)
            for p in facesNew:
                self.cursor.execute("UPDATE `faces` SET `label`='"+ str(p[1]) +"',`label_correct`='"+ str(p[2]) +"' WHERE `id`='"+ str(p[0]) +"' ")
            self.db.commit() 

            self.FacesLabelToDB()

            print("\t.. 已处理完成, 共耗工时: {}".format(usedTime(self.startTime)),'\n')

        except:
            print(traceback.format_exc())

        if self.db:   
            self.cursor.close()
            self.db.close() 
        print("")

    def FaceRecognition(self,unkown_encodings=None,imgZ=None,knownOnly=0):
        #人脸辨识，返回其标签，如果没有找到对应的标签，新增一个标签
        #print(type(unkown_encodings),unkown_encodings)
        if not IsTrue(unkown_encodings):
            return ""

        label = ""
        name = ''

        n = len(self.faceKnown['labels_known'])
        if n:
            try:
                matches = face_recognition.compare_faces(self.faceKnown['encodings_known'], unkown_encodings,tolerance=self.tolerance)

                # If a match was found in known_face_encodings, just use the first one.
                if True in matches:
                    first_match_index = matches.index(True)
                    label = self.faceKnown['labels_known'][first_match_index][1]
                    name  = self.faceKnown['labels_known'][first_match_index][3]
            except:
                print(traceback.format_exc()) 
        
        if (label and name) or knownOnly:
            return label,name

        self.lastLabelIndex +=1
        label = str(int(self.tolerance*10)) + 'N' + str(self.lastLabelIndex)
        name = ''
        n = len(self.faceKnown['labels'])
        if n:
            try:
                matches = face_recognition.compare_faces(self.faceKnown['encodings'], unkown_encodings,tolerance=self.tolerance)

                # If a match was found in known_face_encodings, just use the first one.
                if True in matches:
                    first_match_index = matches.index(True)
                    label = self.faceKnown['labels'][first_match_index][1]
                    name  = self.faceKnown['labels'][first_match_index][3]
                else:
                    self.faceKnown['labels'].append(['',label,imgZ,name])
                    self.faceKnown['encodings'].append(unkown_encodings) 
            except:
                print(traceback.format_exc())
        else:
            self.faceKnown['labels'].append(['',label,imgZ,name])
            self.faceKnown['encodings'].append(unkown_encodings)   

        return label,name

    def FacesLabelknownListGet(self): 
        print("\n.... get faces labels ... ...")       
        try:
            self.cursor.execute("SELECT distinct `label_correct` FROM `faces_label` WHERE (`label_correct` is not null and `label_correct`<>'') ORDER BY `label_correct` ")
            results = self.cursor.fetchall()
            print(".. get faces labels:", len(results))
            self.faceKnownlabelList.append("")
            for p in results:
                self.faceKnownlabelList.append(p[0])

        except:
            print(traceback.format_exc())
                    
    def FacesLabelGet(self):
        print("\n.... get faces labels ... ...")
        self.faceKnown = {}
        self.faceKnown['encodings'] = []
        self.faceKnown['labels'] = []
        self.faceKnown['encodings_known'] = []
        self.faceKnown['labels_known'] = []
        self.lastLabelIndex = 0
        #cursor = self.db.cursor()
        try:
            n_known = 0
            n_unkown= 0
            self.cursor.execute("SELECT `id`,`label`,`encodings`,if(`label_correct` IS NULL OR `label_correct`='','',`label_correct`) AS `name` FROM `faces_label` WHERE (`excluded` is null or `excluded`=0) ORDER BY `name` desc ") #SELECT `id`,`label`,`encodings`,`label_correct` FROM `faces_label`
            results = self.cursor.fetchall()
            n = len(results)
            for p in results:
                if p[3]:
                    n_known +=1
                    self.faceKnown['labels_known'].append([p[0],p[1],'',p[3]])            
                    self.faceKnown['encodings_known'].append(ZipArray(p[2],isZip=False))   
                else:
                    n_unkown +=1
                    self.faceKnown['labels'].append([p[0],p[1],'',p[3]])            
                    self.faceKnown['encodings'].append(ZipArray(p[2],isZip=False))      

                iindex = int(re.sub(r'^\d+N','',p[1]))
                if self.lastLabelIndex < iindex:
                    self.lastLabelIndex = iindex

            print("\tgot faces labels:total",n,', known',n_known,', unknown',n_unkown,'; lastLabelIndex=',self.lastLabelIndex,'\n')
        except:
            print(traceback.format_exc())

        #try:
        #    cursor.close()
        #except:
        #    pass
    
    def FacesLabelRefresh(self):
        print("\n.... refresh faces labels ... ...")
        
        try:            
            existLabels = {}
            self.cursor.execute("SELECT `id`,`label_correct`,`label` FROM `faces_label` where `label_correct` is not null and `label_correct`<>'' ")
            results = self.cursor.fetchall()  
            print("\tget existing face labels ...", len(results))
            for p in results:
                DictToDict(existLabels,[p[1],p[2]])
                existLabels[p[1]][p[2]] = p[0] 

            self.cursor.execute("SELECT `label_correct`, `label`, `image_id`, `evaluation` FROM `view_face_label_refresh2` order by `label_correct`,`label`,`evaluation` DESC")
            results = self.cursor.fetchall()  
            print("\tget good faces ...", len(results))          
            goodLabels = {}
            for p in results:
                if IsKeyExist(goodLabels,[p[0],p[1]]):
                    if goodLabels[p[0]][p[1]][1] < p[3]:
                        goodLabels[p[0]][p[1]] = [p[2],p[3]]   #`image_id`, `evaluation`
                else:
                    DictToDict(goodLabels,[p[0],p[1]])
                    goodLabels[p[0]][p[1]] = [p[2],p[3]]   #`image_id`, `evaluation`

            print("\tget encodings and images for good faces ...")  
            n = 0
            for name in goodLabels:
                for label in goodLabels[name]:
                    self.cursor.execute("SELECT `encodings`, `image` FROM `faces_image` where `id`='"+ str(goodLabels[name][label][0]) +"' ")
                    results = self.cursor.fetchall() 
                    for p in results:
                        goodLabels[name][label].append(p[0])
                        goodLabels[name][label].append(p[1])
                        n +=1
                        break

            print("\tupdate face labels ...",n)
            for name in goodLabels:
                for label in goodLabels[name]:
                    #print(name,label,goodLabels[name][label])
                    if IsKeyExist(existLabels,[name,label]):
                        self.cursor.execute('UPDATE `faces_label` SET `encodings`="%s", `image`="%s" where `id`="%s"' 
                             % (
                                pymysql.Binary(ZipArray(ZipArray(goodLabels[name][label][2],isZip=False))),     #encodings
                                pymysql.Binary(ZipArray(ZipArray(goodLabels[name][label][3],isZip=False))),     #image
                                pymysql.escape_string(str(existLabels[name][label])),  #id
                             ))
                    else:
                        self.cursor.execute('INSERT INTO `faces_label` (`label_correct`,`label`,`encodings`,`image`) VALUES ("%s","%s","%s","%s")' 
                             % (
                                pymysql.escape_string(str(name)),  #label_correct
                                pymysql.escape_string(str(label)),  #label
                                pymysql.Binary(ZipArray(ZipArray(goodLabels[name][label][2],isZip=False))),    #encodings
                                pymysql.Binary(ZipArray(ZipArray(goodLabels[name][label][3],isZip=False)))     #image                                
                             ))

            self.db.commit() 

        except:
            print(traceback.format_exc())  
    '''
    def FacesImageStatus(status,looking,laplacian,brightness):        
        brn = abs(130 - brightness)/130*100
        if status == '--':
            status = 1000
        if looking == '--':
            looking= 50
        if laplacian == '--':
           laplacian = 1

        evaluation = int(1/((status + looking  + brn) / laplacian))
        return evaluation
    '''

    def FacesLabelToDB(self):
        print("\n.... save faces labels to db ...")
        #cursor = self.db.cursor()

        n = len(self.faceKnown['labels'])
        try:
            for i in range(n):
                if not self.faceKnown['labels'][i][0]:  #no id
                    try:
                        sqlstr = "INSERT INTO `faces_label` (`label`,`encodings`,`image`,`label_correct`) " + \
                                 'VALUES("%s","%s","%s","%s")' \
                                    % (
                                        self.faceKnown['labels'][i][1],
                                        pymysql.Binary(ZipArray(self.faceKnown['encodings'][i])),
                                        pymysql.Binary(self.faceKnown['labels'][i][2]),
                                        self.faceKnown['labels'][i][3]
                                    )

                        self.cursor.execute(sqlstr)                          
                    except:
                        print(traceback.format_exc())
            self.db.commit() 
            self.FacesLabelGet()
        except:
            print(traceback.format_exc())

    def FacesInfoToDB(self,dirID):    
        print(".... save faces data to db ...\n")
        try:
            #self.facesData.append([fname,label,faceID,encodeZ,imgZ,self.eyeLips])  #[path,label,idx,encodings,image,self.eyeLips]
            for face in self.facesData:
                try:
                    sqlstr = "INSERT INTO `faces` (`path`,`label`,`label_correct`,`idx`,`dir_id`,`image_face_side`,`image_bias_eyes`, " + \
                                                   "`image_slope_eyes`,`image_slope_nose_bridge`,`image_face_looking_bias`,`image_laplacian`,`image_brightness`,`image_overall_evaluation`) " + \
                            'VALUES("%s","%s","%s","%s","%s","%s", "%s","%s","%s","%s","%s","%s","%s")' \
                                % (
                                    pymysql.escape_string(face[0]),  #path
                                    pymysql.escape_string(face[1]),  #label
                                    face[5]['label_correct'],
                                    pymysql.escape_string(face[2]),  #faceID - idx
                                    str(dirID),                      #dir_id
                                    str(face[5]['face_side']),
                                    str(face[5]['bias_eyes']),

                                    str(face[5]['slope_eyes']),
                                    str(face[5]['slope_nose_bridge']),
                                    str(face[5]['face_looking_bias']),
                                    str(face[5]['laplacian']),
                                    str(face[5]['brightness']),
                                    str(face[5]['overall_evaluation'])
                                )

                    self.cursor.execute(sqlstr)    

                    sqlstr = "INSERT INTO `faces_image` (`path`,`encodings`,`image`,`landmark`,`landmark_image_size`,`dir_id`) " + \
                            'VALUES("%s","%s","%s","%s","%s","%s")' \
                                % (
                                    pymysql.escape_string(face[0]),           #path
                                    pymysql.Binary(face[3]),                  #encodings
                                    pymysql.Binary(face[4]),                  #image
                                    pymysql.Binary(face[5]['landmarks']),     #landmarks
                                    pymysql.escape_string(str(face[5]['reSize'])),  #landmark_image_size
                                    str(dirID)                      #dir_id
                                )

                    self.cursor.execute(sqlstr)                                           
                except:
                    print(traceback.format_exc())
            self.db.commit()             
        except:
            print(traceback.format_exc())        
        self.facesData = []

    def FacePrepareIm(self,rwidth=0,rheight=0,FixSize=0,im=None):
        try:
            if not im:
                im = self.curImg.copy()
            if not rwidth:
                rwidth = self.face_rec_width    
            if not rheight:
                rheight= self.face_rec_height
        
            if im.size[0] > rwidth:
                w  = rwidth
                h  = int(rwidth / im.size[0] * im.size[1])
                im = im.resize((w, h))
                #print("\tresize to",w,'x',h)

            if im.size[1] > rheight:
                h  = rheight
                w  = int(rheight / im.size[1] * im.size[0])
                im = im.resize((w, h))
                #print("\tresize to",w,'x',h)
            
            if FixSize == 1:  #fix size to rwidth x rheight
                im_tmp = Image.new("RGB", (rwidth, rwidth))
                im_tmp.paste(im,(0,0))
                im = im_tmp
        except:
            print(traceback.format_exc())
        #print ("\tresized to size : %s, mode: %s" % (im.size, im.mode),'\n')
        #im = im.convert('L') #转换成灰度图片 L = R * 0.299 + G * 0.587+ B * 0.114 

        return im

    def FacesGet_batch_framelist(self):
        n = 0
        frame_number = 0
        for i in range(self.gpuLastBsize):            
            if len(self.curImgAll):  
                try:                   
                    f = self.curImgAll.pop()                    

                    ilist = []   
                    try:                   
                        im = f[-1].copy()  

                        img_xx = cv2.cvtColor(numpy.array(im.convert('L')),cv2.COLOR_RGB2BGR)                                  
                        self.frames.append(img_xx[:, :, ::-1]) #保存0度角的灰度照片
                        frame_number +=1
                        self.frames_s[frame_number] = [n,0]

                        #转角度90,180,270
                        rotateN = 0
                        for ii in range(3):
                            rotateN += 90   
                            img = cv2.cvtColor(numpy.array(im),cv2.COLOR_RGB2BGR) 
                            img = cv2.flip(cv2.transpose(img), 1)  
                            im  = Image.fromarray(cv2.cvtColor(img,cv2.COLOR_BGR2RGB))  

                            ilist.append(im)  #保存+90度角的原色照片
                            img_xx = cv2.cvtColor(numpy.array(im.convert('L')),cv2.COLOR_RGB2BGR)                                   
                            self.frames.append(img_xx[:, :, ::-1]) #保存+90度角的灰度照片                    
                            frame_number +=1
                            self.frames_s[frame_number] = [n,rotateN]                           
                    except:
                        print(traceback.format_exc())
                    
                    f = f + ilist
                    self.imglistTmp.append(f)  #self.imglistTmp临时保存 [[self.ik,fname,self.curFilepath,self.picK,im,im90,im180],...]
                    n +=1
                except:
                    print(traceback.format_exc())
        cv2.destroyAllWindows()

    def FacesGet_batch_run(self):
        #批处理人脸识别
        print("\n\tbatch_face_locations, batch size=",self.gpuLastBsize*3,', actual size=',len(self.frames))
        try:            
            batch_of_face_locations = face_recognition.batch_face_locations(self.frames, number_of_times_to_upsample=self.nott_upsample,batch_size=len(self.frames))
            # Now let's list all the faces we found in all frames
            faceList = []
            lastN = 0
            for frame_number_in_batch, face_locations in enumerate(batch_of_face_locations):
                number_of_faces_in_frame = len(face_locations)
                if number_of_faces_in_frame:
                    frame_number = frame_number_in_batch + 1 #frame_count - self.gpuLastBsize + frame_number_in_batch
                    print("\t\tI found {} face(s) in frame #{}.".format(number_of_faces_in_frame, frame_number))

                    #获取当前原色照片                    
                    n = self.frames_s[frame_number][0]
                    if lastN != n:
                        faceList = []
                        lastN = n

                    rotateN = self.frames_s[frame_number][1]
                    p = 4
                    if rotateN == 90:
                        p = 5
                    elif rotateN == 180:
                        p = 6
                    
                    #从照片抓取人脸
                    self.FacesCropFromImage(faces=face_locations,curframe=self.frames[frame_number_in_batch],im=self.imglistTmp[n][p],faceList=faceList,rotateN=rotateN)
                    self.FacePush([[self.imglistTmp[n][0],self.imglistTmp[n][2],faceList]])  
            return ''      
        except:
            err = traceback.format_exc()
            print(err)
            return err

    def FacesGet_batch(self):
        #处理过程：
        #-- 每次读取bsize张照片
        #   每张照片，旋转角度0-90-180,照片1变3，保存进列表
        #-- 批量人脸辨识
        #   如果没有错误溢出，获取所有人脸特征，并对同一张照抽取出来的人脸进行过滤去除重复的人脸，保存进人脸列表
        #   如果有错误溢出，先减少bsize再试，如果self.gpuLastBsize = 1时还出现错误，改为单张人脸识别 self.gpuUseBatch = 0， 并且把列表self.curImgAll里的照片出来完毕

        stime = time.time()
        qty = len(self.curImgAll)
        if not qty:
            return

        self.faceLists = []
        if self.gpuLastBsize < 1:
            self.gpuLastBsize = 32
            self.gpuUseBatch  = 0
            #改为单张人脸识别
            n = 0
            for p in self.curImgAll: 
                n+=1
                self.FacesGet(ik=p[0],fpath=p[2],picK=n,im=p[4])
            self.curImgAll = []

            print("\tbatch - single: processed images",qty,', used time',usedTime(stime),',',int((time.time()-stime)*100)/100,'sec/image\n')
            return
        
        reRun = 0
        while len(self.curImgAll):   #[[self.ik,fname,self.curFilepath,self.picK,im], ...]             
            #每批抽取的图片数量，每张照片要从3角度0-90-180辨识人脸
            self.frames = []            
            self.frames_s = {}
            self.imglistTmp = []
            self.FacesGet_batch_framelist()
            if len(self.frames):
                #批处理人脸识别
            
                err = self.FacesGet_batch_run()
                '''
                Traceback (most recent call last):
                File "h:/WE4/_git/Photo-Manager.py", line 877, in FacesGet_batch_run
                    batch_of_face_locations = face_recognition.batch_face_locations(self.frames, number_of_times_to_upsample=0)
                File "C:\ProgramData\Anaconda3\envs\tensorflow_gpu\lib\site-packages\face_recognition\api.py", line 146, in batch_face_locations
                    raw_detections_batched = _raw_face_locations_batched(images, number_of_times_to_upsample, batch_size)
                File "C:\ProgramData\Anaconda3\envs\tensorflow_gpu\lib\site-packages\face_recognition\api.py", line 129, in _raw_face_locations_batched
                    return cnn_face_detector(images, number_of_times_to_upsample, batch_size=batch_size)
                RuntimeError: Error while calling cudaMalloc(&data, new_size*sizeof(float)) in file I:\dlib-19.17\dlib\cuda\gpu_data.cpp:218. code: 2, reason: out of memory
                如果有错误溢出，先减少bsize再试，如果self.gpuLastBsize = 1时还出现错误，改为单张人脸识别 self.gpuUseBatch = 0， 并且把列表self.curImgAll里的照片出来完毕
                '''
                if err:
                    err = re.sub(r'\n+|\t','',err,0,re.M)
                    if re.match(r'.*reason\:\s+out\s+of\s+memory',err,re.I):
                        MemoryStatus()                                                
                        self.gpuLastBsize = int(self.gpuLastBsize/2)
                        print('\t... reduce batch size to',self.gpuLastBsize,'images/batch')
                        #把临时列表self.imglistTmp里的数据放回原来的列表self.curImgAll
                        for p in self.imglistTmp:  
                            self.curImgAll.append([p[0],p[1],p[2],p[3],p[4]])
                        reRun = 1
                        break
                    else:
                        #改为单张人脸识别
                        for p in self.imglistTmp:  #self.imglistTmp临时保存 [[self.ik,fname,self.curFilepath,self.picK,im,im90,im180],...]
                            self.FacesGet(ik=p[0],fpath=p[2],picK=p[3],im=p[4])
            else:
                #改为单张人脸识别
                for p in self.imglistTmp:  #self.imglistTmp临时保存 [[self.ik,fname,self.curFilepath,self.picK,im,im90,im180],...]
                    self.FacesGet(ik=p[0],fpath=p[2],picK=p[3],im=p[4])

            self.imglistTmp = []

        if reRun:
            self.FacesGet_batch()
        else:
            print("\tbatch processed images",qty,', used time',usedTime(stime),',',int((time.time()-stime)*100)/100,'sec/image\n')
    
    def FacesCropFromImage(self,faces=None,curframe=None,im=None,faceList=None,rotateN=0):
        #从照片抓取人脸
        try:
            #获取人脸特征face_encodings             
            #print("\tface_encodings ...")
            face_encodings = face_recognition.face_encodings(curframe, faces)            

            nn= 0
            for (A,B,C,D) in faces:    #top, right, bottom, left                  
                dx = 10                              
                face_encoding = face_encodings[nn] 
                nn +=1 
                try:
                    box = (D-dx,A-dx,B+dx,C+dx)
                    iface = im.crop(box) 
                    
                    if len(faceList):
                        isThere = 0
                        for fi in faceList:
                            if fi[0] != rotateN:
                                result = face_recognition.compare_faces([fi[1]], face_encoding, tolerance=0.6)
                                #--print('\t\tcompare_faces ...',faceCount,'(',rotateN,') v.s. ',fi[3],'(',fi[0],'), result=',result)
                                if result:
                                    isThere += 1
                                    
                        if isThere == 0:
                            faceList.append([rotateN,face_encoding,iface])
                    else:                                                             
                        faceList.append([rotateN,face_encoding,iface])                                          
                except:
                    MemoryStatus()
                    print(traceback.format_exc())
        except:
            MemoryStatus()
            print(traceback.format_exc())

    def FacesGet(self,ik=None,im=None,fpath=None,picK=0):
        #单张照片人脸识别    
        stime = time.time()        
        
        if not ik:
            ik = self.ik
        if not im:
            im = self.FacePrepareIm() 
        if not fpath:
            fpath = self.curFilepath
        if not picK:
            picK = self.picK
        
        print("\t",str(picK) + "/" + str(self.allPicQTY),"checking faces:",fpath)

        try:
            if im:      
                print ("\timage size : %s, mode: %s" % (im.size, im.mode))                              
                angles = [0,1,1,1]
                rotateN = 0
                faceList = []
                for rotate in angles:
                    if rotate:
                        rotateN += 90   
                        img = cv2.cvtColor(numpy.array(im),cv2.COLOR_RGB2BGR) 
                        img = cv2.flip(cv2.transpose(img), 1)  
                        im  = Image.fromarray(cv2.cvtColor(img,cv2.COLOR_BGR2RGB))                           

                    #--print("\timage size : %s, mode: %s" % (im.size, im.mode),', rotateN=',rotateN)
                    
                    img_xx = cv2.cvtColor(numpy.array(im.convert('L')),cv2.COLOR_RGB2BGR)
                    rgb_small_frame = img_xx[:, :, ::-1]   

                    #model: hog or cnn, return a list of (top, right, bottom, left) 
                    #如果使用self.face_recognition_mode='cnn'时有内存溢出，改用self.face_recognition_mode ='hog'
                    faces = []
                    #MemoryStatus()
                    try: 
                        faces = face_recognition.face_locations(rgb_small_frame,number_of_times_to_upsample=self.nott_upsample, model=self.face_recognition_mode)                    
                    except:
                        err = traceback.format_exc()
                        print(err)
                        err = re.sub(r'\n+|\t','',err,0,re.M)
                        if re.match(r'.*reason\:\s+out\s+of\s+memory',err,re.I):
                            MemoryStatus()
                            if self.face_recognition_mode != 'hog':
                                print("\t... face_recognition.face_locations: reset to CPU mode - hog, and redo ...")
                                self.face_recognition_mode = 'hog' 
                                faces = face_recognition.face_locations(rgb_small_frame,number_of_times_to_upsample=self.nott_upsample, model=self.face_recognition_mode)                                   
                    if len(faces):        
                        #print("\t\tfaces:",faces)                             
                        self.FacesCropFromImage(faces=faces,curframe=rgb_small_frame,im=im,faceList=faceList,rotateN=rotateN)
                
                if len(faceList):
                    #保存抓取到的人脸
                    self.FacePush([[ik,fpath,faceList]])    

                cv2.destroyAllWindows()
            else:
                print('\tinvalid image!!')
        except:
            print(traceback.format_exc())
            MemoryStatus()

        print('\tchecked faces - used time:',usedTime(stime),"\n")

    def FacePush(self,faceLists):  
        #保存抓取到的人脸      
        for p in faceLists:
            ik       = p[0]
            faceID   = hashlib.md5((p[1] + str(time.time())).encode(encoding='UTF-8',errors='strict')).hexdigest() 
            faceList = p[2]

            nn = 0
            for fi in faceList:
                nn +=1
                fname = self.FacesPath+ '/faces_' + faceID + '_' + str(nn)  

                n = 0
                name = fname
                while os.path.exists(name + '.png'):    
                    n +=1
                    name = fname + '_' + str(n)
                
                if n >0:
                    fname += '_' + str(n) + '.png'      
                else:
                    fname += '.png'
                
                im = fi[2]        

                rwidth = 80
                rheight= 80
                im = fi[2]
                if im.size[0] > rwidth:
                    w  = rwidth
                    h  = int(rwidth / im.size[0] * im.size[1])
                    im = im.resize((w, h))
                    #print("\tresize to",w,'x',h)

                if im.size[1] > rheight:
                    h  = rheight
                    w  = int(rheight / im.size[1] * im.size[0])
                    im = im.resize((w, h))
                    #print("\tresize to",w,'x',h)

                try:
                    im_array = numpy.array(im)
                    if IsTrue(im_array):
                        img2gray = cv2.cvtColor(im_array, cv2.COLOR_BGR2GRAY)
                        self.ifiles[ik]['image_laplacian']  = int(cv2.Laplacian(img2gray, cv2.CV_64F).var())
                        self.ifiles[ik]['image_brightness'] = int(ImageStat.Stat(Image.fromarray(im_array).convert('L')).mean[0])
                except:
                    print(traceback.format_exc())

                self.eyeLips = { 'eye_y': [],
                            'lip_y': [],
                            'avg_eye_y':0,
                            'avg_lip_y':0,

                            'bias_eyes':-1,   
                            'face_side': '',
                            'slope_eyes': 1000,
                            'slope_nose_bridge': 0,
                            'face_looking_bias': -1,
                            'reSize':0,
                            'landmarks':b'',
                            'laplacian':1,
                            'brightness':0,
                            'overall_evaluation': 100,
                            'label_correct':''
                            }

                imx = self.FaceLandmarks(im,ik)
                if imx:
                    im = imx

                try:
                    self.eyeLips['laplacian'] = 1
                    self.eyeLips['brightness'] = 0

                    im_array = numpy.array(im)
                    if IsTrue(im_array):
                        img2gray = cv2.cvtColor(im_array, cv2.COLOR_BGR2GRAY)
                        self.eyeLips['laplacian']  = int(cv2.Laplacian(img2gray, cv2.CV_64F).var())
                        self.eyeLips['brightness'] = int(ImageStat.Stat(Image.fromarray(im_array).convert('L')).mean[0])
                except:
                    print(traceback.format_exc())

                im.save(fname)
                self.ifiles[ik]['face_idx'] = faceID 

                imgZ = ZipArray(numpy.array(im))
                label,self.eyeLips['label_correct'] = self.FaceRecognition(fi[1],imgZ)
                encodeZ = ZipArray(fi[1])                
                
                #评估照片                     
                looking = self.eyeLips['laplacian']
                if looking == -1:
                    looking = 50
                laplacian  = self.eyeLips['laplacian']
                brightness = abs(130 - self.eyeLips['brightness'])/130*100   #亮度0-255，取中间值130，照片亮度与130的偏差值 
                status = 1000
                if self.eyeLips['slope_nose_bridge'] > 0:
                    status = int( (abs(self.eyeLips['bias_eyes'] * 100) + abs(self.eyeLips['slope_eyes'] * 1000)) / abs(self.eyeLips['slope_nose_bridge']))
                score = int(1/((status + looking  + brightness) / laplacian))   #int((status + looking + brightness) / laplacian*10000)
                self.eyeLips['overall_evaluation'] = score

                self.facesData.append([fname,label,faceID,encodeZ,imgZ,self.eyeLips])  #[path,label,idx,encodings,image]

                print("\n\tfname=",fname,'\n\tlabel=',label,'\n\tname=',self.eyeLips['label_correct'])
            
            print("\t" + p[1] + ", total found faces:",nn,"\n")

    def FaceLandmarks(self,im,ik):
        isDone = 0

        for reSize in [0,160,320]:
            if isDone:
                break  

            if reSize:
                if im.size[0] > im.size[1]:
                    w  = reSize
                    h  = int(reSize / im.size[0] * im.size[1])
                    im = im.resize((w, h))
                else:
                    h  = reSize
                    w  = int(reSize / im.size[1] * im.size[0])
                    im = im.resize((w, h))

            angles = [0,1,1,1]
            rotateN = 0
            
            face_landmarks_list = []
            imc = None
            for rotate in angles:
                if isDone:
                    break     

                try:
                    if rotate:
                        rotateN += 90    
                        im  = Image.fromarray( cv2.cvtColor(cv2.flip(cv2.transpose( cv2.cvtColor(numpy.array(im),cv2.COLOR_RGB2BGR) ), 1) ,cv2.COLOR_BGR2RGB))
                        
                    img= cv2.cvtColor(numpy.array(im.convert('L')),cv2.COLOR_RGB2BGR)                
                    im_frame = img[:, :, ::-1]  

                    face_landmarks_list = face_recognition.face_landmarks(im_frame)
                    #faces_locations = face_recognition.face_locations(im_frame,number_of_times_to_upsample=self.nott_upsample, model=self.face_recognition_mode)  #can not play face_locations after face_landmarks!!!!
                    #print("\t\trotation= {:0>3d}, len(face_landmarks_list) = {}".format(rotateN,len(face_landmarks_list)))
                    #imc = im.copy()           
               
                    kk = self.Landmarks_parse(face_landmarks_list,imc=imc)   

                    if kk:                                                                                      
                        #print("\t\t"+str(kk)+" detected features in its landmark!")       
                        if self.eyeLips['avg_eye_y'] and self.eyeLips['avg_lip_y'] and self.eyeLips['avg_eye_y'] < self.eyeLips['avg_lip_y']:
                            #print("\t\t.. good landmark detected!") 
                            isDone  = 1
                            self.eyeLips['reSize'] = reSize
                            self.eyeLips['landmarks'] = ZipArray(face_landmarks_list)

                            #if rotateN > 0 or reSize:
                            #    self.face_encodings.append([ik,im])
                except:
                    print(traceback.format_exc())

            if isDone:
                print("\t\tThe face Landmark list:",len(face_landmarks_list))
                #imc.show()
                #cv2.waitKey(500)            
        
        if not isDone:
            im = None  

        cv2.destroyAllWindows()
        return im

    def Landmarks_parse(self,face_landmarks_list,imc=None):
            '''
            lineA: （两眼，脸廓线两端点）的拟合直线，斜率
            lineB: 鼻梁的拟合直线，斜率
            B线分割A线的，左右两段的长度dLeft，dRight
            '''
            dataset = {'AX':[],
                    'AY':[],
                    'BX':[],  
                    'BY':[]
                    }

            kk = 0
            if not IsTrue(face_landmarks_list):
                return kk

            try:
                d = None
                if imc:
                    d = ImageDraw.Draw(imc)

                for face_landmarks in face_landmarks_list:                        
                    # Print the location of each facial feature in this image                        
                    for facial_feature in face_landmarks.keys():
                        kk +=1
                        #print("\t\t.. The {} in the points: {}".format(facial_feature, face_landmarks[facial_feature]))
                        if re.match(r'.*_eye',facial_feature,re.I):
                            x1 = 100000000
                            y1 = 0
                            x2 = 0
                            y2 =0
                            for e in face_landmarks[facial_feature]:
                                self.eyeLips['eye_y'].append(e[1])
                                dataset['AX'].append(e[0])
                                dataset['AY'].append(e[1])
                                if x1 > e[0]:
                                    x1 = e[0]
                                    y1 = e[1]
                                if x2 < e[0]:
                                    x2 = e[0]
                                    y2 = e[1]

                            if re.match(r'.*left_eye',facial_feature,re.I):
                                dataset['eye_left_len']     = x2 - x1
                                dataset['eye_left_xyLeft']  = [x1,y1]
                                dataset['eye_left_xyRight'] = [x2,y2]    
                            else:
                                dataset['eye_right_len'] = x2 - x1
                                dataset['eye_right_xyLeft']  = [x1,y1]
                                dataset['eye_right_xyRight'] = [x2,y2]    

                        elif re.match(r'.*_lip',facial_feature,re.I): 
                            xs = []
                            ys = []  
                            x1 = 0
                            y1 = 0   
                            for e in face_landmarks[facial_feature]:
                                self.eyeLips['lip_y'].append(e[1])
                                xs.append(e[0])
                                ys.append(e[1])
                                if e[1] > y1:
                                    x1 = e[0]
                                    y1 = e[1]

                            dataset['lip_center_xy'] = [numpy.mean(xs),numpy.mean(ys)]
                            dataset['lip_bot_xy'] = [x1,y1]

                        elif re.match(r'nose\_bridge',facial_feature,re.I):    
                            x = 0
                            y = 100000000                    
                            for e in face_landmarks[facial_feature]:
                                dataset['BX'].append(e[0])
                                dataset['BY'].append(e[1])
                                if e[1] < y:
                                    y = e[1]
                                    x = e[0]                        
                            dataset['nose_top_xy'] = [x,y]

                        elif re.match(r'nose\_tip',facial_feature,re.I):
                            y = 0
                            x = 0
                            x1= 1000000000000000
                            y1 =0
                            x2 =0
                            y2 =0
                            for e in face_landmarks[facial_feature]:
                                if y < e[1]:
                                    y = e[1]
                                    x = e[0]
                                if x1 > e[0]:
                                    x1 = e[0]
                                    y1 = e[1]
                                if x2 < e[0]:
                                    x2 = e[0]
                                    y2 = e[1]

                            dataset['nose_len_x']   = x2 - x1
                            dataset['nose_bot_xy']  = [x,y]
                            dataset['nose_left_xy'] = [x1,y1]
                            dataset['nose_right_xy']= [x2,y2]

                        elif re.match(r'chin',facial_feature,re.I):
                            x1 = 1000000000
                            y1 = 0
                            x2 = 0
                            y2 = 0
                            x3 = 0
                            y3 = 0
                            for e in face_landmarks[facial_feature]:
                                if x1 > e[0]:
                                    x1 = e[0]
                                    y1 = e[1]

                                if x2 < e[0]:
                                    x2 = e[0]
                                    y2 = e[1]

                                if y3 < e[1]:
                                    y3 = e[1]
                                    x3 = e[0]
                                
                            dataset['chin_left_xy'] = [x1,y1]
                            dataset['chin_right_xy']= [x2,y2]
                            dataset['chin_bot_xy']  = [x3,y3]
                            dataset['AX'].append(x1) 
                            dataset['AX'].append(x2)
                            dataset['AY'].append(y1)
                            dataset['AY'].append(y2)                           
                                    
                    #Let's trace out each facial feature in the image with a line!
                    if d:
                        for facial_feature in face_landmarks.keys():
                            d.line(face_landmarks[facial_feature], fill = (255,0,0), width=1)
                
                try:
                    if d:
                        icolor = (0,255,0)
                        iwidth = 1
                        
                        d.line( ( (dataset['eye_left_xyLeft'][0], dataset['eye_left_xyLeft'][1]), (dataset['eye_left_xyRight'][0],dataset['eye_left_xyRight'][1] ) ), fill = icolor, width=iwidth)    #1                 
                        d.line( ( (dataset['eye_right_xyLeft'][0],dataset['eye_right_xyLeft'][1]),(dataset['eye_right_xyRight'][0],dataset['eye_right_xyRight'][1]) ), fill = icolor, width=iwidth)   #2                 
                        d.line( ( (dataset['nose_left_xy'][0], dataset['nose_left_xy'][1]), (dataset['nose_right_xy'][0],dataset['nose_right_xy'][1]) ), fill = icolor, width=iwidth)                 #3
            
                        d.line( ( (dataset['nose_bot_xy'][0], dataset['nose_bot_xy'][1]), (dataset['chin_bot_xy'][0],dataset['chin_bot_xy'][1]) ), fill = icolor, width=iwidth)   #4                 
                        d.line( ( (dataset['nose_bot_xy'][0], dataset['nose_bot_xy'][1]), (dataset['nose_top_xy'][0],dataset['nose_top_xy'][1]) ), fill = icolor, width=iwidth)   #5
                        
                        d.line( ( (dataset['nose_bot_xy'][0], dataset['nose_bot_xy'][1] ), (dataset['lip_bot_xy'][0], dataset['lip_bot_xy'][1] ) ), fill = icolor, width=iwidth)  #6
                        d.line( ( (dataset['chin_bot_xy'][0], dataset['chin_bot_xy'][1] ), (dataset['lip_bot_xy'][0], dataset['lip_bot_xy'][1] ) ),  fill = icolor, width=iwidth) #7
                        
                        d.line( ( (dataset['nose_bot_xy'][0], dataset['nose_bot_xy'][1]), (dataset['lip_center_xy'][0], dataset['lip_center_xy'][1] ) ), fill = icolor, width=iwidth) #8                  
                        d.line( ( (dataset['chin_bot_xy'][0], dataset['chin_bot_xy'][1]), (dataset['lip_center_xy'][0], dataset['lip_center_xy'][1] ) ), fill = icolor, width=iwidth) #9
                        
                    chin_width = abs(dataset['chin_right_xy'][0] - dataset['chin_left_xy'][0])
                    face_width = chin_width * 5 /4
                    bias = []
                    if face_width > 0:
                        bias.append((face_width/5 - dataset['eye_left_len'] ) / (face_width/5) *100)  #1
                        bias.append((face_width/5 - dataset['eye_right_len']) / (face_width/5) *100)  #2
                        bias.append((face_width/5 - dataset['nose_len_x']   ) / (face_width/5) *100)  #3
                    
                    nose_chin_dist    = int(math.sqrt((dataset['nose_bot_xy'][0] - dataset['chin_bot_xy'][0])**2 +  (dataset['nose_bot_xy'][1] - dataset['chin_bot_xy'][1])**2))   #4
                    nose_len_y        = int(math.sqrt((dataset['nose_bot_xy'][0] - dataset['nose_top_xy'][0])**2 +  (dataset['nose_bot_xy'][1] - dataset['nose_top_xy'][1])**2))   #5

                    noseBot_lipBot    = int(math.sqrt((dataset['nose_bot_xy'][0] - dataset['lip_bot_xy' ][0] )**2 + (dataset['nose_bot_xy'][1] - dataset['lip_bot_xy' ][1])**2))   #6
                    lipBot_chinBot    = int(math.sqrt((dataset['chin_bot_xy'][0] - dataset['lip_bot_xy' ][0] )**2 + (dataset['chin_bot_xy'][1] - dataset['lip_bot_xy' ][1])**2))   #7

                    noseBot_lipCenter = int(math.sqrt((dataset['nose_bot_xy'][0] - dataset['lip_center_xy'][0] )**2 + (dataset['nose_bot_xy'][1] - dataset['lip_center_xy'][1] )**2))  #8
                    lipCenter_chinBot = int(math.sqrt((dataset['chin_bot_xy'][0] - dataset['lip_center_xy'][0] )**2 + (dataset['chin_bot_xy'][1] - dataset['lip_center_xy'][1] )**2))  #9              

                    half_nose_chin = (nose_chin_dist + nose_len_y)/2
                    if(half_nose_chin):
                        bias.append((nose_chin_dist - nose_len_y    ) / half_nose_chin *100)
                        bias.append((noseBot_lipBot - half_nose_chin/2) / (half_nose_chin / 2) *100)
                        bias.append((lipBot_chinBot - half_nose_chin/2) / (half_nose_chin / 2) *100)
                        bias.append((noseBot_lipCenter - half_nose_chin/3) / (half_nose_chin / 3) *100)
                        bias.append((lipCenter_chinBot - half_nose_chin*2/3) / (half_nose_chin*2/3) *100)
                    
                    if(len(bias)):
                        self.eyeLips['face_looking_bias'] = int(numpy.sqrt(numpy.mean(numpy.square(numpy.array(bias)))))

                except:
                    print(traceback.format_exc())

                self.eyeLips['avg_eye_y'] = numpy.average(numpy.array(self.eyeLips['eye_y']))
                self.eyeLips['avg_lip_y'] = numpy.average(numpy.array(self.eyeLips['lip_y']))

                #lineA: （两眼，脸廓线两端点）的拟合直线，斜率
                zA = numpy.polyfit(dataset['AX'],dataset['AY'],1)
                #lineA = numpy.poly1d(zA)
                #print("\nlineA: （两眼，脸廓线两端点）的拟合直线，斜率\n",zA,"\n",lineA,"\n")
                #[ 0.07307172 23.51962111]
                #0.07307 x + 23.52

                #lineB: 鼻梁的拟合直线，斜率
                zB = [] #numpy.polyfit(dataset['BX'],dataset['BY'],1)
                #lineB = numpy.poly1d(zB)
                #print("lineB: 鼻梁的拟合直线，[斜率,截距]=\n",zB,"\n",lineB)
                #[ -3.4 180.5]
                #-3.4 x + 180.5
                if(dataset['BX'][0] == dataset['BX'][-1]):
                    if(dataset['BY'][0] != dataset['BY'][-1]):
                        #print("\t公式计算: 垂直斜率无穷大\n")
                        zB = [10000000000,dataset['BX'][0]]   
                    else:
                        print("\t公式计算: 就一点，没有计算斜率\n")
                elif dataset['BY'][0] == dataset['BY'][-1]:
                    #print("\t公式计算: 水平斜率=0\n")
                    zB = [0,dataset['BY'][0]]      
                else:
                    slope = (dataset['BY'][0] - dataset['BY'][-1])/(dataset['BX'][0] - dataset['BX'][-1])
                    b = dataset['BY'][0] - slope*dataset['BX'][0]
                    zB = [slope, b]
                    #print("\t公式计算: [斜率,截距]=",zB,"\n")
                
                #print("lineB: 鼻梁的拟合直线, (公式计算) [斜率,截距]=",zB,"\n")

                #B线分割A线的，左右两段的长度dLeft，dRight
                if(zA[0] == zB[0]): #如果斜率相等, 鼻梁线与两眼平齐，不科学，不考虑这种情况！
                    print('\t（两眼，脸廓线两端点）的拟合直线, 鼻梁的拟合直线, 没有交点！！')
                else:
                    topY = numpy.min(dataset['BY'])
                    botY = numpy.max(dataset['BY'])
                    topX = 0
                    botX = 0
                    leftX  = numpy.min(dataset['AX'])
                    rightX = numpy.max(dataset['AX'])
                    leftY  = 0
                    rightY = 0
                    x = 0
                    y = 0
                    slopes = [0,0]

                    if zA[0] != 0:
                        slopes[0] = int(zA[0]*10)/10

                        leftY  = zA[0]*leftX  + zA[1]                
                        rightY = zA[0]*rightX + zA[1]

                        if zB[0] == 10000000000:
                            slopes[1] = 10000000000
                            topX = zB[1]
                            botX = zB[1]
                            x    = zB[1] 
                            y    = zA[0]*x + zA[1]

                        elif zB[0] == 0:
                            slopes[1] = 0
                            topX = dataset['BX'][0]
                            botX = dataset['BX'][-1]
                            y    = dataset['BY'][0]
                            x    = (y - zA[1])/zA[0]
                        else:
                            slopes[1] = int(zB[1]*10)/10

                            topX = (topY - zB[1])/zB[0]            
                            botX = (botY - zB[1])/zB[0]
                            x    = (zB[1] - zA[1]) / (zA[0] - zB[0])                
                            y    = zA[0]*x + zA[1]
                    else:
                        slopes[0] = 0

                        leftY  = zA[1]                
                        rightY = zA[1]

                        if zB[0] == 10000000000:
                            slopes[1] = 10000000000

                            topX = zB[1]
                            botX = zB[1]
                            x    = zB[1] 
                            y    = zA[1]
                        #elif zB[0] == 0:  #not this case any more here!
                        else:
                            slopes[1] = int(zB[1]*10)/10

                            topX = (topY - zB[1])/zB[0]            
                            botX = (botY - zB[1])/zB[0]
                            x    = (zB[1] - zA[1]) / (zA[0] - zB[0])                
                            y    = zA[1]            
                    if d:
                        d.line([(leftX,leftY), (rightX,rightY)], fill = (0,255,0), width=1)
                        d.line([(topX, topY ), (botX,  botY  )], fill = (0,0,255), width=2)            
                    
                    dLeft  = int(math.sqrt((x - leftX)**2  + (y - leftY)**2))      #左眼中心到鼻梁线的距离
                    dRight = int(math.sqrt((x - rightX)**2 + (y - rightY)**2))     #右眼中心到鼻梁线的距离       
                    if leftX > x:
                        dLeft = 0
                    elif rightX < x:
                        dRight = 0

                    bia = 1000
                    if(dLeft + dRight) > 0:
                        bia = int((dLeft - dRight)*2 / (dLeft + dRight) *100)
                        if zB[0] == 10000000000:
                            bia = int(bia / zB[0])

                        xxs = str(bia) + "\n" + str(slopes[0]) + ', ' + str(slopes[1]) + ' : ' + str(abs(int((bia + slopes[0]*100)/ slopes[1] * 10000))) + ', lookBias ' + str(self.eyeLips['face_looking_bias'])
                        if abs(bia) > 10:
                            if dLeft > dRight: #face turns left
                                #print("\t人脸向左转,看到右脸",zA,zB,bia)
                                if d:
                                    d.text((0,0),'right.' + xxs,fill = (255, 0 ,0))
                                self.eyeLips['face_side'] = 'right'
                            else: 
                                #print("\t人脸向右转，看到左脸",zA,zB,bia)
                                if d:
                                    d.text((0,0),'left.' + xxs,fill = (255, 0 ,0))
                                self.eyeLips['face_side'] = 'left'
                        else:
                            #print("\t人脸端正",zA,zB,bia)
                            if d:
                                d.text((0,0),'full.' + xxs,fill = (255, 0 ,0))
                            self.eyeLips['face_side'] = 'full'

                    else:
                        print("\t两眼到脸边的距离是0，不科学！！")

                    self.eyeLips['bias_eyes'] = bia
                    self.eyeLips['slope_eyes'] = slopes[0]
                    self.eyeLips['slope_nose_bridge'] = slopes[1]

                    #print((leftX,leftY), (x,y), (rightX,rightY),(dLeft,dRight),(dLeft - dRight,int((dLeft + dRight)/2),bia),"\n")
            except:
                print(traceback.format_exc())
            
            return kk
            '''
                    .. The chin in the points: [(13, 32), (14, 36), (14, 39), (16, 44), (18, 47), (22, 49), (26, 50), (31, 51), (36, 50), (40, 49), (43, 46), (45, 44), (46, 40), (47, 36), (46, 32), (45, 29), (44, 25)]
                    .. The left_eyebrow in the points: [(16, 26), (18, 24), (21, 22), (24, 22), (27, 23)]
                    .. The right_eyebrow in the points: [(30, 23), (33, 21), (36, 21), (39, 21), (41, 23)]

                    .. The nose_bridge in the points: [(30, 26), (30, 28), (31, 30), (32, 32)]
                    .. The nose_tip in the points: [(28, 36), (30, 36), (32, 36), (34, 35), (35, 34)]

                    .. The left_eye in the points:  [(20, 28), (22, 27), (24, 27), (26, 28), (24, 28), (22, 28)]
                    .. The right_eye in the points: [(33, 27), (35, 25), (37, 25), (38, 26), (37, 26), (35, 27)]

                    .. The top_lip in the points:    [(25, 41), (28, 39), (31, 37), (33, 37), (35, 37), (38, 37), (41, 37), (39, 38), (35, 38), (33, 38), (31, 39), (26, 41)]
                    .. The bottom_lip in the points: [(41, 37), (38, 40), (36, 41), (34, 42), (32, 42), (29, 42), (25, 41), (26, 41), (32, 41), (34, 40), (36, 40), (39, 38)]
            '''
        
class iSeparator:
    def __init__(self,frm,row=0,col=0,txt='|',fg='#FFFFFF',bg='#E0E0E0',p=[CENTER,FLAT,0,0]):
        self.label = Label(frm, 
                            text=txt, 
                            justify=p[0], 
                            relief=p[1],
                            pady=p[2],
                            padx=p[3],
                            fg=fg,
                            bg=bg
                            )
        self.label.grid(
                    row=row,
                    column=col,
                    sticky=E+W+N+S,
                    pady=0,
                    padx=0,
                        )
        
class iButton:
    def __init__(self,frm,row=0,col=0,cmd=None,txt='?',fg='blue',bg='#E0E0E0',
                    colspan=1, width = 0, tip = "", gridpadx = 0, gridpady = 0,
                    p=[LEFT,FLAT,3,1,'#FFFF66','#FFFF99',0,E+W+N+S,0,0]):

        if width:
            p[6] = width
            
        if gridpadx:
            p[9] = gridpadx
        if gridpady:
            p[8] = gridpady

        self.b = Button( frm, 
                    text=txt, 
                    fg=fg,
                    bg=bg,
                    justify=p[0], 
                    relief=p[1],
                    padx=p[2],
                    pady=p[3],                    
                    activebackground=p[4],
                    highlightbackground=p[5],
                    width=p[6],
                    command=cmd
                    )
        self.b.grid( row=row,
                column=col,
                sticky=p[7],
                pady=p[8],
                padx=p[9],
                columnspan=colspan
                )
        self.b.bind('<Motion>',self.iMotion)
        self.b.bind('<Leave>',self.iLeave)
        self.b.bind('<ButtonRelease-1>',self.iClick)
        self.bg = bg  
        
        if tip:
            WindX['winBalloon'].bind_widget(self.b, balloonmsg= tip)        
        
    def iMotion(self,event):
        self.b.config(bg = '#FFFFF0')

    def iLeave(self,event):
        self.b.config(bg = self.bg)
        
    def iClick(self,event):
        if WindX['WindowStatus'] == "normal":
            self.b.config(relief=RAISED)
                
if __name__ == '__main__':
    GUI()