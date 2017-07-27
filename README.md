Django Blog

-------


### Technologies

- Django 1.10
- Python 3.5


### Features

* Archives views
* Related entries
* RSS or Atom Feeds
* Tags and categories views
* Advanced search engine
* Custom templates for various contents
* Editing in Markdown
* Admin dashboard
* Django REST Framework
* Comments
* Sitemaps


### Instalation

I assume you already setup your django development with virtual enviroment (virtualenv).

**1. Create virtual enviroment and activate it.**

```
$ virtualenv --python=/usr/bin/python3 yourenv
$ source bin/activate
```

**2. Cloning this project**

```
$ git clone git@github.com:fountainhead-gq/DjangoBlog.git
```

**3. Install all requirements**

```
$ pip install -r requirements.txt
```

**4. Database migrations**

```
 python manage.py makemigrations
 python manage.py migrate
```

**5. Run the server**

```
python manage.py runserver
```
-------
