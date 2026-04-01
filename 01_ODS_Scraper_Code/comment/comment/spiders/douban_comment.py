import scrapy


class DoubanCommentSpider(scrapy.Spider):
    name = "douban_comment"
    allowed_domains = ["movie.douban.com"]
    start_urls = ["https://movie.douban.com/subject/3286552/comments?start=0&limit=20&status=P&sort=new_score"]

    id=3600
    page=0

    def parse(self, response):
        comments=response.css("div.comment-item")
        for comment in comments:
            item_id=self.id
            season=10
            content=comment.css("p.comment-content span.short::text").get()
            name=comment.css("div.comment span.comment-info a::text").get()
            yield {
                "id":item_id,
                "season":season,
                "comment":content,
                "name":name
            }
            self.id+=1
        self.page += 20
        if self.page <= 400:
            next_url = f"https://movie.douban.com/subject/3286552/comments?start={self.page}&limit=20&status=P&sort=new_score"
            yield scrapy.Request(url=next_url, callback=self.parse)


        pass
