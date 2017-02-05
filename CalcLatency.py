#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division
import pickle
import math
import os
import re as re

def GetSample(rawfilename):
    inputfile = open(rawfilename,'rb')

    data_array=pickle.load(inputfile)
    inputfile.close()
    count_map={}
    delay_map={}
    avg_map={}


    for item in data_array:
            if not item:
                continue
            metrics = item.split(':')
            value = data_array[item]

            if value:
                if metrics[0] == 'count':
                    count_map[metrics[1]+':'+metrics[2]+':'+metrics[3]]=value

                if metrics[0] == 'delay':
                    delay_map[metrics[1]+':'+metrics[2]+':'+metrics[3]]=value


    for key in count_map.keys():
        if delay_map.has_key(key):

            delay=float(delay_map[key])/float(count_map[key])
            temp=key.split(':')
            member_ip_port=temp[0]+':'+temp[1]
            timestamp = int(temp[2])

            if avg_map.has_key(member_ip_port):
                avg_map[member_ip_port][timestamp]=delay
            else:
                avg_map[member_ip_port]={}
                avg_map[member_ip_port][timestamp]=delay
    return avg_map


class StdDev(object):


    def __init__(self):

        self.__Sample = []
        self.__AvgValue = 0
        self.__StdDev = 0
        self.__ActiveStatus='Enabled'
        self.__Ratio = 0

    @property
    def StdDev(self):
        return self.__StdDev

    @property
    def AvgValue(self):
        return self.__AvgValue
    @property
    def Ratio(self):
        return self.__Ratio

    @property
    def Sample(self):
        return self.__Sample

    @property
    def ActiveStatus(self):
        return self.__ActiveStatus

    def SetSample(self,sample):
        self.__Sample = sample

    def setStatus(self,status):
        self.__ActiveStatus = status

    def setRatio(self,Ratio):
        self.__Ratio = Ratio



    def AddSample(self,value):
        self.__Sample.append(value)

    def GetSampleCount(self):
        return len(self.__Sample)

    def CalcStdDev(self):


        TotalCount = 0
        TotalValue = 0
        TotalValue_sqrt = 0

        print 'sample count is:'+str(len(self.__Sample))
        for value in self.__Sample:

            TotalValue += float(value)
            TotalValue_sqrt += float(value)**2
            TotalCount += 1

        AvgValue= float(TotalValue/TotalCount)

        StdDev = math.sqrt((TotalValue_sqrt+TotalCount*(AvgValue**2)-2*(TotalValue)*AvgValue)/TotalCount)
        self.__AvgValue = AvgValue
        self.__StdDev = StdDev


    def getSigma(self,value):

        if value > self.__AvgValue:
            return [abs(value-self.__AvgValue)/self.__StdDev,1]
        return [abs(value-self.__AvgValue)/self.__StdDev,-1]

def __isVirtualServer(line):
        if re.match(r"^ltm\svirtual\s\S+\s{$", line):
            return True

def __GetLtmConfigAndFilterPoolHasRule(LtmFileNameV11, RuleFilter):

    vsName = ''
    vsRule =''
    vsSet = {}
    vsRulesList = []
    FilteredPoolList = []

    #with open(LtmFileNameV11, 'rb') as f:

    try:
        f = open(LtmFileNameV11, 'rb')
        while 1:
            row = f.readline()

            if row == '':
                    break

            if __isVirtualServer(row):
                vsName = re.search("^ltm\svirtual\s(\S+)\s{$", row).group(1)
                vsPool = ''

                while 1:
                    row = f.readline()

                    if re.match("^}.*$", row):
                            break

                    row = row.rstrip()
                    if re.match("^\s+pool\s(.*)$", row):
                        vsPool = re.search("^\s+pool\s(.*)$", row).group(1)
                        vsSet[vsName + '-pool'] = vsPool
                        continue

                    if re.match("^\s+rules\s{", row):

                        while 1:
                            row = f.readline();                            

                            if re.match("^\s+}.*$", row):
                                    break

                            if re.match("^\s+\/Common\/(\S+).*$", row):
                                vsRule = row.strip()
                                ####print vsRule
                                if vsRule == RuleFilter and vsPool != '':
                                    FilteredPoolList.append(vsSet.get((vsName + '-pool'), vsPool))
                                
                                else:
                                    continue
                            else:
                                continue
    except Exception,ex:
        print 'open bigip.conf failed'
        raise
        
    return set(FilteredPoolList)


if __name__ == '__main__':
    pathname= '/dev/shm/'
    ####Pools = ['/Common/Pool_test']
    Pools = __GetLtmConfigAndFilterPoolHasRule('/config/bigip.conf', '/Common/calu')

    for PoolName in  Pools:
        filename = '/dev/shm/'+PoolName.replace('/','_')
        sample_set = GetSample(filename)

        for member in sample_set.keys():

            inputfilename = pathname+'Calc'+PoolName.replace('/','_')+'_'+member.replace(':','_')
            if os.path.isfile(inputfilename):

                input = open(inputfilename,'rb')
                stddev=pickle.load(input)
                input.close()

                if stddev.ActiveStatus != 'Enabled':
                    print 'this is not in Enabled status for member: '+member
                    continue
            stddev=StdDev()
            avg_map=sample_set[member]

            i=0

            for key in avg_map.keys():
                i +=1
                value = int(avg_map[key])
                if value >1000:
                    continue
                count =1
                for x in range(1,180):
                    if avg_map.has_key(key-x):
                        if avg_map[key-x]<1000:
                            value +=int(avg_map[key-x])
                            count += 1
                stddev.AddSample(int(value/count))

            stddev.CalcStdDev()


            print 'save '+member+ ' recode '+ str(stddev.GetSampleCount())
            print 'the avg value is '+str(stddev.AvgValue)
            print 'the stddev value is '+str(stddev.StdDev)
            outputfile = open(pathname+'Calc_Common_Pool_test'+'_'+member.replace(':','_'),'wb')
            pickle.dump(stddev,outputfile)
            outputfile.close()


