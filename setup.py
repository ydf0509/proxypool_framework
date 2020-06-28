# coding=utf-8
from pathlib import Path
from setuptools import setup, find_packages

# with open("README.md", "r",encoding='utf8') as fh:
#     long_description = fh.read()

# filepath = ((Path(__file__).parent / Path('README.md')).absolute()).as_posix()
filepath = 'README.md'
print(filepath)

setup(
    name='proxypool_framework',  #
    version="1.7",
    description=(
        'proxypool_framework 是万能通用代理池架构，实现核心代码很少只有87行，同时想扩展一个代理平台仅需要写三行代码。通用代理池附带20+ 免费网站代理'
    ),
    keywords=("proxy", "proxy_pool",),
    # long_description=open('README.md', 'r',encoding='utf8').read(),
    long_description_content_type="text/markdown",
    long_description=open(filepath, 'r', encoding='utf8').read(),
    # data_files=[filepath],
    author='bfzs',
    author_email='ydf0509@sohu.com',
    maintainer='ydf',
    maintainer_email='ydf0509@sohu.com',
    license='BSD License',
    packages=find_packages(),
    include_package_data=True,
    platforms=["all"],
    url='',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries'
    ],
    install_requires=['redis2',
                      'nb_log',
                      'threadpool_executor_shrink_able',
                      'decorator_libs',
                      'tornado',
                      'db_libs',
                      'requests',
                      'urllib3',
                      ]
)
"""
打包上传
python setup.py sdist upload -r pypi


python setup.py sdist & twine upload dist/proxypool_framework-1.7.tar.gz
twine upload dist/*


pip install proxypool_framework --upgrade -i https://pypi.org/simple   # 及时的方式，不用等待 阿里云 豆瓣 同步
"""
