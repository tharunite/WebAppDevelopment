from flask_login import UserMixin
import sqlite3

class User(UserMixin):
    def __init__(self, user_id, username, role, fullname):
        self.id = user_id
        self.username = username
        self.role = role
        self.fullname = fullname

