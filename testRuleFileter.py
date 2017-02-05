#!/usr/bin/env python
# -*- coding: utf-8 -*-
import httplib
import pickle
import os
import re

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
	print __GetLtmConfigAndFilterPoolHasRule('/config/bigip.conf', '/Common/calu')