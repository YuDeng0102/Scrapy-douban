## scrapy-douban

使用 scrapy-redis 爬取豆瓣热门电影评论

使用三台机器分布式爬取，其中一台有共有 ip 的云服务器作为主节点，其他两台作为从节点，开始爬取的 url 已经通过 jsonl 文件（crawled_movies.jsonl）传递给主节点。

### 安装依赖

在每个节点上安装 redis-server，以及 scrapy-redis 依赖

```bash
sudo apt update
sudo apt install redis-server
pip install scrapy-redis
pip install redis
```

### 主节点配置 redis 密码认证

在主节点修改 redis 配置，开启密码认证，运行所有 ip 都可以连接
修改 /etc/redis/redis.conf，添加以下内容

```
bind 0.0.0.0
protected-mode yes
requirepass password
```

重启 redis 服务

```
sudo service redis-server restart
```

同时在腾讯云服务器上开放 6379 端口，允许所有 ip 连接

### 从节点配置 redis 密码认证

在 settings.py 中添加以下内容,确保可以通过密码认证连接到主节点的 redis 服务器

```
REDIS_HOST = '120.53.106.5'
REDIS_PORT = 6379
REDIS_PARAMS = {
    'password': 'password',
}
# 启用Redis管道
ITEM_PIPELINES = {
    'scrapy_redis.pipelines.RedisPipeline': 300,
    "douban.pipelines.DoubanPipeline": 400,
}
```

为了避免请求过于频繁，设置请求延迟为 2 秒

```
DOWNLOAD_DELAY = 2
```

### 开始爬取

在主节点，运行以下 python 文件，在 redis 的任务队列中添加所有要爬取的 url

```
python3 start_distributed.py
```

为了加快爬取效率，我们让主节点也作为一个从节点，同时运行一个 scrapy 进程,在每个节点上运行以下命令

```bash
scrapy crawl douban -o douban.jsonl
```

可以通过以下 Redis 命令监控爬取进度：

```bash
# 查看队列中的URL数量
redis-cli -h 120.53.106.5 -p 6379 -a password llen douban:start_urls

# 查看已处理的请求数量
redis-cli -h 120.53.106.5 -p 6379 -a password llen douban:items

# 查看统计数据
redis-cli -h 120.53.106.5 -p 6379 -a password hgetall douban:dupefilter
```

最后合并所有节点的结果文件 douban.jsonl 即可
