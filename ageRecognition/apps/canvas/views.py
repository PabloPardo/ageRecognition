import time
import datetime
import random
import imagehash
import cv2

from django.shortcuts import RequestContext, render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.image import Image
from apps.canvas.models import UserProfile, Picture, Votes, Report
from apps.canvas.forms import PictureForm, VoteForm, ReportForm
from django_facebook.api import get_facebook_graph


def home(request):
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

    context = RequestContext(request)

    # Load pictures for the home page
    user_pictures_list = Picture.objects.filter(owner=request.user)

    # Handle file upload
    if request.method == 'POST':

        pic_form = PictureForm(data=request.POST, files=request.FILES)

        if pic_form.is_valid():

            # Since we need to set the new picture attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            newpic = pic_form.save(commit=False)
            newpic.pic = pic_form.cleaned_data['pic']
            newpic.owner = request.user.userprofile
            newpic.real_age = pic_form.cleaned_data['real_age']
            newpic.date = str(datetime.datetime.now().date())

            if request.FILES.has_key('pic'):
                ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
                request.FILES['pic'].name = str(request.user.id) + '_' + ts + '.jpg'

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

            # TODO: Improve detection accuracy
            # if newpic.pk:
            #     # Check if there is a single face in the image
            #     imagePath = 'media/' + newpic.pic.name
            #     cascPath = 'haarcascade_frontalface_default.xml'
            #
            #     # Create the haar cascade
            #     faceCascade = cv2.CascadeClassifier(cascPath)
            #
            #     # Read the image
            #     image = cv2.imread(imagePath)
            #     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            #
            #     # Detect faces in the image
            #     faces = faceCascade.detectMultiScale(
            #         gray,
            #         scaleFactor=1.1,
            #         minNeighbors=2,
            #         minSize=(30, 30),
            #         flags = cv2.cv.CV_HAAR_SCALE_IMAGE
            #     )
            #
            #     # Check if the new image contains just one face
            #     if len(faces) != 1:
            #         newpic.delete()
            #         request.user.userprofile.upload_pic -= 1
            #         request.user.userprofile.score_global -= 50
            #         request.user.userprofile.save()
            #
            #         messages['noOneFace'] = 'The image must contain exactly one person.'
            #
            #         print 'The image must contain exactly one person.'

            # Redirect to the document list after POST
            return HttpResponseRedirect(reverse('apps.canvas.views.home'))
        else:
            print pic_form.errors

    else:
        pic_form = PictureForm()  # A empty, unbound pic_form

    context_dict = {'pic_form': pic_form,
                    'user': request.user,
                    'messages': messages}

    return render_to_response('home.html', context_dict, context_instance=context)


def game(request):
    context = RequestContext(request)

    user_votes_list = Votes.objects.filter(user=request.user)

    # Chose a random picture to guess
    # Restrict the selected images to the ones the user haven't vote
    game_picture_list = Picture.objects.exclude(owner=request.user)

    try:
        voted_pics = [v.pic for v in user_votes_list]
        for v in voted_pics:
            game_picture_list = game_picture_list.exclude(pic=v)

        random_idx = random.randint(0, game_picture_list.count() - 1)
        actual_game_picture = game_picture_list[random_idx]
    except:
        actual_game_picture = []

    # Handle file upload
    if request.method == 'POST':
        vote_form = VoteForm(data=request.POST, files=request.FILES)

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
            return HttpResponseRedirect(reverse('apps.canvas.views.game'))
        else:
            print vote_form.errors
    else:
        vote_form = VoteForm()

    context_dict = {'vote_form': vote_form,
                    'user': request.user,
                    'game_pic': actual_game_picture}

    return render_to_response('game.html', context_dict, context_instance=context)


def ranking(request):
    context = RequestContext(request)

    # Load users ordered by global score
    user_list = UserProfile.objects.exclude(pk=-1).order_by('-score_global')[:20]

    context_dict = {'users': user_list,
                    'user': request.user}

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
    context_dict = {'user': request.user}
    return render_to_response('achievements.html', context_dict, context_instance=context)


def report(request):
    context = RequestContext(request)

    if request.method == 'POST':
        report_form = ReportForm(data=request.POST, files=request.FILES)
        if report_form.is_valid():
            newreport = report_form.save(commit=False)
            newreport.pic
            return HttpResponseRedirect(reverse('apps.canvas.views.home'))
        else:
            print report_form.errors
    else:
        report_form = ReportForm()

    context_dict = {'report_form': report_form}

    return render_to_response('report.html', context_dict, context_instance=context)