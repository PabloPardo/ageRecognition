import time
import datetime
import random
import math
import operator

from django.shortcuts import RequestContext, render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.image import Image
from apps.canvas.models import UserProfile, Picture, Votes
from apps.canvas.forms import PictureForm, VoteForm
from django.contrib.auth import logout as django_logout


# Create your views here.
def home(request):
    context = RequestContext(request)

    # Load pictures for the home page
    user_pictures_list = Picture.objects.filter(owner=request.user)

    # Load users for the home page
    user_list = UserProfile.objects.order_by('-score_global')[:5]

    # Load votes for the home page
    user_votes_list = Votes.objects.filter(user=request.user)

    # Chose a random picture to guess
    # Restrict the selected images to the ones the user haven't vote
    voted_pics = [v.pic for v in user_votes_list]
    game_picture_list = Picture.objects.exclude(owner=request.user).exclude(pic=voted_pics)

    try:
        random_idx = random.randint(0, game_picture_list.count() - 1)
        actual_game_picture = game_picture_list[random_idx].save(commit=False)
    except:
        actual_game_picture = []

    # Handle file upload
    if request.method == 'POST':

        pic_form = PictureForm(data=request.POST, files=request.FILES)
        vote_form = VoteForm(data=request.POST, files=request.FILES)

        if pic_form.is_valid():

            # Since we need to set the new picture attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            newpic = pic_form.save(commit=False)
            newpic.pic = pic_form.cleaned_data['pic']
            newpic.owner = request.user.userprofile

            if request.FILES.has_key('pic'):
                ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
                request.FILES['pic'].name = str(request.user.id) + '_' + ts + '.jpg'

            newpic.save()

            # Update the number of uploaded pictures
            request.user.userprofile.upload_pic += 1
            request.user.userprofile.save()

            # TODO: Check if the new image has been uploaded by the user
            # for p in user_pictures_list:
            # h1 = Image.open('media/' + p.pic.name)

            #     Problem accessing the Uploaded Image, is not saves so
            #     the image is in a InMemoryUploadedFile variable.

            #     h2 = Image.open('media/images/uploaded_images' + request.FILES['pic'].name)
            #
            #     rms = math.sqrt(reduce(operator.add, map(lambda a, b: (a-b)**2, h1, h2))/len(h1))
            #
            #     if rms > 0.1:
            #         newpic.save()
            #         newpic.delate()
            #
            #         # Update the number of uploaded pictures
            #         request.user.userprofile.upload_pic += 1
            #         request.user.userprofile.save()
            #     else:
            #         print pic_form.errors

            # TODO: Check if there is a single face in the image

            # Redirect to the document list after POST
            return HttpResponseRedirect(reverse('apps.canvas.views.home'))
        elif vote_form.is_valid():
            newvote = vote_form.save(commit=False)
            newvote.vote = vote_form.cleaned_data['vote']
            newvote.user = request.user.userprofile
            newvote.pic = actual_game_picture

            newvote.save()

            # Update the number of voted pictures
            request.user.userprofile.eval_pic += 1
            request.user.userprofile.save()

            # Update Ground Truth of the voted picture
            # TODO: Calculate the score according the difference between the vote and the ground truth
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

            # Redirect to the document list after POST
            return HttpResponseRedirect(reverse('apps.canvas.views.home'))
        else:
            print pic_form.errors, vote_form.errors

    else:
        pic_form = PictureForm()  # A empty, unbound pic_form
        vote_form = VoteForm()  # A empty, unbound vote_form

    # Create dictionary with the list of users, the list of pictures and the pic_form
    context_dict = {'users': user_list,
                    'pictures': user_pictures_list,
                    'pic_form': pic_form,
                    'vote_form': vote_form,
                    'user': request.user,
                    'game_pic': actual_game_picture}

    # Render list page with the documents and the pic_form
    return render_to_response('home.html', context_dict, context_instance=context)
