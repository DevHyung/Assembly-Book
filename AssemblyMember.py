"""
    File name: Parser.py
    Author: DevHyung
    Date last modified: 2017/12/09
    Python Version: 3.6
    Description : Parsing modules descript this file
"""
import pymysql
import requests
from bs4 import BeautifulSoup
import time
#___DB부분 변수
ip = 'localhost'
id = 'root'
pw = 'autoset'
name = 'projectd'
chs ='utf8'
#---DB연결
conn = pymysql.connect(ip,id,pw,name,charset="utf8")
curs = conn.cursor()
sql = """insert into congress(idx,dept_cd,num,name,party,shrtnm)
                   values (%s, %s, %s, %s, %s, %s)"""
# 국회관련 변수
congress_num = 298
api_key = "TeInuDkG7xTP8mVZlMrmZ4Z7btqFpzoiM6L4FnY5S6oxkAAtxXszqbUOmZ2g6V6j34%2FoxhD%2B8DFPco85O%2B2YSw%3D%3D"
memberList = []
class AssemblyMember:
    def __init__(self):
        self.deptcd = 0
        self.email = ""
        self.name = ""
        self.tel = ""
        self.birth = ""
        self.hjName = ""
        self.origName = ""
        self.polyName = ""
        self.electedNum = ""
        self.electedTitleList = ""
        self.myCommitteeList = ""
        self.talent = ""
        self.hobby = ""
        self.career = ""
        self.exposeNum = 0
        self.exposeUrlList = []
        self.attendCommitteeList = []
        self.attendHistoryList = []
        self.attendTitleList = []
    def getDeptcd(self):
        return str(self.deptcd)
    def getName(self):
        return self.name
    def getPoly(self):
        return self.polyName
    def getShrtNm(self):
        return self.myCommitteeList
    def setDefaultInfo(self,deptcd,name,hjName,orignm):
        self.deptcd = deptcd
        self.name = name
        self.hjName = hjName
        self.origName = orignm
    def setDetailInfo(self,email,tel,birth,poly,electedNum,eletedTitleList,committeelist,talent,hobby,career):
        self.email =email
        self.tel = tel
        self.birth = birth
        self.polyName =poly
        self.electedNum = electedNum
        self.electedTitleList = eletedTitleList
        self.myCommitteeList = committeelist
        self.talent = talent
        self.hobby = hobby
        self.career = career

class Committee:
    def __init__(self):
        self.cmtId = 0 # 회의 번호
        self.cmtName = "" # 회의 이름
        self.cmtCount = 0 # 회의 갯수
        self.cmtTitleList = [] # 회의 제목 list
        self.cmtAttendDataList = [] # 회의 마다마다 출결정보
    def getAttendListByName(self,name):#이름을 가지고 출결List 반환
        print("getAttendListByName")

class StandingCommittee(Committee):
    def __init__(self):
        Committee.__init__()
class PlenaryCommittee(Committee):
    def __init__(self):
        Committee.__init__()

if __name__=="__main__":
    print("__main__ 실행")
else:
    # member list parsing
    html = "http://apis.data.go.kr/9710000/NationalAssemblyInfoService/getMemberCurrStateList?numOfRows=" + str(
        congress_num) + "&ServiceKey=" + api_key
    detail_html = "http://apis.data.go.kr/9710000/NationalAssemblyInfoService/getMemberDetailInfoList?ServiceKey=" + api_key
    url_deptcd = "&dept_cd="
    url_num = "&num="
    tmpnumlist = []
    tmpdeptlist = []
    # request and paring
    source = requests.get(html)
    bs = BeautifulSoup(source.text, "html.parser")
    item = bs.find_all("item")
    # ---기본정보뽑는곳
    print("> START : 의원기본정보 파싱")
    for k in item:
        deptcd = k.find("deptcd").get_text()
        tmpdeptlist.append(deptcd)
        name = k.find("empnm").get_text()
        hjname = k.find("hjnm").get_text()
        orignm = k.find("orignm").get_text()
        tmpnumlist.append(k.find("num").get_text())
        tmpAssemblyClass = AssemblyMember()
        tmpAssemblyClass.setDefaultInfo(deptcd, name, hjname, orignm)
        memberList.append(tmpAssemblyClass)
    print("> END : 의원기본정보 파싱완료")
    # ---상세정보 뽑는곳
    print("> START : 의원상세정보 파싱")
    for i in range(0, congress_num):
        url = detail_html + url_deptcd + tmpdeptlist[i] + url_num + tmpnumlist[i]
        if i % int(congress_num / 10) == 0:
            print(str(int((i / congress_num) * 100)) + "% processing...")
        source = requests.get(url);
        detailbs = BeautifulSoup(source.text, "html.parser")
        detailitem = detailbs.find("item")
        # 가져오기
        try:
            email = detailitem.find("assememail").get_text()
        except:
            email = ""
        tel = detailitem.find("assemtel").get_text()
        birth = detailitem.find("bthdate").get_text()
        poly = detailitem.find("polynm").get_text()
        electedNum = detailitem.find("reelegbnnm").get_text().split("제")[0]
        electedTitleList = detailitem.find("electionnum").get_text()
        try:
            committeelist = detailitem.find("shrtnm").get_text()
        except:
            #print('shrtnm 누락 :', detailitem.find("empnm").get_text())
            committeelist = ""
        try:
            talent = detailitem.find("examcd").get_text()
        except:
            #print('talent 누락 :', detailitem.find("empnm").get_text())
            talent = ""
        try:
            hobby = detailitem.find("hbbycd").get_text()
            #print('hobby 누락 :', detailitem.find("empnm").get_text())
        except:
            hobby = ""
        try:
            career = detailitem.find("memtitle").get_text()
        except:
            #print('경력 누락 :', detailitem.find("empnm").get_text())
            career =""
        memberList[i].setDetailInfo(email, tel, birth, poly, electedNum, electedTitleList, committeelist, talent,
                                         hobby, career)
    print("> END : 의원상세정보 파싱완료")
    for i in range(0, congress_num):
        dept = memberList[i].getDeptcd()
        num =  str(tmpnumlist[i])
        name = memberList[i].getName()
        poly = memberList[i].getPoly()
        shrt = memberList[i].getShrtNm()
        print(name,num,dept,shrt,poly)
        curs.execute(sql, (i+1, dept,num,name,poly,shrt) )
    conn.commit()
