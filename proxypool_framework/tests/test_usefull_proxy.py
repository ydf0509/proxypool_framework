from proxypool_framework.proxy_pool_config import REDIS_CLIENT
import random
import requests

sucess_count = 0
fail_count = 0
for _ in range(100000):
    pr = random.choice(REDIS_CLIENT.hkeys('useful_proxy')).decode()
    # print(pr)

    try:
        requests.get('http://www.baidu.com',proxies={'https':f'https://{pr}','http':f'http://{pr}'},timeout=5)
        sucess_count += 1
    except Exception as e:
        print(e)
        fail_count += 1
    print(f'成功率 {sucess_count / (sucess_count + fail_count)}')
