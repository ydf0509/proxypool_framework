import copy
import sys
import nb_log  # noqa
import redis2  # pip install redsi2

# 可以直接修改这里的值为自己的最终值，也可以使用命令行方式覆盖这里的配置。命令行是为了可以快速的不修改代码配置而进行方便质量数量调优,和不改配置，多次启动分别生成优质代理池、普通代理池。
REDIS_URL = 'redis://:@'  # redis的url连接方式百度，可以指定db和ip和密码。
MAX_NUM_PROXY_IN_DB = 1000  # redis中存在超过这个代理数量后，将不再拉取新代理，防止检测存量ip消耗资源过多。

"""代理池是sorted set结构，键是ip,值是该ip最后一次的检测时间戳。一轮一轮的扫描，检测到存量代理ip的最后一次检测时间离现在超过这个时间就重新检测，否则此轮不检测此代理，
MAX_SECONDS_MUST_CHECK_AGAIN 的值要适当，过大会导致检测不及时，取出来后使用时成功率变低；过小会导致检测存量代理ip的密度过大，当存量代理太多的时候，会导致cpu消耗高。

MAX_SECONDS_MUST_CHECK_AGAIN = 2 REQUESTS_TIMEOUT = 1， 则会导致数据库检测及时，并且都是优质代理ip，但存量数量会有所减少（但数量还是秒杀任意收费代理），成功率和响应时间很好。
MAX_SECONDS_MUST_CHECK_AGAIN = 10 REQUESTS_TIMEOUT = 5， 这个是比较均衡的配置，兼容数量和质量。
MAX_SECONDS_MUST_CHECK_AGAIN = 30 REQUESTS_TIMEOUT = 10， 这个可以造成数据库中存量ip非常多，但有些代理ip响应时间长，随机使用成功率也会有所降低。

MAX_SECONDS_MUST_CHECK_AGAIN = 1 REQUESTS_TIMEOUT = 40，这种配置就相当不好了，会造成存量大质量差，但又想检测密度高，会造成cpu消耗高。
建议MAX_SECONDS_MUST_CHECK_AGAIN是REQUESTS_TIMEOUT的2倍。

"""
MAX_SECONDS_MUST_CHECK_AGAIN = 2
REQUESTS_TIMEOUT = 1  # 请求响应时间超过这个值，视为废物代理。
FLASK_PORT = 6795  # 代理ip获取的接口。
PROXY_KEY_IN_REDIS_DEFAULT = 'proxy_free' # 默认的redis sorted set键，指的是如果你不在ProxyCollector实例化时候亲自指定键的名字（主要是为了一次启动实现维护多个redis代理池）。

# python util.py REDIS_URL=redis://:123456@ MAX_NUM_PROXY_IN_DB=500 MAX_SECONDS_MUST_CHECK_AGAIN=12 REQUESTS_TIMEOUT=6 FLASK_PORT=6795 PROXY_KEY_IN_REDIS=proxy_free
for para in sys.argv[1:]:
    print(f'配置项:  {para}')
    config_name = para.split('=')[0]
    if config_name in ['REDIS_URL','PROXY_KEY_IN_REDIS_DEFAULT']:
        globals()[config_name] = para.split('=')[1]
    if config_name in ['MAX_NUM_PROXY_IN_DB', 'MAX_SECONDS_MUST_CHECK_AGAIN', 'REQUESTS_TIMEOUT', 'FLASK_PORT']:
        globals()[config_name] = int(para.split('=')[1])

globals_copy = copy.copy(globals())
for g_var in globals_copy:
    if g_var.isupper():
        print(f'最终配置是 {g_var} : {globals()[g_var]}')

REDIS_CLIENT = redis2.from_url(REDIS_URL)
REDIS_CLIENT.ping()  # 测试账号密码错误没有。
