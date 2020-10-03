# DSC-IEM Blog 📰

Blogs for tech and beyond from DSC-IEM community.
With the help of this project we hope to give the students of this community a platform to share,
showcase and help each other in their exciting journey of learning and building amazing things.

## About the codebase 📁

We are using Python 🐍 and Django for our blog server

## How to start working on the server code ⚒

#### Create a virtualenv 🌎

```bash
virtualenv blogenv
```

#### Activate our python virtual environment ✈

```bash
blogenv\Scripts\activate
```

#### Install all required packages 📦

```bash
pip install -r requirements.txt
```

#### After making changes to static files

```bash
python manage.py collectstatic
```

#### After modifying database models, generate necessary migration code 💾

```bash
python manage.py makemigrations dscblog
```

#### Apply any database migration 💿

```bash
python manage.py migrate --run-syncdb
```

#### Run server in dev mode 🏃‍♀️

```bash
python manage.py runserver 0.0.0.0:8000
```

#### Run server in production mode 🏁

  (This will only work on linux)

```bash
gunicorn -b 0.0.0.0:80 dscblog.wsgi
```

## Env variables for django ⚙

For local setup, you can also use `settings_dev.py` file

- `DJ_SECRET_KEY`: Django secret key
- `BASE_URL`: Root url of the server. eg: `https://example.com`
- `DATABASE_URL`: eg: `postgres://user:password@localhost/dbname`

## Be a super user 😎

To be abe to access the admin page `/admin` you need a super user account.

```bash
python manage.py createsuperuser
```

## On first run 🏃‍♀️

A few features needs to be configured first before they can be used

### Sign In with Google 📧

- In Django Admin page `/admin` go to `SITES` make sure you have the domain name set properly.
For local environment use `Domain name` and `Display name` as  `http://localhost:8000`

- In Django Admin page `/admin` go to `SOCIAL ACCOUNTS > Social applications`
Choose `google` as the provider and fill up the required info.
Keep `key` field blank.
Follow the [docs](https://django-allauth.readthedocs.io/en/latest/providers.html#google)
for more info.

### Featured blogs 📢

Once you have written some blogs, its time to feature some of them in the home page.
To feature a blog, go to Django Admin page `/admin`, now go to `DSCBLOG > Featureds`
use `ADD FEATURED` button and fill up the form, you can keep `Info` field blank.
Note that your blog post must be public to actually show up in the featured section.
