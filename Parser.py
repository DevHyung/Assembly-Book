"""
    File name: Parser.py
    Author: DevHyung
    Date last modified: 2017/12/09
    Python Version: 3.6
    Description : Parsing modules descript this file
"""
import AssemblyMember
import requests
from bs4 import BeautifulSoup,NavigableString
import time
import pymysql.cursors
from datetime import datetime
import dateutil.relativedelta
# 국회의원 목록
#___DB부분 변수
ip = 'localhost'
id = 'root'
pw = 'autoset'
name = 'projectd'
chs ='utf8'
#---DB연결
conn = pymysql.connect(ip,id,pw,name,charset="utf8")
curs = conn.cursor()
assembly_member_list = []
deptcdList = AssemblyMember.deptcd_list
nameList = AssemblyMember.name_list
CURRENT_DATETIME = datetime.today()
BEFORE_ONE_MONTH = CURRENT_DATETIME - dateutil.relativedelta.relativedelta(months=1)
#
rankCntList = [0 for _ in range(0,len(nameList))]
sql_article = """insert into article(dept_cd,name,count)
                   values (%s, %s, %s)"""
sql_articleinfo = """insert into articleinfo(dept_cd,title,link,newscompany,newsdate)
                   values (%s, %s, %s,%s, %s)"""
sql_card = """insert into cardnews(title,link,tag,newsdate)
                   values (%s, %s, %s,%s)"""
def get_string(parent):
    l = []
    for tag in parent:
        if isinstance(tag, NavigableString):
            l.append(tag.string)
        else:
            l.extend(get_string(tag))
    return l
class Parsing:
    def __init__(self, lastParsingData, status):
        self.lastParsingData = lastParsingData
        self.status = status
        self.logList = []
        self.memberList = AssemblyMember.memberList
class newsParsing(Parsing):
    def __init__(self, lastParsingData, status):
        Parsing.__init__(self,lastParsingData,status)
        self.keywordList = ["여성","통일"]
        self.cardNewsList = []
    def extractNews(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0; ko-KR))',
        }
        for key in self.keywordList:
            response = requests.get('https://search.naver.com/search.naver?where=news&sm=tab_jum&query='+key,
                headers=headers)
            html = response.text
            soup = BeautifulSoup(html,"lxml")
            for li in soup.find('ul', {'class': 'type01'}).findAll('li'):
                try:
                    link = li.find('dt').find('a')
                    self.cardNewsList.append(cardNews(key,link.text,link['href'],self.lastParsingData))
                    #print(get_string(li.find('dd'))[0])
                except:
                    pass
    def updateDbNews(self):
        print("DB업그레이드")
        try:
            for data in self.cardNewsList:
                curs.execute(sql_card, (data.title, data.link, data.tag, data.date))
            conn.commit()
        except:
            pass
class cardNews:
    def __init__(self, tag, title,link,date):
        self.tag = tag
        self.title = title
        self.link = link
        self.date = date
class RankParsing(Parsing):
    def __init__(self, lastParsingData, status):
        Parsing.__init__(self,lastParsingData,status)
        self.newsCompanyList = ['한겨례']
        self.rankNewsList = []
    def extractRankByMember(self):
        print("멤버로 랭크뽑는거")
        # parse from hani(한겨레)
        # 정치면에서만 갖고옴.
        cnt = 0
        while True:
            cnt += 1;
            print(cnt, end=' ', flush=True)
            if cnt == 1:
                url = "http://www.hani.co.kr/arti/politics/home01.html"
            else:
                url = "http://www.hani.co.kr/arti/politics/list" + str(cnt) + ".html"
            page = requests.get(url)
            page.raise_for_status()
            page.encoding = None  # 한글깨짐 수정
            # print(page.text)
            # exit(-1)
            soup = BeautifulSoup(page.text, "lxml")
            soup = soup.find("div", class_="section-list-area")
            article_list = soup.find_all(name="div", attrs={"class": "list"}, recursive=True)
            for item in article_list:
                article = item.find(name="div", attrs={"class": "article-area"})
                title = article.find(name="h4", attrs={"class": "article-title"})
                # print(title.find(name="a").text)
                prologue = article.find("p", class_="article-prologue")
                content = prologue.find("a")
                date = prologue.find("span")
                date_obj = datetime.strptime(date.text, "%Y-%m-%d %H:%M")
                #print(date_obj)

                # 1 month check
                if date_obj < BEFORE_ONE_MONTH:
                    print(str(cnt) + " page !")
                    return
                title_txt = title.find("a").text
                article_link = "http://www.hani.co.kr" + title.find("a")['href']
                content_txt = content.text
                for idx in range(0,len(nameList)):
                    if (nameList[idx] in title_txt) or (nameList[idx] in content_txt):
                        rankCntList[idx] += 1
                        self.rankNewsList.append(rankNews(nameList[idx],title_txt,article_link,'한겨례',date_obj,deptcdList[idx]))
    def updateDbRank(self):
        print("DB에 저장")
        try:
            for data in  self.rankNewsList:
                curs.execute(sql_articleinfo, (data.deptcd,data.title,data.link,data.company,data.date))
            conn.commit()
        except:
            pass
    def setMemberRankInfo(self):
        print("멤버rank정해주는거")
        try:
            for idx in range(0, len(rankCntList)):
                curs.execute(sql_article,(deptcdList[idx], nameList[idx],rankCntList[idx]))
            conn.commit()
        except:
            pass
class rankNews:
    def __init__(self,name,title,link,compnay,date,deptcd):
        self.name = name #의원이름
        self.title = title # 기사제목
        self.link = link # 기사링크
        self.company = compnay # 기사 뉴스
        self.date = date #뉴스 날짜
        self.deptcd = deptcd



if __name__ == "__main__":
    now = time.localtime()
    s = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
    rankParser = RankParsing(s, 0)
    rankParser.extractRankByMember()
    rankParser.updateDbRank()
    rankParser.setMemberRankInfo()
    newsParser = newsParsing(s,0)
    newsParser.extractNews()
    newsParser.updateDbNews()

