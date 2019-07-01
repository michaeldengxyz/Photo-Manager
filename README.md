# Photo-Manager
This is a python project.
The project is to auto treat my own photos after I backup them into my local computer drive from cellphone, camera, etc。

这是一个Python写的项目。
家里有很多照片，我通常照时间顺序把他们按保存在一个硬盘里，越堆越多，现在足足有30多万。

做这个项目的的目的是，处理这些一大推的照片，想知道：

--- 照片在哪里拍的 （GPS信息）

--- 照片什么时候拍的（拍摄时间）

--- 照片里有什么人  （人脸识别）

--- 照片里的人与我的关系 （大数据）

--- 其他的，还没有想好，后面再加进去。


##----------- 基本需求 -----------##

1）软件：

--Pyhton

--MySQL

--PHP

--JAVA Script


2）硬件配置 （渣渣的配置，表笑！）：

--操作系统	Windows 10 Enterprise 64位

--处理器	英特尔 第三代酷睿 i5-3470 @ 3.20GHz 四核

--主板	映泰 TZ77A

--内存	16 GB ( 金士顿 DDR3 1600MHz )

--主硬盘	ADATA SP900 ( 256 GB / 固态硬盘 )

--主显卡	Nvidia GeForce GTX 960 ( 2 GB / 七彩虹 )

--网卡	瑞昱 RTL8168/8111/8112 Gigabit Ethernet Controller / 映泰


##----------- 基本思路 -----------##

后台：Python整理照片，把信息保存到MySQL数据库，

前台：使用内部网页显示照片，局域网内的电脑和移动设备都可以访问。


1.后台处理：
程序：Photo-Manager.py

1.1）遍历每个文件夹，找出所有照片，格式['BMP', 'TIFF', 'GIF', 'JPEG', 'PNG', 'JPG']， 
     遍历每个视频，格式MP3|MP4|MOV|AVI|RM|RMVB|MTV|FLV|MKV|3GP|RMVB；
     
1.2） 抽取视频的第一帧，方便以后在内部网页显示；

1.3） 给每张照片做小图，最长边的分辨率为[1080,500,350]， 保存在其目录里的ThumbABC文件夹，即ThumbABC/W1080，ThumbABC/W500，ThumbABC/W350；方便以后在内部网页显示；

1.4）给每张照片做人脸识别，截取人脸图片，并设置相应的标签（TA是谁）。

这一部分需要用到卷积神经网络CNN，需要GPU的算力支持，不然处理速度会很慢，所以我需要装卡。


2.前台网页：

做一个PHP的网页，连接MySQL数据库，读取硬盘目录下的照片，显示在页面上。

