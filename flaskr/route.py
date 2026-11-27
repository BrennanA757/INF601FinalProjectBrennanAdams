from flask import (
    Blueprint, render_template, request, url_for, flash, redirect, g
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required

import os
import requests
from flaskr.db import get_db
import json

bp = Blueprint('route', __name__)

url = "https://www.googleapis.com/books/v1/volumes"
key=os.environ["API_KEY"]

@bp.route('/', methods=["POST", "GET"])
@login_required
def index():
    item_lookup=""
    if request.method=="POST":
        item_lookup=request.form.get('book_lookup')
    else:
        item_lookup="Python Programming"
    params={
        "key": key,
        "q": item_lookup
    }
    response = requests.get(url, params=params)
    books = []
    image_urls = []
    if(response.ok and response.text):
        data = response.json()
        for book in data.get("items", []):
            books.append(book)

            image_url=get_book_img(book)

            if(image_url!=""):
                image_urls.append(image_url)

    return render_template('index/index.html', books=books, image_urls=image_urls, user_id=g.user['user_id'])

@bp.route('/book_view/<volume_id>/<user_id>')
@login_required
def book_view(volume_id, user_id):
    new_url=f"{url}/{volume_id}"
    params={"key": os.environ["API_KEY"]}

    response = requests.get(f"{new_url}", params=params)

    if(not response.ok or not response.text):
        abort(404) #Render error template if book retrieval was unsuccessful.

    book_data=response.json()
    image_url=get_book_img(book_data)
    comments=get_book_comments(volume_id)
    rating=get_book_rating(volume_id)
    has_rated=get_has_user_rated(user_id)
    return render_template('index/book_view.html', book=book_data, image_url=image_url, comments=comments, rating=rating, has_rated=has_rated)

@bp.route('/book_view/<volume_id>/<user_id>/<username>/comment', methods=["POST"])
def add_comment(volume_id, user_id, username):
    body=request.form.get('body', '').strip()

    if not body:
        flash('Comment cannot be empty')
        return redirect(url_for('route.book_view'))

    db=get_db()
    db.execute(
        'INSERT INTO comments (author_id, author_name, volume_id, body) VALUES (?, ?, ?, ?)',
        (user_id, username, volume_id, body)
    )
    db.commit()
    return redirect(url_for('route.book_view', volume_id=volume_id))

@bp.route('/book_view/<volume_id>/<user_id>/add_rating', methods=["POST"])
def add_rating(volume_id, user_id):
    rating=int(request.form["rating"].split()[0])
    print(f"Selected rating: {rating}")

    db=get_db()
    db_data=db.execute(
        'SELECT ratings FROM ratings WHERE volume_id=?',
        (volume_id,)
    ).fetchone()

    if(db_data != None):
        ratings_list=json.loads(db_data["ratings"])
        ratings=[float(x) for x in ratings_list]

        ratings.append(rating)
        print(f"Appended rating to ratings: {ratings}")

        db.execute(
            'UPDATE ratings SET ratings=? WHERE volume_id=?',
            (json.dumps(ratings), volume_id,)
        )
    else:
        ratings=[rating]
        print(f"Adding new rating to book: {ratings}")
        db.execute(
            'INSERT INTO ratings (ratings, volume_id) VALUES (?, ?)',
            (json.dumps(ratings), volume_id,)
        )
    db.commit()

    #Include user's id to this book's ratings list
    add_user_rating_to_book(volume_id, user_id)

    return redirect(url_for('route.book_view', volume_id=volume_id))



#Helper functions
def get_book_img(book):
    image_url=""
    image_links=book["volumeInfo"].get("imageLinks", {})

    if(image_links!={}):
        thumbnail = image_links.get("thumbnail", {})
        small_thumbnail = image_links.get("smallThumbnail", {})
        if(thumbnail != {}):
            image_url=thumbnail
        elif(small_thumbnail!={}):
            image_url=small_thumbnail

    return image_url

def get_book_comments(volume_id):
    db=get_db()
    query='SELECT * FROM comments WHERE volume_id = ?'
    comments=db.execute(query, (volume_id,)).fetchall()
    return comments

def get_book_rating(volume_id):
    db=get_db()
    query='SELECT ratings FROM ratings WHERE volume_id = ?'
    response=db.execute(query, (volume_id,)).fetchone()
    if(response == None):
        return None
    else:
        ratings_list=json.loads(response['ratings'])
        ratings=[float(x) for x in ratings_list]
        rating=sum(ratings)/len(ratings_list)
        return rating

def get_has_user_rated(user_id):
    db=get_db()
    query='SELECT users_who_have_set_ratings FROM ratings'
    response=db.execute(query).fetchone()
    print(f"response: {response}")

    #If no response, book has no current ratings and thus user has not rated book yet.
    if(response == None or response['users_who_have_set_ratings'] in (None, "")):
        return False
    else:
        response_json=json.loads(response['users_who_have_set_ratings'])
        print(f"response_json: {response_json}")
        id_string=str(response_json)
        print(f"id_string: {id_string}")
        id_list=id_string.split(',')
        print(f"id_list: {id_list}")
        return user_id in id_list

def add_user_rating_to_book(volume_id, user_id):
    db=get_db()

    query='SELECT users_who_have_set_ratings FROM ratings WHERE volume_id=?'
    response=db.execute(query, (volume_id,))
    if(response != None and response.get("users_who_have_set_ratings", "") != ""):
        id_list=response["users_who_have_set_ratings"]
        new_list=id_list+user_id+','
        query='UPDATE ratings SET users_who_have_set_ratings TO ? WHERE volume_id=?'
        response=db.execute(query, (new_list, volume_id,))
    else:
        query='INSERT INTO ratings (users_who_have_set_ratings) VALUES (?) WHERE user_id=?'
        db.execute(query, (user_id, volume_id,))
    db.commit()