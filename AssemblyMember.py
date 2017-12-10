"""
    File name: Parser.py
    Author: DevHyung
    Date last modified: 2017/12/09
    Python Version: 3.6
    Description : Parsing modules descript this file
"""
#-*-encoding:utf8-*-
import pymysql
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict
import urllib.request
import os
import io
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
sql_detail = """insert into congressinfo(con_num,email,birthday,hjname,talent,hobby,orignm,electionnum,sharnm,memtitle)
                           values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
sql_scommittee = """insert into scommittee(idx,sc_name,cg_num,cg_name,sc_totalcnt,sc_attend,sc_per,sc_title)
                   values (%s, %s, %s, %s, %s, %s,%s,%s)"""
sql_bcommittee = """insert into bcommittee(title,cg_num,cg_name,attend)
                   values (%s, %s, %s, %s)"""
# 국회관련 변수
congress_num = 298
api_key = "TeInuDkG7xTP8mVZlMrmZ4Z7btqFpzoiM6L4FnY5S6oxkAAtxXszqbUOmZ2g6V6j34%2FoxhD%2B8DFPco85O%2B2YSw%3D%3D"
memberList = []
#
tmpnumlist = []
nameList = []
scList = []
#
deptcd_list = []
party_list = [' ' for _ in range(congress_num)]
shrt_list = [' ' for _ in range(congress_num)]
name_list = []
num_list = []
scommittee_class_list = []
class sc_list:
    def __init__(self, _name):
        self.IsFirst=  True #처음 들어오면 리스트 할당해주는는
        self.sc_name = _name  # 상임위 이름
        self.cnt = 0  # 위원회수
        self.cg_num = []  # 의원들번호
        self.cg_name = []  # 의원들이름
        self.cg_dang = [] # 의원들 당리스트
        self.sc_totalcnt = 0 # 위원회열린수
        self.sc_history = [] # '참참불불참참'같은거 적을거 초기화필요
        self.cntlist = []  # 출석횟수, 출석률낵위한 초기화필요
        self.sc_title=""
    def print(self):
        for i in range (0,self.cnt):
            print(self.sc_name+' '+self.cg_name[i])
    def attend(self, _name):#이름이 있으면 출석을 올려주는거 이름리스트가 날다치자
        if self.IsFirst: #처음이면
            #print("처음이네")
            for i in range(0,self.cnt):
                self.sc_history.append('')
                self.cntlist.append(0)
            self.IsFirst = False
        #넘어온 이름을 받아서 거기에해당하는 history 업그레이드해주고, cntlist 올려주는거
        atend_idxlist = []
        dangidx = 0

        for namevalue in _name:#출석자 이름 리스트가 넘어옴

            #print ( self.cg_dang[dangidx], self.cg_name[dangidx])
            for idx in range(0,self.cnt):#의원 이름리스트를돈다
                if self.cg_name[idx] == namevalue:#출석을했다
                    #if self.cg_dang[idx].replace(" ","") == _dang[dangidx].replace(" ",""): 당도매칭되면 뽑을랬는데 당옮기면 기록이 계속기록되서 안됨
                    atend_idxlist.append(idx)
                    break
                dangidx = dangidx+1
        atend_idxlist = list( set (atend_idxlist))
        for idx in range(0,self.cnt):
            try:
                atend_idxlist.index(idx) #인덱스가있으면
                _name.index(self.cg_name[idx])
                self.sc_history[idx] = self.sc_history[idx] +"참"
                self.cntlist[idx] = self.cntlist[idx] +1
            except:#없으면
                self.sc_history[idx] = self.sc_history[idx] + "불"
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
        self.exposeNum = 0 #
        self.exposeUrlList = [] #
        self.attendCommitteeList = [] # 구현
        self.attendHistoryList = [] # 불참 참 내역
        self.attendTitleList = [] # 불참 참 한 회의제목


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
    def __init__(self,cmtname):
        self.cmtId = 0 # 회의 번호
        self.cmtName = cmtname # 회의 이름
        self.cmtCount = 0 # 회의 갯수
        self.cmtTitleList = [] # 회의 제목 list
        self.cmtAttendDataList = [] # 회의 마다마다 출결정보
    def getAttendListByName(self,name):#이름을 가지고 출결List 반환
        print("getAttendListByName")

class StandingCommittee(Committee):
    def __init__(self, cmtnm):
        Committee.__init__(self,cmtnm)
class PlenaryCommittee(Committee):
    def __init__(self,cmtnm):
        Committee.__init__(self,cmtnm)

def get_congressinfo():
    # member list parsing
    html = "http://apis.data.go.kr/9710000/NationalAssemblyInfoService/getMemberCurrStateList?numOfRows=" + str(
        congress_num) + "&ServiceKey=" + api_key
    detail_html = "http://apis.data.go.kr/9710000/NationalAssemblyInfoService/getMemberDetailInfoList?ServiceKey=" + api_key
    url_deptcd = "&dept_cd="
    url_num = "&num="
    tmpdeptlist = []
    # request and paring
    source = requests.get(html)
    bs = BeautifulSoup(source.text, "html.parser")
    item = bs.find_all("item")
    # ---기본정보뽑는곳
    print("> START : 의원기본정보 파싱")
    for k in item:
        deptcd = k.find("deptcd").get_text()
        deptcd_list.append(deptcd)
        tmpdeptlist.append(deptcd)
        name = k.find("empnm").get_text()
        name_list.append(name)
        nameList.append(name)
        hjname = k.find("hjnm").get_text()
        orignm = k.find("orignm").get_text()
        tmpnumlist.append(k.find("num").get_text())
        num_list.append(k.find("num").get_text())
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
        party_list[i] = poly
        electedNum = detailitem.find("reelegbnnm").get_text().split("제")[0]
        electedTitleList = detailitem.find("electionnum").get_text()
        try:
            committeelist = detailitem.find("shrtnm").get_text()
            shrt_list[i] = committeelist
        except:
            # print('shrtnm 누락 :', detailitem.find("empnm").get_text())
            committeelist = ""
            print(url)
        splitlist = committeelist.split(',')
        for tmp in splitlist:
            try:
                scList.index(tmp)
            except:  # 없을시
                scList.append(tmp)
        scList.sort()
        try:
            talent = detailitem.find("examcd").get_text()
        except:
            # print('talent 누락 :', detailitem.find("empnm").get_text())
            talent = ""
        try:
            hobby = detailitem.find("hbbycd").get_text()
            # print('hobby 누락 :', detailitem.find("empnm").get_text())
        except:
            hobby = ""
        try:
            career = detailitem.find("memtitle").get_text()
        except:
            # print('경력 누락 :', detailitem.find("empnm").get_text())
            career = ""
        memberList[i].setDetailInfo(email, tel, birth, poly, electedNum, electedTitleList, committeelist, talent, hobby,
                                    career)
    print("> END : 의원상세정보 파싱완료")
def db_insertcongress():
    try:
        for i in range(0, congress_num):
            dept = memberList[i].getDeptcd()
            num = str(tmpnumlist[i])
            name = memberList[i].getName()
            poly = memberList[i].getPoly()
            shrt = memberList[i].getShrtNm()
            curs.execute(sql, (i + 1, dept, num, name, poly, shrt))
            curs.execute(sql_detail, (
            num, memberList[i].email, memberList[i].birth, memberList[i].hjName, memberList[i].talent, memberList[i].hobby,
            memberList[i].origName, memberList[i].electedNum + "(" + memberList[i].electedTitleList + ")",
            memberList[i].myCommitteeList, memberList[i].career))
        conn.commit()
    except:
        pass
def get_scommitteeinfo():
    global scommittee_class_list
    scommittee_class_list = get_sclist()  # 상임위 이름목록만 지니고있는 클래스 리스트 반환
    for classidx in scommittee_class_list:  # 클래스를 순회한다
        for i in range(0, congress_num):  # 모든국회의원을 돌면서
            if not shrt_list[i].find(classidx.sc_name) == -1:  # 찾은거
                classidx.cnt = classidx.cnt + 1
                classidx.cg_name.append(name_list[i])
                classidx.cg_num.append(num_list[i])
                classidx.cg_dang.append(party_list[i])
def get_sclist():
    _list = extract_scname()
    scommittee_list = []
    for i in _list:
        scommittee_list.append(sc_list(i))
    return scommittee_list
def extract_scname():
    _list =[]
    for shrtlist in shrt_list:
        splitlist =  shrtlist.split(',')
        for i in splitlist:
            try:
                _list.index(i)
            except: #없을시
                _list.append(i)
    _list.sort()
    return _list
def calc_scommitteeinfo():

    global scommittee_class_list
    # 전체회의록
    scommittee_url = "http://apis.data.go.kr/9710000/ProceedingInfoService/getAllConInfoList?class_code=2&dae_num=20&serviceKey=TeInuDkG7xTP8mVZlMrmZ4Z7btqFpzoiM6L4FnY5S6oxkAAtxXszqbUOmZ2g6V6j34%2FoxhD%2B8DFPco85O%2B2YSw%3D%3D&numOfRows=1000"
    # 특별위원회
    scommittee_spcial_url = "http://apis.data.go.kr/9710000/ProceedingInfoService/getAllConInfoList?class_code=3&dae_num=20&serviceKey=TeInuDkG7xTP8mVZlMrmZ4Z7btqFpzoiM6L4FnY5S6oxkAAtxXszqbUOmZ2g6V6j34%2FoxhD%2B8DFPco85O%2B2YSw%3D%3D&numOfRows=1000"
    # 참석자 요약 url 부정확해
    attend_url = "http://apis.data.go.kr/9710000/ProceedingInfoService/getSummaryAttenInfoList?serviceKey=TeInuDkG7xTP8mVZlMrmZ4Z7btqFpzoiM6L4FnY5S6oxkAAtxXszqbUOmZ2g6V6j34%2FoxhD%2B8DFPco85O%2B2YSw%3D%3D&numOfRows=1000&confer_num="  # 뒤에 confernum을 붙이면됨
    # 요약페이지 URL
    summary_url = "http://likms.assembly.go.kr/record/mhs-10-030.do?conferNum="
    _error_list = []
    # ---연결
    source = requests.get(scommittee_url)
    bs = BeautifulSoup(source.text, "html.parser")
    item = bs.find_all("item")
    # ---기본상임위원회
    for classidx in range(0, len(scommittee_class_list)):
        flag = True
        totalcnt = 0  # 회의한 숫자
        sctitle = ""  # 상임위 타이르 ㅐoo차oo회 가져오기위한거 meeting1 , meeting2 에 split (으로 찾아온다
        for k in item:
            if k.find("commname").get_text().replace(" ", "") == scommittee_class_list[classidx].sc_name.replace(" ",
                                                                                                                 ""):
                totalcnt = totalcnt + 1
                print(k.find("commname").get_text(), str(totalcnt), "개 분석중... ")
                _confernum = k.find("confernum").get_text()  # 회의록 넘버를 가져옴
                # _confernum = "046931"
                _name = []
                _dang = []
                sctitle = sctitle + k.find("meeting1").get_text().split('(')[0]
                sctitle = sctitle + k.find("meeting2").get_text()
                sctitle = sctitle + ","
                source = requests.get(summary_url + _confernum)
                tmpbs = BeautifulSoup(source.text, "html.parser")
                tmpitem = tmpbs.find_all('li')

                for t in tmpitem:
                    try:
                        _dang.append(t.find("span").get_text().split(' ')[0])
                        _name.append(t.find("span").get_text().split(' ')[1])
                    except:
                        nonemean = 1
                for removeidx in range(0, len(_dang)):
                    try:
                        _dang.remove('')
                    except:
                        nomean = 1
                if _name == []:
                    _error_list.append(_confernum)
                else:
                    # print(_dang)
                    # print(_name)
                    scommittee_class_list[classidx].attend(_name)
                    flag = False
            # 누락된정보는 들어가질떄까지 돌린다

            while flag:
                #print("출석부 누락된 리스트 : ", end='')
                #print(_error_list)
                roofcnt = 0
                #print("누락된 정보수: " + str(len(_error_list)))
                if len(_error_list) == 0:
                    break;
                i = _error_list[0]
                #print(str(i) + "인덱스 처리중...")
                Isempty = True
                while Isempty:
                    url = summary_url + str(i)
                    source = requests.get(url)
                    _tmpbs = BeautifulSoup(source.text, "html.parser")
                    _tmpitem = _tmpbs.find_all('li')
                    # print(tmpitem)
                    for t in _tmpitem:
                        try:
                            _dang.append(t.find("span").get_text().split(' ')[0])
                            _name.append(t.find("span").get_text().split(' ')[1])
                        except:
                            nonemean = 1
                    print(attend_url + _confernum)
                    # print(_name)
                    roofcnt = roofcnt + 1
                    if roofcnt == 2:
                        Isempty = False
                        _error_list.remove(i)
                        tmp = []
                        scommittee_class_list[classidx].attend(tmp)
                    if not _name == []:
                        Isempty = False
                        _error_list.remove(i)
                        scommittee_class_list[classidx].attend(_name)

        if not totalcnt == 0:
            print(scommittee_class_list[classidx].sc_name.replace(" ", ""), end='')
            print(totalcnt, end=' ')
            print(scommittee_class_list[classidx].cnt, end='')
            print("명 있음")
            scommittee_class_list[classidx].sc_totalcnt = totalcnt
            scommittee_class_list[classidx].sc_title = sctitle
            #####################################################################################################
    source = requests.get(scommittee_spcial_url)
    bs = BeautifulSoup(source.text, "html.parser")
    item = bs.find_all("item")
    # ---특별위원회
    for classidx in range(0, len(scommittee_class_list)):
        flag = True
        totalcnt = 0  # 회의한 숫자
        sctitle = ""  # 상임위 타이르 ㅐoo차oo회 가져오기위한거 meeting1 , meeting2 에 split (으로 찾아온다
        for k in item:
            if k.find("commname").get_text().replace(" ", "") == scommittee_class_list[classidx].sc_name.replace(" ",
                                                                                                                 ""):
                totalcnt = totalcnt + 1
                print(k.find("commname").get_text(), str(totalcnt), "개 분석중... ")
                _confernum = k.find("confernum").get_text()  # 회의록 넘버를 가져옴
                # _confernum = "046931"
                _name = []
                _dang = []
                sctitle = sctitle + k.find("meeting1").get_text().split('(')[0]
                sctitle = sctitle + k.find("meeting2").get_text()
                sctitle = sctitle + ","
                source = requests.get(summary_url + _confernum)
                tmpbs = BeautifulSoup(source.text, "html.parser")
                tmpitem = tmpbs.find_all('li')
                for t in tmpitem:
                    try:
                        _dang.append(t.find("span").get_text().split(' ')[0])
                        _name.append(t.find("span").get_text().split(' ')[1])
                    except:
                        nonemean = 1
                for removeidx in range(0, len(_dang)):
                    try:
                        _dang.remove('')
                    except:
                        nomean = 1
                if _name == []:
                    _error_list.append(_confernum)
                else:
                    scommittee_class_list[classidx].attend(_name)
                    flag = False
            # 누락된정보는 들어가질떄까지 돌린다

            while flag:
                #print("출석부 누락된 리스트 : ", end='')
                #print(_error_list)
                roofcnt = 0
                #print("누락된 정보수: " + str(len(_error_list)))
                if len(_error_list) == 0:
                    break;
                i = _error_list[0]
                print(str(i) + "인덱스 처리중...")
                Isempty = True
                while Isempty:
                    url = summary_url + str(i)
                    source = requests.get(url)
                    _tmpbs = BeautifulSoup(source.text, "html.parser")
                    _tmpitem = _tmpbs.find_all('li')
                    # print(tmpitem)
                    for t in _tmpitem:
                        try:
                            _dang.append(t.find("span").get_text().split(' ')[0])
                            _name.append(t.find("span").get_text().split(' ')[1])
                        except:
                            nonemean = 1
                    print(attend_url + _confernum)
                    # print(_name)
                    roofcnt = roofcnt + 1
                    if roofcnt == 2:
                        Isempty = False
                        _error_list.remove(i)
                        tmp = []
                        scommittee_class_list[classidx].attend(tmp)
                    if not _name == []:
                        Isempty = False
                        _error_list.remove(i)
                        scommittee_class_list[classidx].attend(_name)
        if not totalcnt == 0:
            print(scommittee_class_list[classidx].sc_name.replace(" ", ""), end='')
            print(totalcnt, end=' ')
            print(scommittee_class_list[classidx].cnt, end='')
            print("명 있음")
            scommittee_class_list[classidx].sc_totalcnt = totalcnt
            scommittee_class_list[classidx].sc_title = sctitle
def db_insertscommittee():
    idx = 1  # db에 들어가는 index 넘버
    try:
        for i in scommittee_class_list:
            # print(i.cnt)
            # idx , 상임위이름, 의원번호,의원이름,총회의수, 참석히스토리, 출석률
            for cnt in range(0, i.cnt):
                try:
                    curs.execute(sql_scommittee, (
                    idx, i.sc_name, i.cg_num[cnt], i.cg_name[cnt], i.sc_totalcnt, i.sc_history[cnt], i.cntlist[cnt],
                    i.sc_title))
                    idx = idx + 1
                except IndexError:
                    print(i.sc_name + str(i.cnt) + "명")
                conn.commit()
    except:
        pass
def get_photo():
    cnt = 0;
    url = "http://www.assembly.go.kr/photo/"
    ext = ".jpg"
    print("START : 이미지 다운로드")
    for idx in range(0, len(deptcd_list)):
        if cnt == congress_num:
            break
        else:
            cnt += 1

        print(idx + 1, "개  진행중..")
        html = url + str(deptcd_list[idx]) + ext
        try:
            urllib.request.urlretrieve(html, "img/"+deptcd_list[idx] + ".jpg")
        except:
            urllib.request.urlcleanup()
            urllib.request.urlretrieve(html, "img/"+deptcd_list[idx] + ".jpg")
    print("총 " + str(len(deptcd_list)) + "개 파일 다운로드완료")
def get_bcommitteeinfo():
    global democnt
    cnt = 0
    global api_key
    bonurl = "http://apis.data.go.kr/9710000/ProceedingInfoService/getAllConInfoList?class_code=1&dae_num=20&numOfRows=1000&serviceKey=" + api_key
    filename_list = []
    hwplink_list = []
    # ---연결하여서 hwp다운경로, 파일이름들을 다저장
    source = requests.get(bonurl)
    bs = BeautifulSoup(source.text, "html.parser")
    item = bs.find_all("item")
    for k in item:
        if cnt == democnt:
            break
        else:
            cnt += 1
        tmptitle = ""
        hwplink_list.append(k.find("hwplink").get_text())
        tmptitle = tmptitle + k.find("meeting1").get_text().split('(')[0]
        tmptitle = tmptitle + k.find("meeting2").get_text().split('(')[0]
        filename_list.append(tmptitle)
    # print(len(hwplink_list))
    print(len(filename_list))
    if not len(hwplink_list) == len(filename_list):
        print(str(abs(len(hwplink_list) - len(filename_list))) + "개의 파일이 누락됨")
    # -- 다운로드와 컨버팅하는 함수호출
    print(len(hwplink_list), " 개 파일 다운로드중....")
    down_hwp(hwplink_list, filename_list)
    print(len(filename_list), " 개 파일 변환중....")
    convert_txt(filename_list)
    calc_bcommittee(filename_list)
def down_hwp(hwplink_list, filename_list):
    for idx in range(0,len(hwplink_list)):
        print(  filename_list[idx] + "파일  진행중..")
        try:
            urllib.request.urlretrieve(hwplink_list[idx], filename_list[idx]+".hwp")
        except:
            urllib.request.urlcleanup()
            urllib.request.urlretrieve(hwplink_list[idx], filename_list[idx]+".hwp")
    print( "총 " + str( len(hwplink_list)) + "개 파일 다운로드완료")
def convert_txt(filename_list):
    cmd = "hwp5txt "
    hwpext = ".hwp"
    txtext = ".txt"
    for idx in range(0,len(filename_list)):
        print(  filename_list[idx] + "파일  변환중,,  hwp -> txt")

        os.system(cmd + filename_list[idx] + hwpext + " > " + filename_list[idx] + txtext)
    print( "총 " + str( len(filename_list)) + "개 파일 변환완료")
def calc_bcommittee(filename_list):
    tmpnumlist = []
    tmpnamelist = []
    tmppartylist = []
    # 9771029	22	    최경환	새누리당 -> 자유한국당
    # 9770976	2947	최경환	국민의당 -> 국민의당
    # 9770974	2643	김성태	바른정당 -> 자유한국당
    # 9771046	2950	김성태	새누리당 金成泰 -> 자유한국당
    with open("congress.txt", 'r') as f:
        while True:
            line = f.readline()
            line = line.strip()
            if not line: break
            txt = line.split(',')
            tmpnumlist.append(txt[1])
            IsSet = False
            if txt[1] == '22':
                tmpnamelist.append("최경환(한)")#예전엔 새
                IsSet = True
            if txt[1] == '2947':
                tmpnamelist.append("최경환(국)")
                IsSet = True
            if txt[1] == '2950':
                tmpnamelist.append("金成泰")
                IsSet = True
            if not IsSet:
                tmpnamelist.append(txt[2])
            tmppartylist.append(txt[3])

    # 김성태 , 최경환만 동명이인이다.
    for roof in range(0, len(filename_list)):
        print(roof + 1, "번째 파일 분석중")
        # print (filename_list[roof])
        fname = filename_list[roof] + ".txt"
        test = open(fname, 'r', io.DEFAULT_BUFFER_SIZE, 'utf-8')
        at = ""  # 출석버튼 한번이라도 누르고간 리스트
        at1 = ""  # 개의시 있었던 리스트
        at2 = ""  # 산회시 있었던 리스트
        at3 = ""  # 청가한사람 리스트
        at_list = []  # 출석리스트
        at1_list = []  # 개의리스트
        at2_list = []  # 산회리스트
        at3_list = []  # 청가리스트
        getaway = ""  # 출장텍스트
        getaway_list = []  # 출장리스트
        attend_txtlist = ['' for i in range(0, len(tmpnamelist))]
        tt = test.read()
        ttt = tt.split("◯출석 의원")
        Isfirstcommitte = False
        try:
            tttt = ttt[1].split("◯개의 시")[0]
            at = tttt.split("인)")[1]  # 개의시 있었던 리스트
        except:  # 개회시일때
            print("개회회의1")
            ttt = tt.split("◯참석 의원")
            tttt = ttt[1].split("◯국회")[0]
            at = tttt.split("인)")[1]  # 출석리스트
            Isfirstcommitte = True  # 개회식을알림
            # print (at)
        if not Isfirstcommitte:
            # ◯속개 시  가 있을떄
            ttt = tt.split("◯개의 시")
            tttt = ttt[1].split("◯산회 시")[0]
            if len(tttt.split("◯속개 시")) == 1:  # 속개시가 없다
                at1 = tttt.split("인)")[1]  # 개의시 있었던 리스트
            else:  # 속개시가있어
                print("속개시있음")
                tttt = tttt.split("◯속개 시")[0]
                at1 = tttt.split("인)")[1]  # 개의시 있었던 리스트

            ttt = tt.split("◯산회 시")

            if(len(ttt)!=1): #산회있
                lensplit = 0
                if not ttt[1].find('◯출장 의원') == -1:  # 출장의원이 있으면면
                    tttt = ttt[1].split("◯출장")[0]
                    lensplit = len(ttt[1].split("◯출장"))
                else:
                    tttt = ttt[1].split("◯청가")[0]
                    lensplit = len(ttt[1].split("◯청가"))
                if lensplit == 1:  # 출장 청가 아무것도없는거
                    tttt = ttt[1].split("◯국회")[0]
                at2 = tttt.split("인)")[1]  # 산회시 있었던 리스트

                if not ttt[1].find('◯출장 의원') == -1:  # 출장의원리스트
                    print("출장인원언도있")
                    ttt = tt.split("◯출장")
                    tttt = ttt[1].split("◯청가")[0]
                    if len(ttt[1].split("◯청가")) == 1:  # 출장은있는데 청가가없
                        tttt = ttt[1].split("◯국회")[0]
                    getaway = tttt.split("인)")[1]
                IsNoCG = False
                ttt = tt.split("◯청가")
                if len(ttt) == 1:  # 청가가없다
                    print("청가없음")
                    IsNoCG = True
                else:
                    tttt = ttt[1].split("◯국회")[0]
                    at3 = tttt.split("인)")[1]  # 청가 리스트
                # print(getaway)
            else:
                if not ttt[0].find('◯출장 의원') == -1:  # 출장의원이 있으면면
                    tttt = ttt[0].split("◯출장")[0]
                    lensplit = len(ttt[0].split("◯출장"))
                else:
                    tttt = ttt[0].split("◯청가")[1]
                    lensplit = len(ttt[0].split("◯청가"))
                #print(tttt)
                if lensplit == 1:  # 출장 청가 아무것도없는거
                    tttt = ttt[0].split("◯국회")[0]
                at2 = at1.split("◯")[0]  # 산회시 있었던 리스트

                if not ttt[0].find('◯출장 의원') == -1:  # 출장의원리스트
                    print("출장인원언도있")
                    ttt = tt.split("◯출장")
                    tttt = ttt[1].split("◯청가")[0]
                    if len(ttt[1].split("◯청가")) == 1:  # 출장은있는데 청가가없
                        tttt = ttt[1].split("◯국회")[0]
                    getaway = tttt.split("인)")[1]
                IsNoCG = False
                ttt = tt.split("◯청가")

                if len(ttt) == 1:  # 청가가없다
                    print("청가없음")
                    IsNoCG = True
                else:
                    tttt = ttt[1].split("◯국회")[0]
                    at3 = tttt.split("인)")[1]  # 청가 리스트
                # print(getaway)
                at1 = at1.split("◯")[0]
                at2 = at2.split("◯")[0]





            at_ = at.strip().split("  ")
            at1_ = at1.strip().split("  ")
            at2_ = at2.strip().split("  ")
            at3_ = at3.strip().split("  ")
            getaway_ = getaway.strip().split("  ")
            for idx in range(0, len(at_)):
                at_[idx] = at_[idx].strip()
            for idx in range(0, len(at1_)):
                at1_[idx] = at1_[idx].strip()
            for idx in range(0, len(at2_)):
                at2_[idx] = at2_[idx].strip()
            for idx in range(0, len(at3_)):
                at3_[idx] = at3_[idx].strip()

            # 외자처리
            tmpstr = ""
            IsOne = True
            for str in at1_:
                if len(str) == 1:
                    tmpstr = tmpstr + str
                    if IsOne:  # 외자인데처음
                        IsOne = False
                    else:
                        at1_list.append(tmpstr)
                        tmpstr = ""
                        IsOne = True
                else:
                    if not str == '김종태':
                        at1_list.append(str)
            # 외자처리
            tmpstr = ""
            IsOne = True
            for str in at2_:
                if len(str) == 1:
                    tmpstr = tmpstr + str
                    if IsOne:  # 외자인데처음
                        IsOne = False
                    else:
                        at2_list.append(tmpstr)
                        tmpstr = ""
                        IsOne = True
                else:
                    if not str == '김종태':
                        at2_list.append(str)
            # 외자처리
            tmpstr = ""
            IsOne = True
            for str in at3_:
                if len(str) == 1:
                    tmpstr = tmpstr + str
                    if IsOne:  # 외자인데처음
                        IsOne = False
                    else:
                        at3_list.append(tmpstr)
                        tmpstr = ""
                        IsOne = True
                else:
                    if not str == '김종태':
                        at3_list.append(str)
            tmpstr = ""
            IsOne = True
            for str in at_:
                if len(str) == 1:
                    tmpstr = tmpstr + str
                    if IsOne:  # 외자인데처음
                        IsOne = False
                    else:
                        at_list.append(tmpstr)
                        tmpstr = ""
                        IsOne = True
                else:
                    if not str == '김종태':
                        at_list.append(str)
            tmpstr = ""
            IsOne = True
            for str in getaway_:
                str = str.strip()
                if len(str) == 1:
                    tmpstr = tmpstr + str
                    if IsOne:  # 외자인데처음
                        IsOne = False
                    else:
                        getaway_list.append(tmpstr)
                        tmpstr = ""
                        IsOne = True
                else:
                    if not str == '':
                        if not str == '김종태':
                            getaway_list.append(str)

            # print(at1_list)
            # print(at2_list)
            # ____DB에 저장할꺼에요
            # ____이부분은 계산하는거
            real_cslist = []  # 정말 진정한 출석자
            late_cslist = []  # 지각자
            escape_cslist = []  # 출튀
            jt_cslist = []  # 지튀 리스트

            # 찐탱이 출석자
            plus_set = at1_list + at2_list
            for i in plus_set:
                if plus_set.count(i) == 2:
                    if not i == '김종태' or i=='안철수':
                        try:
                            idx = tmpnamelist.index(i)
                            attend_txtlist[idx] = '출석'
                            real_cslist.append(i)
                        except:
                            pass
            real_cslist = list(set(real_cslist))

            # 지각,  산회엔 있는데 개의때 없음
            # 산회를 돌면서 개의에 index 를 해보면되겠다
            for i in at2_list:
                try:
                    at1_list.index(i)
                except:
                    if not i == '김종태'or i=='안철수'or i=='문미옥':
                        # print (i)
                        try:
                            idx = tmpnamelist.index(i)
                            attend_txtlist[idx] = '지각'
                            late_cslist.append(i)
                        except:
                            pass
            # 출튀, 개의땐 있는데 산회떈 없는거
            # 개의리스트를 가지고 산회에 index를 했을때 없으면 출튀
            for i in at1_list:
                try:
                    at2_list.index(i)
                except:
                    if not i == '김종태' or i=='안철수'or i=='문미옥':
                        try:
                            idx = tmpnamelist.index(i)
                            attend_txtlist[idx] = '출튀'
                            escape_cslist.append(i)
                        except:
                            pass
            # 지튀, 개의도 산회도 없는데 카드는찍고나감
            # 출석명단돌면서 개의에도 산회에도 없는 사람을 찾으면된다
            for i in at_list:
                try:
                    at1_list.index(i)
                except:
                    try:
                        at2_list.index(i)
                    except:  # 아무데도 없는데 출석은함
                        if not i == '김종태'or i=='안철수'or i=='문미옥':
                            try:
                                idx = tmpnamelist.index(i)
                                attend_txtlist[idx] = '지튀'
                                jt_cslist.append(i)
                            except:
                                pass
            # 결석, 출석 + 청가 + 출장 다더한거에서 전체목록 뺸거
            if not getaway_list == []:
                total = at_list + at3_list + getaway_list
                for i in getaway_list:
                    if not i == '김종태'or i=='안철수'or i=='문미옥':
                        try:
                            idx = tmpnamelist.index(i)
                            attend_txtlist[idx] = '출장'
                        except:
                            pass
            else:
                total = at_list + at3_list

            # 전체리스트에서 - 출석자뺴고 - 청가빼고 - 그거누구냐 출장뺴자
            if not IsNoCG:
                for i in at3_list:
                    if not i == '김종태'or i=='안철수'or i=='문미옥':
                        try:
                            idx = tmpnamelist.index(i)
                            attend_txtlist[idx] = '청가'
                        except:
                            pass
            for idx in range(0, len(attend_txtlist)):
                if attend_txtlist[idx] == '':
                    attend_txtlist[idx] = '결석'
            # print( tmpnamelist, len(tmpnamelist))
            # print(attend_txtlist)
            print("결석", attend_txtlist.count('결석'))
            print("출석", len(at_list))
            print("출장", getaway_list, len(getaway_list))
            print("청가", len(at3_list))
            # print("출석의원총", len(at_list))
            # print("지튀:", jt_cslist, len(jt_cslist))
            # print("출튀:",escape_cslist, len(escape_cslist))
            # print("찐탱이:", real_cslist, len(real_cslist))
            # print("개의때 있던사람",len(at1_list))
            # print("지각:",late_cslist, len(late_cslist))
            for idx in range(0, len(tmpnamelist)):
                curs.execute(sql_bcommittee,
                             (filename_list[roof], tmpnumlist[idx], tmpnamelist[idx], attend_txtlist[idx]))
            conn.commit()
        else:  # 개최식일때
            print("개회식파일분석")
            at_ = at.strip().split("  ")
            tmpstr = ""
            IsOne = True
            for str in at_:
                if len(str) == 1:
                    tmpstr = tmpstr + str
                    if IsOne:  # 외자인데처음
                        IsOne = False
                    else:
                        at_list.append(tmpstr)
                        tmpstr = ""
                        IsOne = True
                else:
                    if not str == '김종태'and str=='안철수'or str=='문미옥':
                        at_list.append(str)
            for i in range(0, len(tmpnamelist)):
                try:
                    at_list.index(tmpnamelist[i])  # 있으면
                    attend_txtlist[i] = '출석'
                except:
                    attend_txtlist[i] = '결석'
            # print (attend_txtlist,len(attend_txtlist))
            print(tmpnamelist, len(tmpnamelist))
            try:
                for idx in range(0, len(tmpnamelist)):
                    curs.execute(sql_bcommittee,
                                 (filename_list[roof], tmpnumlist[idx], tmpnamelist[idx], attend_txtlist[idx]))
                conn.commit()
            except:
                pass
def get_filelist():
    global democnt
    cnt = 0
    global api_key
    bonurl = "http://apis.data.go.kr/9710000/ProceedingInfoService/getAllConInfoList?class_code=1&dae_num=20&numOfRows=1000&serviceKey=" + api_key
    filename_list = []
    hwplink_list = []
    # ---연결하여서 hwp다운경로, 파일이름들을 다저장
    source = requests.get(bonurl)
    bs = BeautifulSoup(source.text, "html.parser")
    item = bs.find_all("item")
    for k in item:
        if cnt == democnt:
            break
        else:
            cnt += 1
        tmptitle = ""
        hwplink_list.append(k.find("hwplink").get_text())
        tmptitle = tmptitle + k.find("meeting1").get_text().split('(')[0]
        tmptitle = tmptitle + k.find("meeting2").get_text().split('(')[0]
        filename_list.append(tmptitle)
    return filename_list
democnt = congress_num
if __name__=="__main__":
    print("direct 실행")
    get_congressinfo()
    db_insertcongress()
    # 회의정보부여하기
    for member in memberList:
        sclist = member.myCommitteeList.split(',')
        for sc in sclist:
            member.attendCommitteeList.append(StandingCommittee(sc))
        member.attendCommitteeList.append(PlenaryCommittee("본회의"))
    get_scommitteeinfo()
    calc_scommitteeinfo()
    db_insertscommittee()
    get_photo()
    get_bcommitteeinfo()
    tmplist = get_filelist()
    tmplist = list(OrderedDict.fromkeys(tmplist))
    calc_bcommittee(tmplist)
else:
    print("module 실행")
    get_congressinfo()
    db_insertcongress()
    # 회의정보부여하기
    for member in memberList:
        sclist = member.myCommitteeList.split(',')
        for sc in sclist:
            member.attendCommitteeList.append(StandingCommittee(sc))
        member.attendCommitteeList.append(PlenaryCommittee("본회의"))


