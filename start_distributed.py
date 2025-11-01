import redis
import json

def initialize_redis_queue():
    """初始化Redis队列，将电影URL添加到Redis中"""
    # 连接到Redis
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    # 清空之前的队列
    r.delete('douban:start_urls')
    
    # 从文件中读取电影数据并生成URL
    jsonl_file = '/home/yudeng/code/cqu/big-data/scrapy/douban/crawled_movies.jsonl'
    
    try:
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    movie_data = json.loads(line.strip())
                    movie_id = movie_data.get('id')
                    
                    if movie_id:
                        # 构建评论页面URL
                        comments_url = f'https://movie.douban.com/subject/{movie_id}/comments'
                        # 将URL添加到Redis队列
                        r.lpush('douban:start_urls', comments_url)
                        print(f"Added URL for movie {movie_id} to Redis queue")
                    else:
                        print(f'第 {line_num} 行缺少电影ID')
                        
                except json.JSONDecodeError as e:
                    print(f'第 {line_num} 行JSON解析错误: {e}')
    except FileNotFoundError:
        print(f'文件 {jsonl_file} 未找到')
    except Exception as e:
        print(f'读取文件时发生错误: {e}')
    
    print("Redis队列初始化完成")

if __name__ == "__main__":
    initialize_redis_queue()