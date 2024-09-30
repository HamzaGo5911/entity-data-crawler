from entity_crawler import EntityDataCrawler

if __name__ == "__main__":
    # List of URLs to crawl
    urls = [
        "https://www.pap.gov.pk/members/contactdetails/en/21?bycontact=true",
    ]

    crawler = EntityDataCrawler(urls)
    crawler.start_crawling()