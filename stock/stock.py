# -*- coding:utf-8 -*-

#-*- coding:utf-8 -*-
import requests
from bs4 import BeautifulSoup
import traceback
import re
import xlwt
import time
import MySQLdb

def getHTMLText(url, code="utf-8"):
    try:
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
        headers = {'User-Agent': user_agent}
        r = requests.get(url,headers = headers,timeout = 30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text
    except: 
        return ""
#获取股票列表
def getStockList(lst, stockURL):
    html = getHTMLText(stockURL,"GB2312")
    soup = BeautifulSoup(html, 'html.parser') 
    a = soup.find_all('a')
    # print a
    for i in a:
        try:
            href = i.attrs['href']
            # lst.append(re.findall(r"sh\d{6}",href)[0])
            lst.append(re.findall(r"[s][zh][06]\d{5}", href)[0])
        except:
            continue

#根据股票的代号查找股票的交易信息，并将结果存储到相关文件
def getStockInfo(lst, stockURL):
    # 添加当天日期(交易日)
    date = time.strftime("%Y-%m-%d", time.localtime())
    #创建EXCEL文件
    book=xlwt.Workbook(encoding='utf-8')
    sheet1=book.add_sheet('sheet1',cell_overwrite_ok=True)
    heads=['交易日','股票代码','股票名称','最高','最低','今开','昨收','成交额','成交量','流通市值','每股收益','每股净资产','市净率','总股本','流通股本']
    num=0
    for head in heads:
        sheet1.write(0,num,head)
        num=num+1
    book.save('gupiao'+date+'.xls')
    count = 1
    length=len(lst)
    #每次将一个查询的数据输出到EXCEl表中
    for stock in lst:
        # print stock[2:]
        url = stockURL + stock + ".html"
        html = getHTMLText(url)
        try:
            if html=="":
                continue
            infoDict = {}
            soup = BeautifulSoup(html, 'html.parser')
            stockInfo = soup.find('div',attrs={'class':'stock-bets'})
            #查找股票名称
            if stockInfo:
                name = stockInfo.find_all(attrs={'class':'bets-name'})[0]
                # print name.text
                # print name.text.split()
                infoDict.update({'股票名称': name.text.split()[0]})
                #寻找所有键和值（最高、最低）
                keyList = stockInfo.find_all('dt')
                valueList = stockInfo.find_all('dd')
                # print keyList[1].text
                for i in range(len(keyList)):
                    key = keyList[i].text.encode('utf-8')
                    val = valueList[i].text
                    infoDict[key] = val
                
                sheet1.write(count,0,date)
                sheet1.write(count,1,stock[2:])

                j=2
                # for i in infoDict:
                #     print i
                for i in heads:
                    if i in infoDict:
                        # print i
                        sheet1.write(count,j,infoDict[i])
                        j=j+1
                    else:
                        pass
                book.save('gupiao'+date+'.xls')
                # print("\r当前进度: {:.2f}%".format(count*100/length), end="")
                count=count+1
        except:
            # print("\r当前进度: {:.2f}%".format(count * 100 / length), end="")
            count = count + 1
            continue
if __name__=='__main__':
    #找寻将数据静态写在html页面的网页
    stock_list_url = 'http://quote.eastmoney.com/stocklist.html'
    stock_info_url = 'https://gupiao.baidu.com/stock/'
    slist=[]
    getStockList(slist, stock_list_url)
    getStockInfo(slist, stock_info_url)

#建立本地数据库连接(需要先开启数据库服务)
db = MySQLdb.connect(host='127.0.0.1', port=3306, user='root', passwd='123456', db='stock_data' ,charset='utf8')
cursor = db.cursor()
#创建数据库stockDataBase
# sqlSentence1 = "create database stockDataBase"
# cursor.execute(sqlSentence1) 
#选择使用当前数据库
sqlSentence2 = "select * from stock;"
cursor.execute(sqlSentence2)

data = pd.read_excel('gupiao'+date+'.xls', encoding="utf-8")
#创建数据表，如果数据表已经存在，会跳过继续执行下面的步骤print('创建数据表stock_%s'% fileName[0:6])
# sqlSentence3 = "create table stock_%s" % date + "(交易日 date, 股票代码 VARCHAR(100),  股票名称 VARCHAR(100),\
#                    最高 float, 最低 float, 今开 float, 昨收 float, 成交额 VARCHAR(100), 成交量 VARCHAR(100), 流通市值 VARCHAR(100),\
#                    每股收益 float, 每股净资产 float, 市净率 float, 总股本 VARCHAR(100), 流通股本 VARCHAR(100))"

# cursor.execute(sqlSentence3)
# 交易日, 股票代码, 股票名称, 最高, 最低, 今开, 昨收, 成交额, 成交量, 流通市值, 每股收益, 每股净资产, 市净率, 总股本, 流通股本

#迭代读取表中每行数据，依次存储（整表存储还没尝试过）
# print('正在存储stock_%s'% fileName[0:6])
length = len(data)
for i in range(0, length):
    record = tuple(data.loc[i])
    #插入数据语句
    try:
        sqlSentence4 = "insert into stock (交易日, 股票代码, 股票名称, 最高, 最低, 今开, 昨收, 成交额, 成交量, 流通市值, \
        每股收益, 每股净资产, 市净率, 总股本, 流通股本) values ('%s',%s,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % record
        #获取的表中数据很乱，包含缺失值、Nnone、none等，插入数据库需要处理成空值
        sqlSentence4 = sqlSentence4.replace('nan','null').replace('None','null').replace('none','null') 
        cursor.execute(sqlSentence4)
    except:
        #如果以上插入过程出错，跳过这条数据记录，继续往下进行
        break

#关闭游标，提交，关闭数据库连接
cursor.close()
db.commit()
db.close()


# # -*- coding: utf-8 -*-
# # @Author : Torre Yang Edit with Python3.6
# # @Email  : klyweiwei@163.com
# # @Time   : 2018/6/28 10:50
# # 定时 爬取每日股票行情数据;
# # 股票数据内容：
# import requests
# import MySQLdb
# import os
# import re
# import json
# # from requests import connect_dataBase
# import time

# db1 = MySQLdb.connect(
#             host="localhost",
#             db="stock_data",
#             user="root",
#             passwd="123456",
#             port=3306,
#             charset='utf8'
#         )

# # 第一步, 通过东方财富网  获取 上海/深圳 所有股票的 股票代码, 存储到list中
# url = 'http://quote.eastmoney.com/stocklist.html#'
# soup = requests.get(url)
# uls = soup.select('div#quotesearch li')
# # 正则表达式获取所有的股票代码
# re1 = re.compile(r'href="http://quote.eastmoney.com/(.+?).html"')
# stockCodes = re1.findall(str(uls))
# # print(stockCodes)

# # 第二步, 将股票代码加入到 股票搜索 的网址中
# stockValues = []
# for stockCode in stockCodes:
#     # url = 'https://gupiao.baidu.com/stock/'+stockCode+'.html'
#     url = 'https://gupiao.baidu.com/api/rails/stockbasicbatch?from=pc&os_ver=1&cuid=xxx&vv=100&format=json&stock_code='+stockCode+''
#     # print(url)
#     # url = 'https://gupiao.baidu.com/api/rails/stockbasicbatch?from=pc&os_ver=1&cuid=xxx&vv=100&format=json&stock_code=sh201003'
#     response = requests.get(url)
#     response.raise_for_status()
#     res = response.content
#     try:
#         JsonDatas = json.loads(res, encoding='utf-8')
#     except:
#         print('解析为空')
#     datas = JsonDatas['data']
   
#     for data in datas:
#         # 添加当天日期(交易日)
#         date = time.strftime("%Y-%m-%d", time.localtime())
#         stockCode = data['stockCode']
#         stockName = data['stockName']
#         close = data['close']
#         high = data['high']
#         low = data['low']
#         amplitudeRatio = data['amplitudeRatio']
#         turnoverRatio = data['turnoverRatio']
#         preClose = data['preClose']
#         open = data['open']
#         sql = 'insert into stockmarket(date,stockCode,stockName,close,high,low,amplitudeRatio,turnoverRatio,preClose,open)values("'+str(date)+'","'+str(stockCode)+'","'+str(stockName)+'","'+str(close)+'","'+str(high)+'","'+str(low)+'","'+str(amplitudeRatio)+'","'+str(turnoverRatio)+'","'+str(preClose)+'","'+str(open)+'")'
#         print(sql)
#         if 'None' in sql:
#             print('jump this data')
#         else:
#             # try:
#             #     connectDB.get_fetch(conn, cur, sql)
#             # except:
#                 print('数据异常, 跳过')

# print('采集数据完毕')
 


# import urllib
# import re
# import pandas as pd
# import MySQLdb
# import os
# import requests

# # #爬虫抓取网页函数
# # def getHtml(url):
# #     html = urllib.urlopen(url).read()
# #     html = html.decode('gbk')
# #     return html

# #抓取网页股票代码函数
# def getStackCode(html):
#     s = r'<li><a target="_blank" href="http://quote.eastmoney.com/\S\S(.*?).html">'
#     pat = re.compile(s)
#     code = pat.findall(html)
#     return code
    
# #########################开始干活############################
# Url = 'http://quote.eastmoney.com/stocklist.html'#东方财富网股票数据连接地址
# filepath = '/Users/keji/Downloads/data/'#定义数据文件保存路径
# #实施抓取
# code = getStackCode(requests.get(Url)) 
# #获取所有股票代码（以6开头的，应该是沪市数据）集合
# CodeList = []
# for item in code:
#     if item[0]=='6':
#         CodeList.append(item)
# #抓取数据并保存到本地csv文件
# for code in CodeList:
#     print('正在获取股票%s数据'%code)
#     url = 'http://quotes.money.163.com/service/chddata.html?code=0'+code+\
#         '&end=20161231&fields=TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER;TCAP;MCAP'
#     urllib.urlretrieve(url, filepath+code+'.csv')


# ##########################将股票数据存入数据库###########################

# #数据库名称和密码
# name = 'stock_data'
# password = '123456'  #替换为自己的账户名和密码
# #建立本地数据库连接(需要先开启数据库服务)
# db = MySQLdb.connect(host='127.0.0.1', port=3306, user='root', passwd='123456', db='stock_data' ,charset='utf8')
# cursor = db.cursor()
# #创建数据库stockDataBase
# sqlSentence1 = "create database stockDataBase"
# cursor.execute(sqlSentence1) #选择使用当前数据库
# sqlSentence2 = "use stockDataBase;"
# cursor.execute(sqlSentence2)

# #获取本地文件列表
# fileList = os.listdir(filepath)
# #依次对每个数据文件进行存储
# for fileName in fileList:
#     data = pd.read_csv(filepath+fileName, encoding="gbk")
#    #创建数据表，如果数据表已经存在，会跳过继续执行下面的步骤print('创建数据表stock_%s'% fileName[0:6])
#     sqlSentence3 = "create table stock_%s" % fileName[0:6] + "(日期 date, 股票代码 VARCHAR(10),     名称 VARCHAR(10),\
#                        收盘价 float,    最高价    float, 最低价 float, 开盘价 float, 前收盘 float, 涨跌额    float, \
#                        涨跌幅 float, 换手率 float, 成交量 bigint, 成交金额 bigint, 总市值 bigint, 流通市值 bigint)"
#     cursor.execute(sqlSentence3)


#     #迭代读取表中每行数据，依次存储（整表存储还没尝试过）
#     print('正在存储stock_%s'% fileName[0:6])
#     length = len(data)
#     for i in range(0, length):
#         record = tuple(data.loc[i])
#         #插入数据语句
#         try:
#             sqlSentence4 = "insert into stock_%s" % fileName[0:6] + "(日期, 股票代码, 名称, 收盘价, 最高价, 最低价, 开盘价, 前收盘, 涨跌额, 涨跌幅, 换手率, \
#             成交量, 成交金额, 总市值, 流通市值) values ('%s',%s','%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % record
#             #获取的表中数据很乱，包含缺失值、Nnone、none等，插入数据库需要处理成空值
#             sqlSentence4 = sqlSentence4.replace('nan','null').replace('None','null').replace('none','null') 
#             cursor.execute(sqlSentence4)
#         except:
#             #如果以上插入过程出错，跳过这条数据记录，继续往下进行
#             break

# #关闭游标，提交，关闭数据库连接
# cursor.close()
# db.commit()
# db.close()


# ###########################查询刚才操作的成果##################################

# #重新建立数据库连接
# db = pymysql.connect('localhost', name, password, 'stockDataBase')
# cursor = db.cursor()
# #查询数据库并打印内容
# cursor.execute('select * from stock_600000')
# results = cursor.fetchall()
# for row in results:
#     print(row)
# #关闭
# cursor.close()
# db.commit()
# db.close()