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

for i in range(10000):
    """

    本项目的public代理
    :return:
    """

    pr = json.loads(requests.get('http://127.0.0.1:6795/get_a_proxy/30', auth=('user', 'mtfy123')).text)


    t_start = time.time()
    try:
        pr = json.loads(random.choice(REDIS_CLIENT.zrevrange('proxy_free', 0, 50)))
        # print(pr)
        # print(pr)

        # https://ydgf.sohu.com/schedule/index.json
        # 'http://www.baidu.com/content-search.xml'
        # https://ydgf.sohu.com/schedule/index.json
        resp = requests.get('https://www.baidu.com', proxies=pr, timeout=5)
        # print(resp.text[:10])
        logger.info(f'成功, 消耗时间 {round(time.time() - t_start, 2)}，  代理是 \033[0;41m{pr}\033[0m')
        suceess_count += 1
        total_request_time += time.time() - t_start
    except Exception as e:
        logger.warning(f'失败, 消耗时间{round(time.time() - t_start, 2)}，  代理是 \033[0;41m{pr}\033[0m')
    total_count += 1
    if i % 10 == 0:
        logger.debug(f'当前请求总次数是 {total_count}， 成功次数是 {suceess_count} ,成功率是 {round((suceess_count / total_count) * 100, 3)}%, '
                     f'平均响应时间 {round(total_request_time / suceess_count, 2)}')


