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
import json
import xlrd
class Command(BaseCommand):
    def handle(self, *args, **options):
        # path = r'/home/xian/桌面/sutra/jingmu'
        # pathList = myEachFiles(path)
        # filePathList = getFilePath(pathList)
        # for filePath in filePathList:
        #     if os.path.isfile(filePath):
        #         Store_Normal_Sutra_FromJingMuExcel(filePath)
        #     else:
        #         print('not file:',filePath,'-----')
        #         pass
        
        path = r'/home/xian/桌面/sutra/xiangmu'
        pathList = myEachFiles(path)
        filePathList = getFilePath(pathList)
        for filePath in filePathList:
            if os.path.isfile(filePath):
                Store_Normal_Sutra_FromXiangMuExcel(filePath)
            else:
                print('not file:',filePath,'-----')
                pass
                

#遍历文件夹，获取所有txt文件路径
def myEachFiles(path):
    _pathList=[]
    filepath = path
    
    fileTypes = ['.xlsx','.xls']
    
    if os.path.isdir(filepath):
        pathDir =  os.listdir(filepath)
        for allDir in pathDir:
            child = os.path.join('%s/%s' % (filepath, allDir))
            if os.path.isdir(child):
                _pathList.append(myEachFiles(child))
                pass
            else:
                typeList = os.path.splitext(child)
                if typeList[1] in fileTypes:#check file type:.txt
                    _pathList.append(child)
                    #print('child:','%s' % child.encode('utf-8','ignore'))
                    pass
                else:#not .txt
                    pass
            
        pass
    else:
        typeList = os.path.splitext(filepath)
        if typeList[1] in fileTypes:#check file type:.txt
            _pathList.append(filepath)
            pass    
        
        
        #print ('---',child.decode('cp936') )# .decode('gbk')是解决中文显示乱码问题
    return _pathList

#整理txt文件路径，统一放到一个列表当中，便于使用
def getFilePath(pathList):
    txtPathList = []
    fileTypes = ['.xlsx','.xls']
    for index in pathList:
        if type(index) is list:
            for item in getFilePath(index):
                typeList = os.path.splitext(item)
                if typeList[1] in fileTypes:#check file type:.txt
                    txtPathList.append(item)
                
            
            pass  
        else:
            typeList = os.path.splitext(index)
            if typeList[1] in fileTypes:#check file type:.txt
                txtPathList.append(index)
                pass
    return txtPathList

def readExcelLines(filePath):
    # load data
    data = xlrd.open_workbook(filePath)
    table = data.sheets()[0]
    nrows = table.nrows
    ncols = table.ncols
    
    #解析属性
    properties = table.row_values(0)
    resultDatas = list()
    for i in range(nrows):
        if i > 0:
            values = table.row_values(i)
            valueDic = dict()
            for j in range(len(properties)):
                property = properties[j]
                valueDic[property] = values[j]
            resultDatas.append(valueDic)

    return json.dumps(resultDatas)
def isNumber(str_number):
    str_number = str_number.replace('\'','')
    if str_number.isdigit():
        return True
    value = re.compile(r'^[-+]?[0-9]+\.[0-9]+$')
    result = value.match(str_number)
    if result:
        return True
    else:
        return False
def Store_Normal_Sutra_FromJingMuExcel(filePath):
    jsonData = readExcelLines(filePath)
    datas = json.loads(jsonData)
    for i in range(len(datas)):
        dataDic = datas[i]
        sid = None  #龙泉编码
        sutra_father_sid = None #实体藏编码
        name = None #实体经名
        reel_no = -1 #卷序号
        total_reels = -1 #实际卷数
        start_vol = -1 #起始册码
        end_vol = -1 #终止册码
        
        code = None
        #龙泉编码
        lqCodes = ['龍泉編碼','龙泉编码']
        for lqCode in lqCodes:
            if lqCode in dataDic:
                sid = dataDic[lqCode]
                strSid = str(sid)
                sid = strSid.replace('-','')
                if len(str(sid)) > 2:
                    code = sid[:2]#此处有问题，当sid全部是数字时，无法进行辨别
                    if code != 'LQ':
                        print(dataDic,code)
                    if len(sid) < 7:
                        for i in range(8-len(sid)-1):
                            sid = sid[0:2] + '0' + sid[2:]
                    if len(sid) == 7:
                        sid = sid + '0'
                    if len(sid) == 8:
                        pass
                    else:
                        print('sid error!  sid=',sid)
                        # continue    #进入下一个循环
                else:
                    print('no sid',dataDic)
                    # continue    #进入下一个循环
                break
        if len(sid) > 8 or len(sid)<=2:
            # continue    #进入下一个循环
            pass
        #实体藏编码
        sutraCodeNames = ['高麗編碼','高麗初刻編碼','洪武南藏編碼','開寶遺珍編碼','契丹編碼','磧砂藏編碼'
                        ,'乾隆藏編碼','宋藏遺珍編碼','永樂北藏編碼','趙城編碼','中華藏編碼']
        for sutraCodeName in sutraCodeNames:
            if sutraCodeName in dataDic:
                sutra_father_sid = dataDic[sutraCodeName]
                strSid = str(sutra_father_sid)
                sutra_father_sid = strSid.replace('-','')
                sutraCode = sutra_father_sid[:2]#此处有问题，当sid全部是数字时，无法进行辨别
                sutraCodes = ['SZ','ZH','CB','DZ','WX','WZ','FS','GL',
                'LC','QL','JX','YB','YN','HN','YG','PN','QS','SX',
                'ZF','YJ','PL','CN','ZC','QD','KB']
                if sutraCode in sutraCodes:
                    pass
                else:
                    print('code error! code =',sutraCode)
                    continue    #进入下一个循环
                if len(str(sutra_father_sid)) > 2:
                    if len(sutra_father_sid) < 7:
                        for i in range(8-len(sutra_father_sid)-1):
                            sutra_father_sid = sutra_father_sid[0:2] + '0' + sutra_father_sid[2:]
                    if len(sutra_father_sid) == 7:
                        sutra_father_sid = sutra_father_sid + '0'
                    if len(sutra_father_sid) == 8:
                        pass
                    else:
                        print('sid error!  sutra_father_sid=',sutra_father_sid)
                        continue    #进入下一个循环
                break
        #藏经名
        sutraNames = ['實體經名','实体经名']
        for sutraName in sutraNames:
            if sutraName in dataDic:
                name = dataDic[sutraName]
                break
        #卷序号
        reelNames = ['卷序號']
        for reelName in reelNames:
            if reelName in dataDic:
                reel_no = dataDic[reelName]
                if isNumber(str(reel_no)):
                    pass
                else:
                    reel_no = -1
                break
        #实际卷数
        totalReelNames = ['實際卷數','实际卷数']
        for totalReelName in totalReelNames:
            if totalReelName in dataDic:
                total_reels = dataDic[totalReelName]
                if isNumber(str(total_reels)):
                    pass
                else:
                    total_reels = -1
                break
        #起始册码
        startVolNames = ['起始冊碼']
        for startVolName in startVolNames:
            if startVolName in dataDic:
                start_vol = dataDic[startVolName]
                if isNumber(str(start_vol)):
                    pass
                else:
                    start_vol = -1
                break
        #终止册码
        endVolNames = ['終止冊碼']
        for endVolName in endVolNames:
            if endVolName in dataDic:
                end_vol = dataDic[endVolName]
                if isNumber(str(end_vol)):
                    pass
                else:
                    end_vol = -1
                break
        
        #----------------------------- create LQSutra--------------------------------
        lqsutra = None
        try:
            lqsutra = LQSutra.objects.get(sid=sid)
        except:
            try:
                LQSutra.objects.create(sid=sid, name=name, total_reels=total_reels)
            except:
                # print(dataDic)
                # print('creat lqsutra not save:','sid=',sid,'name=',name,'total_reels=',total_reels,'---')
                # continue # 进入下一循环
                pass
        #------------------------------ create Sutra-----------------------------------
        # 初始化
       
        lqsutra = LQSutra.objects.get(sid=sid)
        sutra_father_code = str(sutra_father_sid)[0:2]        #大藏经版本code
        sutra_code = str(sutra_father_sid)[3:]            #大藏经类目code
        try:
            variant_code = str(sutra_father_sid)[-1]
        except:
            variant_code = 0
            print('variant_code = str(sutra_father_sid)[-1] error',sutra_father_sid)
        #创建sutra
        
        try:
            normal_sutra = Sutra.objects.get(sid= sutra_father_sid)
        except: 
            # create Sutra
            
            try:
                tripitaka = Tripitaka.objects.get(code=sutra_father_code)
            except :
                print('Tripitaka matching query does not exist.tripitaka code =',sutra_father_code,dataDic)
                continue #跳出，进入下一循环
            Sutra.objects.create(sid=sutra_father_sid, tripitaka=tripitaka, code=sutra_code, variant_code=variant_code,
            name=name, lqsutra=lqsutra, total_reels=total_reels)
            
        #--------------------------------end---------------------------------------
    pass
def Store_Normal_Sutra_FromXiangMuExcel(filePath):
    jsonData = readExcelLines(filePath)
    datas = json.loads(jsonData)
    for i in range(len(datas)):
        dataDic = datas[i]
        sid = None  #龙泉编码
        sutra_father_sid = None #实体藏编码
        name = None #实体经名
        reel_no = -1 #卷序号
        start_vol = -1 #起始册码
        end_vol = -1 #终止册码
        start_vol_page = -1 #起始页码
        end_vol_page = -1 #终止页码
        code = None
        #龙泉编码
        lqCodes = ['龍泉編碼','龙泉编码']
        for lqCode in lqCodes:
            if lqCode in dataDic:
                sid = dataDic[lqCode]
                strSid = str(sid)
                sid = strSid.replace('-','')
                if len(str(sid)) > 2:
                    code = sid[:2]#此处有问题，当sid全部是数字时，无法进行辨别
                    if code != 'LQ':
                        print(dataDic,code)
                    if len(sid) < 7:
                        for i in range(8-len(sid)-1):
                            sid = sid[0:2] + '0' + sid[2:]
                    if len(sid) == 7:
                        sid = sid + '0'
                    if len(sid) == 8:
                        pass
                    else:
                        print('sid error!  sid=',sid)
                else:
                    # print('no sid',dataDic)
                    pass
                break
                    
        if len(sid) > 8 :
            print('error:len(sid)>8.',dataDic)
            continue    #进入下一个循环
        #实体藏编码
        sutraCodeNames = ['高麗編碼','高麗初刻編碼','洪武南藏編碼','開寶遺珍編碼','契丹編碼','磧砂藏編碼'
                        ,'乾隆藏編碼','宋藏遺珍編碼','永樂北藏編碼','趙城編碼','中華藏編碼']
        for sutraCodeName in sutraCodeNames:
            if sutraCodeName in dataDic:
                sutra_father_sid = dataDic[sutraCodeName]
                strSid = str(sutra_father_sid)
                sutra_father_sid = strSid.replace('-','')
                sutraCode = sutra_father_sid[:2]#此处有问题，当sid全部是数字时，无法进行辨别
                sutraCodes = ['SZ','ZH','CB','DZ','WX','WZ','FS','GL',
                'LC','QL','JX','YB','YN','HN','YG','PN','QS','SX',
                'ZF','YJ','PL','CN','ZC','QD','KB']
                if sutraCode in sutraCodes:
                    pass
                else:
                    print('code error! code =',sutraCode)
                    continue    #进入下一个循环
                if len(str(sutra_father_sid)) > 2:
                    if len(sutra_father_sid) < 7:
                        for i in range(8-len(sutra_father_sid)-1):
                            sutra_father_sid = sutra_father_sid[0:2] + '0' + sutra_father_sid[2:]
                    if len(sutra_father_sid) == 7:
                        sutra_father_sid = sutra_father_sid + '0'
                    if len(sutra_father_sid) == 8:
                        pass
                    else:
                        print('sid error!  sutra_father_sid=',sutra_father_sid)
                        continue    #进入下一个循环
                break
                
        #藏经名
        sutraNames = ['實體經名','实体经名']
        for sutraName in sutraNames:
            if sutraName in dataDic:
                name = dataDic[sutraName]
                break
        #卷序号
        reelNames = ['卷序號']
        for reelName in reelNames:
            if reelName in dataDic:
                reel_no = dataDic[reelName]
                if isNumber(str(reel_no)):
                    pass
                else:
                    reel_no = -1
                break
        
        #起始册码
        startVolNames = ['起始冊碼']
        for startVolName in startVolNames:
            if startVolName in dataDic:
                start_vol = dataDic[startVolName]
                if isNumber(str(start_vol)):
                    pass
                else:
                    start_vol = -1
                break
        #终止册码
        endVolNames = ['終止冊碼']
        for endVolName in endVolNames:
            if endVolName in dataDic:
                end_vol = dataDic[endVolName]
                if isNumber(str(end_vol)):
                    pass
                else:
                    end_vol = -1
                break
        #起始页码
        startVolPageNames = ['起始頁碼']
        for startVolPageName in startVolPageNames:
            if startVolPageName in dataDic:
                start_vol_page = dataDic[startVolPageName]
                if isNumber(str(start_vol_page)): 
                    pass
                else:
                    start_vol_page = -1
                break
        #终止页码
        endVolPageNames = ['終止頁碼']
        for endVolPageName in endVolPageNames:
            if endVolPageName in dataDic:
                end_vol_page = dataDic[endVolPageName]
                if isNumber(str(end_vol_page)):
                    pass
                else:
                    end_vol_page = -1
                break
        
        
        #--------------------------create reel-----------------------------------------
        #get LQSutra
        lqsutra_sid = sid
        sutra_name = name
        lqsutra = None
        try:
            lqsutra = LQSutra.objects.get(sid=lqsutra_sid)
        except:
            try:
                lqsutra = normal_sutra.lqsutra
            except :
                print('lqsutra does not exist.',dataDic)
                # continue #进入下一个循环
                LQSutra.objects.create(sid=lqsutra_sid, name=sutra_name, total_reels=-1)
            pass
        #get normal_sutra
        normal_sutra = None
        try:
            normal_sutra = Sutra.objects.get(sid= sutra_father_sid)
        except: 
            # create Sutra
            print('normal_sutra does not exist!',sutra_father_sid,dataDic)
            # continue #进入下一个循环
            # create Sutra
            sutra_father_code = str(sutra_father_sid)[0:2]        #大藏经版本code
            sutra_code = str(sutra_father_sid)[3:]            #大藏经类目code
            tripitaka = None
            try:
                variant_code = str(sutra_father_sid)[-1]
            except:
                variant_code = 0
                print('variant_code = str(sutra_father_sid)[-1] error',sutra_father_sid)
            try:
                tripitaka = Tripitaka.objects.get(code=sutra_father_code)
            except :
                print('Tripitaka matching query does not exist.tripitaka code =',sutra_father_code,dataDic)
                # continue #跳出，进入下一循环
                pass
                try:
                    Sutra.objects.create(sid=sutra_father_sid, tripitaka=tripitaka, code=sutra_code, variant_code=variant_code,
                        name=name, lqsutra=lqsutra, total_reels=-1)
                except :
                    print('create normal sutra error!')
                    continue #进入下一循环
                    pass
            
            pass
        
        
        #创建reel
        #准备数据
        sid =sutra_father_sid
        sutra_name_text = name
        reel_no = int(reel_no)
        vol_no = int(start_vol)
        start_page_no = int(start_vol_page)
        end_page_no = int(end_vol_page)
        try:
            # 创建reel
            Reel.objects.create(sutra=normal_sutra, reel_no=reel_no, start_vol=vol_no,
                start_vol_page=start_page_no, end_vol=vol_no, end_vol_page=end_page_no)
        except:
            try:
                # 更新reel
                Reel.objects.filter(sutra=normal_sutra,reel_no=reel_no).update(start_vol=vol_no,
                    start_vol_page=start_page_no, end_vol=vol_no, end_vol_page=end_page_no)
                # print('ss',normal_sutra,reel_no,vol_no,start_page_no,end_vol_page,end_vol)
            except:
                print('try store reel exception.',normal_sutra,dataDic)
        
            pass
        
    pass

