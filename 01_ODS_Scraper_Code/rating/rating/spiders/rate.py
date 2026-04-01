import scrapy


class RateSpider(scrapy.Spider):
    name = "rate"
    allowed_domains = ["movie.douban.com"]
    start_urls = ["https://www.douban.com/search?cat=1002&q=%E8%80%81%E5%8F%8B%E8%AE%B0"]


    def parse(self, response):
        records=response.css("div.result")
        for record in records[:10]:
            season=record.css("div.title a::text").get()
            rating=record.css("div.title div.rating-info span.rating_nums::text").get()
            total_people=record.css("div.title div.rating-info span::text").re_first(r'\((\d+)人评价\)')
            total=int(total_people)
            yield {
                "season":season,
                "rating":rating,
                "total_people":total
            }



        pass
