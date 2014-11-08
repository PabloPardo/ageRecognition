import math
import operator
from models import Picture, Votes, UserProfile
import matplotlib.pyplot as plt
import matplotlib.dates as dts


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
    # ----------------------------------------
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
    # ----------------------------------------
    pic_usr_hist = []
    for u in usr:
        pic_usr_hist.append(u.upload_pic)
    pic_usr_hist = sorted(pic_usr_hist, key=int)
    plt.figure()
    plt.bar(range(len(pic_usr_hist)), pic_usr_hist)
    plt.xlabel('User ID')
    plt.ylabel('Number of Uploaded Images')
    plt.savefig(path + 'img_usr_distr.png')

    # Plot the evolution in time of the DB
    # ------------------------------------

    # Plot the number of users in time
    user_join_dates = [u.user.date_joined for u in usr]
    cum_num_usr = []
    count_usr = 0
    for u in usr:
        count_usr += 1
        cum_num_usr.append(count_usr)

    dates_usr = dts.date2num(user_join_dates)

    # Plot the number of pictures in time
    picture_dates = [p.date for p in img]
    cum_num_img = []
    count_img = 0
    for p in img:
        count_img += 1
        cum_num_img.append(count_img)

    dates_img = dts.date2num(picture_dates)

    # Plot the number of pictures in time
    votes_dates = [v.date for v in vte]
    cum_num_vte = []
    count_vte = 0
    for v in vte:
        count_vte += 1
        cum_num_vte.append(count_vte)

    dates_vte = dts.date2num(votes_dates)

    months = dts.MonthLocator(range(1, 13), bymonthday=1, interval=3)
    monthsFmt = dts.DateFormatter("%b '%y")

    fig, ax = plt.subplots()
    p1, = ax.plot_date(dates_usr, cum_num_usr, fmt="-")
    p2, = ax.plot_date(dates_img, cum_num_img, fmt="r-")
    p3, = ax.plot_date(dates_vte, cum_num_vte, fmt="g-")

    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(monthsFmt)
    ax.autoscale_view()

    fig.autofmt_xdate()

    plt.xlabel('Time')
    ax.legend([p1, p2, p3], ['Users', 'Pictures', 'Votes'])
    ax.grid(True)
    plt.savefig(path + 'time_usr.png')
