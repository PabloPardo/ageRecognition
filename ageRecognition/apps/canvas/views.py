from django.shortcuts import render, RequestContext, render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django_facebook.models import FacebookCustomUser
from apps.canvas.models import UserProfile, Picture
from apps.canvas.forms import PictureForm


# Create your views here.
def home(request):
    context = RequestContext(request)
    # if not hasattr(request.user, 'UserProfile') and request.user.is_authenticated:
        # request.user.userprofile = UserProfile.objects.get_or_create(user_id=request.user.facebook_id)

    # Handle file upload
    if request.method == 'POST':
        form = PictureForm(request.POST, request.FILES)
        if form.is_valid():
            newpic = Picture(pic=request.FILES['pic'], owner=request.user.userprofile)

            # TODO: Check if the new image has been uploaded by the user.

            newpic.save()

            # Update the number of uploaded pictures
            request.user.userprofile.upload_pic += 1
            request.user.userprofile.save()

            # RedirUserProfile.objects.filter(user.id = request.user.id)ect to the document list after POST
            return HttpResponseRedirect(reverse('apps.canvas.views.home'))
    else:
        form = PictureForm()  # A empty, unbound form

    # TODO: load a random image (excluding the images uploaded by the user and the
    # TODO: images already voted) and change the image every time the user uploades a vote

    # Load pictures for the home page
    pictures = Picture.objects.all()

    # Load users for the home page
    user_list = UserProfile.objects.order_by('-score_global')[:5]  # filter('user_id' >= 0)

    # Create dictionary with the list of users, the list of pictures and the form
    context_dict = {'users': user_list, 'pictures': pictures, 'form': form, 'user': request.user}

    # Render list page with the documents and the form
    return render_to_response('home.html', context_dict, context_instance=context)
