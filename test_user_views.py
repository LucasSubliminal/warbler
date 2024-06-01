import os
from unittest import TestCase
from models import db, connect_db, User, Message, Follows
from app import app, CURR_USER_KEY

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

with app.app_context():
    db.create_all()

# Disable CSRF for testing
app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users."""

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

    def test_signup(self):
        """Can user sign up?"""
        with self.client as c:
            resp = c.post("/signup", data={
                "username": "newuser",
                "password": "password",
                "email": "new@test.com",
                "image_url": ""
            }, follow_redirects=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Hello, newuser!", resp.data)

            user = User.query.filter_by(username="newuser").first()
            self.assertIsNotNone(user)

    def test_login(self):
        """Can user log in?"""
        with self.client as c:
            resp = c.post("/login", data={
                "username": "testuser",
                "password": "password"
            }, follow_redirects=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Hello, testuser!", resp.data)

    def test_logout(self):
        """Can user log out?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get("/logout", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"You have logged out, hope to see you soon!", resp.data)
            self.assertNotIn(CURR_USER_KEY, session)

    def test_show_following(self):
        """Can user see the following list?"""
        with self.client as c:
            u1 = User.signup(username="user1", email="user1@test.com", password="password", image_url=None)
            u2 = User.signup(username="user2", email="user2@test.com", password="password", image_url=None)
            db.session.commit()

            u1.following.append(u2)
            db.session.commit()

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = u1.id

            resp = c.get(f"/users/{u1.id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"user2", resp.data)

    def test_profile_update(self):
        """Can user update their profile?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/users/profile", data={
                "username": "updateduser",
                "email": "updated@test.com",
                "image_url": "",
                "header_image_url": "",
                "bio": "Updated bio",
                "password": "password"
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Profile updated successfully.", resp.data)

            user = User.query.get(self.testuser.id)
            self.assertEqual(user.username, "updateduser")
            self.assertEqual(user.email, "updated@test.com")
            self.assertEqual(user.bio, "Updated bio")
