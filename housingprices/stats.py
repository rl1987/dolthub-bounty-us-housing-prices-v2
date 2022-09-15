# Based on:
# https://stackoverflow.com/questions/61402939/scrapy-how-to-save-crawling-statistics-to-json-file

from scrapy.statscollectors import StatsCollector
from scrapy.utils.serialize import ScrapyJSONEncoder

class MyStatsCollector(StatsCollector):
    def _persist_stats(self, stats, spider):
        encoder = ScrapyJSONEncoder()
        
        filename = "stats.json"
        if spider.stats_filepath is not None:
            filename = spider.stats_filepath

        out_f = open(filename, "w")
        data = encoder.encode(stats)
        out_f.write(data)
        out_f.close()
