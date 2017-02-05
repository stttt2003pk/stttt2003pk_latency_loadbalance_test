# stttt2003pk_latency_loadbalance

## Introduction(For Study)

本方案主要描述在双活数据中心当中，在第二中心应用服务器访问第一中心数据库服务器存在固定延迟的情况，如何通过F5 iRule特性，实时计算服务器延迟，并实服务器流量分配比例跟随服务器延迟进行实时动态调整。

在正常场景下，主数据中心DB处于Active状态，此时主中心的APP访问DB速度比较快，备份数据中心连接主中心的DB由于存在广域传输延迟，访问速度比较慢，由于需要保证主备中心的应用都处于可用状态，在备中心APP也需要对外提供服务，为在访问体验和高可用性之间进行平衡，日常流量的1/10（暂定）通过F5发向备中心APP，其他流量发往主中心，该步骤可以通过BIGIP的比例负载均衡算法实现，如下图：

![](https://raw.github.com/stttt2003pk/stttt2003pk_latency_loadbalance_test/master/screenshot/ag1.png)

在数据库从主中心切到备中心的情况下，延迟情况出现逆转，备中心的APP延迟较低，主中心的延迟较高，此时BIGIP需要将更多的流量发送给备中心，如下图：

![](https://raw.github.com/stttt2003pk/stttt2003pk_latency_loadbalance_test/master/screenshot/ag2.png)

传统做法为找到受DB切换影响的所有业务进行手工一一调整，该做法缺点明显：

（1）配置业务量大，响应时间慢，业务情况紧急，需要短时间内调整完毕，否则严重影响业务
（2）容易出现配置缺失和错误，一个数据库涉及到的应用会非常多，在短时间内下进行大量的配置手工调整很可能造成配置错漏。

考虑到双中心出现数据库切换的场景，对于双活非等比例的APP，F5可以根据iRule和F5自定义健康检查EAV来实现自动化的、基于延迟的动态比率负载均衡算法，来实现该场景下流量的反转。

## Deployment and Pre-operaton-contact

可阅读doc文档和相关数据，希望获得相关资料可以联系414150392@qq.com

## Theory

* 通过提供延迟的api获取延迟信息(实验中的api是由f5计算每个连接的开始结束时间，通过irule计算开始和结束时间获得的)
* 获得延迟数据后通过二进制cPickle进行数据的存储和计算(另外一个版本是通过记录csv文件进行计算)
* 判断延迟的相关情况进行相关的自动化调度

## Need To Solved

* cPickle在记录文档条目达到一定数量后会进行重置，以往的延迟数据会丢失
* 需要有更可靠的存储延迟数据并且进行大量计算的机制提高效率
