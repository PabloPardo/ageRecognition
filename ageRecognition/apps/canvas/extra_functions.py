import math
import operator
from models import Picture, Votes, UserProfile
import matplotlib.pyplot as plt


def compare(h1, h2):
    """
    Compare tow images histograms and return the Root Mean Square Error
    """

    rms = math.sqrt(reduce(operator.add, map(lambda a, b: (a - b) ** 2, h1, h2)) / len(h1))

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
    # and discard repeated votes.
    vts_pic = Votes.objects.values_list('score', 'pic').filter(user=user)
    vts = []
    for v in range(vts_pic.count()):
        flag = True
        for p in range(v):
            if vts_pic[v][1] == vts_pic[p][1]:
                flag = False
                break
        if flag:
            vts.append(vts_pic[v][0])

    user.eval_pic = len(vts)

    vts_score = 0
    for v in vts:
        vts_score += 5 if v > 10 else 3 * (10 - v)

    user.score_global = upl_img_score + vts_score
    user.save()
    return


def plot_stats(usr, img, vte, rpt, path):
    # Plot Distribution of votes over pictures
    pic_votes_hist = []
    for p in img:
        count = 0
        for v in vte:
            if v.pic == p:
                count += 1
        pic_votes_hist.append(count)
    pic_votes_hist = sorted(pic_votes_hist, key=int)
    plt.figure()
    plt.bar(range(len(pic_votes_hist)), pic_votes_hist)
    plt.xlabel('Picture ID')
    plt.ylabel('Number of Votes')
    plt.savefig(path + 'img_votes_distr.png')

    # Plot Distribution of pictures over users
    pic_usr_hist = []
    for u in usr:
        pic_usr_hist.append(u.upload_pic)
    pic_usr_hist = sorted(pic_usr_hist, key=int)
    plt.figure()
    plt.bar(range(len(pic_usr_hist)), pic_usr_hist)
    plt.xlabel('User ID')
    plt.ylabel('Number of Uploaded Images')
    plt.savefig(path + 'img_usr_distr.png')