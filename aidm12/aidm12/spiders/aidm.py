import re
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class AidmSpider(CrawlSpider):

    游戏类型列表 = ['android', 'galgame', 'krkr', 'ons', 'psp', 'rpg', 'slg', 'otome']


    cookies = {
        "Hm_lvt_89c5cd8dee61019d41d5cbb2084e2ec6": "1678683817",
        "b2_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczpcL1wvd3d3LmFpZG0xMi5jb20iLCJpYXQiOjE2Nzg2ODM5MDQsIm5iZiI6MTY3ODY4MzkwNCwiZXhwIjoxNjc5ODkzNTA0LCJkYXRhIjp7InVzZXIiOnsiaWQiOiIxMDMzNSJ9fX0.no5qERDpKB1NgiaqMbRPhAQIEa-tP_3hqxzg5X7hmyc",
        "wordpress_logged_in_1273cc8e9ab14e192a32c30e4233d29e": "user10335_719|1679245504|7uMFJtZSebq95V7nbaEUgPL8puanynZtVN4jWYA6Cro|969e0355dcef1374445f9d73a29404aee2b1d145cd6b889a34f6908fc3ea3a2c",
        "Hm_lpvt_89c5cd8dee61019d41d5cbb2084e2ec6": "1678975589"
    }

    name = "aidm"
    allowed_domains = ["aidm12.com"]
    start_urls = [f"https://www.aidm12.com/games/{游戏类型列表[0]}/page/1"]
    # start_urls = [f"https://www.aidm12.com/games/{游戏类型}/page/1" for 游戏类型 in 游戏类型列表]
    print(start_urls)
    rules = (Rule(LinkExtractor(allow=r'https://www.aidm12.com/\d+/', restrict_xpaths='//*[@id="post-list"]/ul'),
                  callback="parse_game_page", follow=False),)

    def start_requests(self):
        if not self.start_urls and hasattr(self, "start_url"):
            raise AttributeError(
                "Crawling could not start: 'start_urls' not found "
                "or empty (but found 'start_url' attribute instead, "
                "did you miss an 's'?)"
            )
        for url in self.start_urls:
            yield scrapy.Request(url, dont_filter=True, cookies=self.cookies)

    def parse_start_url(self, response):
        print(response)
        referer = response.request.headers.get('Referer')
        if referer:
            referer = referer.decode('utf-8')

        if response.xpath('//*[@id="post-list"]/div/p/text()'):
            return
        first_url = response.url.split("page/")[0] + "page/"
        last_url = str(int(response.url.split("page/")[1]) + 1)
        next_page_url = first_url + last_url
        # print(next_page_url)
        yield scrapy.Request(next_page_url, cookies=self.cookies)

    def parse_game_page(self, response):
        # 来源页面判断
        referer = response.request.headers.get('Referer')
        if referer:
            referer = referer.decode('utf-8')

        # 判断游戏类型
        当前页面游戏类型 = None
        for 游戏类型 in self.游戏类型列表:
            if 游戏类型 in referer:
                当前页面游戏类型 = 游戏类型
                break
            else:
                当前页面游戏类型 = None
        if 当前页面游戏类型 is None:
            return
        
        网址 = response.url

        网页序号 = int(网址.replace('https://www.aidm12.com/', '').replace('/', ''))

        游戏名, 游戏类型重判定 = self.游戏名处理(response.xpath('//*[@id="primary-home"]/article/header/h1').extract())
        游戏类型 = 游戏类型重判定

        h4 = response.xpath('//*[@id="primary-home"]/article/div[1]/h4/text()').extract()
        if h4 != ['游戏简介', '游戏截图', '备注']:
            with open('log.log', 'a+', encoding='utf-8')as f:
                f.write(f'{response.url}\t{h4}\n')
        
    def 文章主体获取(self, response):
        pass

    def 筛选函数(self, article: str, h4: list, 字段类型: str) -> str:
        输出 = ''

        if 字段类型 not in h4:
            return 输出
        字段类型索引 = h4.index(字段类型)

        if 字段类型索引 < (len(h4) - 1):
            pattern_output = re.compile(r'<h4>[\s\S]{0,15}' + h4[
                字段类型索引] + r'[\s\S]{0,15}</h4>[\s\S]*<h4>[\s\S]{0,15}' + h4[
                                            字段类型索引 + 1] + r'[\s\S]{0,15}</h4>')
            output_1 = pattern_output.findall(article)[0]
            output_2 = re.sub('<h4>[\s\S]{0,15}' + h4[字段类型索引] + '[\s\S]{0,15}</h4>', '',
                                output_1)  # 去头
            output_3 = re.sub('<h4>[\s\S]{0,15}' + h4[字段类型索引 + 1] + '[\s\S]{0,15}</h4>', '',
                                output_2)  # 去尾
            输出 = output_3.replace('<br>', '').replace('<p>', '').replace('</p>', '').replace(
                '<br />', '').strip()  # 去掉html符号
        elif 字段类型索引 == (len(h4) - 1):
            pattern_output = re.compile(
                r'<h4>[\s\S]{0,15}' + h4[字段类型索引] + r'[\s\S]{0,15}</h4>[\s\S]*</article>')
            output_1 = pattern_output.findall(article)[0]
            output_2 = re.sub('<h4>[\s\S]{0,15}' + h4[字段类型索引] + '[\s\S]{0,15}</h4>', '',
                                output_1)  # 去头
            输出 = output_2.replace('</div>', '').replace('</article>', '').replace('<p>', '').replace(
                '</p>', '').replace('<br>', '').replace('<br />', '').strip()  # 去尾及去掉html符号
        return 输出

    def 游戏名处理(self, 游戏名):
        游戏名 = 游戏名
        游戏类型重判定 = None
        if '【安卓游戏】' in 游戏名:
            游戏名 = 游戏名.replace('【安卓游戏】')
            游戏类型重判定 = 'android'
        if '【Galgame】' in 游戏名:
            游戏名 = 游戏名.replace('【Galgame】')
            游戏类型重判定 = 'galgame'
        if '【KRKR游戏】' in 游戏名:
            游戏名 = 游戏名.replace('【KRKR游戏】')
            游戏类型重判定 = 'krkr'
        if '【PSP游戏】' in 游戏名:
            游戏名 = 游戏名.replace('【PSP游戏】')
            游戏类型重判定 = 'psp'
        if '【RPG游戏】' in 游戏名:
            游戏名 = 游戏名.replace('【RPG游戏】')
            游戏类型重判定 = 'rpg'
        if '【SLG游戏】' in 游戏名:
            游戏名 = 游戏名.replace('【SLG游戏】')
            游戏类型重判定 = 'slg'
        if '【乙女游戏】' in 游戏名:
            游戏名 = 游戏名.replace('【乙女游戏】')
            游戏类型重判定 = 'otome'
        if "ONS" in 游戏名:
            游戏类型重判定 = 'ons'
        return 游戏名, 游戏类型重判定

