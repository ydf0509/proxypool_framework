# proxy_pool_public 

proxy_pool_public是通用ip代理池架构 + 内置的10个免费代理ip网站爬取函数。

proxy_pool_public文件夹是独立的代理池，和整个项目项目其他文件夹没有互相调用。

```
十分方便扩展各种免费和收费的代理池维护，具有高性能和高并发检测。

只要写5行代理ip解析函数，传给ProxyCollector类，运行work方法，就可以循环执行拉取新代理ip并检测入库，
同时按最后一次的检测时间戳,重新检测超过指定时间的存量代理ip

代理ip池使用的是 redis的sortedset结构，键是代理ip，评分是检测时候的时间戳。

可以一键 将多个网站维护到一个代理池，也可以维护多个不同的redis键代理池。
```   

### 文件作用介绍
```
fnctions_of_get_https_proxy__from_websites.py 
是从各个网站或付费api获取代理ip的解析函数大全。

proxy_collector.py 
1）是自动维护代理池,是万能通用的代理池。可以用于任意免费平台或者收费平台进行代理池维护。
2）启动一个web接口，返回一个代理ip。/get_a_proxy后面接的数字为最近检测时候的n个代理中随机返回一个，数字越小范围越小质量越好。 

proxy_pool_config.py 
代理池配置。

tests/test_check_proxy_pool_public_rate_of_success.py 
是大规模检测代理池中的ip访问百度的成功率统计。
```