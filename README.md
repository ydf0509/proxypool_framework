# proxypool_framework 

proxypool_framework 是通用ip代理池架构 + 内置的20+ 个免费代理ip网站爬取函数。
从ip数量、ip质量、代理池实现本身的难度和代码行数、代理池扩展平台需要的代码行数和难度、配置方式、代理检测设计算法，
是py史上最强的代理池，欢迎对比任意项目代理池项目，如果这不是最强的，可以写出理由反驳，并贴出更好代码的地址。

使用方式如下，安装pip包，然后执行python -m proxypool_framework.proxy_collector 接一大串自定义的配置。（也可以拉取git使用）

pip install proxypool_framework

python -m proxypool_framework.proxy_collector REDIS_URL=redis:// 
MAX_NUM_PROXY_IN_DB=500 MAX_SECONDS_MUST_CHECK_AGAIN=10 REQUESTS_TIMEOUT=5 FLASK_PORT=6795 PROXY_KEY_IN_REDIS_DEFAULT=proxy_free 

### 关于免费代理
```
关于免费代理，免费都是垃圾的论断，是由于被xici这类型的网站坑惨了，只弄过xici，然后发现可用数量比例低，响应时间大，接得出结论免费都是垃圾。
为什么总是要用xici这种实验，是由于基础代码扩展性太差，导致没时间测试验证。代码写好了，验证一个平台就只需要3分钟了。
目前验证了20个平台，得出结论是xici是中等网站，比xici更垃圾的也有一堆网站。但至少发现了有3个平台，每1个平台的可用数量都是xici的30倍以上。

这种方式的代理池数量秒杀任意收费代理，质量超过大部分收费代理（可以通过参数配置调优，来控制数量和质量的平衡）。
```


### 设计思路
```
对于主流程相同，但其中某一个环节必须不同的项目代码布局，都用通用的设计思路，完全不需要设计规划打草稿，直接敲键盘就是了。
对于这种项目，如果学了设计模式，就很容易轻松不懂大脑就能设计。

设计这种项目主要有两种大的方向:
一种是使用模板模式，模板基类实现主流程，空缺一个必须被继承的方法，然后各个扩展平台只需要继承实现那个方法就可以了。这是继承。
另一种是使用策略模式，Context类实现业务主流程，接受一个策略类(也可以是策略函数)，context对象的运行随着策略类（策略函数）的不同而表现不同。
这两种方式都能很好的轻松节约流程相似的代码，只需要写不相同部分的代码。本项目使用的是第二种是策略模式，扩展品台可以采用喜闻乐见的面向过程函数编程。

设计ProxyCollector类和测试需要2小时，然后扩展一个代理平台由于只需要写一个函数3行代码，如果一个函数花费5分钟，这需要100分钟扩展20个平台。

```

### 介绍。
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

tests/test_rate_of_success.py 
是大规模统计代理池中的ip访问互联网的成功率统计。
```

### 三种启动方式
```
初次运行时候由于redis中没有代理ip做爬取第三方网站的引子，会被免费代理网站反爬，ip在前几分钟内会比较少。之后会增多，耐心等待。
    
启动方式种类：
1)
export PYTHONPATH=/codes/proxypool_framework （指的是你的代码的位置，codes换成你的位置） # 这个原理就不需解释了，不知道PYTHONPATH是什么就太low了。

python proxy_collector.py REDIS_URL=redis:// MAX_NUM_PROXY_IN_DB=500 MAX_SECONDS_MUST_CHECK_AGAIN=12 REQUESTS_TIMEOUT=6 FLASK_PORT=6795 PROXY_KEY_IN_REDIS_DEFAULT=proxy_free
或者在 proxy_pool_config.py 文件中把配置写好，就不需要命令行来传参了。直接 python proxy_collector.py

2)pycharm中打开此项目，可以直接右键点击run proxy_collector.py

3)pip install proxypool_framework
python -m proxypool_framework.proxy_collector REDIS_URL=redis:// MAX_NUM_PROXY_IN_DB=500 MAX_SECONDS_MUST_CHECK_AGAIN=12 REQUESTS_TIMEOUT=6 FLASK_PORT=6795 PROXY_KEY_IN_REDIS_DEFAULT=proxy_free
 
也可以分两次启动，指定不同的redis默认键和flask ，
弄一个 MAX_SECONDS_MUST_CHECK_AGAIN  REQUESTS_TIMEOUT 时间小的启动配置,生成优质代理池默认维护在proxy1键中，数量少，成功率高。
再启动一个 MAX_SECONDS_MUST_CHECK_AGAIN  REQUESTS_TIMEOUT 时间大的启动配置,生成中等代理池默认维护在proxy2键中，数量多，成功率低。


启动后可以访问127.0.0.1:6795（指定的端口号），有多个api接口
http://127.0.0.1:6795/get_a_proxy/30?u=user2&p=pass2  #指得是从最接近现在的检测时间的30个代理中随机返回一个。
```

### 配置说明
```
# 可以直接修改这里的值为自己的最终值，也可以使用命令行方式覆盖这里的配置。命令行是为了可以快速的不修改代码配置而进行方便质量数量调优,和不改配置，多次启动分别生成优质代理池、普通代理池。
REDIS_URL = 'redis://:@'  # redis的url连接方式百度，可以指定db和ip和密码。
MAX_NUM_PROXY_IN_DB = 1000  # redis中存在超过这个代理数量后，将不再拉取新代理，防止检测存量ip消耗资源过多。

"""代理池是sorted set结构，键是ip,值是该ip最后一次的检测时间戳。一轮一轮的扫描，检测到存量代理ip的最后一次检测时间离现在超过这个时间就重新检测，否则此轮不检测此代理，
MAX_SECONDS_MUST_CHECK_AGAIN 的值要适当，过大会导致检测不及时，取出来后使用时成功率变低；过小会导致检测存量代理ip的密度过大，当存量代理太多的时候，会导致cpu消耗高。

如果使 MAX_SECONDS_MUST_CHECK_AGAIN = 2 REQUESTS_TIMEOUT = 1， 则会导致数据库检测及时，并且都是优质代理ip，但存量数量会有所减少（但数量还是秒杀任意收费代理），成功率和响应时间很好。
如果使 MAX_SECONDS_MUST_CHECK_AGAIN = 10 REQUESTS_TIMEOUT = 5， 这个是比较均衡的配置，兼容数量和质量。
如果使 MAX_SECONDS_MUST_CHECK_AGAIN = 18 REQUESTS_TIMEOUT = 10， 这个可以造成数据库中存量ip多，但有些代理ip响应时间长，随机使用成功率也会有所降低。
如果使 MAX_SECONDS_MUST_CHECK_AGAIN = 30 REQUESTS_TIMEOUT = 20， 这样数量非常多。

如果使 MAX_SECONDS_MUST_CHECK_AGAIN = 1 REQUESTS_TIMEOUT = 40，这种配置就相当不好了，会造成存量大质量差，但又想检测密度高，会造成cpu消耗高。
建议MAX_SECONDS_MUST_CHECK_AGAIN是REQUESTS_TIMEOUT的 1-2 倍，可以根据自己要数量大自己重试还是实时必须响应速度快进行不同的配置调优。

"""
MAX_SECONDS_MUST_CHECK_AGAIN = 2
REQUESTS_TIMEOUT = 1  # 请求响应时间超过这个值，视为废物代理。
FLASK_PORT = 6795  # 代理ip获取的接口
PROXY_KEY_IN_REDIS_DEFAULT = 'proxy_free' # 默认的redis sorted set键，指的是如果你不在ProxyCollector实例化时候亲自指定键的名字（主要是为了一次启动实现维护多个redis代理池）。
```


### 代理池维护的图片
```
代理池是sorted set结构，元素是代理ip本身，评分是该代理ip的最后一次的检测时间。

流程是：

1）有专门的n个独立线程去监控每个代理平台的页面，同时支持了分页监控。按照ProxyCollector对象的设置的时间来进行多久重新拉取一次代理ip，解析得到代理ip列表。

2）使用了专门的线程池检测解析得到的代理ip列表，有效的跟新时间戳放到数据库，无效的丢弃。

3）对于存量ip，检测完一轮后，休息1秒，然后进行下一轮扫描需要被重新检测的代理ip，有专门的线程池检测存量代理ip。
如果一个存量代理的最后一次检测时间与当前时间差超过了 MAX_SECONDS_MUST_CHECK_AGAIN 则会重新检测，
如果检测没有失效，则更新检测的时间戳为当前时间；如果检测失效了则删除。请求检测的requests timeout时间是使用 REQUESTS_TIMEOUT。
一直高速循环检测。

```
![Image text](https://i.niupic.com/images/2020/06/18/8hbZ.png)


### 随机统计检测代理池的质量
```
这是设置 MAX_SECONDS_MUST_CHECK_AGAIN=2 REQUESTS_TIMEOUT=1 配置的代理池维护的，然后取出来的随机测试结果。
可以发现平均响应时间是1.5秒，只请求1次不做重试就成功的概率是98.5%。
如果重试两次，可以保证成功率达到99.9%，这成功率足够可以秒杀任意收费代理。

python -m proxypool_framework.proxy_collector REDIS_URL=redis:// MAX_NUM_PROXY_IN_DB=500 MAX_SECONDS_MUST_CHECK_AGAIN=2 REQUESTS_TIMEOUT=1 FLASK_PORT=6795 
```
![Image text](https://i.niupic.com/images/2020/06/18/8hbY.png)



