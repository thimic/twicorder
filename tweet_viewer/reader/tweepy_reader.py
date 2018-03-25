
import json

from tweet_viewer.constants import Ascending, Decending
from tweet_viewer.reader.base_reader import BaseReader


class TweepyReader(BaseReader):

    def read(self, sort_key='mtime', sort_order=Decending):
        reverse = True if sort_order == Decending else False
        sorted_files = sorted(
            self.get_files().items(),
            key=lambda x: x[1][sort_key],
            reverse=reverse
        )
        for basename, filedict in sorted_files:
            with open(filedict['path'], 'r') as stream:
                lines = stream.read().splitlines()
                print(len(lines))
                if sort_order == Decending:
                    lines = reversed(lines)
                for line in lines:
                    yield json.loads(line)


if __name__ == '__main__':
    reader = TweepyReader('~/Dropbox/Zheniya/smc/data')
    data = reader.read()
    print(next(data))
