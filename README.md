# Installation

In LXC:

```
$ cd /fortipoc
$ git clone https://github.com/sha-02/fpoc-manager.git
$ cd fpoc-manager
```

With Pip:
```
$ python3.8 -m venv venv
$ source venv/bin/activate
(venv) $ pip install pip --upgrade 
(venv) $ pip install -r requirements.txt
```

With Pipenv:

```
$ pipenv install
$ pipenv shell
```

# Start
```
(venv) $ python manage.py runserver 0.0.0.0:8000
```

# Resynch
```
git pull
```
