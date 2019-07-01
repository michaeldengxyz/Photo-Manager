#Pyhton 3.x
# -*- coding: UTF-8 -*-
#rev: beta 00.01.00

import os
import sys 
import glob
import time 
import traceback
import re
from PIL import Image
from PIL.ExifTags import TAGS
import cv2
import pymysql
import base64 
import hashlib
import shutil

import numpy
import face_recognition
import zlib
import pickle
import pynvml  #pip install nvidia-ml-py3;  #Python bindings to the NVIDIA Management Library
import psutil

def main():   
    photo_dir = "H:/WE4/_git/tmp"   #给定存放照片的根文件夹，如果没有，默认为当前目录
    p = Photo(photo_dir)
    p.run()  #开始运行
    
class Photo():
    def __init__(self,pdir=None):   
        self.dir       = pdir
        self.refresh_all  = 0 #1 - 重新开始处理所有照片；0-保留上次已经处理的照片信息
        self.allPicQTY = 0  #初始默认路径下的照片数量
        self.picK      = 0       #已经遍历照片的数量
        self.formats   = ['BMP', 'TIFF', 'GIF', 'JPEG', 'PNG', 'JPG']  #照片格式
        self.pixels    = [1080,500,350] #,250,100,50  #照片小图的分辨率

        self.faceKnown = {}    #存放 - 已知人脸照片的特征        
        self.faceKnown['encodings'] = []
        self.faceKnown['labels'] = []
        self.facesData = []    #存放 - 人脸照片数据

        self.db        = None  #连接数据库的句柄
        self.dbName    = 'we3' #数据库名称 
        self.username  = 'we2' #登录数据库的用户名
        self.password  = '12345$9876' #登录密码

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

        checkNVIDIA_GPU(self) #check NVIDIA GPU only
        print('gpuUseBatch=',self.gpuUseBatch,'\ngpuLastBsize=',self.gpuLastBsize,'\nface_recognition_mode=',self.face_recognition_mode,'\nnott_upsample=',self.nott_upsample,'\n')
       
    def run(self):
        self.dir = re.sub(r'\\+','/',self.dir)
        self.dir = re.sub(r'\/*$','',self.dir)    
        print('start from this folder:',self.dir)

        if (not self.dir) or (not os.path.exists(self.dir)):
            #self.dir = re.sub(r'\\','/',os.path.abspath(os.path.dirname(__file__)))  #获取当前路径
            print("Please set a valid path where your photos were stored!!",'\n')
            return

        self.ConnectDB()
        self.cursor = self.db.cursor()  #连接数据库的指针

        self.FacesLabelGet()  
        self.startTime= time.time()

        #创建存放人脸图片的文件夹
        self.FacesPath = self.dir + '/Faces'
        if not os.path.exists(self.dir + '/Faces'):  
            os.makedirs(self.dir + '/Faces')

            #获取当前目录及子目录下所有照片的数量
        self.GetFileQTY(self.dir);  

        print (u"所有照片: ",self.allPicQTY,"\n");  
        
        #开始扫描照片：获取照片EXIF，人脸等信息，并创建照片的小图
        self.MakeThumbs(self.dir);          
        print ('\nTotal processed image&video:',self.process_qty,'/',self.allPicQTY,'\nAll done, Total used:',usedTime(self.startTime),'\n')      

        if self.db:   
            self.cursor.close()
            self.db.close() 

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
        
        for f in glob.glob("*"): 
            if (f == '.') or (f == '..') or (str(f).upper() == "THUMBABC") or (f=='Faces') or (f=='_git'):
                continue
                
            if os.path.isdir(curDir + "/" + f):
                self.GetFileQTY(curDir + "/" + f)    

    def MakeThumbs(self,curDir):   
        #遍历文件夹，找出照片与视频  
        sstime = time.time()

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
                    else:
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

            self.process_qty += processed_image
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
                    os.remove(f)

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
            for dirx in sorted(dirs):
                self.MakeThumbs(dirx)

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
            self.dirs = {}
            self.DirsGet()           
            self.DBColumnCheck()
            
            self.fields['dir_id'] = 1
            self.DirsCheck(cdir)
            
            idir = str(base64.b64encode(cdir.encode(encoding='utf-8')),'utf-8')
            if IsKeyExist(self.dirs,[idir]) and self.dirs[idir]:
                dir_id = self.dirs[idir]

                #如果是重新处理，删除在数据库里的当前文件夹的信息
                if self.refresh_all:
                    self.cursor.execute("DELETE FROM `filelist` WHERE `dir_id`='" + dir_id + "'")
                    self.cursor.execute("DELETE FROM `faces`    WHERE `dir_id`='" + dir_id + "'")
                    self.db.commit()  
            
            for n in self.ifiles:
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
                        fs.append("`" + fd.lower() + "`")
                        vals.append('%s')
                        arg.append(pymysql.escape_string(self.ifiles[n][fd]))
                    
                self.cursor.execute("INSERT INTO `filelist` ("+','.join(fs)+") VALUES("+",".join(vals)+")", arg)
            
            self.db.commit()                         
        except:
            print("\t.. Save to db error: \n\t\t",traceback.format_exc())
            self.db.rollback()  
        
        self.FacesLabelToDB(dir_id)

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
        
        if n >0:
            name = mtime + '_' + str(n) + '.' + str(ftype[-1]).upper()        
        else:
            name = mtime + '.' + str(ftype[-1]).upper() 
        
        os.rename(file,name) 
        if not NotCheckThumbABC:   
            if os.path.exists(name):    
                for p in self.pixels:
                    if os.path.exists('ThumbABC/W'+str(p)+'/' + file):
                        os.rename('ThumbABC/W'+str(p)+'/' + file,'ThumbABC/W'+str(p)+'/' + name) 
            else:
                name = file
        else:
            print("\tRename: from ",file,"to",name)
            
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
        
                im.thumbnail((w, h))
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
    
    def FaceRecognition(self,unkown_encodings=None,imgZ=None):
        #人脸辨识，返回其标签，如果没有找到对应的标签，新增一个标签
        #print(type(unkown_encodings),unkown_encodings)
        if not IsTrue(unkown_encodings):
            return ""
        
        n = len(self.faceKnown['labels'])
        name = "Unknown" + str(n + 1)
        if n:
            try:
                matches = face_recognition.compare_faces(self.faceKnown['encodings'], unkown_encodings,tolerance=0.5)

                # If a match was found in known_face_encodings, just use the first one.
                if True in matches:
                    first_match_index = matches.index(True)
                    name = self.faceKnown['labels'][first_match_index][1]
                else:
                    self.faceKnown['labels'].append(['',name,imgZ])
                    self.faceKnown['encodings'].append(unkown_encodings) 
            except:
                print(traceback.format_exc())
        else:
            self.faceKnown['labels'].append(['',name,imgZ])
            self.faceKnown['encodings'].append(unkown_encodings)   

        return name

    def FacesLabelGet(self):
        self.faceKnown = {}
        self.faceKnown['encodings'] = []
        self.faceKnown['labels'] = []

        #cursor = self.db.cursor()
        try:
            self.cursor.execute("SELECT `id`,`label`,`encodings` FROM `faces_label`")
            results = self.cursor.fetchall()
            for p in results:
                self.faceKnown['labels'].append([p[0],p[1]])            
                self.faceKnown['encodings'].append(ZipArray(p[2],isZip=False))            
        except:
            print(traceback.format_exc())

        #try:
        #    cursor.close()
        #except:
        #    pass

    def FacesLabelToDB(self,dirID):
        print("\n.... save faces labels to db ...")
        #cursor = self.db.cursor()

        n = len(self.faceKnown['labels'])
        try:
            for i in range(n):
                if not self.faceKnown['labels'][i][0]:  #no id
                    try:
                        sqlstr = "INSERT INTO `faces_label` (`label`,`encodings`,`image`) " + \
                                'VALUES("%s","%s","%s")' \
                                    % (
                                        self.faceKnown['labels'][i][1],
                                        pymysql.Binary(ZipArray(self.faceKnown['encodings'][i])),
                                        pymysql.Binary(self.faceKnown['labels'][i][2])
                                    )

                        self.cursor.execute(sqlstr)                          
                    except:
                        print(traceback.format_exc())
            self.db.commit() 
            self.FacesLabelGet()
        except:
            print(traceback.format_exc())
        
        print(".... save faces data to db ...\n")
        try:
            #self.facesData.append([fname,label,faceID,encodeZ,imgZ])  #[path,label,idx,encodings,image]
            for face in self.facesData:
                try:
                    #print(face[0],'\n',face[1],"\n",face[2],"\n",str(dirID),"\n",face[0])
                    sqlstr = "INSERT INTO `faces` (`path`,`label`,`idx`,`dir_id`,`encodings`,`image`) " + \
                            'VALUES("%s","%s","%s","%s","%s","%s")' \
                                % (
                                    pymysql.escape_string(face[0]),
                                    pymysql.escape_string(face[1]),
                                    pymysql.escape_string(face[2]),
                                    str(dirID),
                                    pymysql.Binary(face[3]),
                                    pymysql.Binary(face[4])
                                )

                    self.cursor.execute(sqlstr)                          
                except:
                    print(traceback.format_exc())
            self.db.commit()             
        except:
            print(traceback.format_exc())        
        self.facesData = []

        #try:
        #    cursor.close()
        #except:
        #    pass

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

                        #转角度90,180
                        rotateN = 0
                        for ii in range(2):
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
                angles = [0,1,1]
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
            
                im.save(fname)
                self.ifiles[ik]['face_idx'] = faceID 

                imgZ = ZipArray(numpy.array(im))
                label   = self.FaceRecognition(fi[1],imgZ)
                encodeZ = ZipArray(fi[1])                
                self.facesData.append([fname,label,faceID,encodeZ,imgZ])  #[path,label,idx,encodings,image]
                print("\n\tfname=",fname,'\n\tlabel=',label)
            
            print("\t" + p[1] + ", total found faces:",nn,"\n")

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

def usedTime(stime,t=0):
    if not t:
        t = time.time() - stime

    tt={'h':'00','m':'00','s':'00'}
    
    if t > 3600:
        h = int(t/3600)
        tt['h'] = "{:0>2d}".format(h)
        t = t - h*3600
       
    if t > 60:
        m = int(t/60);
        tt['m'] = "{:0>2d}".format(m)
        t = t - m*60;

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
        
if __name__ == '__main__':
    main()