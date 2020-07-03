import os
import warnings
import json
# noinspection PyUnresolvedReferences
from collections import defaultdict
from functools import wraps
import urllib3
# noinspection PyUnresolvedReferences
import random
from nb_log import LogManager
from multiprocessing import Process
# noinspection PyUnresolvedReferences
from threadpool_executor_shrink_able import BoundedThreadPoolExecutor
import decorator_libs

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from flask import Flask, request, make_response

# noinspection PyUnresolvedReferences
from proxypool_framework.proxy_pool_config import *
from proxypool_framework.functions_of_get_https_proxy_from_websites import *

warnings.simplefilter('ignore', category=urllib3.exceptions.InsecureRequestWarning)
CHECK_PROXY_VALIDITY_URL = 'https://www.baidu.com/content-search.xml'


def create_app():
    app = Flask(__name__)

    if REDIS_CLIENT.exists('proxy_user_config') is False:
        time_begin = int(time.time())
        REDIS_CLIENT.hmset('proxy_user_config', {
            "user": json.dumps(
                {"password": "mtfy123", "max_count_per_day": 99999999, "max_use_seconds": 3600 * 24 * 3650,
                 "use_begin_time": time_begin}),
            "user2": json.dumps(
                {"password": "pass2", "max_count_per_day": 99999999, "max_use_seconds": 3600 * 24 * 3650,
                 "use_begin_time": time_begin}),
            "test": json.dumps(
                {"password": "test", "max_count_per_day": 1000, "max_use_seconds": 3600,
                 "use_begin_time": time_begin}),
        })

    @decorator_libs.FunctionResultCacher.cached_function_result_for_a_time(cache_time=60)
    def get_user_config_from_redis():
        config_dict_bytes = REDIS_CLIENT.hgetall('proxy_user_config')
        print(config_dict_bytes)
        return {k.decode(): json.loads(v) for k, v in config_dict_bytes.items()}

    def auth_deco(v):
        @wraps(v)
        def _auth_deco(*args, **kwargs):
            users_config_dict = get_user_config_from_redis()
            if request.authorization:  # 请求方式如 requests.get('http://127.0.0.1:6795/get_a_proxy/10',auth=('xiaomin','pass123456')
                username = request.authorization.username
                password = request.authorization.password
            else:  # 为了方便浏览器地址栏测试，兼容在？后面传参。
                username = request.args.get('u', None)
                password = request.args.get('p', None)
            if username in users_config_dict and password == users_config_dict[username]['password']:
                if users_config_dict[username]['use_begin_time'] + users_config_dict[username]['max_use_seconds'] >= int(time.time()):
                    return v(*args, **kwargs)
                else:
                    return '免费试用时间已经结束,如需继续使用请联系管理员'
            else:
                print('账号密码不正确')
                return '账号密码不正确'

        return _auth_deco

    @app.route('/get_a_proxy/')
    @app.route('/get_a_proxy/<int:random_num>')
    @auth_deco
    def get_a_proxy(random_num=30):
        """
        :param random_num: 在最后一次检测可用性时间的最接近现在时间的多少个ip范围内随机返回一个ip.数字范围越小，最后检测时间的随机范围越靠近当前时间。
        此代理池通用架构，可以实现超高的检测频率，基本上任何时刻每秒钟都有几十个比当前时间错小一两秒的。比当前时间戳小10秒的有几百个代理。
        :return:
        """
        random_num = 100 if random_num > 100 else random_num  # 最大值100
        proxy_dict = json.loads(random.choice(REDIS_CLIENT.zrevrange(PROXY_KEY_IN_REDIS_DEFAULT, 0, random_num)))
        proxy_dict['http'] = proxy_dict['https'].replace('https', 'http')
        proxy_dict.pop('platform')
        proxy_str = json.dumps(proxy_dict, ensure_ascii=False)
        return proxy_str

    @app.route('/get_m_proxy/')
    @app.route('/get_m_proxy/<int:bulk_num>')
    @auth_deco
    def get_many_proxy(bulk_num=10):
        proxy_list = REDIS_CLIENT.zrevrange(PROXY_KEY_IN_REDIS_DEFAULT, 0, bulk_num)
        proxy_list_hide_platform = list()
        for proxy_item in proxy_list:
            proxy_item_hide_platform = json.loads(proxy_item)
            proxy_item_hide_platform.pop('platform')
            proxy_item_hide_platform['http'] = proxy_item_hide_platform['https'].replace('https', 'http')
            proxy_list_hide_platform.append(proxy_item_hide_platform)
        return json.dumps(proxy_list_hide_platform)

    @app.route('/txt/')
    @auth_deco
    def get_proxy_with_newline():
        """
        Content-Type: text/plain; charset=utf-8
        :return:
        """
        # sep = request.args.get('sep','</br>')
        # return sep.join([json.loads(proxy_str)['https'] for proxy_str in REDIS_CLIENT.zrevrange(PROXY_KEY_IN_REDIS_DEFAULT, 0, request.args.get('num',50))])

        response = make_response('\r\n'.join([json.loads(proxy_str)['https'].replace('https://', '') for proxy_str in REDIS_CLIENT.zrevrange(PROXY_KEY_IN_REDIS_DEFAULT, 0, request.args.get('num', 50))]))
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        return response

    @app.route('/st')
    def statistic_ip_count_by_platform_name():
        platform___ip_count_map = defaultdict(int)
        ip__check_time_map = dict()
        for proxy_str, timestamp in REDIS_CLIENT.zscan_iter(PROXY_KEY_IN_REDIS_DEFAULT, ):
            proxy_dict = json.loads(proxy_str)
            ip__check_time_map[proxy_dict['https']] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
            platform___ip_count_map[proxy_dict['platform']] += 1
        return json.dumps({'platform___ip_count_map': dict(sorted(platform___ip_count_map.items(), key=lambda x: x[1], reverse=True)),
                           'ip__check_time_map': dict(sorted(ip__check_time_map.items(), key=lambda x: x[1], reverse=True))}, ensure_ascii=False, indent=4)

    return app


class ProxyCollector:
    pool_for_check_new = BoundedThreadPoolExecutor(100)
    pool_for_check_exists = BoundedThreadPoolExecutor(200)
    redis_key___has_start_check_exists_proxies_in_database_map = dict()
    logger_for_check_exists = LogManager('ProxyCollector-check_exists').get_logger_and_add_handlers(
        log_filename=f'ProxyCollector-check_exists.log', formatter_template=7)

    @staticmethod
    def check_proxy_validity(proxy_dict: dict):
        # noinspection PyUnusedLocal
        # noinspection PyBroadException
        try:
            # print(proxy_dict)
            requests.get(CHECK_PROXY_VALIDITY_URL, timeout=REQUESTS_TIMEOUT, proxies=proxy_dict, verify=False)
            return True
        except Exception as e:
            # print(e)
            return False

    def __init__(self, function_of_get_new_https_proxies_list_from_website, func_args=tuple(), func_kwargs: dict = None,
                 platform_name='xx平台', redis_key=PROXY_KEY_IN_REDIS_DEFAULT,
                 time_sleep_for_get_new_proxies=60,
                 ):
        """
        :param function_of_get_new_https_proxies_list_from_website: 獲取代理ip列表的函數，使用策略模式。
        :param time_sleep_for_get_new_proxies:
        """
        self.function_of_get_new_https_proxies_list_from_website = function_of_get_new_https_proxies_list_from_website
        self._func_args = func_args
        self._func_kwargs = func_kwargs or {}
        self.platform_name = platform_name
        self._redis_key = redis_key
        self._time_sleep_for_get_new_proxies = time_sleep_for_get_new_proxies
        self.logger = LogManager(f'ProxyCollector-{platform_name}').get_logger_and_add_handlers(
            log_filename=f'ProxyCollector-{platform_name}.log', formatter_template=7)

    def __check_a_new_proxy_and_add_to_database(self, proxy_dict: dict):
        if self.check_proxy_validity(proxy_dict):
            # print(type(proxy_dict))
            self.logger.info(f'新增 {self.platform_name} 代理ip到数据库 {json.dumps(proxy_dict, ensure_ascii=False)}')
            REDIS_CLIENT.zadd(self._redis_key, json.dumps(proxy_dict, ensure_ascii=False), time.time())
        else:
            self.logger.warning(f'新拉取的 {self.platform_name} 平台 代理无效')

    def _check_all_new_proxies(self, pool=None):
        """
        并发检测新代理，有效的入库
        :return:
        """
        pool = pool or self.pool_for_check_new
        exists_num_in_db = REDIS_CLIENT.zcard(self._redis_key)
        if exists_num_in_db < MAX_NUM_PROXY_IN_DB:
            pool.map(self.__check_a_new_proxy_and_add_to_database,
                     [{'https': f'https://{ip}', 'platform': self.platform_name} for ip in
                      self.function_of_get_new_https_proxies_list_from_website(
                          *self._func_args, **self._func_kwargs)])
        else:
            self.logger.critical(
                f'{self._redis_key} 键中的代理ip数量为 {exists_num_in_db},超过了制定阈值 {MAX_NUM_PROXY_IN_DB},此次循环暂时不拉取新代理')

    def __check_a_exists_proxy_and_drop_from_database(self, proxy_dict):
        if not self.check_proxy_validity(proxy_dict):
            self.logger_for_check_exists.warning(f'刪除数据库中失效代理ip {json.dumps(proxy_dict, ensure_ascii=False)}')
            REDIS_CLIENT.zrem(self._redis_key, json.dumps(proxy_dict, ensure_ascii=False))
        else:
            self.logger_for_check_exists.info(f'数据库中的代理ip {json.dumps(proxy_dict, ensure_ascii=False)} 没有失效')
            REDIS_CLIENT.zadd(self._redis_key, json.dumps(proxy_dict, ensure_ascii=False), time.time())  # 更新检测时间。

    def _check_exists_proxies_in_database(self):
        """
        并发删除数据库中的失效代理。上次检测时间离当前超过了指定的秒数，就重新检测。
        :return:
        """
        redis_proxies_list = REDIS_CLIENT.zrangebyscore(self._redis_key, 0, time.time() - MAX_SECONDS_MUST_CHECK_AGAIN)
        self.logger_for_check_exists.debug(f'需要检测的 {self._redis_key} 键中 {MAX_SECONDS_MUST_CHECK_AGAIN} '
                                           f'秒内没检查过的 存量代理数量是 {len(redis_proxies_list)}，总数量是 {REDIS_CLIENT.zcard(self._redis_key)}')
        self.pool_for_check_exists.map(self.__check_a_exists_proxy_and_drop_from_database,
                                       [json.loads(redis_proxy) for redis_proxy in redis_proxies_list])

    @decorator_libs.synchronized
    def work(self):
        if not self.__class__.redis_key___has_start_check_exists_proxies_in_database_map.get(self._redis_key, False):
            self.__class__.redis_key___has_start_check_exists_proxies_in_database_map[self._redis_key] = True
            self.logger.warning(f'启动对数据库中 {self._redis_key} zset键 已有代理的检测')
            decorator_libs.keep_circulating(1, block=False)(
                self._check_exists_proxies_in_database)()
        decorator_libs.keep_circulating(self._time_sleep_for_get_new_proxies, block=False)(
            self._check_all_new_proxies)()


if __name__ == '__main__':
    """初次运行时候由于redis中没有代理ip做爬取第三方网站的引子，会被免费代理网站反爬，ip在前几分钟内会比较少。之后会增多，耐心等待。
    
    启动方式种类：
    1)
    export PYTHONPATH=/codes/proxypool_framework （指的是你的代码的位置，codes换成你的位置） # 这个原理就不需解释了，不知道PYTHONPATH是什么就太low了。
    
    python proxy_collector.py REDIS_URL=redis:// MAX_NUM_PROXY_IN_DB=500 MAX_SECONDS_MUST_CHECK_AGAIN=12 REQUESTS_TIMEOUT=6 FLASK_PORT=6795 PROXY_KEY_IN_REDIS_DEFAULT=proxy_free
    或者在 proxy_pool_config.py 文件中把配置写好，就不需要命令行来传参了。直接 python proxy_collector.py
    
    2)pycharm中打开此项目，可以直接右键点击run proxy_collector.py
    
    3)pip install proxypool_framework
    python -m proxypool_framework.proxy_collector REDIS_URL=redis:// MAX_NUM_PROXY_IN_DB=500 MAX_SECONDS_MUST_CHECK_AGAIN=12 REQUESTS_TIMEOUT=6 FLASK_PORT=6795 PROXY_KEY_IN_REDIS_DEFAULT=proxy_free
    """
    # os.system(f"""ps -aux|grep FLASK_PORT={FLASK_PORT}|grep -v grep|awk '{{print $2}}' |xargs kill -9""")  # 杀死端口，避免ctrl c关闭不彻底，导致端口被占用。

    """启动代理池自动持续维护"""
    ProxyCollector(get_iphai_proxies_list, platform_name='iphai', time_sleep_for_get_new_proxies=70, ).work()
    ProxyCollector(get_from_seofangfa, platform_name='seofangfa', time_sleep_for_get_new_proxies=70, ).work()
    for p in range(1, 3):
        ProxyCollector(get_https_proxies_list_from_xici_by_page, (p,), platform_name='xici',
                       time_sleep_for_get_new_proxies=70, redis_key='proxy_xici').work()  # 这个是演示此框架是如何一次性启动维护多个代理池的,通过设置不同的redis_key来实现。
        ProxyCollector(get_89ip_proxies_list, (p,), platform_name='89ip', time_sleep_for_get_new_proxies=70, ).work()
    for p in range(1, 6):
        ProxyCollector(get_from_superfastip, (p,), platform_name='superfastip', time_sleep_for_get_new_proxies=65).work()
    for area in range(1, 30):  # 有30个城市区域
        ProxyCollector(get_66ip_proxies_list, func_kwargs={'area': area}, platform_name='66ip', time_sleep_for_get_new_proxies=300, ).work()
    for p in range(1, 20):
        if p < 5:
            time_sleep_for_get_new_proxiesx = 30
        else:
            time_sleep_for_get_new_proxiesx = 300
        ProxyCollector(get_https_proxies_list_from_xila_https_by_page, func_args=(p,), platform_name='西拉', time_sleep_for_get_new_proxies=time_sleep_for_get_new_proxiesx, ).work()
        ProxyCollector(get_https_proxies_list_from_xila_gaoni_by_page, func_kwargs={'p': p}, platform_name='西拉', time_sleep_for_get_new_proxies=time_sleep_for_get_new_proxiesx, ).work()
        ProxyCollector(get_nima_proxies_list, (p, 'gaoni'), platform_name='nima', time_sleep_for_get_new_proxies=time_sleep_for_get_new_proxiesx).work()
        ProxyCollector(get_nima_proxies_list, (p, 'https'), platform_name='nima', time_sleep_for_get_new_proxies=time_sleep_for_get_new_proxiesx).work()
        ProxyCollector(get_from_jiangxianli, func_kwargs={'p': p}, platform_name='jiangxianli', time_sleep_for_get_new_proxies=time_sleep_for_get_new_proxiesx).work()

    """启动api"""
    http_server = HTTPServer(WSGIContainer(create_app()))
    http_server.listen(FLASK_PORT)
    IOLoop.instance().start()
