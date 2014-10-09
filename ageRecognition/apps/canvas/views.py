import time
import datetime
import random
from django.db.models import Count
from django.db.models.query import QuerySet
import imagehash
import cv2

from django.shortcuts import RequestContext, render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.image import Image
from apps.canvas.models import UserProfile, Picture, Votes, Report
from apps.canvas.forms import UserForm, PictureForm, VoteForm, ReportForm
from django_facebook.api import get_facebook_graph
from django_facebook.models import FacebookProfile


def home(request):
    context = RequestContext(request)

    # Terms & Conditions
    if not request.user.pk == None:
        if not request.user.userprofile.terms_conditions:
            if request.method == 'POST':
                user_form = UserForm(data=request.POST, files=request.FILES)
                if user_form.is_valid():
                    request.user.userprofile.terms_conditions = user_form.cleaned_data['terms_conditions']
                    request.user.userprofile.save()
                    return HttpResponseRedirect(reverse('apps.canvas.views.help'))
            else:
                user_form = UserForm()
            context_dict = {'user_form': user_form}

            return render_to_response('terms.html', context_dict, context_instance=context)

    # Get the graph from the FB API
    graph = get_facebook_graph(request=request)

    # Store messages
    messages = {}

    if request.user.username:
        if not request.user.userprofile.hometown:
            hometown = graph.get('me', fields='hometown')
            if 'hometown' in hometown.keys():
                request.user.userprofile.hometown = hometown['hometown']['name']
            else:
                request.user.userprofile.hometown = ''
            request.user.userprofile.save()

    # Load pictures for the home page
    user_pictures_list = Picture.objects.filter(owner=request.user)

    # Handle file upload
    if request.method == 'POST':

        pic_form = PictureForm(data=request.POST, files=request.FILES)

        if pic_form.files:
            real_age_list = pic_form.data.getlist('real_age')
            for i in range(0, len(pic_form.files)):
                file_name = 'pic[' + str(i) + ']'
                newpic = Picture()
                newpic.pic = pic_form.files[file_name]
                newpic.owner = request.user.userprofile
                newpic.real_age = real_age_list[i]
                newpic.date = str(datetime.datetime.now().date())

                ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
                request.FILES[file_name].name = str(request.user.id) + str(i) + '_' + ts + '.jpg'

                newpic.save()
                newpic.hash = imagehash.average_hash(Image.open('media/' + newpic.pic.name))
                newpic.save()

                # Update the number of uploaded pictures
                request.user.userprofile.upload_pic += 1

                #Update the global score:
                request.user.userprofile.score_global += 50
                request.user.userprofile.save()

                # Check if the new image has been uploaded by the user
                for p in range(0, user_pictures_list.count()-1):
                    if str(newpic.hash) == user_pictures_list[p].hash:
                        newpic.delete()
                        request.user.userprofile.upload_pic -= 1
                        request.user.userprofile.score_global -= 50
                        request.user.userprofile.save()

                        messages['repeated'] = 'This picture is already uploaded.'

                        print 'The image is has already been uploaded.'
                        break

            # Redirect to the document list after POST
            return HttpResponseRedirect('/upload/')
        else:
            print pic_form.errors

    else:
        pic_form = PictureForm()  # A empty, unbound pic_form


    context_dict = {'pic_form': pic_form,
                    'user': request.user,
                    'messages': messages}

    if request.path == '/upload/':
        return render_to_response('upload.html', context_dict, context_instance=context)
    else:
        return render_to_response('home.html', context_dict, context_instance=context)


def game(request):
    context = RequestContext(request)

    user_votes_list = Votes.objects.filter(user=request.user)

    # Chose a random picture to guess
    # Restrict the selected images to the ones the user haven't vote
    game_picture_list = Picture.objects.exclude(owner=request.user).exclude(visibility=False)

    try:
        UserProfile.objects.select_related('pic')
        voted_pics = [v.pic for v in user_votes_list]
        game_picture_list = game_picture_list.exclude(pic__in=voted_pics)

        # Sort the images by the users global score (se the users with highest scores get their images voted more).
        game_picture_list = game_picture_list.order_by('-owner__score_global')

        # Sort the images by number of votes
        pics_ord_by_votes = Picture.objects.raw("SELECT canvas_picture.* from canvas_picture LEFT JOIN (SELECT pic_id as vote_pic_id, Count(*) as num_votes FROM canvas_votes GROUP BY pic_id) ON canvas_picture.id=vote_pic_id ORDER BY num_votes")

        # Sort the images by number of ppl from

        # Get the four images to show:
        actual_game_pic_list = game_picture_list[:4]

        random_idx = random.randint(0, game_picture_list.count() - 1)
        actual_game_picture = game_picture_list[random_idx]
    except:
        actual_game_picture = []
        actual_game_pic_list = []

    # Handle file upload
    if request.method == 'POST':
        vote_form = VoteForm(data=request.POST, files=request.FILES)
        report_form = ReportForm(data=request.POST, files=request.FILES)

        if vote_form.is_valid():
            newvote = vote_form.save(commit=False)
            newvote.vote = vote_form.cleaned_data['vote']
            newvote.user = request.user.userprofile
            newvote.pic = actual_game_picture
            newvote.date = str(datetime.datetime.now().date())

            if actual_game_picture.ground_truth == 0:
                if actual_game_picture.real_age:
                    newvote.score = abs(actual_game_picture.real_age - vote_form.cleaned_data['vote'])
                else:
                    newvote.score = 1
            else:
                newvote.score = abs(actual_game_picture.ground_truth - vote_form.cleaned_data['vote'])
            newvote.save()

            # Update the number of voted pictures
            request.user.userprofile.eval_pic += 1

            # Update the global score
            if newvote.score > 10:
                request.user.userprofile.score_global += 1
            else:
                request.user.userprofile.score_global += 1 + 2*(10 - newvote.score)

            # Update Ground Truth of the voted picture
            if actual_game_picture.ground_truth == 0:
                actual_game_picture.ground_truth = newvote.vote
            else:
                votes_act_pic = Votes.objects.filter(pic=actual_game_picture)
                gt = 0.
                for v in votes_act_pic:
                    gt += v.vote
                gt = int(gt / votes_act_pic.count())
                actual_game_picture.ground_truth = gt

            actual_game_picture.save()

            # Calculate the score of the user
            user_votes_scores_list = [v.score for v in user_votes_list].append(newvote.score)
            try:
                assert isinstance(user_votes_scores_list, list)
            except:
                user_votes_scores_list = [newvote.score]

            precision = sum(user_votes_scores_list)/(len(user_votes_scores_list))
            if precision > 10:
                request.user.userprofile.ach_precision = 0
            else:
                request.user.userprofile.ach_precision = 10 - precision

            request.user.userprofile.save()

            # Redirect to the document list after POST
            return HttpResponseRedirect('/game/')
        elif report_form.is_valid():
            newreport = report_form.save(commit=False)
            newreport.pic = actual_game_picture
            newreport.user = request.user.userprofile
            newreport.date = str(datetime.datetime.now().date())

            if Report.objects.filter(pic=actual_game_picture).count() >= 3:
                actual_game_picture.visibility = False
                actual_game_picture.save()
            return HttpResponseRedirect('/game/')
        else:
            print vote_form.errors, report_form.errors
    else:
        vote_form = VoteForm()
        report_form = ReportForm()

    context_dict = {'vote_form': vote_form,
                    'report_form': report_form,
                    'user': request.user,
                    'game_pic_list': actual_game_pic_list}

    if request.path == '/game/':
        return render_to_response('game.html', context_dict, context_instance=context)
    else:
        return render_to_response('report.html', context_dict, context_instance=context)


def ranking(request):
    context = RequestContext(request)

    # Get the graph from the FB API
    graph = get_facebook_graph(request=request)
    friends = graph.get('me/friends', fields='')['data']
    friends = [f['name'] for f in friends]

    # Load users ordered by global score
    user_list = UserProfile.objects.exclude(pk=-1)[:20]

    friends_user_list = UserProfile.objects.filter(user__facebookprofile__facebook_name__in=friends)
    friends_user_list = friends_user_list | UserProfile.objects.filter(user=request.user)

    context_dict = {'users': user_list,
                    'user': request.user,
                    'friends': friends_user_list}

    return render_to_response('ranking.html', context_dict, context_instance=context)


def gallery(request):
    context = RequestContext(request)

    # Load pictures for the home page
    user_pictures_list = Picture.objects.filter(owner=request.user)

    context_dict = {'pictures': user_pictures_list,
                    'user': request.user}

    return render_to_response('gallery.html', context_dict, context_instance=context)


def achievements(request):
    context = RequestContext(request)

     # Get the graph from the FB API
    graph = get_facebook_graph(request=request)
    num_friends = len(graph.get('me/friends', fields='')['data'])

    stars = ['<i class="fa fa-star-o"><i class="fa fa-star-o"><i class="fa fa-star-o"><i class="fa fa-star-o"><i class="fa fa-star-o">',
             '<i class="fa fa-star-half-o"><i class="fa fa-star-o"><i class="fa fa-star-o"><i class="fa fa-star-o"><i class="fa fa-star-o">',
             '<i class="fa fa-star"><i class="fa fa-star-o"><i class="fa fa-star-o"><i class="fa fa-star-o"><i class="fa fa-star-o">',
             '<i class="fa fa-star"><i class="fa fa-star-half-o"><i class="fa fa-star-o"><i class="fa fa-star-o"><i class="fa fa-star-o">',
             '<i class="fa fa-star"><i class="fa fa-star"><i class="fa fa-star-o"><i class="fa fa-star-o"><i class="fa fa-star-o">',
             '<i class="fa fa-star"><i class="fa fa-star"><i class="fa fa-star-half-o"><i class="fa fa-star-o"><i class="fa fa-star-o">',
             '<i class="fa fa-star"><i class="fa fa-star"><i class="fa fa-star"><i class="fa fa-star-o"><i class="fa fa-star-o">',
             '<i class="fa fa-star"><i class="fa fa-star"><i class="fa fa-star"><i class="fa fa-star-half-o"><i class="fa fa-star-o">',
             '<i class="fa fa-star"><i class="fa fa-star"><i class="fa fa-star"><i class="fa fa-star"><i class="fa fa-star-o">',
             '<i class="fa fa-star"><i class="fa fa-star"><i class="fa fa-star"><i class="fa fa-star"><i class="fa fa-star-half-o">',
             '<i class="fa fa-star"><i class="fa fa-star"><i class="fa fa-star"><i class="fa fa-star"><i class="fa fa-star">',
             ]

    precision_coments = ['This is awkward',
                         'You should check your sight',
                         'That\'s all you can do?',
                         'Well, you can do better',
                         'Good, but try harder',
                         'You are in the right track, keep improving',
                         'Well done',
                         'Great!',
                         'Excellent guessing skills!',
                         'Incredible, you are reaching perfection',
                         'Amazing! Prefect precision!']

    share_goals = [1, 3, 5, 7, 10, 15, 20, 25, 35, 50]
    vote_goals = [5, 10, 20, 50, 150, 400, 1000, 5000, 12000, 30000]
    pic_goals = [1, 2, 5, 10, 15, 30, 50, 75, 100, 200]

    for i in range(0, len(share_goals)):
        if num_friends < share_goals[i]:
            share = 'Invite ' + str(share_goals[i]) + ' of your friends to play'
            share_stars = stars[i]
            break
        elif num_friends >= share_goals[-1]:
            share = 'Keep inviting your friends'
            share_stars = stars[-1]

    for i in range(0, len(precision_coments)):
        if request.user.userprofile.ach_precision == i:
            precision = precision_coments[i]
            precision_stars = stars[i]
            break

    for i in range(0, len(vote_goals)):
        if request.user.userprofile.eval_pic < vote_goals[i]:
            vote = 'Vote ' + str(vote_goals[i]) + ' pictures'
            vote_stars = stars[i]
            break
        elif request.user.userprofile.eval_pic >= vote_goals[-1]:
            vote = 'Keep Voting'
            vote_stars = stars[-1]

    for i in range(0, len(pic_goals)):
        if request.user.userprofile.upload_pic < pic_goals[i]:
            pic = 'Upload ' + str(pic_goals[i]) + ' pictures'
            pic_stars = stars[i]
            break
        elif request.user.userprofile.upload_pic >= pic_goals[-1]:
            pic = 'Keep uploading pictures'
            pic_stars = stars[-1]

    context_dict = {'user': request.user,
                    'num_friends': num_friends,
                    'share_stars': share_stars,
                    'share': share,
                    'precision': precision,
                    'precision_stars': precision_stars,
                    'vote': vote,
                    'vote_stars': vote_stars,
                    'pic': pic,
                    'pic_stars': pic_stars}

    return render_to_response('achievements.html', context_dict, context_instance=context)


def policy(request):
    context = RequestContext(request)
    return render_to_response('policy.html', context_instance=context)


def help(request):
    context = RequestContext(request)
    return render_to_response('help.html', context_instance=context)
