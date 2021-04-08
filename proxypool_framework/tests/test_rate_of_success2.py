from proxypool_framework.contrib.proxy_client import ProxyClient


REDIS_URL = 'redis://:yMxsueZD9yx0AkfR@192.168.199.202:6543/7'
ProxyClient(redis_url=REDIS_URL,redis_proxy_key='proxy_free_good').statistic_rate_of_sucess()