from entity_crawler import EntityDataCrawler

if __name__ == "__main__":
    # List of URLs to crawl
    urls = [
        "https://lslbc.louisiana.gov/violations/",
        "https://embassyofalgeria.uk/the-ambassador/",
        "https://www.parlament.mt/en/14th-leg/political-groups/",
        "https://members.parliament.uk/members/commons",
        "https://docs.fcdo.gov.uk/docs/UK-Sanctions-List.html",
        "https://www.worldbank.org/en/projects-operations/procurement/debarred-firms",
        "https://www.smcl.bt/#/",
        "https://www.smv.gob.pe/ServicioSancionesImpuestas/frm_SancionesEmpresas?data=6D9FF7643381613ADE8EEBB66B8E0CF2C6CC64BCC4",
    ]

    crawler = EntityDataCrawler(urls)
    crawler.start_crawling()