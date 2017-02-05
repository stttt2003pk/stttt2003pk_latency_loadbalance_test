#!/usr/bin/python
# -*- coding: utf-8 -*-
import httplib
import os

def SendTestRange(times, ServerList):
	conn = None
	for count in range(times):
		for server in ServerList:
			headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
			conn = httplib.HTTPConnection(server)
			conn.request('GET', None, None, headers)
			httpres = conn.getresponse()

if __name__ == '__main__':
	times=1000
	ServerList = [
	    '192.168.6.4',
	    '192.168.6.5',
	]

	SendTestRange(times, ServerList)
