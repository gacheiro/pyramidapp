from urllib.parse import urlparse
from pyramid.config import Configurator

from pymongo import MongoClient


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application."""
    config = Configurator(settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)

    db_url = urlparse(settings['mongo_uri'])
    config.registry.db = MongoClient(
        host=db_url.hostname,
        port=db_url.port,
    )

    # add the db to request as a attribute
    # so we can access as `request.db` inside views
    def add_db(request):
        db = config.registry.db[db_url.path[1:]]
        if db_url.username and db_url.password:
            db.authenticate(db_url.username, db_url.password)
        return db

    config.add_request_method(add_db, 'db', reify=True)

    config.include('pyramid_jinja2')

    config.add_route('home', '/')
    config.add_route('add', '/add')
    config.add_route('video', 'videos/{id}')
    config.add_route('thumbs_up', 'videos/{id}/thumbs_up')
    config.add_route('thumbs_down', 'videos/{id}/thumbs_down')
    config.add_route('themes', '/themes')
    config.scan('.views')

    return config.make_wsgi_app()
