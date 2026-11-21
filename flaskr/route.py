from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

import os
import requests

bp = Blueprint('route', __name__)

url = "https://www.googleapis.com/books/v1/volumes"
params={
    "q": "python programming",
    "key": os.environ["API_KEY"]
}



@bp.route('/')
@login_required
def index():
    response = requests.get(url, params=params)
    books = []
    image_urls = []
    if(response.ok and response.text):
        data = response.json()
        for book in data.get("items", []):
            books.append(book)

            image_url=""
            image_links=book["volumeInfo"]["imageLinks"]

            if(image_links!=None):
                if(image_links["thumbnail"] != None):
                    image_url=image_links["thumbnail"]
                elif(image_links["smallThumbnail"]!=None):
                    image_url=image_links["smallThumbnail"]

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
    return render_template('index/book_view.html', book=book_data)