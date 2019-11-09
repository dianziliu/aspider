import os
import pandas as pd
from opensubtitles import Agent
from basics import *
from sub import subtitle_exist_in_d as exist
from plan import i,n,t,ids
from plan import get_imdb_ID 
import time

osd_username = 'xxxx'
osd_password = 'xxxx'

def process(agent,id,title):
    # 若返回-1，则表示失败
    # 电影名
    # 中断继续，
    # if id<99044:
    #     if add(id)==-1:
    #         return -1
    #     else:
    #         return 0
    imdb_ID=get_imdb_ID(id)
    if imdb_ID ==-1:
        return -1
    name=title[:-6]
    # 发行时间
    try:
        year=int(title[-5:-1])
    except:
        return -1
    # 存储路径
    path="subtitles\\"+str(id)+".txt"
    return agent.work(name,year,imdb_ID,path)

def add(id): 
    path="subtitles\\"+str(id)+".txt"
    path1="subtitles10M\\subtitles\\"+str(id)+".txt"
    if os.path.exists(path):
        return 0
    elif os.path.exists(path1):
        return 0
    else:
        return -1

    

def main():
    
    # record_path="lost\\plan\\record.csv"
    # record_buf=[] 
    lost_path="lost\\plan\\lost.csv"
    lost_buf=[]
    dayly=1000
    a=Agent(osd_username,osd_password)
    # for i in tqdm(range(1,int(len(t)/100)),ncols=50):
    print("try login")
    a.LogIn()
    for j in tqdm(range(dayly),ncols=50):
        now=i*dayly+j
        if now>n:
            break
        try:
            #flag=0
            #print(ids[now],t[now])
            
            flag=process(a,ids[now],t[now])
        except:
            flag=-1
        if flag==-1:
            word=[]
            word.append(ids[now])
            word.append(t[now])
            lost_buf.append(word)


    a.LogOut()
        #time.sleep(50)
    wt_csv(lost_path,lost_buf,mode="a")
    # wt_csv(record_buf,record_buf,mode="a")
    

if __name__=="__main__":

    #os.chdir("testdown")
    main()
