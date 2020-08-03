import random
import time

from proxypool_framework.proxy_pool_config import REDIS_CLIENT

while 1:
    time.sleep(0.1)
    pr = random.choice(REDIS_CLIENT.hkeys('useful_proxy')).decode()

    if REDIS_CLIENT.hlen('useful_proxy') > random.randint(18,30):
        REDIS_CLIENT.hdel('useful_proxy',pr)

# python -m proxypool_framework.tests.reduce2