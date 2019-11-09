import os
import re
import os
import sys
import time
import gzip
import struct
import argparse
import mimetypes
import subprocess
import shutil
import urllib.request
from xmlrpc.client import ServerProxy, Error
import pandas as pd
from tqdm import tqdm
import csv 

osd_username = "your opensubtitles username"
osd_password = 'the password'

class Agent():
    """ opensubtitle 的用户代理"""
    # __username=""
    # __password=""
    # __languae=""
    # __osd_server=""
    # __session="" 
    opt_selection_mode = 'default'
    opt_search_mode="filename"
    opt_language_separator = '_'

    def __init__(self,username,password,language="en"):
        self.__username=username
        self.__password=password
        self.__languae=language
        self.__osd_server = ServerProxy('http://api.opensubtitles.org/xml-rpc')
    def LogIn(self):
        try:
            # ==== Connection
            try:
                self.__session = self.__osd_server.LogIn(self.__username, self.__password, self.__languae, 'opensubtitles-download 4.0')
            except Exception:
                # Retry once, it could be a momentary overloaded server?
                time.sleep(3)
                try:
                    self.__session = self.__osd_server.LogIn(self.__username, self.__password, self.__languae, 'opensubtitles-download 4.0')
                except Exception:
                    print("error1")
                    #superPrint("error", "Connection error!", "Unable to reach opensubtitles.org servers!\n\nPlease check:\n- Your Internet connection status\n- www.opensubtitles.org availability\n- Your downloads limit (200 subtitles per 24h)\n\nThe subtitles search and download service is powered by opensubtitles.org. Be sure to donate if you appreciate the service provided!")
                    sys.exit(2)

            # Connection refused?
            if self.__session['status'] != '200 OK':
                print("error2")
                #superPrint("error", "Connection error!", "Opensubtitles.org servers refused the connection: " + session['status'] + ".\n\nPlease check:\n- Your Internet connection status\n- www.opensubtitles.org availability\n- Your downloads limit (200 subtitles per 24h)\n\nThe subtitles search and download service is powered by opensubtitles.org. Be sure to donate if you appreciate the service provided!")
                sys.exit(2)
            print("login success!")
        except:
            print("login error3")
            sys.exit(2)
    def LogOut(self):
        if self.__session and self.__session['token']:
            self.__osd_server.LogOut(self.__session['token'])
        print("logout success")
    
    def __search(self,title):
        """ 查询服务器，寻找潜在的字幕"""
        searchList=[]
        searchList.append({'sublanguageid':'eng', 'query':title})
        try:
            subtitlesList = self.__osd_server.SearchSubtitles(self.__session['token'], searchList)
            return subtitlesList
            # time.sleep(1)
        except Exception:
            # Retry once, we are already connected, the server maybe momentary overloaded
            time.sleep(3)
            try:
                subtitlesList = self.__osd_server.SearchSubtitles(self.__session['token'], searchList)
                return subtitlesList
            except Exception:
                print("Search error!")
                #superPrint("error", "Search error!", "Unable to reach opensubtitles.org servers!\n<b>Search error</b>")
                return -1


    def __selectionAuto(self,subtitlesList,year,imdb_ID):
        """ 从众多字幕中寻找合适的字幕 """
        """Automatic subtitles selection using filename match"""
        # 需要用到的属性
        # IDMovieImdb the most import
        # MovieKind
        # MovieYear
        # SubDownloadLink
        # SubFileName
        # SubFormat
        # 顺序选择即可。
        # if len(subtitlesList['data'])==1:
        #     return 0
        data=subtitlesList['data']
        for i in range(len(data)):
            this=data[i]
            if this["IDMovieImdb"]!=imdb_ID:
                continue
            # if this["SubFormat"]=="srt":
            #     return i

            if this["MovieKind"]!="movie":
                continue
            if this["SubFormat"]=="srt" and abs(year-int(this["MovieYear"]))<2:
                return i

        return -1
    
    def __down(self,subtitlesSelected,subtitlesList,subPath):
        # 此处变量与下载有直接关系
        subLangId = self.opt_language_separator  + subtitlesList['data'][subtitlesSelected]['ISO639']
        subLangName = subtitlesList['data'][subtitlesSelected]['LanguageName']
        subURL = subtitlesList['data'][subtitlesSelected]['SubDownloadLink']
        # subPath 为存储路径
        # subPath="1.txt"
        #subPath = videoPath.rsplit('.', 1)[0] + '.' + subtitlesList['data'][subIndex]['SubFormat']
        if sys.version_info >= (3, 0):
            tmpFile1, headers = urllib.request.urlretrieve(subURL)
            tmpFile2 = gzip.GzipFile(tmpFile1)
            byteswritten = open(subPath, 'wb').write(tmpFile2.read())
            if byteswritten > 0:
                process_subtitlesDownload = 0
            else:
                process_subtitlesDownload = 1
        else: # python 2
            tmpFile1, headers = urllib.urlretrieve(subURL)
            tmpFile2 = gzip.GzipFile(tmpFile1)
            open(subPath, 'wb').write(tmpFile2.read())
            process_subtitlesDownload = 0

        # If an error occurs, say so
        if process_subtitlesDownload != 0:
            print("Subtitling error!")
            #superPrint("error", "Subtitling error!", "An error occurred while downloading or writing <b>" + subtitlesList['data'][subIndex]['LanguageName'] + "</b> subtitles for <b>" + videoTitle + "</b>.")
            self.__osd_server.LogOut(self.__session['token'])
            sys.exit(2)

    def __result(self,subtitlesList,year,imdb_ID,subPath):
        """ 主体函数 """
        # Parse the results of the XML-RPC query
        if ('data' in subtitlesList) and (len(subtitlesList['data']) > 0):
            # print("find it")
            #找到数据
            # Mark search as successful
            subtitlesSelected = ''

            # If there is only one subtitles (matched by file hash), auto-select it (except in CLI mode)
            if (len(subtitlesList['data']) == 1) and (subtitlesList['data'][0]['MatchedBy'] == 'moviehash'):
                if opt_selection_mode != 'manual':
                    # subtitlesSelected = subtitlesList['data'][0]['SubFileName']
                    subtitlesSelected=0

            # Get video title
            videoTitle = subtitlesList['data'][0]['MovieName']

            # If there is more than one subtitles and opt_selection_mode != 'auto',
            # then let the user decide which one will be downloaded
            if subtitlesSelected == '':
                subtitlesSelected = self.__selectionAuto(subtitlesList,year,imdb_ID)
                if subtitlesSelected==-1:
                    return -1

            # If a subtitles has been selected at this point, download it!
            if subtitlesSelected==-1:
                # 记录未下载的电影名与ID
                #print("find error!")
                return -1
            else:
                # print("ready to down")
                self.__down(subtitlesSelected,subtitlesList,subPath)
                return 0
        else:
            # print("not find it!")
            return -1

    
    def work(self,title,year,imdb_ID,path):
        """ 查找电影字幕并下载到指定路径中"""
        subtitlesList=self.__search(title)
        time.sleep(2)
        if subtitlesList==-1:
            return -1
        return self.__result(subtitlesList,year,imdb_ID,path)
        pass
    def work_by_imda(self,year,imdb_ID):
        list=self.__search(imdb_ID)
        if list==-1:
            return -1
        return self.__selectionAuto(list,year,imdb_ID)
        pass

    pass


def main():
        # 尚需添加失败记录
    a=Agent(osd_username,osd_password)
    print("try login")
    a.LogIn()
    #flag=process(a,ids[now],t[now])
    # City Hall,100	115907
    # a.work("City Hall",1996,"115907","test.txt")
    a.LogOut()
        #time.sleep(50)
    
    

if __name__=="__main__":

    #os.chdir("testdown")
    main()

