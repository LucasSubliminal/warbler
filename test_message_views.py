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
        with app.app_context():
            db.drop_all()
            db.create_all()
            self.client = app.test_client()
            self.testuser = User.signup(username="testuser",
                                        email="test@test.com",
                                        password="testuser",
                                        image_url=None)
            db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""
        with app.app_context():
            db.session.rollback()

    def test_add_message(self):
        """Can user add a message?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_message_unauthorized(self):
        """Is unauthorized user prohibited from adding a message?"""
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Unauthorized"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Access unauthorized", resp.data)

            msg = Message.query.filter_by(text="Unauthorized").first()
            self.assertIsNone(msg)

    def test_delete_message(self):
        """Can user delete their own message?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            msg = Message(text="Hello", user_id=self.testuser.id)
            db.session.add(msg)
            db.session.commit()

            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            msg = Message.query.get(msg.id)
            self.assertIsNone(msg)

    def test_delete_message_unauthorized(self):
        """Is unauthorized user prohibited from deleting a message?"""
        with self.client as c:
            msg = Message(text="Unauthorized", user_id=self.testuser.id)
            db.session.add(msg)
            db.session.commit()

            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Access unauthorized", resp.data)

            msg = Message.query.get(msg.id)
            self.assertIsNotNone(msg)

    def test_show_message(self):
        """Can user view a message?"""
        with self.client as c:
            msg = Message(text="Hello", user_id=self.testuser.id)
            db.session.add(msg)
            db.session.commit()

            resp = c.get(f"/messages/{msg.id}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Hello", resp.data)
