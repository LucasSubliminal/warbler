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

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()



class UserModelTestCase(TestCase):
    """Test User model."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            db.drop_all()
            db.create_all()
            self.client = app.test_client()

            self.testuser = User.signup(username="testuser",
                                        email="test@test.com",
                                        password="password",
                                        image_url=None)
            db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""
        with app.app_context():
            db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""
        with app.app_context():
            u = User(
                email="test2@test.com",
                username="testuser2",
                password="HASHED_PASSWORD"
            )

            db.session.add(u)
            db.session.commit()

            # User should have no messages & no followers
            self.assertEqual(len(u.messages), 0)
            self.assertEqual(len(u.followers), 0)

    def test_user_follows(self):
        """Test following functionality."""
        with app.app_context():
            u1 = User(
                email="test1@test.com",
                username="testuser1",
                password="HASHED_PASSWORD"
            )

            u2 = User(
                email="test2@test.com",
                username="testuser2",
                password="HASHED_PASSWORD"
            )

            db.session.add_all([u1, u2])
            db.session.commit()

            u1.following.append(u2)
            db.session.commit()

            self.assertEqual(len(u1.following), 1)
            self.assertEqual(len(u2.followers), 1)
            self.assertEqual(u1.following[0].id, u2.id)
            self.assertEqual(u2.followers[0].id, u1.id)

            self.assertTrue(u2.is_followed_by(u1))
            self.assertTrue(u1.is_following(u2))

    def test_user_signup(self):
        """Test user signup."""
        with app.app_context():
            u = User.signup(username="newuser",
                            email="new@test.com",
                            password="password",
                            image_url=None)
            db.session.commit()

            self.assertIsNotNone(u.id)
            self.assertEqual(u.username, "newuser")
            self.assertEqual(u.email, "new@test.com")
            self.assertTrue(u.check_password("password"))

    def test_user_authenticate(self):
        """Test user authentication."""
        with app.app_context():
            user = User.authenticate(username="testuser", password="password")
            self.assertIsNotNone(user)
            self.assertEqual(user.username, "testuser")

            invalid_user = User.authenticate(username="testuser", password="wrongpassword")
            self.assertFalse(invalid_user)

            non_existent_user = User.authenticate(username="notarealuser", password="password")
            self.assertFalse(non_existent_user)