import json
import os
import time
import datetime
from django.db.models import Avg
from django_facebook.decorators import facebook_required_lazy
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import RequestContext, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.utils.image import Image
from apps.canvas.extra_functions import compare, calculate_score, plot_stats
from apps.canvas.models import UserProfile, Picture, Votes, Report
from apps.canvas.forms import UserForm, PictureForm, VoteForm, ReportForm
from django_facebook.api import get_facebook_graph
from django.db.models.fields.files import FieldFile
from ageRecognition.settings.base import Base
from ageRecognition.settings.local import SUPERUSER_ID


@facebook_required_lazy
def stats(request):

    # Get the graph from the FB API
    graph = get_facebook_graph(request=request)
    request.user.facebookprofile.facebook_id = graph.get('me', fields='id')['id']
    request.user.facebookprofile.save()

    if (not request.user.pk is None) and request.user.facebookprofile.facebook_id in SUPERUSER_ID:
        context = RequestContext(request)
        static_stats_path = Base.STATICFILES_DIRS[0] + '/static/stats/'

        # Get Data Base
        usr = list(UserProfile.objects.all().order_by('user__date_joined'))
        img = list(Picture.objects.all().order_by('date'))
        vte = list(Votes.objects.all().order_by('date'))
        rpt = list(Report.objects.all().order_by('date'))

        plot_stats(usr, img, vte, rpt, static_stats_path)

        context_dict = {
            'num_usr': len(usr),
            'num_img': len(img),
            'num_vte': len(vte),
            'num_rpt': len(rpt),
        }

        return render_to_response('stats.html', context_dict, context_instance=context)
    else:
        return HttpResponseRedirect('/canvas/terms/')


@facebook_required_lazy
def home(request):
    if (not request.user.pk is None) and request.user.userprofile.terms_conditions:
        # Computing Global Score of the current user
        calculate_score(request.user.userprofile)

        # Get the graph from the FB API
        if not 'num_friends' in request.session or not 'friends' in request.session:
            graph = get_facebook_graph(request=request)

            friends = graph.get('me/friends', fields='')['data']
            friends = [f['name'] for f in friends]
            request.session['friends'] = friends
            request.session['num_friends'] = len(friends)

        user_list = UserProfile.objects.exclude(pk=-1).order_by('-score_global')
        count = 0
        for u in user_list:
            count += 1
            if u.user.id == request.user.id:
                rank = count
                break

        context = RequestContext(request)
        context_dict = {'user': request.user,
                        'rank': rank}

        return render_to_response('home.html', context_dict, context_instance=context)
    else:
        return HttpResponseRedirect('/canvas/terms/')


@facebook_required_lazy
def game(request):
    if (not request.user.pk is None) and request.user.userprofile.terms_conditions:
        context = RequestContext(request)

        # Handle votes
        if request.method == 'POST':
            vote_form = VoteForm(data=request.POST, files=request.FILES)
            report_form = ReportForm(data=request.POST, files=request.FILES)

            votes_list = vote_form.data.getlist('vote')
            pics_id = request.POST.getlist('id_pic')
            if vote_form.is_valid():
                scores = []
                response = {'scores': scores, 'votes': votes_list}
                for i in range(len(votes_list)):
                    newvote = Votes()
                    newvote.vote = votes_list[i]
                    newvote.user = request.user.userprofile
                    newvote.pic = Picture.objects.get(id=pics_id[i])
                    newvote.date = str(datetime.datetime.now().date())

                    if newvote.pic.ground_truth == 0:
                        newvote.score = abs(newvote.pic.real_age - int(votes_list[i]))
                    else:
                        newvote.score = abs(newvote.pic.ground_truth - int(votes_list[i]))
                    scores.append(5 if newvote.score > 10 else 3*(10 - newvote.score))
                    newvote.save()

                    # Save cum_vote_score in user
                    newvote.user.cum_vote_score += int(newvote.score)
                    newvote.user.eval_pic += 1
                    newvote.user.save()

                    # Update Number of votes and Cumulative votes of the voted picture
                    newvote.pic.num_votes += 1
                    newvote.pic.cum_votes += int(newvote.vote)
                    newvote.pic.save()


                    # Update Ground Truth of the voted picture
                    newvote.pic.ground_truth = int(newvote.pic.cum_votes / newvote.pic.num_votes)
                    newvote.pic.save()

                    # Calculate the precision of the user
                    precision = newvote.user.cum_vote_score / newvote.user.eval_pic
                    newvote.user.ach_precision = 0 if precision > 10 else 10 - precision
                    newvote.user.save()

                    # Computing Global Score of the current user
                    calculate_score(request.user.userprofile)

                return HttpResponse(json.dumps(response), content_type="application/json")

            elif report_form.is_valid():

                newreport = Report()
                newreport.pic = Picture.objects.get(id=request.GET.get('id'))
                newreport.user = request.user.userprofile
                newreport.date = str(datetime.datetime.now().date())
                newreport.options = report_form.cleaned_data['options']
                newreport.other = report_form.cleaned_data['other']
                newreport.save()

                if Report.objects.filter(pic=newreport.pic).count() >= 3:
                    newreport.pic.visibility = False
                    newreport.pic.save()
                return HttpResponseRedirect('/canvas/game/')
            else:
                print vote_form.errors, report_form.errors
        else:
            vote_form = VoteForm()
            report_form = ReportForm()

        # Restrict the selected images to the ones the user haven't vote
        game_picture_list = Picture.objects.exclude(owner=request.user).exclude(visibility=False)

        try:
            user_votes_list = Votes.objects.values_list('pic__id').filter(user=request.user)
            voted_pics = [v[0] for v in user_votes_list]

            game_picture_list = game_picture_list.exclude(pk__in=voted_pics).filter(num_votes__lt=100)

            # Sort the images by the users global score (se the users with highest scores get their images voted more).
            game_picture_list = game_picture_list.order_by('-owner__score_global')
            id_list = [p.id for p in game_picture_list]

            # Sort the images by number of votes (images with less than 100 votes)
            pics_ord_by_votes = Picture.objects.filter(pk__in=id_list, num_votes__lt=100).order_by('num_votes')

            # SELECT x.num_votes,canvas_picture.* from canvas_picture LEFT JOIN (SELECT pic_id as vote_pic_id, Count(*)
            # as num_votes FROM canvas_votes GROUP BY pic_id) AS x ON canvas_picture.id=x.vote_pic_id ORDER BY num_votes

            # Get the four images to show:
            actual_game_pic_list = list(game_picture_list[:2])
            for i in range(pics_ord_by_votes.count()):
                if not pics_ord_by_votes[i].id in id_list[:2]:
                    actual_game_pic_list.append(pics_ord_by_votes[i])
                if len(actual_game_pic_list) == 4:
                    break

        except Exception, e:
            actual_game_pic_list = []
            print e

        # Get statistics of the actual game pictures
        actual_game_pic_stats = []
        for p in actual_game_pic_list:
            stats = {'num_votes': Votes.objects.filter(pic=p).count()}
            avg_votes = Votes.objects.filter(pic=p).annotate(avg=Avg('vote'))
            stats['avg_votes'] = int(avg_votes[0].avg) if avg_votes else 'No one voted yet'

            actual_game_pic_stats.append(stats)

        context_dict = {'vote_form': vote_form,
                        'report_form': report_form,
                        'user': request.user,
                        'game_pic_list': actual_game_pic_list,
                        'game_pic_stats': actual_game_pic_stats}

        if request.path == '/game/' or request.path == '/canvas/game/':
            return render_to_response('game.html', context_dict, context_instance=context)
        else:
            return render_to_response('report.html', context_dict, context_instance=context)
    else:
        return HttpResponseRedirect('/canvas/terms/')


@facebook_required_lazy
def ranking(request):
    if (not request.user.pk is None) and request.user.userprofile.terms_conditions:
        context = RequestContext(request)

        # Get the graph from the FB API
        if not 'friends' in request.session:
            graph = get_facebook_graph(request=request)

            friends = graph.get('me/friends', fields='')['data']
            friends = [f['name'] for f in friends]
            request.session['friends'] = friends

        # Computing Global Score of the current user
        calculate_score(request.user.userprofile)

        friends = request.session['friends']

        # Load users ordered by global score
        user_list = UserProfile.objects.exclude(pk=-1).order_by('-score_global')

        count = 0
        rank = -1
        for u in user_list:
            count += 1
            if u.user.id == request.user.id:
                rank = count
                break

        user_list = user_list[:50]
        user_rank = rank if rank > 50 else -1

        friends_user_list = UserProfile.objects.filter(user__facebookprofile__facebook_name__in=friends)
        friends_user_list = friends_user_list | UserProfile.objects.filter(user=request.user)
        friends_user_list = friends_user_list.order_by('-score_global')

        context_dict = {'users': user_list,
                        'user': request.user,
                        'rank': user_rank,
                        'friends': friends_user_list}

        return render_to_response('ranking.html', context_dict, context_instance=context)
    else:
        return HttpResponseRedirect('/canvas/terms/')


@facebook_required_lazy
def gallery(request):
    if (not request.user.pk is None) and request.user.userprofile.terms_conditions:
        context = RequestContext(request)

        # Load pictures for the home page
        user_pictures_list = Picture.objects.filter(owner=request.user, visibility=True)

        # Handle file upload
        if request.method == 'POST':

            pic_form = PictureForm(data=request.POST, files=request.FILES)

            if pic_form.files:
                real_age_list = pic_form.data.getlist('real_age')
                x = request.POST.getlist('x')
                y = request.POST.getlist('y')
                w = request.POST.getlist('w')
                h = request.POST.getlist('h')
                for i in range(len(pic_form.files)):
                    file_name = 'pic[' + str(i) + ']'
                    newpic = Picture()
                    newpic.pic = pic_form.files[file_name]
                    newpic.thurmnail = pic_form.files[file_name]
                    newpic.owner = request.user.userprofile
                    newpic.real_age = real_age_list[i]
                    newpic.date = str(datetime.datetime.now().date())

                    ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
                    file_extension = os.path.splitext(newpic.pic.path)[-1]
                    request.FILES[file_name].name = str(request.user.id) + '_' + str(i) + '_' + ts + file_extension
                    newpic.save()

                    # Add histogram to the pic
                    newpic.hist = json.dumps(Image.open(newpic.pic.path).convert('RGB').histogram())

                    # Crop Image if needed
                    img = Image.open(newpic.pic.path)
                    if int(float(x[i])) != -1:
                        left = int(float(x[i]))
                        top = int(float(y[i]))
                        width = int(float(w[i]))
                        height = int(float(h[i]))
                        newimg = img.crop((left, top, left + width, top + height))
                        newimg.save(Base.PROJECT_DIR + Base.MEDIA_URL + '/' + newpic.pic.name)
                        field = newpic.pic.field
                        name = newpic.pic.name
                        newpic.pic = FieldFile(newimg, field, name)

                    newpic.save()

                    # Check if the new image has been uploaded by the user
                    for p in range(user_pictures_list.count()-1):
                        if compare(json.loads(newpic.hist),  json.loads(user_pictures_list[p].hist)) < 0.1:
                            if not user_pictures_list[p].visibility:
                                user_pictures_list[p].visibility = True
                                user_pictures_list[p].save()
                            else:
                                request.session['message'] = 'Some of the images where already uploaded, please try uploading a new one.'

                            os.remove(newpic.pic.path)
                            newpic.delete()
                            break

                # Computing Global Score of the current user
                calculate_score(request.user.userprofile)

                # Redirect to the document list after POST
                return HttpResponse(json.dumps({}), content_type="application/json")
            else:
                print pic_form.errors

            if 'id_pic' in request.POST and 'vote' in request.POST:
                p = Picture.objects.get(id=request.POST['id_pic'])
                p.real_age = request.POST['vote']
                p.save()
                return HttpResponseRedirect('/gallery/')
        else:
            pic_form = PictureForm()  # A empty, unbound pic_form

        context_dict = {'pictures': user_pictures_list,
                        'user': request.user,
                        'pic_form': pic_form,
                        'message': request.session.get('message', '')}

        request.session['message'] = ''
        return render_to_response('gallery.html', context_dict, context_instance=context)
    else:
        return HttpResponseRedirect('/canvas/terms/')


@facebook_required_lazy
def rm_image(request, id_rm):
    p = Picture.objects.get(pk=id_rm)
    if request.user.id == p.owner.user.id:
        p.visibility = False
        p.save()

    return HttpResponseRedirect('/canvas/gallery/')


@facebook_required_lazy
def achievements(request):
    if (not request.user.pk is None) and request.user.userprofile.terms_conditions:
        context = RequestContext(request)

        # Get the graph from the FB API
        if not 'num_friends' in request.session:
            graph = get_facebook_graph(request=request)

            friends = graph.get('me/friends', fields='')['data']
            friends = [f['name'] for f in friends]
            request.session['num_friends'] = len(friends)

        num_friends = request.session['num_friends']


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

        for i in range(len(share_goals)):
            if num_friends < share_goals[i]:
                share = 'Invite ' + str(share_goals[i]) + ' of your friends to play'
                share_stars = stars[i]
                break
            elif num_friends >= share_goals[-1]:
                share = 'Keep inviting your friends'
                share_stars = stars[-1]

        if not request.user.pk is None:
            for i in range(len(precision_coments)):
                if request.user.userprofile.ach_precision == i:
                    precision = precision_coments[i]
                    precision_stars = stars[i]
                    break

            for i in range(len(vote_goals)):
                if request.user.userprofile.eval_pic < vote_goals[i]:
                    vote = 'Vote ' + str(vote_goals[i]) + ' pictures'
                    vote_stars = stars[i]
                    break
                elif request.user.userprofile.eval_pic >= vote_goals[-1]:
                    vote = 'Keep Voting'
                    vote_stars = stars[-1]

            for i in range(len(pic_goals)):
                if request.user.userprofile.upload_pic < pic_goals[i]:
                    pic = 'Upload ' + str(pic_goals[i]) + ' pictures'
                    pic_stars = stars[i]
                    break
                elif request.user.userprofile.upload_pic >= pic_goals[-1]:
                    pic = 'Keep uploading pictures'
                    pic_stars = stars[-1]
        else:
            precision = precision_coments[0]
            precision_stars = stars[0]
            vote = 'Vote ' + str(vote_goals[0]) + ' pictures'
            vote_stars = stars[0]
            pic = 'Upload ' + str(pic_goals[0]) + ' pictures'
            pic_stars = stars[0]

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
    else:
        return HttpResponseRedirect('/canvas/terms/')


@facebook_required_lazy
def privacy(request):
    if (not request.user.pk is None) and request.user.userprofile.terms_conditions:
        context = RequestContext(request)
        return render_to_response('privacy.html', context_instance=context)
    else:
        return HttpResponseRedirect('/canvas/terms/')


@facebook_required_lazy
def help(request):
    if (not request.user.pk is None) and request.user.userprofile.terms_conditions:
        context = RequestContext(request)
        return render_to_response('help.html', context_instance=context)
    else:
        return HttpResponseRedirect('/canvas/terms/')


@facebook_required_lazy
def prizes(request):
    if (not request.user.pk is None) and request.user.userprofile.terms_conditions:
        context = RequestContext(request)
        return render_to_response('prizes.html', context_instance=context)
    else:
        return HttpResponseRedirect('/canvas/terms/')


@csrf_exempt
def test(request):
    context = RequestContext(request)
    return render_to_response('test.html', context_instance=context)


@facebook_required_lazy
def terms(request):
    context = RequestContext(request)

    if not request.user.pk is None:  # If user is logged in
        if not request.user.userprofile.terms_conditions:  # If user has not sign the T&C
            if request.method == 'POST':
                user_form = UserForm(data=request.POST, files=request.FILES)
                if user_form.is_valid():
                    request.user.userprofile.terms_conditions = user_form.cleaned_data['terms_conditions']
                    request.user.userprofile.save()

                    # Get User's Home-town
                    if request.user.username:
                        if not request.user.userprofile.hometown:
                            # Get the graph from the FB API
                            graph = get_facebook_graph(request=request)

                            hometown = graph.get('me', fields='hometown')
                            if 'hometown' in hometown.keys():
                                request.user.userprofile.hometown = hometown['hometown']['name']
                            else:
                                request.user.userprofile.hometown = ''
                            request.user.userprofile.save()

                    return HttpResponseRedirect(reverse('apps.canvas.views.help'))
            else:
                user_form = UserForm()
            context_dict = {'user_form': user_form}

            return render_to_response('terms.html', context_dict, context_instance=context)
        else:
            return HttpResponseRedirect('/canvas/home/')

    return render_to_response('terms.html', context_instance=context)
