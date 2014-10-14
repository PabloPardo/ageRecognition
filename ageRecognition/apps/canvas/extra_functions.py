import math
import Image
import operator


def compare(path1, path2):
    h1 = Image.open(path1).histogram()
    h2 = Image.open(path2).histogram()

    rms = math.sqrt(reduce(operator.add, map(lambda a, b: (a-b)**2, h1, h2))/len(h1))

    return rms