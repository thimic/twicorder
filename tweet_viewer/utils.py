
import urllib.request

from PyQt5 import QtGui


def load_avatar(url):
    data = urllib.request.urlopen(url).read()
    image = QtGui.QImage()
    image.loadFromData(data)
    return QtGui.QPixmap(image)
