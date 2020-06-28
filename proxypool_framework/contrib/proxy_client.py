# coding=utf-8
"""
改版包装requests的Session类，主要使用的是设计模式的代理模式（不是代理ip）,
2、支持3种类型的cookie添加
3、支持长会话，保持cookie状态
4、支持一键设置requests请求重试次数，确保请求成功，默认重试一次。
5、记录下当天的请求到文件，方便统计，同时开放了日志级别设置参数，用于禁止日志。
6、从使用requests修改为使用ProxyClient门槛很低，三方包的request方法和此类的方法入参和返回完全100%保持了一致。


user agent 大全 github  https://github.com/tamimibrahim17/List-of-user-agents/blob/master/user-agent.py
user agent 网址 http://www.useragentstring.com/pages/useragentstring.php?name=Firefox
"""
import json
import random
import copy
import sys
import warnings
from typing import Union
import time
from urllib.parse import quote

from db_libs.redis_lib import redis2_from_url
import requests
import urllib3
# from fake_useragent import UserAgent
from nb_log import LoggerLevelSetterMixin, LoggerMixinDefaultWithFileHandler
from threadpool_executor_shrink_able import ThreadPoolExecutorShrinkAble

from proxypool_framework.contrib.user_agents import pc_ua_lists, mobile_ua_lists

warnings.simplefilter('ignore', category=urllib3.exceptions.InsecureRequestWarning)


class HttpStatusError(Exception):
    def __init__(self, http_status_code):
        super().__init__(f'请求返回的状态码是{http_status_code}')


class ProxyClient(LoggerMixinDefaultWithFileHandler, LoggerLevelSetterMixin):

    def __init__(self, flask_addr='127.0.0.1:6795', redis_url='redis://:@', redis_proxy_key='proxy_free',
                 is_priority_get_proxy_from_redis=True, is_use_proxy=True, ua=None, default_use_pc_ua=True,
                 is_change_ua_every_request=False, random_ua_list: list = None,
                 request_retry_times=2, purpose='',
                 white_list_http_status_code: Union[list, tuple] = (200,)):
        """
        :param flask_addr:
        :param redis_url:
        :param redis_proxy_key:
        :param is_priority_get_proxy_from_redis: 是否优先使用redis。因为也可以从api获取ip。
        :param is_use_proxy: 是否使用代理ip来请求。
        :param ua:
        :param default_use_pc_ua:
        :param is_change_ua_every_request:
        :param random_ua_list:
        :param request_retry_times:
        :param purpose: 请求用途
        :param white_list_http_status_code: 白名单状态码，例如403虽然请求没报错，但状态码不对，可以自动重试。例如假如206是正常现象，可以把206添加到白名单。
        """
        self._flask_addr = flask_addr
        self._redis_url = redis_url
        self._redis_proxy_key = redis_proxy_key
        self._is_priority_get_proxy_from_redis = is_priority_get_proxy_from_redis
        self._is_use_proxy = is_use_proxy

        default_ua = (
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36' if default_use_pc_ua else
            'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Mobile Safari/537.36')
        self._ua = ua if ua else default_ua
        self._is_change_ua_every_request = is_change_ua_every_request
        self._random_ua_list = random_ua_list
        if is_change_ua_every_request and not random_ua_list:
            self._random_ua_list = pc_ua_lists if default_use_pc_ua else mobile_ua_lists
        self.ss = requests.Session()
        self._max_request_retry_times = request_retry_times
        self._white_list_http_status_code = list(white_list_http_status_code)
        self._purpose = purpose
        self.prxoy_from_info = ''
        if is_use_proxy:
            if is_priority_get_proxy_from_redis:
                self.prxoy_from_info = f'从redis {redis_url} {redis_proxy_key} 获取的代理'
            else:
                self.prxoy_from_info = f'从flask {flask_addr}  获取的代理'
        else:
            self.prxoy_from_info = f'设置为了不使用代理'

    def __add_ua_to_headers(self, headers):
        # noinspection PyDictCreation
        if not headers:
            headers = dict()
            headers['user-agent'] = self._ua
        else:
            if 'user-agent' not in headers and 'User-Agent' not in headers:
                headers['user-agent'] = self._ua
        if self._is_change_ua_every_request and self._random_ua_list:
            headers['user-agent'] = random.choice(self._random_ua_list)
        headers.update({'Accept-Language': 'zh-CN,zh;q=0.8'})
        return headers

    def get_cookie_jar(self):
        """返回cookiejar"""
        return self.ss.cookies

    def get_cookie_dict(self):
        """返回cookie字典"""
        return self.ss.cookies.get_dict()

    def get_cookie_str(self):
        """返回cookie字典"""
        cookie_str = ''
        for cookie_item in self.get_cookie_dict().items():
            cookie_str += cookie_item[0] + '=' + cookie_item[1] + ';'
        return cookie_str[:-1]

    def add_cookies(self, cookies: Union[str, dict]):
        """
        :param cookies: 浏览器复制的cookie字符串或字典类型或者CookieJar类型
        :return:
        """
        cookies_dict = dict()
        if not isinstance(cookies, (str, dict,)):
            raise TypeError('传入的cookie类型错误')
        if isinstance(cookies, str):
            cookie_pairs = cookies.split('; ')
            for cookie_pair in cookie_pairs:
                k, v = cookie_pair.split('=', maxsplit=1)
                cookies_dict[k] = v
        if isinstance(cookies, (dict,)):
            cookies_dict = cookies
        self.ss.cookies = requests.sessions.merge_cookies(self.ss.cookies, cookies_dict)

    @staticmethod
    def __get_full_url_with_params(url, params):
        """
        主要是用来在发送请求前记录日志，请求了什么url。
        :param url:
        :param params:
        :return:
        """
        params = {} if params is None else params
        url_params_str = ''
        # print(params)
        for k, v in params.items():
            # print(k,v)
            url_params_str += f'{k}={v}&'
        # url = urllib.parse.quote(url)
        return f'{url}?{quote(url_params_str)}'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # print('关闭close')
        self.ss.close()
        return False

    def get_a_proxy(self):
        proxy_dict = None
        if self._is_use_proxy:
            if self._is_priority_get_proxy_from_redis:
                proxy_dict = json.loads(random.choice(redis2_from_url(self._redis_url).zrevrange('proxy_free', 0, 30)))
            else:
                proxy_dict = json.loads(self.ss.request('get', f'http://{self._flask_addr}/get_a_proxy/30?u=user2&p=pass2', ).text)
            proxy_dict['http'] = proxy_dict['https'].replace('https', 'http')
        # self.logger.debug(proxy_dict)
        return proxy_dict

    # noinspection PyProtectedMember
    def request(self, method: str, url: str, verify: bool = None,
                timeout: Union[int, float, tuple] = (5, 20), params: dict = None,
                headers: dict = None, cookies: dict = None, **kwargs):
        """
        使用指定名字的代理请求,从_proxy_name读取,当请求出错时候轮流使用各种代理ip。
        :param method:
        :param url:
        :param verify:
        :param timeout:
        :param headers:
        :param cookies:
        :param params:  get传参的字典
        :param kwargs :可接受一切requests.request方法中的参数
        :return:
        """
        # self.logger.debug(locals())
        key_word_args = copy.copy(locals())
        key_word_args.pop('self')
        key_word_args.pop('kwargs')
        key_word_args.pop('headers')
        key_word_args.update(kwargs)
        resp = None
        # self.logger.debug('starting {} this url -->  '.format(method) + url)
        # print(key_word_args)
        exception_request = None
        t_start_for_all_retry = time.time()

        # 方向定位到发出request请求的文件行，点击可跳转到该处。
        # 获取被调用函数在被调用时所处代码行数
        line = sys._getframe().f_back.f_lineno
        # 获取被调用函数所在模块文件名
        file_name = sys._getframe(1).f_code.co_filename
        sys.stdout.write(
            f'"{file_name}:{line}"  {time.strftime("%H:%M:%S")}  \033[0;30;47m 这一行触发 RequestClient 发送 {method} 请求此网址 \033[0m {self.__get_full_url_with_params(url, params)} \n')  # 36  93 96 94 101
        headers_replace = self.__add_ua_to_headers(headers)
        for i in range(self._max_request_retry_times + 1):
            t_start = time.time()
            try:
                resp = self.ss.request(**key_word_args, proxies=self.get_a_proxy(), headers=headers_replace)
                time_spend = round(time.time() - t_start, 2)
                resp.time_spend = time_spend
                resp.ts = time_spend  # 简写
                log_str = f'{self._purpose} {self.prxoy_from_info} request响应状态: [{i}  {method}  {resp.status_code}  {time_spend:>3.2f}  {resp.is_redirect}  {resp.text.__len__():>8d}]  ----->\033[0m  {resp.url}\033[0m'
                if resp.status_code in self._white_list_http_status_code:
                    self.logger.debug(log_str)
                else:
                    self.logger.warning(log_str)
                if resp.status_code not in self._white_list_http_status_code and i < self._max_request_retry_times + 1:
                    raise HttpStatusError(resp.status_code)
                if i != 0:
                    pass
                break
            except Exception as e:
                exception_request = e
                if i != self._max_request_retry_times:
                    msg_level = 30
                else:
                    msg_level = 40
                self.logger.log(msg_level,
                                f'{self._purpose} {self.prxoy_from_info}  ProxyClient内部第{i}次请求出错,此次浪费时间[{round(time.time() - t_start, 2)}],'
                                f'{i + 1}次错误总浪费时间为{round(time.time() - t_start_for_all_retry, 2)}，再重试一次，原因是：{type(e)}    {e}')
        if resp is not None:  # 如<Response [404]>也是false,但不是none
            return resp
        else:
            raise exception_request

    def pressure_test(self, *args, threads_num=50, is_print_resp=False, **kwargs):
        """
        压力测试
        :return:
        """
        pool = ThreadPoolExecutorShrinkAble(threads_num)

        def __pressure_test_url():
            resp = self.request(*args, **kwargs)
            if is_print_resp:
                print(resp.text)

        while 1:
            pool.submit(__pressure_test_url)

    def statistic_rate_of_sucess(self):
        suceess_count = 0
        total_count = 0
        total_request_time = 0

        while 1:
            t_start = time.time()
            for j in range(0, self._max_request_retry_times + 1):
                pr = self.get_a_proxy()
                try:
                    resp = requests.get('https://ydgf.sohu.com/schedule/index.json', proxies=pr, timeout=5)
                    self.logger.info(f'重试 {j} 次请求成功, 消耗时间 {round(time.time() - t_start, 2)}，  代理是 \033[0;41m{pr}\033[0m ，结果长度是 {len(resp.text)}')
                    suceess_count += 1
                    total_request_time += time.time() - t_start
                    break
                    # print(resp.text[:10])
                except Exception as e:
                    if j == self._max_request_retry_times:
                        self.logger.warning(f'重试了 {self._max_request_retry_times}次后仍然失败, 消耗时间{round(time.time() - t_start, 2)}， '
                                            f' 代理是 \033[0;41m{pr}\033[0m，错误类型是 {type(e)}')

            total_count += 1
            if total_count % 10 == 0 and total_count:
                self.logger.debug(f'当前请求总次数是 {total_count}， 成功次数是 {suceess_count} ,成功率是 {round((suceess_count / total_count) * 100, 3)}%, '
                                  f'平均响应时间 {round(total_request_time / suceess_count, 2)}')


if __name__ == '__main__':
    # with ProxyClient(is_priority_get_proxy_from_redis=False) as pc:
    #     pc.request('get', 'https://www.baidu.com')
    #     pc.request('get', 'https://www.baidu.com')
    # ProxyClient().pressure_test('get', 'https://www.baidu.com/content-search.xml', threads_num=200, )
    ProxyClient().statistic_rate_of_sucess()
