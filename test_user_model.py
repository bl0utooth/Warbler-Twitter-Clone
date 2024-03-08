"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///twitter-testing"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        self.user1 = User.signup("user1", "user1@test.com", "password", None)
        self.user2 = User.signup("user2", "user2@test.com", "password", None)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        u = User.query.filter_by(username= "user1").first()
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_is_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()
        self.assertTrue(self.user1.is_following(self.user2))

    def test_not_following(self):
        self.assertFalse(self.user1.is_following(self.user2))

    def test_create_user(self):
        user = User.signup("user3", "user3@email.com", "password", None)
        db.session.commit()
        self.assertIsNotNone(User.query.get(user.id))

    def test_correct_password(self):
        self.assertFalse(User.authenticate(self.user1.username, 'incorrectpassword'))

    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "user@email.com", "", None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "user@email.com", None, None)

    def test_invalid_password(self):
        self.assertFalse(User.authenticate(self.user1.username, 'invalidpassword'))

    def test_user_authentication(self):
        user = User.authenticate(self.user1.username, 'password')
        self.assertTrue(user)
        self.assertEqual(user.id, self.user1.id)
        