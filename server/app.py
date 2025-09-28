#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        json = request.get_json()
        try:
            user = User(
                username=json.get('username'),
                image_url=json.get('image_url'),
                bio=json.get('bio'),
            )
            user.password_hash = json.get('password')
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return user.to_dict(only=('id','username','image_url','bio')), 201
        except Exception as e:
            db.session.rollback()
            # handle integrity errors and validation errors
            message = str(e)
            return {'errors': [message]}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = db.session.get(User, user_id)
            if user:
                return user.to_dict(only=('id','username','image_url','bio'))
        return {'error': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        json = request.get_json()
        username = json.get('username')
        password = json.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return user.to_dict(only=('id','username','image_url','bio'))
        return {'error': 'Invalid username or password'}, 401

class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session['user_id'] = None
            return '', 204
        return {'error': 'No active session'}, 401

class RecipeIndex(Resource):
    def get(self):
        if not session.get('user_id'):
            return {'error': 'Unauthorized'}, 401
        recipes = Recipe.query.all()
        return [r.to_dict(only=('id','title','instructions','minutes_to_complete','user')) for r in recipes]

    def post(self):
        if not session.get('user_id'):
            return {'error': 'Unauthorized'}, 401
        json = request.get_json()
        try:
            recipe = Recipe(
                title=json.get('title'),
                instructions=json.get('instructions'),
                minutes_to_complete=json.get('minutes_to_complete'),
            )
            recipe.user_id = session.get('user_id')
            db.session.add(recipe)
            db.session.commit()
            return recipe.to_dict(only=('id','title','instructions','minutes_to_complete','user')), 201
        except Exception as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)