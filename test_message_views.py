"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

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

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_successful_message_post(self):
        self.login('user1', 'testpassword')
        response = self.client.post('/messages/new', data = {'text': 'test message'}, follow_redirects = True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('test message', str(response.data))

        message = Message.query.filter_by(text = 'test message').first()
        self.assertTrue(message)

    def test_delete_message_by_owner(self):
        user = User.signup(username = 'testuser', email = 'user@email.com', password = 'testpassword')
        db.session.add(user)
        db.session.commit()

        message = Message(text = 'test message', user_id = user.id)
        db.session.add(message)
        db.session.commit()

        self.login_as(user)

        response = self.client.post(f'/messages/{message.id}/delete', follow_redirects = True)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(Message.query.get(message.id))

    def test_unauthorized_message_deletion_attempt(self):
        user1 = User.signup(username = 'user1', email = 'user@email.com', password = 'password', image_url = None)
        user2 = User.signup(username = 'user2', email = 'user@email.com', password = 'password', image_url = None)
        db.session.add_all([user1, user2])
        db.session.commit()

        message = Message(text = 'test message', user_id = user1.id)
        db.session.add(message)
        db.session.commit()

        self.login_as(user2)

        response = self.client.post(f'/messages/{message.id}/delete', follow_redirects = True)

        self.assertNotEqual(response.status_code, 200)
        self.assertIsNotNone(Message.query.get(message.id))