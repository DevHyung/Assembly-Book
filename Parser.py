"""
    File name: Parser.py
    Author: DevHyung
    Date last modified: 2017/12/09
    Python Version: 3.6
    Description : Parsing modules descript this file
"""
import AssemblyMember
import time
class Parsing:
    def __init__(self, lastParsingData, status):
        self.lastParsingData = lastParsingData
        self.status = status
        self.logList = []
        self.memberList = []


class AttendParsing(Parsing):
    def __init__(self, lastParsingData, status):
        Parsing.__init__(self, lastParsingData, status)
        self.committeeList = [] # 상임위원회
        self.memAttendList = [] # 본회의


if __name__ == "__main__":
    now = time.localtime()
    s = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
    print(len(AssemblyMember.memberList))