import json
import random
import sys
import time
import nb_log
import requests
from threadpool_executor_shrink_able import BoundedThreadPoolExecutor

from proxypool_framework.proxy_pool_config import REDIS_CLIENT

pool = BoundedThreadPoolExecutor(10)
logger = nb_log.LogManager(__name__).get_logger_and_add_handlers(formatter_template=7, log_filename='rate_of_success.log')

suceess_count = 0
total_count = 0
total_request_time = 0

def test(max_retry=0):
    global  suceess_count
    global total_count
    global  total_request_time

    t_start = time.time()
    for j in range(0,max_retry +1):
        pr = json.loads(requests.get('http://127.0.0.1:6795/get_a_proxy/30', auth=('user', 'mtfy123')).text)  # 接口方式
        # pr = json.loads(random.choice(REDIS_CLIENT.zrevrange('proxy_free', 0, 50)))  # 数据库直接取


        try:
            # print(pr)
            # print(pr)
            # https://ydgf.sohu.com/schedule/index.json
            # 'http://www.baidu.com/content-search.xml'
            # https://ydgf.sohu.com/schedule/index.json
            resp = requests.get('https://ydgf.sohu.com/schedule/index.json', proxies=pr, timeout=5)
            logger.info(f'重试 {j} 次请求成功, 消耗时间 {round(time.time() - t_start, 2)}，  代理是 \033[0;41m{pr}\033[0m ，结果长度是 {len(resp.text)}')
            suceess_count += 1
            total_request_time += time.time() - t_start
            break
            # print(resp.text[:10])
        except Exception as e:
            if j == max_retry:
                logger.warning(f'重试了 {max_retry}次后仍然失败, 消耗时间{round(time.time() - t_start, 2)}，  代理是 \033[0;41m{pr}\033[0m，错误类型是 {type(e)}')

    total_count += 1
    if total_count % 10 == 0 and total_count:
        logger.debug(f'当前请求总次数是 {total_count}， 成功次数是 {suceess_count} ,成功率是 {round((suceess_count / total_count) * 100, 3)}%, '
                     f'平均响应时间 {round(total_request_time / suceess_count, 2)}')


for i in range(1,10000):
    test(max_retry=2)


