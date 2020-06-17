import json
import random
import sys
import time
import nb_log
import requests
import traceback
from threading import Lock
import decorator_libs
from threadpool_executor_shrink_able import BoundedThreadPoolExecutor

from proxypool_framework.proxy_pool_config import REDIS_CLIENT

pool = BoundedThreadPoolExecutor(10)
logger = nb_log.LogManager(__name__).get_logger_and_add_handlers(formatter_template=7,log_filename='rate_of_success.log')


suceess_count = 0
total_count = 0
total_request_time = 0

lock_for_count = Lock()

t1 = time.time()


def f1():
    """

    本项目的public代理
    :return:
    """

    pr = json.loads(requests.get('http://127.0.0.1:6795/get_a_proxy/10', auth=('user', 'mtfy123')).text)
    t_start = time.time()
    try:
        # pr = json.loads(random.choice(REDIS_CLIENT.zrevrange('proxy_free', 0, 50)))
        # print(pr)
        # print(pr)

        #https://ydgf.sohu.com/schedule/index.json
        # 'http://www.baidu.com/content-search.xml'
        resp = requests.get('https://ydgf.sohu.com/schedule/index.json', proxies=pr, timeout=20)
        # print(resp.text[:10])
        logger.info(f'成功, 消耗时间 {time.time() - t_start}，  代理是 \033[0;41m{pr}\033[0m')
    except Exception as e:
        logger.warning(f'失败, 消耗时间{time.time() - t_start}，  代理是 \033[0;41m{pr}\033[0m')


def f2():
    """
    自动路由代理
    :return:
    """
    global total_count
    global suceess_count
    global total_request_time

    try:
        # pr = json.loads(random.choice(REDIS_CLIENT.zrevrange('proxy_free', 0, 50)))

        proxies_str = requests.get('http://47.107.99.8:10080/proxy/get_offline_ip',
                                   params={'platform': 'kuaidaili', 'priority': 3},
                                   auth=('user', 'mtfy123')).text
        # print(proxies_str)
        # self.logger.debug(proxies_str)
        pr = json.loads(proxies_str)
        # print(pr)

        # print(pr)
        t_start = time.time()
        resp = requests.get('https://www.baidu.com/content-search.xml', proxies=pr, timeout=20)
        # print(resp.text[:10])
        with lock_for_count:
            suceess_count += 1
            total_request_time += time.time() - t_start
        with lock_for_count:
            if total_count % 100 == 0 :  # 最开始的不打印，原因自己看代码理解为什么。
                print(f'当前总请求 {total_count} ,成功 {suceess_count} ,成功率 {suceess_count / total_count},平均响应时间 {total_request_time / suceess_count}')
    except Exception as e:
        pass
        # print(type(e))
    with lock_for_count:
        total_count += 1


def f3():
    """
    github代理池
    :return:
    """
    global total_count
    global suceess_count
    try:
        # pr = json.loads(random.choice(REDIS_CLIENT.zrevrange('proxy_free', 0, 50)))

        proxies_str = requests.get('http://192.168.199.202:5666/get/',
                                   params={'platform': 'zdaye', 'priority': 3},
                                   auth=('user', 'mtfy123')).text
        # print(proxies_str)
        # self.logger.debug(proxies_str)
        pr1 = json.loads(proxies_str)
        # print(pr1)
        pr = {'https': pr1['proxy']}
        # print(pr)

        # print(pr)
        resp = requests.get('https://www.baidu.com/content-search.xml', proxies=pr, timeout=20)
        # print(resp.text[:10])
        with lock_for_count:
            suceess_count += 1
        with lock_for_count:
            if total_count % 100 == 0:  # 最开始的不打印，原因自己看代码理解为什么。
                print(f'当前总请求 {total_count} ,成功 {suceess_count} ,成功率 {suceess_count / total_count}')
    except Exception as e:
        pass
        # print(type(e))
    with lock_for_count:
        total_count += 1

@decorator_libs.keep_circulating(0.1,block=False)
def show_sucess_rate():
    if total_count % 100 == 0 and total_count:  # 最开始的不打印，原因自己看代码理解为什么。
        print(f'当前总请求 {total_count} ,成功 {suceess_count} ,成功率 {suceess_count / total_count},平均响应时间 {total_request_time / suceess_count}')



for _ in range(100000):
    pool.submit(f1)

pool.shutdown()
print(suceess_count)

print(time.time() - t1)
