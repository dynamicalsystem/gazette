from dynamicalsystem.gazette.content import GitHub


class Review:
    def __init__(self, chart, placing) -> None:
        self.chart = chart
        self.placing = placing
        self.publishers = []
        self.content = GitHub(chart, placing)
        # .get, not [] -- a missing key is graded 'not_ready' by classify()
        # and held quietly, rather than crashing the whole publish sweep.
        item = self.content.item if isinstance(self.content.item, dict) else {}
        self.artist = item.get("artist", "")
        self.work = item.get("work", "")
        self.review = item.get("review", "")
        self.verdict = item.get("verdict", "")
