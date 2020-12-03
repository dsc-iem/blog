from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from dscblog.common import to_json, apiRespond
from django.contrib.sessions.models import Session
from dscblog.models import User, Blog, Featured, Reaction, Comment, View, Topic
from dscblog.forms import UserSettingsForm
import markdown
import html
from pyembed.markdown import PyEmbedMarkdown
import bleach
from bleach_allowlist import markdown_tags, markdown_attrs, all_styles
from urllib.parse import urlparse
from dscblog.settings import BASE_URL


markdown_attrs['*'] += ['class']

md_tags = markdown_tags+['dl','table','thead','tr','th','tbody','td']

md = markdown.Markdown(
    extensions=['extra', 'fenced_code', 'markdown.extensions.codehilite'])


def convert_session_to_user(request):
    session = get_session(request)
    if request.user.is_authenticated and session != None:
        if request.session.get('has_views', False):
            View.convert_to_user(session, request.user)
            request.session['has_views'] = False


def get_domain_from_url(url):
    parsed_uri = urlparse(url)
    result = '{uri.netloc}'.format(uri=parsed_uri)
    return result


def get_session(request):
    try:
        return Session.objects.get(session_key=request.session.session_key)
    except:
        return None


def get_catagories(request):
    user = None
    session = None
    if request.user.is_authenticated:
        user = request.user
    else:
        session = get_session(request)
    return User.get_catagories(user, session)


def page_loader(request, **args):
    opts = {'header': {
        'is_loggedin': False, 'is_empty': True}}
    res = render(request, args['page']+'.html', opts)
    return res


def check_referer(request):
    return render(request, 'referer.html', {'ref': get_domain_from_url(request.META.get('HTTP_REFERER', ''))})


def index(request):
    convert_session_to_user(request)
    opts = {'header': {
        'is_loggedin': False, 'is_empty': False}, 'cat': get_catagories(request), 'active_cat': 'all'}
    opts['blogs'] = []
    if request.user.is_authenticated:
        opts['header']['is_loggedin'] = True
        opts['blogs'] = User.get_feed(request.user)
    else:
        opts['blogs'] = User.get_feed()
    try:
        featured = Featured.pickOne().blog
    except Exception as e:
        print(e)
        opts['featured_blog'] = None
    else:
        opts['featured_blog'] = featured.get_obj_min()
        opts['featured_blog']['intro'] = html.escape(featured.content[:300])
    res = render(request, 'index.html', opts)
    return res


def top25(request):
    convert_session_to_user(request)
    opts = {'header': {
        'is_loggedin': False, 'is_empty': False}, 'cat': get_catagories(request), 'active_cat': 'popular'}
    if request.user.is_authenticated:
        opts['header']['is_loggedin'] = True
    opts['blogs'] = []
    blogs = Blog.top25()
    for b in blogs:
        opts['blogs'].append(b.get_obj_min())
    res = render(request, 'top25.html', opts)
    return res


def new_blogs(request):
    convert_session_to_user(request)
    opts = {'header': {
        'is_loggedin': False, 'is_empty': False}, 'cat': get_catagories(request), 'active_cat': 'new'}
    if request.user.is_authenticated:
        opts['header']['is_loggedin'] = True
    opts['blogs'] = []
    blogs = Blog.recents()[:30]
    for b in blogs:
        opts['blogs'].append(b.get_obj_min())
    res = render(request, 'new.html', opts)
    return res


def trending_blogs(request):
    convert_session_to_user(request)
    opts = {'header': {
        'is_loggedin': False, 'is_empty': False}, 'cat': get_catagories(request), 'active_cat': 'trending'}
    if request.user.is_authenticated:
        opts['header']['is_loggedin'] = True
    opts['blogs'] = []
    blogs = Blog.trending()[:30]
    for b in blogs:
        opts['blogs'].append(b.get_obj_min())
    res = render(request, 'trending.html', opts)
    return res


def topic(request, topic):
    _topic = topic.strip().lower().replace(" ", "")
    if _topic == topic:
        convert_session_to_user(request)
        opts = {'header': {
            'is_loggedin': False, 'is_empty': False}, 'cat': get_catagories(request), 'active_cat': topic}
        if request.user.is_authenticated:
            opts['header']['is_loggedin'] = True
        opts['blogs'] = []
        try:
            t = Topic.get_by_name(topic)
        except:
            pass
        else:
            blogs = t.top_blogs()[:30]
            for b in blogs:
                opts['blogs'].append(b.get_obj_min())
        res = render(request, 'topic.html', opts)
        return res
    else:
        return redirect(to='/topic/'+_topic)


@login_required
def my_profile(request):
    return redirect(to='/@'+request.user.username)


def cat(request, topic):
    pages = ['popular', 'new', 'trending']
    if topic == 'all':
        return redirect(to='/')
    elif topic in pages:
        return redirect(to='/'+topic)
    else:
        return redirect(to='/topic/'+topic)


def followers(request, username):
    try:
        user = User.get_by_username(username)
    except:
        return page404(request)
    else:
        data = {'header': {'is_loggedin': True},
                'user': user.get_profile_min(), 'chaselist': []}
        chaselist = user.get_followers()
        for follower in chaselist:
            data['chaselist'].append(follower.user.get_profile_min())
        return render(request, 'followers.html', data)


@login_required
def blog_reactions(request, id):
    convert_session_to_user(request)
    try:
        b = Blog.get_by_id(id)
    except:
        return page404(request)
    else:
        if request.user == b.author:
            data = {'header': {'is_loggedin': True, 'float': True},
                    'users': [], 'blog': b.get_obj_min()}
            reactions = b.get_reactions()
            for reaction in reactions:
                obj = reaction.user.get_profile_min()
                obj['reaction'] = reaction.reaction
                data['users'].append(obj)
            return render(request, 'reactions.html', data)
        else:
            return page404(request)


@login_required
def user_settings(request):
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('/profile')
    else:
        form = UserSettingsForm(instance=request.user)
    opts = {'header': {
        'is_loggedin': True, 'is_empty': False, 'float': True},
        'form': form}
    return render(request, 'userSettings.html', opts)


def profile(request, username):
    convert_session_to_user(request)
    opts = {'header': {
        'is_loggedin': False, 'is_empty': False, 'float': True},
        'is_owner': request.user.is_authenticated and request.user.username == username}
    if request.user.is_authenticated:
        opts['header']['is_loggedin'] = True
    try:
        user = User.get_by_username(username)
    except:
        return page404(request)
    else:
        opts['user'] = user.get_profile(
            request.user if request.user.is_authenticated else None)
        res = render(request, 'profile.html', opts)
        return res


def blog(request, slug, id):
    convert_session_to_user(request)
    try:
        b = Blog.get_by_id(id)
    except:
        return page404(request)
    else:
        if b.get_slug() == slug:
            if b.is_published or (request.user.is_authenticated and request.user == b.author):
                htm = bleach.clean(md.reset().convert(
                    b.content), tags=md_tags, attributes=markdown_attrs, styles=all_styles)
                opts = {'header': {
                    'is_loggedin': False, 'is_empty': False},
                    'BASE_URL':BASE_URL,
                    'blog': b.get_obj(user=request.user if request.user.is_authenticated else None),
                    'html': htm,
                    'more_blogs': [],
                    'is_owner': request.user.is_authenticated and request.user == b.author}
                ref = get_domain_from_url(
                    request.META.get('HTTP_REFERER', ''))
                if request.user.is_authenticated:
                    opts['header']['is_loggedin'] = True
                    view_key = View.create(
                        user=request.user, blog=b, referer=ref)
                    opts['more_blogs'] = b.related_blogs(user=request.user)
                else:
                    request.session['has_views'] = True
                    view_key = View.create(
                        user=None, blog=b, session=get_session(request), referer=ref)
                    opts['more_blogs'] = b.related_blogs(
                        session=get_session(request))
                opts['view_key'] = view_key
                res = render(request, 'blog.html', opts)
                return res
            else:
                return page404(request)
        else:
            return redirect(to=b.get_url())


def blog_comments(request, blog_id):
    convert_session_to_user(request)
    try:
        b = Blog.get_by_id(blog_id)
    except:
        return page404(request)
    else:
        user = request.user if request.user.is_authenticated else None
        if b.is_published or (request.user.is_authenticated and request.user == b.author):
            opts = {'comments': [],
                    'blog': b.get_obj_min(),
                    'is_owner': request.user.is_authenticated and request.user == b.author}
            comments = b.get_comments()
            for comment in comments:
                opts['comments'].append(comment.get_obj(user=user))
            res = render(request, 'comments.html', opts)
            return res
        else:
            return page404(request)


@login_required
def create(request):
    if request.method == 'GET':
        res = render(request, 'create.html')
    else:
        if 'title' in request.POST:
            title = request.POST['title'].strip()
            if len(title) > 2:
                b = Blog.create(request.user, title)
                res = redirect(to='/blog/'+str(b.id)+'/edit')
            else:
                res = render(request, 'create.html', {
                             'error': 'Title too small (min 3 characters)'})
        else:
            res = render(request, 'create.html', {
                         'error': 'Title field missing'})
    return res


@login_required
def blog_settings(request, id):
    try:
        b = Blog.get_by_id(id)
    except:
        return page404(request)
    else:
        if request.user == b.author:
            opts = {'header': {'is_loggedin': True, 'is_empty': False, 'float': True},
                    'blog': b.get_obj_min()}
            topics = []
            for topic in b.get_topics():
                topics.append(topic.name)
            opts['blog']['topics'] = to_json(topics)
            return render(request, 'blogSettings.html', opts)
        else:
            return page404(request)


@login_required
def blog_edit(request, id):
    try:
        b = Blog.get_by_id(id)
    except:
        return page404(request)
    else:
        if request.user == b.author:
            opts = {'header': {'is_loggedin': True, 'is_empty': False},
                    'blog': b.get_obj(escape_html=False)}
            return render(request, 'blogEditor.html', opts)
        else:
            return page404(request)


@require_http_methods(["POST"])
def pingback(request):
    if 'view_key' in request.POST:
        try:
            view = View.get_by_key(request.POST['view_key'])
        except:
            return apiRespond(400, msg='View not found')
        else:
            pingbacks = view.pingback()
            return apiRespond(201, pingbacks=pingbacks)
    else:
        return apiRespond(400, msg='Pingback: Required fields missing')


@require_http_methods(["POST"])
def follow_user(request):
    if request.user.is_authenticated:
        if 'user_id' in request.POST:
            try:
                target = User.get_by_id(request.POST['user_id'])
            except:
                return apiRespond(400, msg='Target user not found')
            else:
                result = request.user.follow(target)
                return apiRespond(201, result=result)
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def unfollow_user(request):
    if request.user.is_authenticated:
        if 'user_id' in request.POST:
            try:
                target = User.get_by_id(request.POST['user_id'])
            except:
                return apiRespond(400, msg='Target user not found')
            else:
                result = request.user.unfollow(target)
                return apiRespond(201, result=result)
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def blog_react(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST and 'reaction' in request.POST and request.POST['reaction'] in Reaction.CODES:
            reaction = request.POST['reaction']
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Target blog not found')
            else:
                obj = request.user.react(blog=b, reaction=reaction)
                return apiRespond(201, result=True)
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def blog_unreact(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST:
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Target blog not found')
            else:
                res = request.user.unreact(blog=b)
                return apiRespond(201, result=res)
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def blog_comment(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST and 'text' in request.POST and len(request.POST['text'].strip()) > 2:
            ref = None
            if 'ref_comment_id' in request.POST:
                ref_id = request.POST['ref_comment_id']
                try:
                    ref = Comment.get_by_id(ref_id)
                except:
                    return apiRespond(400, msg='Reference comment not found')
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Target blog not found')
            else:
                comment = request.user.comment(
                    blog=b, text=request.POST['text'].strip(), reference=ref)
                return apiRespond(201, comment=comment.get_obj())
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def blog_uncomment(request):
    if request.user.is_authenticated:
        if 'comment_id' in request.POST:
            try:
                comment = Comment.get_by_id(request.POST['comment_id'])
            except:
                return apiRespond(400, msg='Target comment not found')
            else:
                if comment.user == request.user:
                    comment.delete()
                return apiRespond(201, result=True)
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def set_blog_title(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST and 'title' in request.POST:
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Blog not found')
            else:
                if b.author == request.user:
                    title = request.POST['title'].strip()
                    if len(title) > 2:
                        b.update_title(title)
                        return apiRespond(201, title=title)
                    else:
                        return apiRespond(400, msg='Title too short')
                else:
                    return apiRespond(400, msg='Access denied')
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def add_blog_topic(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST and 'topic' in request.POST:
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Blog not found')
            else:
                if b.author == request.user:
                    topic = request.POST['topic'].strip(
                    ).lower().replace(" ", "")
                    if len(topic) > 1:
                        if topic not in Topic.BANNED:
                            if not b.has_topic(topic):
                                b.add_topic(topic)
                                return apiRespond(201, topic=topic)
                            else:
                                return apiRespond(400, msg='Topic already tagged')
                        else:
                            return apiRespond(400, msg='This topic is disabled')
                    else:
                        return apiRespond(400, msg='Topic name too short')
                else:
                    return apiRespond(400, msg='Access denied')
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def remove_blog_topic(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST and 'topic' in request.POST:
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Blog not found')
            else:
                if b.author == request.user:
                    topic = request.POST['topic'].strip(
                    ).lower().replace(" ", "")
                    if b.remove_topic(topic):
                        return apiRespond(201, topic=topic)
                    else:
                        return apiRespond(400, msg='Could not remove the topic')
                else:
                    return apiRespond(400, msg='Access denied')
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def set_blog_img(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST and 'img_url' in request.POST:
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Blog not found')
            else:
                if b.author == request.user:
                    img_url = request.POST['img_url'].strip()
                    if len(img_url) > 2:
                        b.update_img(img_url)
                        return apiRespond(201, img_url=img_url)
                    else:
                        return apiRespond(400, msg='img_url too short')
                else:
                    return apiRespond(400, msg='Access denied')
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def publish_blog(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST:
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Blog not found')
            else:
                if b.author == request.user:
                    b.publish()
                    return apiRespond(201, is_published=b.is_published)
                else:
                    return apiRespond(400, msg='Access denied')
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def unpublish_blog(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST:
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Blog not found')
            else:
                if b.author == request.user:
                    b.unpublish()
                    return apiRespond(201, is_published=b.is_published)
                else:
                    return apiRespond(400, msg='Access denied')
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def delete_blog(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST:
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Blog not found')
            else:
                if b.author == request.user:
                    b.remove()
                    return apiRespond(201, removed=True)
                else:
                    return apiRespond(400, msg='Access denied')
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


@require_http_methods(["POST"])
def set_blog_content(request):
    if request.user.is_authenticated:
        if 'blog_id' in request.POST and 'content' in request.POST:
            try:
                b = Blog.get_by_id(request.POST['blog_id'])
            except:
                return apiRespond(400, msg='Blog not found')
            else:
                if b.author == request.user:
                    content = request.POST['content']
                    b.update_content(content)
                    return apiRespond(201)
                else:
                    return apiRespond(400, msg='Access denied')
        else:
            return apiRespond(400, msg='Required fields missing')
    else:
        return apiRespond(401, msg='User not logged in')


def page404(request, exception=None):
    response = render(request, '404.html')
    response.status_code = 404
    return response
