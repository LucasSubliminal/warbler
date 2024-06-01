import os
import unittest
from datetime import datetime

from app import app, db
from models import User, Message



app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['warbler']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TESTING'] = True

with app.app_context():
    db.create_all()

class MessageModelTestCase(unittest.TestCase):
    """Test cases for the Message model."""

    def setUp(self):
        """Create test client, add sample data."""
        self.client = app.test_client()

        # Create a sample user
        self.user = User.signup(
            username="testuser",
            email="test@test.com",
            password="password",
            image_url=None
        )
        db.session.commit()
        self.user_id = self.user.id

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        db.session.commit()

    def test_message_model(self):
        """Does basic model work?"""
        msg = Message(
            text="This is a test message.",
            user_id=self.user_id
        )
        db.session.add(msg)
        db.session.commit()

        self.assertEqual(msg.text, "This is a test message.")
        self.assertEqual(msg.user_id, self.user_id)
        self.assertIsInstance(msg.timestamp, datetime)
        self.assertEqual(msg.user.id, self.user_id)

    def test_message_user_relationship(self):
        """Test the relationship between Message and User models."""
        msg = Message(
            text="Another test message.",
            user_id=self.user_id
        )
        db.session.add(msg)
        db.session.commit()

        self.assertEqual(msg.user.username, "testuser")
        self.assertEqual(msg.user.email, "test@test.com")

if __name__ == '__main__':
    unittest.main()
