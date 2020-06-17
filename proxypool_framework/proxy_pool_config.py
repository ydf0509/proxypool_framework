import copy
import sys
import nb_log  # noqa
import redis2  # pip install redsi2

# 可以直接修改这里的值为自己的最终值，也可以使用命令行方式覆盖这里的配置。
REDIS_URL = 'redis://:123456@'  # redis的url连接方式百度，可以指定db和ip。
MAX_NUM_PROXY_IN_DB = 1000  # redis中存在超过这个代理数量后，将不再拉取新代理，防止检测存量ip消耗资源过多。

"""代理池是sorted set结构，键是ip,值是该ip最后一次的检测时间戳。一轮一轮的扫描，检测到存量代理ip的最后一次检测时间离现在超过这个时间就重新检测，否则此轮不检测此代理，
MAX_SECONDS_MUST_CHECK_AGAIN 的值要适当，过大会导致检测不及时，取出来后使用时成功率变低；过小会导致检测存量代理ip的密度过大，当存量代理太多的时候，会导致cpu消耗高。"""
MAX_SECONDS_MUST_CHECK_AGAIN = 1
REQUESTS_TIMEOUT = 1  # 请求响应时间超过这个值，视为废物代理。
FLASK_PORT = 6795  # 代理ip获取的接口。

# python util.py REDIS_URL=redis// MAX_NUM_PROXY_IN_DB=500 MAX_SECONDS_MUST_CHECK_AGAIN=12 REQUESTS_TIMEOUT=6 FLASK_PORT=6796
for para in sys.argv[1:]:
    print(f'配置项:  {para}')
    config_name = para.split('=')[0]
    if config_name == 'REDIS_URL':
        globals()[config_name] = para.split('=')[1]
    if config_name == 'MAX_NUM_PROXY_IN_DB':
        globals()[config_name] = min(int(para.split('=')[1]), 1000)
    if config_name == 'MAX_SECONDS_MUST_CHECK_AGAIN':
        globals()[config_name] = max(int(para.split('=')[1]), 10)
    if config_name == 'REQUESTS_TIMEOUT':
        globals()[config_name] = max(int(para.split('=')[1]), 5)
    if config_name == 'FLASK_PORT':
        globals()[config_name] = int(para.split('=')[1])

globals_copy = copy.copy(globals())
for g_var in globals_copy:
    if g_var.isupper():
        print(f'最终配置是 {g_var} : {globals()[g_var]}')

REDIS_CLIENT = redis2.from_url(REDIS_URL)
REDIS_CLIENT.ping()  # 测试账号密码错误没有。
