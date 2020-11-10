from django.db import models
from django.db.models import Q, F, Avg, Count, Min, Sum, ExpressionWrapper
from django.contrib.sessions.models import Session
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
import datetime
from django.utils import timezone
from dscblog.common import makecode, dump_datetime
from dscblog.settings import DATABASES
from django.utils.text import slugify
import html
import datetime
import random

MIN_TRENDING_SCORE = 5


def get_top_topics_of_session(session):
    return Topic.objects.annotate(score=Sum('blogs__views__score', filter=Q(blogs__views__session=session)), views_count=Count('blogs__views', filter=Q(blogs__views__session=session))).order_by('-score', '-views_count', '-created_on')


class UserManager(BaseUserManager):
    """
    Custom user model manager
    """

    def create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError('The username must be set')
        if 'email' in extra_fields:
            extra_fields['email'] = self.normalize_email(extra_fields['email'])
        extra_fields.setdefault('name', username)
        user = self.model(
            username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff = True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser = True.')
        return self.create_user(username, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='Email',
        max_length=255,
        null=True, default=None
    )
    name = models.CharField(max_length=100, verbose_name='Name')
    avatar_url = models.CharField(max_length=250, null=True, default=None)
    bio = models.CharField(max_length=300, blank=True,
                           default='', verbose_name='Bio')
    first_name = None
    last_name = None
    REQUIRED_FIELDS = []

    objects = UserManager()

    def get_profile_min(self):
        return {'user_id': self.id, 'username': self.username, 'name': self.name, 'avatar_url': self.avatar_url}

    def get_name(self):
        return self.name or self.username

    def get_profile(self, user=None):
        obj = self.get_profile_min()
        obj['bio'] = self.bio
        obj['followers_count'] = self.followers_count()
        if user != None:
            obj['is_following'] = user.is_following(self)
            obj['is_follower'] = user.is_follower(self)
        obj['blogs'] = []
        if user != self:
            blogs = self.get_published_blogs()
            obj['is_self'] = False
        else:
            blogs = self.get_all_blogs()
            obj['is_self'] = True
        for blog in blogs:
            obj['blogs'].append(blog.get_obj_min())
        return obj

    def update_name(self, name):
        self.name = name
        self.save()

    def update_avatar(self, avatar_url):
        self.avatar_url = avatar_url
        self.save()

    def follow(self, target):
        try:
            follow_obj = Follower.follow(self, target)
        except:
            return False
        else:
            return True

    def unfollow(self, target):
        try:
            follow_obj = Follower.get_by_users(user=self, target=target)
        except Exception as e:
            return False
        else:
            follow_obj.unfollow()
            return True

    def is_follower(self, user):
        try:
            follow_obj = self.followers.get(user=user)
        except:
            return False
        else:
            return True

    def is_following(self, target):
        try:
            follow_obj = self.following.get(target=target)
        except:
            return False
        else:
            return True

    def followers_count(self):
        return self.followers.count()

    def get_followers(self):
        return self.followers.all()

    def get_all_blogs(self):
        blogs = self.blogs.filter(author=self).order_by(
            '-modified_on', '-created_on')
        return blogs

    def get_published_blogs(self):
        blogs = self.blogs.filter(author=self, is_published=True).order_by(
            '-published_on', '-modified_on')
        return blogs

    def react(self, blog, reaction):
        try:
            obj = Reaction.react(user=self, blog=blog, reaction=reaction)
        except:
            return None
        else:
            return obj

    def unreact(self, blog):
        try:
            obj = Reaction.objects.get(user=self, blog=blog)
        except:
            return False
        else:
            obj.unreact()
            return True

    def comment(self, blog, text, reference=None):
        try:
            obj = Comment.create(user=self, blog=blog,
                                 text=text, reference=reference)
        except:
            return None
        else:
            return obj

    def get_top_topics(self):
        return Topic.objects.annotate(score=Sum('blogs__views__score', filter=Q(blogs__views__user=self)), views_count=Count('blogs__views', filter=Q(blogs__views__user=self))).order_by('-score', '-views_count', '-created_on')

    def get_author_feed(self):
        return Blog.objects.filter(is_published=True, published_on__gte=timezone.now()-datetime.timedelta(days=3), author__followers__user=self).order_by('-modified_on', '-published_on')

    def get_likes_feed(self, limit=100):
        q = Reaction.objects.filter(blog__is_published=True, date__gte=timezone.now(
        )-datetime.timedelta(days=1, hours=6), user__followers__user=self).order_by('-date')
        likes_feed = []
        for reaction in q:
            new = True
            for existing in likes_feed:
                if existing['blog'] == reaction.blog:
                    if reaction.user not in existing['users']:
                        existing['users'].append(reaction.user)
                    new = False
                    break
            if new:
                likes_feed.append(
                    {'blog': reaction.blog, 'users': [reaction.user]})
            if len(likes_feed) >= limit:
                break
        return likes_feed

    def get_comments_feed(self, limit=100):
        q = Comment.objects.filter(blog__is_published=True, date__gte=timezone.now(
        )-datetime.timedelta(days=2), user__followers__user=self).order_by('-date')
        comments_feed = []
        for comment in q:
            new = True
            for existing in comments_feed:
                if existing['blog'] == comment.blog:
                    if comment.user not in existing['users']:
                        existing['users'].append(comment.user)
                    new = False
                    break
            if new:
                comments_feed.append(
                    {'blog': comment.blog, 'users': [comment.user]})
            if len(comments_feed) >= limit:
                break
        return comments_feed

    @classmethod
    def get_catagories(cls, user=None, session=None):
        topics = []
        if user != None:
            topics = list(user.get_top_topics()[:5])
        elif session != None:
            topics = list(get_top_topics_of_session(session)[:5])
        if len(topics) < 5:
            for topic in Topic.top_topics():
                if topic not in topics:
                    topics.append(topic)
                if len(topics) >= 5:
                    break
        # random.shuffle(topics)
        names = []
        for topic in topics:
            names.append(topic.name)
        return ['all', 'popular', 'new', 'trending']+names

    @classmethod
    def feed_from_top_topics(cls, user=None, session=None, init_topics=[], xcept=None):
        top_topics = init_topics
        posts = []
        blogs = []
        if user != None:
            for topic in user.get_top_topics()[:7]:
                if topic not in top_topics:
                    top_topics.append(topic)
        elif session != None:
            for topic in get_top_topics_of_session(session)[:7]:
                if topic not in top_topics:
                    top_topics.append(topic)
        if len(top_topics) < 7:
            hot_topics = Topic.top_topics()
            for topic in hot_topics:
                if topic not in top_topics:
                    top_topics.append(topic)
                if len(top_topics) >= 9:
                    break
        random.shuffle(top_topics)
        for topic in top_topics:
            counter = 0
            for blog in topic.top_blogs():
                if blog not in blogs and blog != xcept:
                    counter += 1
                    blogs.append(blog)
                    obj = blog.get_obj_min()
                    obj['highlight'] = {'type': 'TOPIC',
                                        'text': topic.name}
                    posts.append(obj)
                if counter >= 3:
                    break
            if len(posts) >= 12:
                break
        return posts

    @classmethod
    def get_feed(cls, usr=None, session=None):
        posts = []
        if usr != None:
            author_feed = usr.get_author_feed()[:5]
            for post in author_feed:
                obj = post.get_obj_min()
                obj['highlight'] = {'type': 'NEW',
                                    'text': 'New post from '+post.author.get_name()}
                posts.append(obj)
            comments_feed = usr.get_comments_feed(5)
            for comment in comments_feed:
                obj = comment['blog'].get_obj_min()
                txt = ''
                for ind, user in enumerate(comment['users']):
                    txt += user.get_name()
                    if ind != len(comment['users'])-1:
                        txt += ', '
                obj['highlight'] = {'type': 'COMMENT',
                                    'text': txt+' commented'}
                posts.append(obj)
            likes_feed = usr.get_likes_feed(5)
            for reaction in likes_feed:
                obj = reaction['blog'].get_obj_min()
                txt = ''
                for ind, user in enumerate(comment['users']):
                    txt += user.get_name()
                    if ind != len(comment['users'])-1:
                        txt += ', '
                obj['highlight'] = {'type': 'LIKE',
                                    'text': txt+' liked'}
                posts.append(obj)
        if len(posts) >= 15:
            trending_feed = Blog.trending()[:5]
        else:
            trending_feed = Blog.trending()[:10]
        for post in trending_feed:
            obj = post.get_obj_min()
            obj['highlight'] = {'type': 'TRENDING', 'text': 'Trending'}
            posts.append(obj)
        psts = cls.feed_from_top_topics(usr, session)
        for post in psts:
            posts.append(post)
        if len(posts) < 25:
            if len(posts) <= 10:
                recents_feed = Blog.recents()[:10]
            else:
                recents_feed = Blog.recents()[:5]
            for post in recents_feed:
                obj = post.get_obj_min()
                obj['highlight'] = {'type': 'NEW', 'text': 'Recently added'}
                posts.append(obj)
        random.shuffle(posts)
        return posts

    @classmethod
    def get_by_id(cls, pk):
        return cls.objects.get(id=pk)

    @classmethod
    def get_by_username(cls, pk):
        return cls.objects.get(username=pk)


class Follower(models.Model):
    user = models.ForeignKey(
        User, related_name="following", on_delete=models.CASCADE)
    target = models.ForeignKey(
        User, related_name="followers", on_delete=models.CASCADE)
    date = models.DateTimeField()

    class Meta:
        unique_together = ['user', 'target']

    def unfollow(self):
        self.delete()

    def __str__(self):
        return self.user.username+' > '+self.target.username

    @classmethod
    def follow(cls, user, target):
        existing = cls.objects.filter(user=user, target=target).count()
        if existing == 0:
            obj = cls(user=user, target=target, date=timezone.now())
            obj.save()
            return obj
        else:
            raise ValueError("Already following")

    @classmethod
    def get_by_users(cls, user, target):
        return cls.objects.get(user=user, target=target)


class Blog(models.Model):
    title = models.CharField(max_length=200, verbose_name='Title')
    img_url = models.CharField(max_length=200, null=True, default=None)
    content = models.CharField(
        max_length=20000, verbose_name='Content', default='')
    author = models.ForeignKey(
        User, related_name="blogs", on_delete=models.CASCADE)
    created_on = models.DateTimeField()
    modified_on = models.DateTimeField()
    published_on = models.DateTimeField(null=True, default=None)
    is_published = models.BooleanField(default=False)
    score = models.FloatField(verbose_name='Engagement Score', default=0.0)
    topics = models.ManyToManyField('Topic', related_name="blogs")

    def addScore(self, amt):
        self.score = self.score+amt
        self.save()
        return self.score

    def reduceScore(self, amt):
        self.score = self.score-amt
        self.save()
        return self.score

    def get_topics(self):
        return self.topics.all()

    def get_obj_min(self):
        obj = {'title': self.title, 'img_url': self.img_url, 'blog_id': self.id, 'blog_url': self.get_url(),
               'is_published': self.is_published, 'modified_on': self.modified_on, 'published_on': self.published_on, 'author': self.author.get_profile_min()}
        return obj

    def get_obj(self, user=None, escape_html=False):
        obj = self.get_obj_min()
        obj['views_count'] = self.get_views_count()
        obj['content'] = self.content
        obj['reaction_counts'] = self.get_reaction_counts()
        obj['comments_count'] = self.get_comments_count()
        obj['user_reaction'] = None
        obj['topics'] = []
        for topic in self.get_topics():
            obj['topics'].append(topic.name)
        if user != None:
            react_obj = self.get_user_reaction(user)
            if react_obj != None:
                obj['user_reaction'] = react_obj.reaction
        if escape_html:
            obj['content'] = html.escape(obj['content'])
        return obj

    def get_comments_count(self):
        return Comment.objects.filter(blog=self).count()

    def get_comments(self):
        return Comment.objects.filter(blog=self).order_by('-id')

    def get_reaction_counts(self):
        counts = {}
        for react, name in Reaction.REACTS:
            counts[react] = Reaction.objects.filter(
                blog=self, reaction=react).count()
        return counts

    def get_reactions(self):
        reacts = Reaction.objects.filter(
            blog=self).order_by('-date')
        return reacts

    def get_user_reaction(self, user):
        try:
            react = Reaction.objects.get(user=user, blog=self)
        except:
            return None
        else:
            return react

    def get_slug(self):
        return slugify(self.title)

    def get_url(self):
        return '/'+self.get_slug()+','+str(self.id)

    def remove(self):
        self.delete()

    def update_content(self, new_content):
        self.content = new_content
        self.modified_on = timezone.now()
        self.save()

    def update_title(self, new_title):
        self.title = new_title
        self.modified_on = timezone.now()
        self.save()

    def update_img(self, new_img):
        self.img_url = new_img
        self.modified_on = timezone.now()
        self.save()

    def publish(self):
        if not self.is_published:
            self.is_published = True
            self.published_on = timezone.now()
            self.modified_on = timezone.now()
            self.save()

    def unpublish(self):
        if self.is_published:
            self.is_published = False
            self.published_on = None
            self.modified_on = timezone.now()
            self.save()

    def has_topic(self, name):
        try:
            self.topics.get(name=name)
        except:
            return False
        else:
            return True

    def add_topic(self, name):
        return Topic.tag(self, name)

    def remove_topic(self, name):
        return Topic.untag(self, name)

    def related_blogs(self, user=None, session=None):
        topics = []
        for topic in self.get_topics():
            topics.append(topic)
        return User.feed_from_top_topics(user, session, topics, self)[:6]

    def get_views_count(self):
        return View.objects.filter(blog=self).count()

    @classmethod
    def create(cls, author, title):
        obj = cls(author=author, title=title, created_on=timezone.now(),
                  modified_on=timezone.now(), content='', is_published=False)
        obj.save()
        return obj

    @classmethod
    def get_by_id(cls, pk):
        return cls.objects.get(id=pk)

    @classmethod
    def trending(cls):
        if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            return cls.objects.annotate(
                engagement_recency=Avg(
                    ExpressionWrapper(
                        timezone.now(
                        )-F('views__date'), output_field=models.IntegerField()
                    ))).filter(is_published=True,
                               engagement_recency__lte=3*24*60*60, score__gte=MIN_TRENDING_SCORE).order_by('engagement_recency', '-score')
        else:
            return cls.objects.annotate(
                engagement_recency=Avg(
                    ExpressionWrapper(timezone.now(
                    )-F('views__date'), output_field=models.DurationField())
                )).filter(is_published=True,
                          engagement_recency__lte=datetime.timedelta(days=3), score__gte=MIN_TRENDING_SCORE).order_by('engagement_recency', '-score')

    @classmethod
    def by_recent_engagement(cls):
        return cls.objects.annotate(
            engagement_recency=Avg(
                ExpressionWrapper(
                    timezone.now(
                    )-F('views__date'), output_field=models.IntegerField()
                ))).filter(is_published=True).order_by('engagement_recency', '-score')

    @classmethod
    def top25(cls):
        return cls.objects.filter(is_published=True).order_by('-score', '-published_on')[:25]

    @classmethod
    def recent4(cls):
        return cls.objects.filter(is_published=True).order_by('-published_on')[:4]

    @classmethod
    def recents(cls):
        return cls.objects.filter(is_published=True).order_by('-published_on')

    def __str__(self):
        return str(self.id)+'. '+self.title


class Topic(models.Model):
    BANNED = ['all', 'trending', 'new', 'recents', 'feed', 'recent', 'feeds', 'recommended',
              'recommendation', 'read', 'latest', 'newpost', 'new-post', 'comment',
              'popular', 'hot', 'top', 'blog', 'blogging', 'cool', 'like', 'likes']
    name = models.CharField(
        max_length=30, verbose_name='Name', primary_key=True)
    created_on = models.DateTimeField()

    def remove(self):
        self.delete()

    def top_blogs(self):
        field = models.DurationField()
        if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            field = models.IntegerField()
        return self.blogs.filter(is_published=True).annotate(
            engagement_recency=Avg(
                ExpressionWrapper(
                    timezone.now(
                    )-F('views__date'), output_field=field
                ))).order_by('engagement_recency', '-score', '-published_on')

    def recent_blogs(self):
        return self.blogs.filter(is_published=True).order_by('-published_on')

    @classmethod
    def get_by_name(cls, name):
        return cls.objects.get(name=name)

    @classmethod
    def tag(cls, blog, name):
        try:
            existing = cls.get_by_name(name=name)
        except:
            if len(name) <= 30:
                topic = cls(name=name, created_on=timezone.now())
                topic.save()
                blog.topics.add(topic)
                blog.save()
                return topic
            else:
                return None
        else:
            blog.topics.add(existing)
            blog.save()
            return existing

    @classmethod
    def untag(cls, blog, name):
        try:
            topic = cls.get_by_name(name)
        except:
            return False
        else:
            if blog.has_topic(name):
                blog.topics.remove(topic)
                blog.save()
                if topic.blogs.count() == 0:
                    topic.remove()
                return True
            else:
                return False

    @classmethod
    def top_topics(cls):
        return cls.objects.annotate(score=Sum('blogs__score')).order_by('-score', '-created_on')

    def __str__(self):
        return self.name


class View(models.Model):
    user = models.ForeignKey(
        User, related_name="viewed", on_delete=models.SET_NULL, null=True, default=None)
    session = models.ForeignKey(
        Session, related_name="viewed",  on_delete=models.SET_NULL, null=True, default=None)
    blog = models.ForeignKey(
        Blog, related_name="views", on_delete=models.CASCADE)
    referer = models.CharField(
        max_length=400, verbose_name='Referer Site', null=True, default=None)
    score = models.FloatField(verbose_name='Engagement Score', default=1.0)
    date = models.DateTimeField()
    key = models.CharField(max_length=30, verbose_name='Key')
    pingbacks = models.IntegerField(default=0)
    last_pingback_date = models.DateTimeField(null=True, default=None)

    def remove(self):
        self.delete()

    def addScore(self, amt):
        self.score = self.score+amt
        self.save()
        return self.score

    def reduceScore(self, amt):
        self.score = self.score-amt
        self.save()
        return self.score

    def pingback(self):
        time_diff = timezone.now()-self.last_pingback_date
        if self.pingbacks <= 30 and time_diff >= datetime.timedelta(seconds=20) and time_diff <= datetime.timedelta(minutes=2):
            self.pingbacks += 1
            self.score += 0.07
            self.blog.addScore(0.07)
            self.last_pingback_date = timezone.now()
            self.save()
        return self.pingbacks

    @classmethod
    def create(cls, user, blog, session=None, referer=None):
        if user != blog.author:
            try:
                existing = cls.objects.filter(user=user, blog=blog, session=session, last_pingback_date__gte=timezone.now(
                )-datetime.timedelta(minutes=10)).order_by('-last_pingback_date')[0]
            except:
                score = 0.1
                prev = cls.objects.filter(
                    user=user, blog=blog, session=session)
                prev_count = prev.count()
                if prev_count == 0:
                    score = 0.5
                elif prev_count <= 5:
                    score = 0.3
                else:
                    score = 0.1
                blog.addScore(score)
                obj = cls(user=user, blog=blog, date=timezone.now(), session=session,
                          last_pingback_date=timezone.now(), score=score, key=makecode(), referer=referer)
                obj.save()
                return obj.key
            else:
                existing.last_pingback_date = timezone.now()
                existing.save()
                return existing.key
        else:
            return None

    @classmethod
    def get_active(cls, user, blog, session=None):
        return cls.objects.filter(user=user, blog=blog, session=session,
                                  last_pingback_date__gte=timezone.now()-datetime.timedelta(hours=1)).order_by('-last_pingback_date')[0]

    @classmethod
    def add_score(cls, user, blog, val=0.1, session=None):
        try:
            view = cls.get_active(user, blog, session)
        except:
            return False
        else:
            view.add_score(val)
            return True

    @classmethod
    def convert_to_user(cls, session, user):
        cls.objects.filter(user=None, session=session).update(
            user=user, session=None)

    @classmethod
    def get_by_key(cls, key):
        return cls.objects.get(key=key, last_pingback_date__gte=timezone.now()-datetime.timedelta(hours=1))


class Reaction(models.Model):
    SCORE = 0.3
    LIKE = 'LIK'
    LOVE = 'LOV'
    LIT = 'LIT'
    COOL = 'COL'
    CLAP = 'CLP'
    REACTS = [
        (LIKE, 'Like'),
        (LOVE, 'Love'),
        (LIT, 'Lit'),
        (COOL, 'Cool'),
        (CLAP, 'Clap'),
    ]
    CODES = {LIKE, LOVE, LIT, COOL, CLAP}
    user = models.ForeignKey(
        User, related_name="reacted", on_delete=models.CASCADE)
    blog = models.ForeignKey(
        Blog, related_name="reactions", on_delete=models.CASCADE)
    date = models.DateTimeField()
    reaction = models.CharField(
        max_length=3,
        choices=REACTS,
        default=LIKE,
    )

    class Meta:
        unique_together = ['user', 'blog']

    def unreact(self):
        self.blog.reduceScore(Reaction.SCORE)
        self.delete()

    def get_obj(self):
        obj = {'user': self.user.get_profile_min(),
               'blog_id': self.blog.id, 'date': self.date, 'reaction': self.reaction}
        return obj

    def __str__(self):
        return self.user.username+' > '+self.blog.title

    @classmethod
    def react(cls, user, blog, reaction):
        try:
            existing = cls.objects.get(user=user, blog=blog)
        except:
            obj = cls(user=user, blog=blog,
                      reaction=reaction, date=timezone.now())
            obj.save()
            blog.addScore(cls.SCORE)
            View.addScore(user, blog, cls.SCORE)
            return obj
        else:
            existing.reaction = reaction
            existing.save()
            return existing

    @classmethod
    def get_by_user_and_blog(cls, user, blog):
        return cls.objects.get(user=user, blog=blog)


class Comment(models.Model):
    user = models.ForeignKey(
        User, related_name="commented", on_delete=models.CASCADE)
    text = models.CharField(
        max_length=300, verbose_name='Text', blank=True, default='')
    blog = models.ForeignKey(
        Blog, related_name="comments", on_delete=models.CASCADE)
    reference = models.ForeignKey(
        'Comment', related_name="replies", null=True, default=None, on_delete=models.SET_NULL)
    date = models.DateTimeField()

    def remove(self):
        self.delete()

    def get_obj(self, user=None):
        obj = {'user': self.user.get_profile_min(), 'comment_id': self.id, 'is_mine': False,
               'blog_id': self.blog.id, 'date': self.date, 'text': self.text, 'reference': None}
        if self.reference != None:
            obj['reference'] = {'user': self.reference.user.get_profile_min(),
                                'text': self.reference.text, 'comment_id': self.reference.id}
        if user != None and user == self.user:
            obj['is_mine'] = True
        return obj

    def reply(self, user, text):
        return Comment.create(user=user, blog=self.blog, reference=self)

    @classmethod
    def create(cls, user, blog, text, reference=None):
        obj = cls(user=user, blog=blog,
                  text=text, date=timezone.now(), reference=reference)
        obj.save()
        if user != blog.author:
            if reference:
                blog.addScore(0.4)
                View.addScore(user, blog, 0.4)
            else:
                # First comment of the user
                if user.commented.filter(blog=blog).count() <= 1:
                    blog.addScore(0.5)
                    View.addScore(user, blog, 0.5)
                else:
                    blog.addScore(0.3)
                    View.addScore(user, blog, 0.3)
        else:
            blog.addScore(0.1)
        return obj

    @classmethod
    def get_by_id(cls, pk):
        return cls.objects.get(id=pk)

    def __str__(self):
        return str(self.user.id)+' > '+self.blog.title


class Featured(models.Model):
    info = models.CharField(
        max_length=60, verbose_name='Info', blank=True, default=None)
    blog = models.OneToOneField(
        to=Blog, primary_key=True, on_delete=models.CASCADE)
    priority = models.IntegerField(verbose_name="Priority", default=0)

    @classmethod
    def pickOne(cls):
        return cls.objects.filter(blog__is_published=True).order_by('?').first()

    def __str__(self):
        return str(self.blog.id)+': '+self.blog.title
