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

    months = dts.MonthLocator(range(1, 13), bymonthday=1, interval=3)
    monthsFmt = dts.DateFormatter("%b '%y")

    # Plot the number of users in time
    user_join_dates = [u.user.date_joined for u in usr]
    cum_num_usr = []
    count_usr = 0
    for u in usr:
        count_usr += 1
        cum_num_usr.append(count_usr)

    dates_usr = dts.date2num(user_join_dates)

    fig, ax = plt.subplots()
    ax.plot_date(dates_usr, cum_num_usr, fmt="-")

    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(monthsFmt)
    ax.autoscale_view()

    fig.autofmt_xdate()

    plt.xlabel('Time')
    plt.ylabel('No. Users')
    ax.grid(True)
    plt.savefig(path + 'time_usr.png')

    # Plot the number of pictures in time
    picture_dates = [p.date for p in img]
    cum_num_img = []
    count_img = 0
    for p in img:
        count_img += 1
        cum_num_img.append(count_img)

    dates_img = dts.date2num(picture_dates)

    fig, ax = plt.subplots()
    ax.plot_date(dates_img, cum_num_img, fmt="r-")

    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(monthsFmt)
    ax.autoscale_view()

    fig.autofmt_xdate()

    plt.xlabel('Time')
    plt.ylabel('No. Pictures')
    ax.grid(True)
    plt.savefig(path + 'time_img.png')

    # Plot the number of pictures in time
    votes_dates = [v.date for v in vte]
    cum_num_vte = []
    count_vte = 0
    for v in vte:
        count_vte += 1
        cum_num_vte.append(count_vte)

    dates_vte = dts.date2num(votes_dates)

    fig, ax = plt.subplots()
    ax.plot_date(dates_vte, cum_num_vte, fmt="g-")

    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(monthsFmt)
    ax.autoscale_view()

    fig.autofmt_xdate()

    plt.xlabel('Time')
    plt.ylabel('No. Votes')
    ax.grid(True)
    plt.savefig(path + 'time_vts.png')
