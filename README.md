# DSC-IEM Blog

Blogs for tech and beyond from DSC-IEM community.
With the help of this project we hope to give the students of this community a platform to share,
showcase and help each other in their exciting journey of learning and building amazing things.\
**Everyone is encouraged to contribute to this project**

## About the codebase

We are using Python and Django for our blog server

## How to start working on the server code

#### Install all required packages

```bash
pip install -r requirements.txt
```

#### Activate our python virtual environment

```bash
blogenv\Scripts\activate
```

#### After making changes to static files

```bash
python manage.py collectstatic
```

#### After modifying database models, generate necessary migration code

```bash
python manage.py makemigrations dscblog
```

#### Apply any database migration

```bash
python manage.py migrate --run-syncdb
```

#### Run server in dev mode

```bash
python manage.py runserver 0.0.0.0:8000
```

#### Run server in production mode

  (This will only work on linux)

```bash
gunicorn -b 0.0.0.0:80 dscblog.wsgi
```

## Env variables for django

For local setup, you can also use `settings_dev.py` file

- `DJ_SECRET_KEY`: Django secret key
- `BASE_URL`: Root url of the server. eg: `https://example.com`
- `DATABASE_URL`: eg: `postgres://user:password@localhost/dbname`
