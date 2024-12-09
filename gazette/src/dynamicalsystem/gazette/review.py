from dynamicalsystem.gazette.content import GitHub


class Review:
    def __init__(self, chart, placing) -> None:
        self.chart = chart
        self.placing = placing
        self.publishers = []
        self.content = GitHub(chart, placing)
        self.artist = self.content.item["artist"]
        self.work = self.content.item["work"]
        self.review = self.content.item["review"]
        self.verdict = self.content.item["verdict"]
