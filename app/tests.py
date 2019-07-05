import unittest

import pymongo
import mongomock
from pyramid import testing


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.videos = [
            {
                'name': 'Funny Cats',
                'theme': 'cats',
                'thumbs_up': 10,
                'thumbs_down': 1,
                'date': 0,
            },
            {
                'name': 'My Playlist',
                'theme': 'music',
                'thumbs_up': 1,
                'thumbs_down': 5,
                'date': 1,
            },
            {
                'name': 'How to cook cuscuz',
                'theme': 'food',
                'thumbs_up': 5,
                'thumbs_down': 0,
                'date': 2,
            },
            {
                'name': 'Funny Cats 2',
                'theme': 'cats',
                'thumbs_up': 7,
                'thumbs_down': 1,
                'date': 3,
            },
            {
                'name': 'My Playlist 2',
                'theme': 'music',
                'thumbs_up': 1,
                'thumbs_down': 10,
                'date': 4,
            },
            {
                'name': 'Nobody cares',
                'theme': 'me',
                'thumbs_up': 0,
                'thumbs_down': 0,
                'date': 5,
            },
        ]

        self.db = mongomock.MongoClient().db
        self.db.videos.insert_many(self.videos)

    def tearDown(self):
        testing.tearDown()

    def test_home(self):
        """Expects all videos to return in reponse, sorted by date desc."""
        from .views import HomeViews
        request = testing.DummyRequest(db=self.db)
        inst = HomeViews(request)
        resp = inst.home()
        
        # 'sort' videos by date desc
        sorted_videos = list(reversed(self.videos))
        self.assertEqual(resp, {'videos': sorted_videos})

    def test_add_video(self):
        from .views import HomeViews

        request = testing.DummyRequest(
            db=self.db,
            post={
                'name': 'My new video', 
                'theme': 'mytheme'
            }
        )

        inst = HomeViews(request)
        resp = inst.add()
        self.assertEqual(resp.status_code, 302)

        new_video = self.db.videos.find_one({'name': 'My new video'})
        self.assertEqual(new_video['theme'], 'mytheme')
        self.assertEqual(new_video['thumbs_up'], 0)
        self.assertEqual(new_video['thumbs_down'], 0)

    def test_thumbs_up(self):
        from .views import VideoViews

        vid = self.db.videos.find_one({'name': 'Funny Cats'})

        request = testing.DummyRequest(
            db=self.db,
            matchdict={'id': vid['_id']}
        )

        inst = VideoViews(request)
        resp = inst.thumbs_up()

        vid_after = self.db.videos.find_one({'name': 'Funny Cats'})

        # undo the thumbs_up action
        vid_after['thumbs_up'] -= 1 
        
        # by comparing all fields we make sure only thumbs changed
        self.assertEqual(vid, vid_after)
        

    def test_thumbs_down(self):
        from .views import VideoViews

        vid = self.db.videos.find_one({'name': 'Funny Cats'})

        request = testing.DummyRequest(
            db=self.db,
            matchdict={'id': vid['_id']}
        )

        inst = VideoViews(request)
        resp = inst.thumbs_down()
        vid_after = self.db.videos.find_one({'name': 'Funny Cats'})

        # undo the thumbs_down action
        vid_after['thumbs_down'] -= 1 
        
        # by comparing all fields we make sure only thumbs changed
        self.assertEqual(vid, vid_after)


    def test_themes(self):
        from .views import ThemeViews

        request = testing.DummyRequest(db=self.db)
        inst = ThemeViews(request)
        resp = inst.themes()

        self.assertEqual(
            {
                'themes': [
                    {
                        '_id': 'cats',
                        'score': 16.0,
                    },
                    {
                        '_id': 'food',
                        'score': 5.0,
                    },
                    {
                        '_id': 'me',
                        'score': 0.0,
                    },
                    {
                        '_id': 'music',
                        'score': -5.5,
                    }
                ],
            },
            resp
        )


class FunctionalTests(unittest.TestCase):
    def setUp(self):
        from app import main
        from webtest import TestApp

        # make sure to use a test database
        self.database_name = 'pyramidapp_db_test'
        settings = {
            'mongo_uri': f'mongodb://localhost:27017/{self.database_name}'
        }
        app = main({}, **settings)
        self.testapp = TestApp(app)

        self.db = pymongo.MongoClient(
            host='localhost',
            port=27017,
        )

        self.db_test = self.db.pyramidapp_db_test

        videos = [
            { 
                'name': 'Pyramid tutorial in 20min',
                'theme': 'programming',
                'thumbs_up': 1,
                'thumbs_down': 5,
                'date': 0,
            },
            { 
                'name': 'How to test pyramid apps',
                'theme': 'programming',
                'thumbs_up': 1,
                'thumbs_down': 7,
                'date': 1,
            },
        ]

        self.db_test.videos.insert_many(videos)

    def tearDown(self):
        self.db.drop_database(self.database_name)        

    def test_root(self):
        resp = self.testapp.get('/', status=200)
        self.assertIn(b'<h2>My Youtube videos</h2>', resp.body)

    def test_add(self):
        self.testapp.post('/add', {
            'name': 'New Title',
            'theme': 'Theme',
        }, status=302)

        new_video = self.db_test.videos.find_one({'name': 'New Title'})
        self.assertEqual(new_video['theme'], 'Theme')
        self.assertEqual(new_video['thumbs_up'], 0)
        self.assertEqual(new_video['thumbs_down'], 0)        

    def test_non_existing_video(self):
        resp = self.testapp.get('/videos/1', status=404)
        self.assertEqual(resp.status_code, 404)

    def test_non_existing_video_thumbs_up(self):
        resp = self.testapp.get('/videos/1/thumbs_up', status=404)
        self.assertEqual(resp.status_code, 404)
    
    def test_non_existing_video_thumbs_down(self):
        resp = self.testapp.get('/videos/1/thumbs_down', status=404)
        self.assertEqual(resp.status_code, 404)

    def test_video_thumbs_up(self):
        video = self.db_test.videos.find_one()
        _id = video['_id']
        before_post = video['thumbs_up']
        
        resp = self.testapp.post(
            f"/videos/{_id}/thumbs_up", status=302)

        video_after = self.db_test.videos.find_one({'_id': _id})
        after_post = video_after['thumbs_up']
        self.assertEqual(after_post, before_post+1)

    def test_video_thumbs_down(self):
        video = self.db_test.videos.find_one()
        _id = video['_id']
        before_post = video['thumbs_down']
        
        resp = self.testapp.post(
            f"/videos/{_id}/thumbs_down", status=302)

        video_after = self.db_test.videos.find_one({'_id': _id})
        after_post = video_after['thumbs_down']
        self.assertEqual(after_post, before_post+1)

    def test_themes(self):
        resp = self.testapp.get('/themes', status=200)
        self.assertIn(b'<h2>Most popular themes</h2>', resp.body)
