#!/usr/bin/python


import httplib
import pickle
import math
import os
import traceback
import re
import logging
import logging.handlers
import commands


logger = logging.getLogger()

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




class Latency(object):

####form IP, make the instance, deal the data,count delay and their aaverage
    def __init__(self, ip,poolname):

        self.__Count_map = {}
        self.__Delay_map = {}
        self.__DelayAvg_map = {}
        self.__PoolName = poolname



        data_array = self.__GetDelayStatFromMonitorVs(ip).split('<br>')


        for item in data_array:
            if not item:
                continue

            metrics = item.split(':')
            Ip_InMap = metrics[1]+':'+metrics[2]
            if len(metrics[3].split('=')) == 2:

                value_str = metrics[3].split('=')[1]
                if value_str:
                    value = int(value_str)
                    if metrics[0] == 'count':
                        self.__CountAndDelayPlus(self.__Count_map, Ip_InMap, value)
                    elif metrics[0] == 'delay':
                        self.__CountAndDelayPlus(self.__Delay_map, Ip_InMap, value)

        for item in self.__Count_map.keys():
            self.__DelayAvg_map[item] = self.__Delay_map.get(item)/self.__Count_map.get(item)


    @property
    def Count_map(self):
        return self.__Count_map

    @property
    def Delay_map(self):
        return  self.__Delay_map

    @property
    def DelayAvg_map(self):
        return  self.__DelayAvg_map

####the http function
    def __GetDelayStatFromMonitorVs(self, ip):
        headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
        conn = httplib.HTTPConnection(ip)
        conn.request('GET', self.__PoolName, None, headers)
        httpres = conn.getresponse()
        return httpres.read()

    def __CountAndDelayPlus(self, data_map, ip, value):
        old_value = data_map.get(ip, 0)
        if old_value:
            value += old_value
            data_map[ip] = value
        else:
            data_map[ip] = value


def main():

    node_ips = os.getenv("NODE_IP")
    node_ip = re.search(r"^\D+(\d+\.\d+\.\d+\.\d+).*$", node_ips).group(1)
    node_port = os.getenv("NODE_PORT")
    logging_level = os.getenv('LogLevel')





    Pid = str(os.getpid())

    hdlr = logging.handlers.TimedRotatingFileHandler("/var/log/LatencyLB.log", when='D', interval=1, backupCount=7)
    formatter = logging.Formatter('%(asctime)s %(levelname)s ' + Pid + ' ' + node_ip + ':' + node_port + ' %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)

    if 'DEBUG' == logging_level:
            logger.setLevel(logging.DEBUG)
    else:
            logger.setLevel(logging.INFO)

    pathname= '/dev/shm/'

    MemberIp = node_ip+':'+node_port

    PoolName = os.getenv('PoolName')
    ltsfilename = '/dev/shm/'+PoolName.replace('/','_')

    try:
        logging.info('checking member '+node_ip+':'+node_port)
        MonitorVsIp = '10.128.5.12'
        inputfilename =pathname+'Calc'+PoolName.replace('/','_')+'_'+MemberIp.replace(':','_')

        stddev=StdDev()

        if os.path.isfile(inputfilename):
            latency=Latency('10.128.5.12',PoolName)
            logging.info('MonitorVsIp :'+MonitorVsIp+' PoolName: '+PoolName)
            logging.info('get Pool: '+PoolName +' latency record '+str(len(latency.DelayAvg_map)))
            input = open(inputfilename,'rb')
            stddev = pickle.load(input)
            input.close()
        else:
            logging.info(' The Calc File is not Exist ')
            print 'up'
            return

        sigma=stddev.getSigma(latency.DelayAvg_map[MemberIp])
        logging.info( 'static stddev:' +str(stddev.StdDev))
        logging.info( 'static avg:'+str(stddev.AvgValue))
        logging.info( 'current avg:'+str(latency.DelayAvg_map[MemberIp]))
        logging.info( 'sigma:'+str(sigma))

        if stddev.ActiveStatus == 'Enabled':
            logging.info(' member '+node_ip+':'+node_port+' in enable state')

            if sigma[0] > 4:
               ratio =commands.getstatusoutput('tmsh list ltm pool '+PoolName+'  members {'+MemberIp+'} |grep ratio |grep -v dynamic')
               ratio=ratio[1]
               ratio = ratio.split()
               ratio = ratio[1]

               if sigma[1] == -1:

                    logging.info('offset value is too big,need switch ratio to 10')
                    os.system('tmsh modify ltm pool '+PoolName +' members  modify {'+MemberIp+'  {ratio  10 } }')


               else:
                    logging.info(' offset value is too big,need switch ratio to 1')
                    os.system('tmsh modify ltm pool '+PoolName +' members  modify {'+MemberIp+'  {ratio  1 } }')

               logging.info(' Disable this member static')
               stddev.setStatus('Disabled')
               stddev.setRatio(ratio)
               output = open(inputfilename,'wb')
               pickle.dump(stddev,output)
               output.close()




        else:
            logging.info(' member '+node_ip+':'+node_port+' in disable state')
            if sigma[0] < 2:

                logging.info(' offset value is close to old value ,switch ratio to old value:'+stddev.Ratio)
                os.system('tmsh modify ltm pool '+PoolName +' members  modify {'+MemberIp+'  {ratio  '+stddev.Ratio+' } }')
                logging.info(' Enable this member static')
                stddev.setStatus('Enabled')
                os.system('rm -f '+ltsfilename)
                output = open(inputfilename,'wb')
                pickle.dump(stddev,output)
                output.close()

        print 'up'




    except Exception, e:
       logging.critical(traceback.format_exc())
       print 'up'




if __name__ == '__main__':
    main()

#    print MemberStatFrag.GetMemberStatFrag(MonitorVsIp)

