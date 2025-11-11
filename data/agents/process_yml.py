import from_yml
import fetch


class processer:

    def __init__(self):

        self.data = from_yml.load_feeds()
        self.fetcher = fetch.fetcher()

    def example_archetecture(self):

        return {
            "default"


if __name__ == "__main__":

    proc = processer()

    print(proc.data)
