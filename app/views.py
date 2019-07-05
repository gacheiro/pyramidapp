import datetime

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from bson.objectid import ObjectId


class HomeViews:

    def __init__(self, request):
        self.request = request    
        self.db = request.db

    @view_config(route_name='home', 
                 renderer='/templates/home.jinja2')
    def home(self):
        videos = self.db.videos.find().sort('date', -1)
        return {
            'videos': list(videos),  # list, so we can compare in the unittest
        }

    @view_config(route_name='add', request_method='POST')
    def add(self):
        name, theme = self.request.POST['name'], self.request.POST['theme']
        if name and theme:
            self.db.videos.insert_one({
                'name': name,
                'theme': theme,
                'thumbs_up': 0,
                'thumbs_down': 0,
                'date': datetime.datetime.utcnow(),
            })
        return HTTPFound('/')


class VideoViews:

    def __init__(self, request):
        self.request = request
        self.db = request.db

    def _update_thumbs(self, id, field):
        id = ObjectId(self.request.matchdict['id'])
        self.db.videos.find_one_and_update(
            {'_id': id}, 
            {'$inc': {field: 1}}
        )

    @view_config(route_name='thumbs_up', request_method='POST')
    def thumbs_up(self):
        self._update_thumbs(
            id=self.request.matchdict['id'],
            field='thumbs_up'
        )
        return HTTPFound('/')

    @view_config(route_name='thumbs_down', request_method='POST')
    def thumbs_down(self):
        self._update_thumbs(
            id=self.request.matchdict['id'],
            field='thumbs_down'
        )
        return HTTPFound('/')


class ThemeViews:

    def __init__(self, request):
        self.request = request
        self.db = request.db

    @view_config(route_name='themes',
                 renderer='templates/themes.jinja2')
    def themes(self):
        themes = self.db.videos.aggregate([
            {
                '$group': {
                    '_id': '$theme', 
                    'score': { 
                        '$sum': {                        
                            '$subtract': [
                                '$thumbs_up', 
                                {
                                    "$divide": [
                                        "$thumbs_down", 2
                                    ]
                                }
                            ]
                        }
                    }
                }
            },
            {
                '$sort': {'score': -1}
            }
        ])
        return {
            'themes': list(themes),
        }
