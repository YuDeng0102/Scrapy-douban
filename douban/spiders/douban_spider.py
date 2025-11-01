import scrapy,re
import json
from pathlib import Path
class DoubanSpider(scrapy.Spider):
    name = "douban"
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
    def start_requests(self):
        # 从探索页面开始，爬取热门的200个电影评论
        jsonl_file = '/home/yudeng/code/cqu/big-data/scrapy/douban/crawled_movies.jsonl'  # 请根据实际文件名修改
        
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        movie_data = json.loads(line.strip())
                        movie_id = movie_data.get('id')
                     
                        if movie_id:
                            # 构建评论页面URL
                            comments_url = f'https://movie.douban.com/subject/{movie_id}/comments'
                            yield scrapy.Request(
                                comments_url,
                                cookies=self.cookies,
                                callback=self.parse_comments,
                                meta={
                                    'movie_id': movie_id,
                                    'comment_count': 0  # 初始化评论计数器
                                }
                            )
                        else:
                            self.logger.warning(f'第 {line_num} 行缺少电影ID')
                            
                    except json.JSONDecodeError as e:
                        self.logger.error(f'第 {line_num} 行JSON解析错误: {e}')
        except FileNotFoundError:
            self.logger.error(f'文件 {jsonl_file} 未找到')
        except Exception as e:
            self.logger.error(f'读取文件时发生错误: {e}')
        
    def parse_comments(self, response):
        # 从meta中获取已解析的评论数量，如果没有则初始化为0
        comment_count = response.meta.get('comment_count', 0)
        
        for comment in response.css("div.comment"):
            # 如果已经达到500条评论，则停止解析
            if comment_count >= 500:
                self.logger.info(f"电影 {response.meta.get('movie_id', '未知')} 已达到500条评论限制")
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
                "movie_id": response.meta.get('movie_id', ''),
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
                    meta={
                        'movie_id': response.meta.get('movie_id', ''),
                        'comment_count': comment_count  # 传递当前评论计数
                    }
                )
        else:
            self.logger.info(f"电影 {response.meta.get('movie_id', '未知')} 评论爬取完成，共 {comment_count} 条评论")