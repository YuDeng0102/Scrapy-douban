import scrapy
import re
import json
from scrapy_redis.spiders import RedisSpider

class DoubanSpider(RedisSpider):
    name = "douban"
    redis_key = 'douban:start_urls'
    
    max_comments_per_movie = 500
    cookies = {
        'bid': 'ie5uTgroo-A',
        'll': '"108309"',
        '_gid': 'GA1.2.1032159099.1760770681',
        '_pk_id.100001.4cf6': 'ff3b44866f268720.1760770683.',
        '__yadk_uid': 'AMiO05FaNvBqkn5aaZsl8CxiPOAYnya8',
        '_vwo_uuid_v2': 'D85DD741B690A41EF59F97F9FB0F6666B|eabd3d087677b8a224793f97924c8350',
        'viewed': '"35583451"',
        'ap_v': '0,6.0',
        '__utma': '30149280.1277051517.1760770681.1760803209.1760839176.4',
        '__utmc': '30149280',
        '__utmz': '30149280.1760839176.4.3.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided)',
        '_ga': 'GA1.2.1277051517.1760770681',
        '_ga_Y4GN1R87RG': 'GS2.1.s1760839694$o3$g0$t1760839696$j58$l0$h0',
        '__utma': '223695111.1277051517.1760770681.1760803209.1760839697.4',
        '__utmb': '223695111.0.10.1760839697',
        '__utmc': '223695111',
        '__utmz': '223695111.1760839697.4.3.utmcsr=m.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/',
        '_pk_ref.100001.4cf6': '%5B%22%22%2C%22%22%2C1760839697%2C%22https%3A%2F%2Fm.douban.com%2F%22%5D',
        '_pk_ses.100001.4cf6': '1',
        'dbcl2': '"291897438:bxu6nbNd90k"',
        'ck': 'pibv',
        'push_noty_num': '0',
        'push_doumail_num': '0',
        'frodotk_db': '"bfefbdfbde03b5a43fcf39f39a0b20ec"',
        '__utmt': '1',
        '__utmv': '30149280.29189',
        '__utmb': '30149280.3.10.1760839176'
    }
    
    def make_requests_from_url(self, url):
        """重写此方法以使用cookies"""
        return scrapy.Request(
            url,
            cookies=self.cookies,
            callback=self.parse_comments,
            meta={
                'movie_id': url.split('/')[-2],  # 从URL中提取电影ID
                'comment_count': 0
            }
        )
    
    def parse(self, response):
        """添加默认的parse方法，解决RedisSpider需要的问题"""
        # 直接调用parse_comments方法处理响应
        yield from self.parse_comments(response)
    
    def parse_comments(self, response):
        # 从meta中获取已解析的评论数量，如果没有则初始化为0
        comment_count = response.meta.get('comment_count', 0)
        movie_id = response.meta.get('movie_id', '')
        
        # 如果没有movie_id，尝试从URL中提取
        if not movie_id:
            movie_id = response.url.split('/')[-2]
        
        for comment in response.css("div.comment"):
            # 如果已经达到500条评论，则停止解析
            if comment_count >= 500:
                self.logger.info(f"电影 {movie_id} 已达到500条评论限制")
                break
                
            # 评论内容
            content = comment.css('span.short::text').get()

            rating_class = comment.css('span[class*="allstar"]::attr(class)').get()
            rating_num = None
            if rating_class:
                match = re.search(r'allstar(\d+)', rating_class)
                if match:
                    rating_num = int(match.group(1)) // 10  # 转换为1-5的评分
            
            yield {
                "content": content,
                "rating": rating_num,
                "movie_id": movie_id,
                "comment_index": comment_count + 1  # 添加评论序号
            }
            
            comment_count += 1
        
        # 只有在未达到500条评论时才继续翻页
        if comment_count < 500:
            next_page = response.css('a.next::attr(href)').get()
            if next_page:
                next_page_url = response.urljoin(next_page)
                yield scrapy.Request(
                    next_page_url, 
                    callback=self.parse_comments,
                    cookies=self.cookies,  # 确保请求携带cookies
                    meta={
                        'movie_id': movie_id,
                        'comment_count': comment_count  # 传递当前评论计数
                    }
                )
        else:
            self.logger.info(f"电影 {movie_id} 评论爬取完成，共 {comment_count} 条评论")