from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
import datetime
from django.utils import timezone
from dscblog.common import makecode, dump_datetime
from django.utils.text import slugify
import html


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
        return {'user_id':self.id,'username': self.username, 'name': self.name, 'avatar_url': self.avatar_url}

    def get_profile(self, user=None):
        obj = self.get_profile_min()
        obj['bio'] = self.bio
        obj['followers_count']=self.followers_count()
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
            follow_obj = Follower.get_by_users(user=self,target=target)
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
        
    def get_all_blogs(self):
        blogs = self.blogs.filter(author=self).order_by(
            '-modified_on', '-created_on')
        return blogs

    def get_published_blogs(self):
        blogs = self.blogs.filter(author=self, is_published=True).order_by(
            '-published_on', '-modified_on')
        return blogs

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
    title = models.CharField(max_length=60, verbose_name='Title')
    img_url = models.CharField(max_length=150, null=True, default=None)
    content = models.CharField(
        max_length=1500, verbose_name='Content', default='')
    author = models.ForeignKey(
        User, related_name="blogs", on_delete=models.CASCADE)
    created_on = models.DateTimeField()
    modified_on = models.DateTimeField()
    published_on = models.DateTimeField(null=True, default=None)
    is_published = models.BooleanField(default=False)

    def get_obj_min(self):
        obj = {'title': self.title, 'img_url': self.img_url, 'blog_id': self.id, 'blog_url': self.get_url(),
               'is_published': self.is_published, 'modified_on': self.modified_on, 'author': self.author.get_profile_min()}
        return obj

    def get_obj(self, escape_html=True):
        obj = self.get_obj_min()
        obj['content'] = self.content
        if not escape_html:
            obj['content'] = html.unescape(obj['content'])
        return obj

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
    def top25(cls):
        return cls.objects.filter(is_published=True).order_by('-modified_on', '-published_on')[:25]

    def __str__(self):
        return str(self.id)+'. '+self.title

'''
class Reaction(models.Model):
    user = models.ForeignKey(
        User, related_name="reacted", on_delete=models.CASCADE)
    blog = models.ForeignKey(
        Blog, related_name="reactions", on_delete=models.CASCADE)
    date = models.DateTimeField()
    reaction = models.Choices()

    class Meta:
        unique_together = ['user', 'blog']

    def unreact(self):
        self.delete()

    def __str__(self):
        return self.user.username+' > '+self.blog.title

    @classmethod
    def react(cls, user,blog, reaction):
        existing = cls.objects.filter(user=user, blog=blog).count()
        if existing == 0:
            obj = cls(user=user, blog=blog, date=timezone.now())
            obj.save()
            return obj
        else:
            raise ValueError("Already reacted")

    @classmethod
    def get_by_users(cls, user, target):
        return cls.objects.get(user=user, target=target)
'''

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
