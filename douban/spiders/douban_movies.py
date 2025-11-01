#这个类用来从近期热门的200个电影评论中提取电影信息
import scrapy


class DoubanMoviesSpider(scrapy.Spider):
    name = "douban_movies"
    start_urls = [
        "https://movie.douban.com/explore",
    ]
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
    max_movie_count = 400
    movie_count = 0
    
    def parse(self, response):
        self.logger.info('开始解析探索页面')
        xhr_url='https://m.douban.com/rexxar/api/v2/subject/recent_hot/movie'
        xhr_payload={
            'start': '0',  # 可能表示从第几个电影开始加载
            'limit': '20',  # 每次加载的数量
            'ck': 'pibv',       # 可能是某种验证参数
        }
        max_load_times = self.max_movie_count // 20
        for load_time in range(0, max_load_times):
            # 更新请求参数，例如每次请求更新start参数
            xhr_payload['start'] = str(load_time * 20)
            
            yield scrapy.FormRequest(
                url=xhr_url,
                formdata=xhr_payload,
                cookies=self.cookies,
                callback=self.parse_xhr_response,
            )
    def parse_xhr_response(self, response):
        """解析XHR请求返回的响应"""
        # 通常XHR返回的是JSON数据，其中包含HTML片段或直接是电影数据列表
        try:
            data = response.json()
            movies = data.get('items', [])
            for movie in movies:
                self.movie_count += 1
                yield {
                    'id': movie.get('id'),
                    'title': movie.get('title'),
                    'rating': movie.get('rating', {}).get('value'),
                    'count':movie.get('rating', {}).get('count'),
                }
        except ValueError:
            self.logger.error("XHR响应返回的不是有效JSON")
