"""
    File name: Parser.py
    Author: DevHyung
    Date last modified: 2017/12/09
    Python Version: 3.6
    Description : Parsing modules descript this file
"""
import AssemblyMember
import requests
from bs4 import BeautifulSoup
import time

class Parsing:
    def __init__(self, lastParsingData, status):
        self.lastParsingData = lastParsingData
        self.status = status
        self.logList = []
        self.memberList = AssemblyMember.memberList





if __name__ == "__main__":
    now = time.localtime()
    s = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
    #parser = AttendParsing(s, 0)
    #parser.extractScmtAttend()
