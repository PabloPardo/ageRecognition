from django.shortcuts import render, RequestContext, render_to_response


# Create your views here.
def home(request):
    context = RequestContext(request)
    return render_to_response('home.html', context)
