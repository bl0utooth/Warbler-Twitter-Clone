"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 8989
        self.testuser.id = self.testuser_id

        self.u1 = User.signup("abc", "test1@email.com", "password", None)
        self.u1_id = 778
        self.u1.id = self.u1_id
        self.u2 = User.signup("def", "test2@email.com", "password", None)
        self.u2_id = 884
        self.u2.id = self.u2_id
        self.u3 = User.signup("ghi", "test3@email.com", "password", None)
        self.u4 = User.signup("testing", "test4@email.com", "password", None)

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_homepage_tweets_display(self):
        user1 = User.signup('user1', 'user1@email.com', 'password', None)
        user2 = User.signup('user2', 'user2@email.com', 'password', None)
        user3 = User.signup('user3', 'user3@email.com', 'password', None)
        db.session.add_all([user1, user2, user3])
        db.session.commit()

        tweet2 = Message(text = "hello from user2", user_id = user2.id)
        tweet3 = Message(text = "hello from user3", user_id = user3.id)
        db.session.add_all([tweet2, tweet3])
        db.session.commit()

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = user1.id
    
        response = self.client.get('/')
        self.assertIn("hello from user2", str(response.data))
        self.assertNotIn("hello from user3", str(response.data))

    def test_user_profile(self):
        user = User.signup('testuser', 'test@email.com', 'password', None)
        db.session.add(user)
        db.session.commit()

        tweet = Message(text="tweet tweet", user_id = user.id)
        db.session.add(tweet)
        db.session.commit()

        with self.client as c:
            response = c.get(f'/users/{user.id}')
        
            self.assertIn("tweet tweet", str(response.data))
        
            self.assertIn('follow', str(response.data))

    def test_tweet_like(self):
        user1 = User.signup('user1', 'user1@email.com', 'password', None)
        user2 = User.signup('user2', 'user2@email.com', 'password', None)
        tweet = Message(text = "like tweet tweet", user_id = user2.id)
    
        db.session.add_all([user1, user2, tweet])
        db.session.commit()

        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = user1.id

        response = self.client.post(f'/tweets/{tweet.id}/like', follow_redirects = True)
    
        self.assertEqual(response.status_code, 200)
        self.assertIn('one like', str(response.data)) 

    def test_unlike_tweet(self):
         user1 = User.signup('user1', 'user1@email.com', 'password', None)
        user2 = User.signup('user2', 'user2@email.com', 'password', None)
        tweet = Message(text = "tweet from user2", user_id = user2.id)
    
        db.session.add_all([user1, user2, tweet])
        db.session.commit()

        user1.liked_messages.append(tweet)
        db.session.commit()

        self.assertIn(tweet, user1.liked_messages)
    
        with self.client.session_transaction() as sess:
        sess[CURR_USER_KEY] = user1.id

        response = self.client.post(f'/tweets/{tweet.id}/unlike', follow_redirects=True)
    
        db.session.refresh(user1)
    
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(tweet, user1.liked_messages)

    def test_show_profile_followers(self):
        user1 = User.signup('user1', 'user@email.com', 'password', None)
        user2 = User.signup('user2', 'user@email.com', 'password', None)
        user3 = User.signup('user3', 'user@email.com', 'password', None)
        db.session.add_all([user1, user2, user3])
        db.session.commit()

        user1.followers.append(user2)
        user1.followers.append(user3)
        db.session.commit()

        with self.client as c:
            response = c.get(f'/users/{user1.id}/followers')

            self.assertEqual(response.status_code, 200)

            self.assertIn('user2', str(response.data))
            self.assertIn('user3', str(response.data))

            self.assertNotIn('user1', str(response.data))