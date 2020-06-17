# db_libs

各种数据库的封装。只封装最难的部分，十分克制,很少去添加一些新的方法然后去调用原生类的方法。

因为原生类已经很好用了，主要是控制一下用户无限实例化连接类，造成反复创建连接就可以了。

```
redis_lib和mongo_lib在redis和pymongo的基础上进行封装。
由于原生的包已经足够好用了，并不需要重新写几百个方法进行过度封装。
仅仅是加了享元模式，使得在相同入参情况下无限实例化相关客户端类的时候不会反复重新连接。
封装方式采用的非常规方式，使用的是继承方式，而非通常情况下的使用组合来进行封装。
继承方式封装的比组合模式封装的好处更多。



mysql_lib使用连接池，兼容在多线程环境运行。使调用时候少关注cursor commit close 等。

sqla_lib 是反射已存在的表，也是使用连接池，兼容多线程环境运行。能够支持orm和原生sql语句两种执行方式。

```

```python
# 组合模式封装的代码一般是如下这种例子。
"""
这种方式封装是组合，精确点是23种设计模式的代理模式。
代理模式说的是定义很多方法，来调用self.r所具有的方法。


另外对于无限实例化，还使用了享元模式。
封装数据库切记不要使用单例模式，如果入参传了不同的主机ip或者不同的db，而仍然返回之前的连接对象，那就大错特错了。

"""
# 使用组合模式封装的redis，没有继承模式的好用。
import redis

class RedisClient:

    params__reids_map = {}

    def __init__(self,host,db,port,password):
        if (host,db,port,password) not in self.__class__.params__reids_map:
            self.r = redis.Redis(host,db,port,password)
            self.__class__.params__reids_map[(host,db,port,password)] = self.r
        else:
            self.r = self.__class__.params__reids_map[(host,db,port,password)]
    
    def my_set(self,key,value):
        print('额外的扩展')
        self.r.set(name=key,value=value)
    
    def my_get(self,name):
        # 这个封装简直是多次一举，在redis实例化时候，
        # 将Redis类的构造方法的入参 decode_responses设置为True，就可以避免几百个方法需要反复decode了。
        return self.r.get(name).decode()

```

#### 例如网上的一种封装，重新封装几百个方法，我不喜欢这样封装工具类。
```python
import redis

class MyRedis():
    def __init__(self,ip,password,port=6379,db=1):#构造函数
        try:
            self.r = redis.Redis(host=ip,password=password,port=port,db=db)  #连接redis固定方法,这里的值必须固定写死
        except Exception as e:
            print('redis连接失败，错误信息%s'%e)
    def str_get(self,k):
        res = self.r.get(k)   #会从服务器传对应的值过来，性能慢
        if res:
            return res.decode()   #从redis里面拿到的是bytes类型的数据，需要转换一下

    def str_set(self,k,v,time=None): #time默认失效时间
        self.r.set(k,v,time)

    def delete(self,k):
        tag = self.r.exists(k)
        #判断这个key是否存在,相对于get到这个key他只是传回一个存在火灾不存在的信息，
        # 而不用将整个k值传过来（如果k里面存的东西比较多，那么传输很耗时）
        if tag:
            self.r.delete(k)
        else:
            print('这个key不存在')

    def hash_get(self,name,k):  #哈希类型存储的是多层字典（嵌套字典）
        res = self.r.hget(name,k)
        if res:
            return res.decode()  #因为get不到值得话也不会报错所以需要判断一下

    def hash_set(self,name,k,v): #哈希类型的是多层
        self.r.hset(name,k,v)   #set也不会报错

    def hash_getall(self,name):
        res = self.r.hgetall(name)   #得到的是字典类型的，里面的k,v都是bytes类型的
        data={}
        if res:
            for k,v in res.items(): #循环取出字典里面的k,v，在进行decode
                k = k.decode()
                v = v.decode()
                data[k]=v
        return data

    def hash_del(self,name,k):
        res = self.r.hdel(name,k)
        if res:
            print('删除成功')
            return 1
        else:
            print('删除失败，该key不存在')
            return 0

    @property   #属性方法，
                # 使用的时候和变量一个用法就好比实例，A=MyRedis(), A.clean_redis使用，
                # 如果不加这个@property,使用时A=MyRedis(), A.clean_redis()   后面需要加这个函数的括号
    def clean_redis(self):
        self.r.flushdb()   #清空 redis
        print('清空redis成功！')
        return 0



a = MyRedis('118.0000','HK0000*')

print(a.str_get('duan'))

```
