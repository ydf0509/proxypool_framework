# noinspection PyUnresolvedReferences
import json
# noinspection PyUnresolvedReferences
import random
from functools import wraps
import re
import time
from typing import List
# noinspection PyUnresolvedReferences
import nb_log
from threadpool_executor_shrink_able import BoundedThreadPoolExecutor
import requests

from proxypool_framework.proxy_pool_config import REDIS_CLIENT

logger_error_for_pull_ip = nb_log.LogManager('logger_error_for_pull_ip').get_logger_and_add_handlers(log_filename='logger_error_for_pull_ip.log')
logger_normol_for_pull_ip = nb_log.LogManager('logger_normol_for_pull_ip').get_logger_and_add_handlers(log_filename='logger_normol_for_pull_ip.log')


def _request_use_proxy(method, url, headers=None):
    """
    有些代理获取网站本身就反扒，这样来请求。
    :param method:
    :param url:
    :param headers:
    :return:
    """
    headers = headers or {}
    if 'User-Agent' not in headers:
        headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko)'
    exceptx = None
    for i in range(10):
        try:
            proxy_list_in_db = REDIS_CLIENT.zrevrange('proxy_free', 0, 50)
            if not proxy_list_in_db:
                logger_error_for_pull_ip.warning('proxy_free 键是空的，将不使用代理ip请求三方代理网站')
                proxies = None
            else:
                proxies_str = random.choice(proxy_list_in_db)
                proxies = json.loads(proxies_str)
                proxies['http'] = proxies['https'].replace('https', 'http')
            if i % 2 == 0:
                proxies = None
            return requests.request(method, url, headers=headers, proxies=proxies)
        except Exception as e:
            time.sleep(1)
            exceptx = e
            # print(e)

    raise IOError(f'请求10次了还错误 {exceptx}')


def _check_ip_list(proxy_list: List[str]):
    print(proxy_list)

    def __check_a_ip_str(proxy_str):
        proxies = {'https': f'https://{proxy_str}', 'http': f'http://{proxy_str}'}
        try:
            requests.get('https://www.baidu.com/content-search.xml', proxies=proxies, timeout=10, verify=False)
            print(f'有效 {proxies}')
        except Exception as e:
            print(f'无效 {proxies} {type(e)}')

    pool = BoundedThreadPoolExecutor(50)
    [pool.submit(__check_a_ip_str, pr) for pr in proxy_list]


def _ensure_proxy_list_is_not_empty_deco(fun):
    """
    亲测有时候页面请求没报错，但解析为空，但换代理ip请求可以得到ip列表。
    :param fun:
    :return:
    """

    @wraps(fun)
    def __ensure_proxy_list_is_not_empty_deco(*args, **kwargs):
        for i in range(7):
            result = fun(*args, **kwargs)
            if result:
                if i != 0:
                    pass
                    logger_error_for_pull_ip.error(f'第 {i} 次  {fun.__name__} 入参 【{args} {kwargs}】 获取代理ip列表才正常')
                logger_normol_for_pull_ip.debug(f'第 {i} 次  {fun.__name__} 入参 【{args} {kwargs}】 获取代理ip列表正常,个数是   {len(result)}')
                return result
            else:
                time.sleep(1)
        logger_error_for_pull_ip.error(f'重试了 {7} 次  {fun.__name__} 入参 【{args} {kwargs}】 获取代理ip失败，请检查代理网站有无反扒或网站有无改版')
        return []

    return __ensure_proxy_list_is_not_empty_deco


@_ensure_proxy_list_is_not_empty_deco
def get_https_proxies_list_from_xici_by_page(p=1):
    """
    十分垃圾，中等偏下。
    :param p:
    :return:
    """
    resp = _request_use_proxy('get', f'https://www.xicidaili.com/wn/{p}')
    ip_port_list = re.findall(r'alt="Cn" /></td>\s*?<td>(.*?)</td>\s*?<td>(.*?)</td>', resp.text)
    return [f'{ip_port[0]}:{ip_port[1]}' for ip_port in ip_port_list]


@_ensure_proxy_list_is_not_empty_deco
def get_https_proxies_list_from_xila_https_by_page(p=1):
    """
    史上最好的免费代理网站
    :param p:
    :return:
    """
    resp = _request_use_proxy('get', f"http://www.xiladaili.com/https/{p}")
    return re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}", resp.text)


@_ensure_proxy_list_is_not_empty_deco
def get_https_proxies_list_from_xila_gaoni_by_page(p=1):
    # 史上最好的免费代理网站
    resp = _request_use_proxy('get', f"http://www.xiladaili.com/gaoni/{p}")
    return re.findall(r"<td>(.*?)</td>\s*?<td>.*?HTTPS代理</td>", resp.text)


def get_89ip_proxies_list(p=1, ):
    """
    抓的可用性代理不到10%
    :param p:

    :return:
    """
    resp = _request_use_proxy('get', f'http://www.89ip.cn/index_{p}.html')
    ip_port_list = re.findall(r'<tr>\s*?<td>\s*?(.*?)</td>\s*?<td>\s*?(.*?)</td>', resp.text)
    return [f'{"".join(ip.split())}:{"".join(port.split())}' for ip, port in ip_port_list]


def get_ip3366_proxies_list(p=1, ):
    """
    抓的https可用性代理可用性为0
    :param p:

    :return:
    """
    resp = _request_use_proxy('get', f'http://www.ip3366.net/?stype=1&page={p}')
    ip_port_list = re.findall(
        r'''<tr>\s*?<td>(.*?)</td>\s*?<td>(.*?)</td>\s*?<td>.*?</td>\s*?<td>HTTPS</td>\s*?<td>GET, POST</td>''',
        resp.content.decode('gbk'), )
    return [f'{"".join(ip.split())}:{"".join(port.split())}' for ip, port in ip_port_list]


def get_kuaidailifree_proxies_list(p=1, ):
    """
    抓的快带理免费代理可用性为1%
    :param p:

    :return:
    """
    resp = _request_use_proxy('get', f'https://www.kuaidaili.com/free/inha/{p}/')
    ip_port_list = re.findall(r'''<tr>\s*?<td data-title="IP">(.*?)</td>\s*?<td data-title="PORT">(.*?)</td>''',
                              resp.text, )
    return [f'{"".join(ip.split())}:{"".join(port.split())}' for ip, port in ip_port_list]


def get_66ip_proxies_list(area=1, ):
    """
    抓的66免费代理，无效198 ，有效9
    :param area:城市，1到30

    :return:
    """
    resp = _request_use_proxy('get', f'http://www.66ip.cn/areaindex_{area}/1.html')
    ip_port_list = re.findall(r'''<tr><td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td><td>(\d+)</td>''', resp.text, )
    return [f'{"".join(ip.split())}:{"".join(port.split())}' for ip, port in ip_port_list]


def get_iphai_proxies_list():
    """
    抓的iphai代理，有效10，无效20

    :return:
    """
    resp = _request_use_proxy('get', f'http://www.iphai.com')
    ip_port_list = re.findall(r'''<tr>\s*?<td>\s*?(.*?)</td>\s*?<td>\s*?(.*?)</td>[\s\S]*?</tr>''', resp.text, )
    return [f'{"".join(ip.split())}:{"".join(port.split())}' for ip, port in ip_port_list]


# noinspection PyUnusedLocal
def get_mimvp_proxies_list(p, ):
    """
    抓的米扑代理，端口是图片。懒的搞。

    :return:
    """
    return []


def get_kxdaili_proxies_list(p=1, ):
    """
    开心代理，可用性是0
    :param p:

    :return:
    """
    resp = _request_use_proxy('get', f'http://www.kxdaili.com/dailiip/1/{p}.html')
    ip_port_list = re.findall(
        r'''<tr[\s\S]*?<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>\s*?<td>(\d+)</td>[\s\S]*?HTTPS</td>[\s\S]*?</tr>''',
        resp.text, )
    return [f'{"".join(ip.split())}:{"".join(port.split())}' for ip, port in ip_port_list]


def get_7yip_proxies_list(p=1, ):
    """
    齐云代理 有效2  无效58
    :param p:

    :return:
    """
    resp = _request_use_proxy('get', f'https://www.7yip.cn/free/?action=china&page={p}')
    ip_port_list = re.findall(
        r'''<tr[\s\S]*?data-title="IP">(.*?)</td>\s*?<td data-title="PORT">(.*?)</td>[\s\S]*?<td data-title="类型">HTTPS</td>''',
        resp.text, )
    return [f'{"".join(ip.split())}:{"".join(port.split())}' for ip, port in ip_port_list]


# http://www.xsdaili.cn/dayProxy/ip/2207.html
def get_xsdaili_proxies_list():
    """
    小舒代理，可用1，不可用98

    :return:
    """
    url = 'http://www.xsdaili.cn/dayProxy/ip/2207.html'  # 测试时候要换成当天的页面url
    resp = _request_use_proxy('get', url)
    return [f'{ip}:{port}' for ip, port in
            re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)@HTTP', resp.text)]


@_ensure_proxy_list_is_not_empty_deco
def get_nima_proxies_list(p=1, gaoni_or_https='gaoni', ):
    """
    又是一个非常犀利的网站。
    gaoni 或https
    有效81，无效93

    :return:
    """
    resp = _request_use_proxy('get', f'http://www.nimadaili.com/{gaoni_or_https}/{p}/')
    return re.findall(r'<td>(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}:\d{1,5})</td>', resp.text)


def get_proxylistplus_proxies_list(p=1, source='SSL-List', ):
    """
    全部无效
    SSL-List-1  只有1页。
    Fresh-HTTP-Proxy-List-2  有多页。
    :param p:
    :param source:

    :return:
    """
    if source == 'SSL-List' and p > 1:
        return []
    resp = _request_use_proxy('get', f'https://list.proxylistplus.com/{source}-{p}')
    return [f'{ip}:{port}' for ip, port in
            re.findall(r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td>(\d+)</td>', resp.text)]


def get_from_seofangfa():
    """
    有效5 无效45

    :return:
    """
    resp = _request_use_proxy('get', 'https://proxy.seofangfa.com/')
    return [f'{ip}:{port}' for ip, port in re.findall('<tr><td>(.*?)</td><td>(.*?)</td><td>', resp.text)]


def get_from_superfastip(p=1, ):
    """
    还可以。
    有效15 无效59

    :return:
    """
    resp = _request_use_proxy('get', f'https://api.superfastip.com/ip/freeip?page={p}')
    return [f'{ip_port["ip"]}:{ip_port["port"]}' for ip_port in resp.json()['freeips']]


@_ensure_proxy_list_is_not_empty_deco
def get_from_jiangxianli(p=1):
    """
    国外代理多。非常犀利的网站。
    有效33，无效27
    :param p:
    :return:
    """
    resp = _request_use_proxy('get', f'https://ip.jiangxianli.com/?page={p}&protocol=http')
    return [f'{ip_port[0]}:{ip_port[1]}' for ip_port in re.findall(f'''data-ip="(.*?)" data-port="(\d+?)"''', resp.text)]


if __name__ == '__main__':
    """
    一定要https的代理，只能访问http的一概不要。
    """
    pass
    # _check_ip_list(get_https_proxies_list_from_xici_by_page(1))
    # get_https_proxies_list_from_xila_https_by_page()
    # get_https_proxies_list_from_xila_gaoni_by_page()
    # print(get_89ip_proxies_list(p=4, ))
    for page in range(1, 5):
        pass
        # print(get_ip3366_proxies_list(p=page, ))
        # print(get_kuaidailifree_proxies_list(p=page, ))
        # print(get_66ip_proxies_list(area=page, ))
        # print(get_kxdaili_proxies_list(page, ))
        # print(get_7yip_proxies_list(page, ))
        # print(get_nima_proxies_list(page,))
        # print(get_nima_proxies_list(page,'https', ))

        # print(get_proxylistplus_proxies_list(page,))
        # print(get_proxylistplus_proxies_list(page, source='Fresh-HTTP-Proxy-List',))

        # _check_ip_list(get_from_superfastip(page, ))

        # print(get_iphai_proxies_list())
        # print(get_xsdaili_proxies_list())
        # print(get_from_seofangfa())
        _check_ip_list(get_from_jiangxianli())
