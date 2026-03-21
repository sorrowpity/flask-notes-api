from flask import session, redirect
from models import db, User

def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)

def login_required():
    if not get_current_user():
        return redirect("/login")
    return None