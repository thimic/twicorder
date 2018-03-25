
import glob
import os

from tweet_viewer.constants import Ascending, Decending


class BaseReader(object):

    def __init__(self, directories, file_pattern='*.txt'):
        self._directories = directories
        self._file_pattern = file_pattern
        self._files = {}
        self._data = []

    def get_files(self):
        if isinstance(self._directories, str):
            self._directories = [self._directories]
        for directory in self._directories:
            directory = os.path.expanduser(directory)
            search = os.path.join(directory, self._file_pattern)
            for filepath in glob.glob(search):
                basename = os.path.basename(filepath)
                mtime = os.path.getmtime(filepath)
                updated = True
                if basename in self._files :
                    if self._files[basename]['mtime'] == mtime:
                        updated = False
                self._files[basename] = {
                    'path': filepath,
                    'mtime': os.path.getmtime(filepath),
                    'updated': updated
                }
        return self._files

    @classmethod
    def read(cls, sort_key='mtime', sort_order=Decending):
        raise NotImplementedError

    @classmethod
    def update(cls, directories):
        raise NotImplementedError
