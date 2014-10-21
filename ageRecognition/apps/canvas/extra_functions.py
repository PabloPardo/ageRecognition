import math
import Image
import operator
from models import Picture, Votes, UserProfile


def compare(h1, h2):
    """
    Compare tow images histograms and return the Root Mean Square Error
    """

    # h1 = Image.open(path1).convert('RGB').histogram()
    # h2 = Image.open(path2).convert('RGB').histogram()

    rms = math.sqrt(reduce(operator.add, map(lambda a, b: (a-b)**2, h1, h2))/len(h1))

    return rms


def calculate_score(user):
    """
    Calculate the Global Score of a user
    """

    # Count number of Uploaded Images
    upl_img = Picture.objects.filter(owner=user, visibility=True).count()
    user.upload_pic = upl_img

    # Give 50 points per Uploaded Image
    upl_img_score = user.upload_pic * 50

    # Count number of Votes and its score
    vts = Votes.objects.values_list('score', flat=True).filter(user=user)
    user.eval_pic = vts.count()

    vts_score = 0
    for v in vts:
        vts_score += 5 if v > 10 else 3*(10 - v)

    user.score_global = upl_img_score + vts_score
    user.save()
    return