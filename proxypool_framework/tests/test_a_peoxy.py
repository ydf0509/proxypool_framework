import json
import datetime
import time

import requests
from collections import defaultdict

from proxy_pool_public.proxy_pool_config import REDIS_CLIENT

ip = '45.76.209.157:8080'

proxies = {'https':ip,'http':ip}
#{'https': 'https://125.126.126.60:60004', 'platform': 'xici','http': 'http://125.126.126.60:60004'}
resp = requests.get('https://www.baidu.com',proxies={'https': '125.126.126.60:60004', 'platform': 'xici','http': '125.126.126.60:60004'})
print(resp.text)
print(resp.url)
#
#
# platform___ip_count_map = defaultdict(int)
# ip__check_time_map = dict()
# for proxy_str,timestamp in REDIS_CLIENT.zscan_iter('proxy_free', ):
#     proxy_dict = json.loads(proxy_str)
#     # print(proxy_dict)
#     ip__check_time_map[proxy_dict['https']] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
#     platform___ip_count_map[proxy_dict['platform']] +=1
#
#
#
# print(platform___ip_count_map)
#
# print(json.dumps({'platform___ip_count_map': dict(sorted(platform___ip_count_map.items(), key=lambda x: x[1], reverse=True)),
#                            'ip__check_time_map': dict(sorted(ip__check_time_map.items(), key=lambda x: x[1], reverse=True))}, ensure_ascii=False, indent=4))


str1 = '''
dsds
dsad
dsad

'''

print(repr(str1))