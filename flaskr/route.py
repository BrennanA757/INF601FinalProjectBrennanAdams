from flask import (
    Blueprint, render_template, request
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required

import os
import requests

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

    return render_template('index/index.html', books=books, image_urls=image_urls)

@bp.route('/book_view/<volume_id>')
@login_required
def book_view(volume_id):
    new_url=f"{url}/{volume_id}"
    params={"key": os.environ["API_KEY"]}

    print(f"URL: {new_url}")
    response = requests.get(f"{new_url}", params=params)
    print(f"Response: {response}")

    if(not response.ok or not response.text):
        abort(404) #Render error template if book retrieval was unsuccessful.


    book_data=response.json()
    image_url=get_book_img(book_data)
    return render_template('index/book_view.html', book=book_data, image_url=image_url)



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