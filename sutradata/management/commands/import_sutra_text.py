from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from sutradata.models import *
from tasks.models import *

import TripitakaPlatform.settings

import os, sys
from os.path import isfile, join
import traceback
import re
import codecs

class Command(BaseCommand):
    def handle(self, *args, **options):
        get_YBSutra()
                    

#*************************************custom methods*******************************************
import json
from urllib import request
def get_reel_text(sid, reel_no, vol_no, start_page_no, end_page_no):
    reel_txt = ''
    for page_no in range(start_page_no, end_page_no+1):
        cut_url = 'https://s3.cn-north-1.amazonaws.com.cn/lqcharacters-images/%s/%s/v%03d/%sv%03dp%04d0.cut' %\
        (
            sid[:2],
            sid[2:],
            vol_no,
            sid,
            vol_no,
            page_no
        )
        print('cut_url:',cut_url)
        page_dict = json.loads(request.urlopen(cut_url).readlines()[0])
        txt = {}
        for c in page_dict['char_data']:
            col_no = int(c['char_id'][18:20])
            char_no = int(c['char_id'][21:])
            char = c['char']
            if col_no in txt.keys():
                txt[col_no][char_no] = char
            else:
                txt[col_no] = {char_no:char}
        for col_no in txt.keys():
            col_txt = sorted(txt[col_no].items(), key = lambda a:a[0], reverse=False)
            txt[col_no] = ''.join(list(zip(*col_txt))[1])
        p_txts = sorted(txt.items(), key=lambda a:a[0], reverse=False)
        p_txt ='p\n'+ '\n'.join(list(zip(*p_txts))[1]) + '\n'
        
        reel_txt = reel_txt + p_txt 
    # 去除最后的换行符
    if reel_txt[-1] == '\n':
        reel_txt = reel_txt[:-1]
    
    return reel_txt

#遍历文件夹，获取所有txt文件路径
def myEachFiles(path):
    _pathList=[]
    filepath = path
    
    fileType = '.txt'
    if os.path.isdir(filepath):
        pathDir =  os.listdir(filepath)
        for allDir in pathDir:
            child = os.path.join('%s/%s' % (filepath, allDir))
            if os.path.isdir(child):
                _pathList.append(myEachFiles(child))
                pass
            else:
                typeList = os.path.splitext(child)
                if typeList[1] == fileType:#check file type:.txt
                    _pathList.append(child)
                    #print('child:','%s' % child.encode('utf-8','ignore'))
                    pass
                else:#not .txt
                    pass
            
        pass
    else:
        typeList = os.path.splitext(filepath)
        if typeList[1] == fileType:#check file type:.txt
            _pathList.append(filepath)
            pass    
        
        
        #print ('---',child.decode('cp936') )# .decode('gbk')是解决中文显示乱码问题
    return _pathList

#整理txt文件路径，统一放到一个列表当中，便于使用
def getTxtPath(pathList):
    txtPathList = []
    for index in pathList:
        if type(index) is list:
            for item in getTxtPath(index):
                typeList = os.path.splitext(item)
                if typeList[1] == '.txt':#check file type:.txt
                    txtPathList.append(item)
                
            
            pass  
        else:
            typeList = os.path.splitext(index)
            if typeList[1] == '.txt':#check file type:.txt
                txtPathList.append(index)
                pass
    return txtPathList
#判断是否包含汉字
zh_pattern = re.compile(u'[\u4e00-\u9fa5]+')
def contain_zh(word):
    '''
    判断传入字符串是否包含中文
    :param word: 待判断字符串
    :return: True:包含中文  False:不包含中文
    '''
    # word = word.decode()
    global zh_pattern
    match = zh_pattern.search(word)

    return match
#逐行读取文件内容
def readNormalLines(filePath):
    lines = list()
    #逐行读取文件内容
    for line in codecs.open(filePath,"r",encoding= u'GBK',errors='ignore'):   
        # line = line.encode("GB2312")
        if 'T09n0278' in line :
            if contain_zh(line):
                #逐行修改文字
                if "◎" in line:
                    line = line.replace('◎','')
                newLine = line
                #逐行将文字写入新字符串
                lines.append(newLine)
        else:
            pass
    return lines
def readFormatLines(filePath):
    lines = list()
    #逐行读取文件内容
    for line in open(filePath):   
        if 'T09n0278' in line :
            if contain_zh(line):
                #逐行修改文字
                if "◎" in line:
                    line = line.replace('◎','')
                newLine = line[18:]
                #逐行将文字写入新文件
                lines.append(newLine)
        else:
            pass
    return lines
#**************************************get_Sutra methods*********************
def get_QLSutra():
    print('hello')
    BASE_DIR = settings.BASE_DIR

    # create LQSutra
    # lqsutra = LQSutra(sid='LQ003100', name='大方廣佛華嚴經', total_reels=60)
    # lqsutra.save()

    lqsutra_sid = 'LQ003100'        #用来查找龙泉大藏经
    sutra_origin_sid = 'QL0087'     #大藏经原始sid
    sutra_father_sid = 'QL000870'   #大藏经sid格式化
    sutra_father_code = 'QL'        #大藏经版本code
    sutra_code = '00087'            #大藏经类目code
    sutra_name = '大方廣佛華嚴經'      #大藏经名字（一般为繁体字）
    sutra_libs_file = 'data/sutra_text/QL_SutraLibs.csv' #大藏经目录文件
    #LQSutra
    lqsutra = LQSutra.objects.get(sid=lqsutra_sid)

    try:
        huayan_sutra = Sutra.objects.get(sid= sutra_father_sid)
    except:
        # create Sutra
        tripitaka = Tripitaka.objects.get(code=sutra_father_code)
        huayan_sutra = Sutra(sid=sutra_father_sid, tripitaka=tripitaka, code=sutra_code, variant_code='0',
        name=sutra_name, lqsutra=lqsutra, total_reels=60)
        huayan_sutra.save()
        print(huayan_sutra)
            
        

    # 大藏经第 卷的文本
    # huayan_sutra_1 = Reel(sutra=huayan_sutra, reel_no=1, start_vol=27,
    # start_vol_page=1, end_vol=27, end_vol_page=23)
    #循环读取文件数据
    filename = os.path.join(BASE_DIR, sutra_libs_file)
    with open(filename,'r') as f:
        sutra_text = f.readlines()

    for x in range(len(sutra_text)):
        line_text = sutra_text[x]
        line_list = line_text.split('\t')
        
        if len(line_list) >= 7:
            if line_list[0] == sutra_origin_sid:#判断经目及其他条件
                sid_list =list(line_list[0])
                sid_list.insert(2,'0')
                sid =''.join(sid_list)+'0'
                sutra_name_text = line_list[1]
                reel_no = int(line_list[2])
                vol_no = int(line_list[3])
                start_page_no = int(line_list[4])
                end_page_no = int(line_list[5])
                # 大藏经第 卷的文本
                huayan_sutra_1 = Reel(sutra=huayan_sutra, reel_no=reel_no, start_vol=vol_no,
                start_vol_page=start_page_no, end_vol=vol_no, end_vol_page=end_page_no)
                huayan_sutra_1.text = get_reel_text(sid, reel_no, vol_no,
                start_page_no, end_page_no)
                huayan_sutra_1.save()
                print(line_list,line_list[3],huayan_sutra_1)
                
    pass


def get_YBSutra():
    print('hello')
    BASE_DIR = settings.BASE_DIR

    # create LQSutra
    # lqsutra = LQSutra(sid='LQ003100', name='大方廣佛華嚴經', total_reels=60)
    # lqsutra.save()

    lqsutra_sid = 'LQ003100'        #用来查找龙泉大藏经
    sutra_origin_sid = 'YLBZ0086'     #大藏经原始sid
    sutra_father_sid = 'YB000860'   #大藏经sid格式化
    sutra_father_code = 'YB'        #大藏经版本code
    sutra_code = '00086'            #大藏经类目code
    sutra_name = '大方廣佛華嚴經'      #大藏经名字（一般为繁体字）
    sutra_libs_file = 'data/sutra_text/YB_SutraLibs.csv' #大藏经目录文件
    #LQSutra
    lqsutra = LQSutra.objects.get(sid=lqsutra_sid)

    try:
        huayan_sutra = Sutra.objects.get(sid= sutra_father_sid)
    except:
        # create Sutra
        tripitaka = Tripitaka.objects.get(code=sutra_father_code)
        huayan_sutra = Sutra(sid=sutra_father_sid, tripitaka=tripitaka, code=sutra_code, variant_code='0',
        name=sutra_name, lqsutra=lqsutra, total_reels=60)
        huayan_sutra.save()
        print(huayan_sutra)
            
        

    # 大藏经第 卷的文本
    # huayan_sutra_1 = Reel(sutra=huayan_sutra, reel_no=1, start_vol=27,
    # start_vol_page=1, end_vol=27, end_vol_page=23)
    #循环读取文件数据
    filename = os.path.join(BASE_DIR, sutra_libs_file)
    with open(filename,'r') as f:
        sutra_text = f.readlines()
    for x in range(len(sutra_text)):
        line_text = sutra_text[x]
        line_list = line_text.split('\t')
            
        if len(line_list) >= 7:
            if line_list[1] == sutra_origin_sid and int(line_list[3]) >= 1:#判断经目及其他条件
                sid_list =list(line_list[1])[4:]
                # # sid_list.insert(2,'0')
                sid ='YB0' + ''.join(sid_list) + '0'
                sutra_name_text = line_list[2]
                reel_no = int(line_list[3])
                vol_no = int(line_list[4])
                start_page_no = int(line_list[5])
                end_page_no = int(line_list[6])
                # 大藏经第 卷的文本
                huayan_sutra_1 = Reel(sutra=huayan_sutra, reel_no=reel_no, start_vol=vol_no,
                start_vol_page=start_page_no, end_vol=vol_no, end_vol_page=end_page_no)
                huayan_sutra_1.text = get_reel_text(sid, reel_no, vol_no,
                start_page_no, end_page_no)
                huayan_sutra_1.save()
                print(line_list,line_list[3],huayan_sutra_1)
    pass
            

def get_CBETASutra():
    #确定藏经存储参数
    print('hello')
    BASE_DIR = settings.BASE_DIR

    lqsutra_sid = 'LQ003100'        #用来查找龙泉大藏经
    sutra_origin_sid = 'CB00278'     #大藏经原始sid
    sutra_father_sid = 'CB002780'   #大藏经sid格式化
    sutra_father_code = 'CB'        #大藏经版本code
    sutra_code = '00278'            #大藏经类目code
    sutra_name = '大方廣佛華嚴經'      #大藏经名字（一般为繁体字）
    sutra_libs_file = 'data/sutra_text/YB_SutraLibs.csv' #大藏经目录文件
    #LQSutra
    lqsutra = LQSutra.objects.get(sid=lqsutra_sid)

    try:
        huayan_sutra = Sutra.objects.get(sid= sutra_father_sid)
    except:
        # create Sutra
        tripitaka = Tripitaka.objects.get(code=sutra_father_code)
        huayan_sutra = Sutra(sid=sutra_father_sid, tripitaka=tripitaka, code=sutra_code, variant_code='0',
        name=sutra_name, lqsutra=lqsutra, total_reels=60)
        huayan_sutra.save()
        print(huayan_sutra)
    filePath = '/home/xian/cbeta导出'
    pathList = myEachFiles(filePath)
    txtPathList = getTxtPath(pathList)
    for path in txtPathList:
        #reel_no
        fileName = os.path.basename(path)
        fileType = os.path.splitext(path)
        
        newFileName = fileName.split(fileType[1])[0]
        reel_no = int(newFileName.split('_')[3])
        #lines
        lines = readNormalLines(path)
        #vlo_no
        line1 = lines[0]
        vol_no = int(line1[1:3])
        #star_page_no
        start_page_no = int(line1[10:14])
        #end_page_no
        line_end = lines[len(lines)-1]
        end_page_no = int(line_end[10:14])
        #sid
        sid = sutra_father_sid
        #sutra_name
        sutra_name_text = sutra_name
        
        # 大藏经第 卷的文本
        huayan_sutra_1 = Reel(sutra=huayan_sutra, reel_no=reel_no, start_vol=vol_no,
        start_vol_page=start_page_no, end_vol=vol_no, end_vol_page=end_page_no)
        sutra_text = 'p'
        first_page = start_page_no
        second_page = start_page_no
        for line in lines:
             if 'T09n0278' in line :
                if contain_zh(line):
                    #逐行修改文字
                    line = line.replace('◎','')
                    line = line.replace('　','')
                    line = line.replace(' ','')
                    line = line.replace('　　','')
                    line = line.replace('\r\n','')#window 文件每行默认换行符为：'\r\n'
                        
                    newLine = line[18:]
                    #逐行将文字写入新文件
                    second_page = int(line[10:14])
                    if second_page == first_page + 1:
                        newLine = 'p\n' + newLine 
                        first_page = second_page
                    sutra_text = sutra_text+ '\n' + newLine
        
        huayan_sutra_1.text = sutra_text
    
        #存储藏经text
        huayan_sutra_1.save()
        cut_url = '/%s/%s/v%03d/%sv%03dp%04d0.cut' %\
        (
            sid[:2],
            sid[2:],
            vol_no,
            sid,
            vol_no,
            start_page_no
        )
        print(cut_url,huayan_sutra_1)
        


    pass