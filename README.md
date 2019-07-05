# Pyramidapp

A simple [Pyramid](https://trypyramid.com/) app using MongoDB as the back-end.

It's possible to add and list videos, like and dislike videos, and list the most popular themes.
# How to install

Clone or download this repository.

Make sure you have ```python >= 3.7```

Start a virtual env:
```
  python -m venv venv
  venv/Scripts/activate
```

Now install this app as package in development mode:
```
  pip install -e .
```

Also make sure you install the development dependencies:
```
  pip install -e ".[dev]"
```

Use the ```development.ini``` to configure database connection. Default is ```"mongodb://localhost:27017/pyramidapp_db"```. 
Also, the database ```"mongodb://localhost:27017/pyramidapp_db_test"``` is needed to run the tests.

Now you can run the app with:
```
  pserve development.ini --reload
```

# Running tests
To run the tests use:
```pytest app/tests.py -q```
