# proxypool_framework 

proxypool_framework 是通用ip代理池架构 + 内置的20+ 个免费代理ip网站爬取函数。


```
十分方便扩展各种免费和收费的代理池维护，具有高性能和高并发检测。

只要写5行代理ip解析函数，传给ProxyCollector类，运行work方法，就可以循环执行拉取新代理ip并检测入库，
同时按最后一次的检测时间戳,重新检测超过指定时间的存量代理ip

代理ip池使用的是 redis的sortedset结构，键是代理ip，评分是检测时候的时间戳。

可以一键 将多个网站维护到一个代理池，也可以维护多个不同的redis键代理池。
```   

### 文件作用介绍
```
functions_of_get_https_proxy_from_websites.py 
是从各个网站或付费api获取代理ip的爬取函数大全。

proxy_collector.py 
1）是自动维护代理池,是万能通用的代理池。可以用于任意免费平台或者收费平台进行代理池维护。
2）启动一个web接口，/get_a_proxy接口返回一个代理ip。/get_a_proxy后面接的数字为最近检测时候的n个代理中随机返回一个，数字越小范围越小质量越好。 

proxy_pool_config.py 
代理池配置,可以写在文件中也可以用python命令参数传参方式。

tests/test_check_proxy_pool_public_rate_of_success.py 
是大规模检测代理池中的ip访问百度的成功率统计。
```