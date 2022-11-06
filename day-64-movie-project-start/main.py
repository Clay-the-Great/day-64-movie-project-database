from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests

API_KEY = "0c0988f491f51854672abd5236d3f225"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.app_context().push()
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies-collection.db"
db = SQLAlchemy(app)


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String, nullable=True)
    img_url = db.Column(db.String, nullable=True)

    def __repr__(self):
        return '<User %r>' % self.username


# db.create_all()

new_movie = Movies(
    title="Phone Booth",
    year=2002,
    description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an "
                "extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation "
                "with the caller leads to a jaw-dropping climax.",
    rating=7.3,
    ranking=10,
    review="My favourite character was the caller.",
    img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
)
# db.session.add(new_movie)
# db.session.commit()


class AddForm(FlaskForm):
    title = StringField(
        label="Movie Title",
        validators=[DataRequired()]
    )
    submit = SubmitField(label="Done")


class EditForm(FlaskForm):
    rating = StringField(
        label="Your rating out of 10, e.g. 7.5"
    )
    review = StringField(
        label="Your review"
    )
    submit = SubmitField(label="Done")


class DeletionForm(FlaskForm):
    delete = SubmitField(label="Delete")
    cancel = SubmitField(label="Cancel")


@app.route("/")
def home():
    # all_movies = Movies.query.order_by(Movies.rating.desc())
    all_movies = Movies.query.order_by(Movies.rating.asc())
    ranking = 1
    for movie in all_movies[::-1]:
        movie.ranking = ranking
        ranking += 1
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=["POST", "GET"])
def add():
    add_form = AddForm()
    if add_form.validate_on_submit():
        new_title = add_form.title.data
        parameters = {
            "api_key": API_KEY,
            "query": new_title,
        }
        response = requests.get(url="https://api.themoviedb.org/3/search/movie", params=parameters).json()
        movies = response["results"]
        return render_template("select.html", movies=movies)
    return render_template("add.html", add_form=add_form)


@app.route("/ready_to_add/<movie_web_id>", methods=["POST", "GET"])
def ready_to_add(movie_web_id):
    parameters = {
        "api_key": API_KEY,
    }
    response = requests.get(url=f"https://api.themoviedb.org/3/movie/{movie_web_id}", params=parameters).json()
    movie_to_add = Movies(
        title=response["title"],
        img_url=f"https://image.tmdb.org/t/p/w500/{response['poster_path']}",
        year=response["release_date"],
        description=response["overview"],
    )
    db.session.add(movie_to_add)
    db.session.commit()
    db.session.refresh(movie_to_add)
    print(movie_to_add.id)
    return redirect(url_for("edit", movie_id=movie_to_add.id))


@app.route("/edit/<movie_id>", methods=["POST", "GET"])
def edit(movie_id):
    movie_to_edit = Movies.query.get(movie_id)
    edit_form = EditForm()
    if edit_form.validate_on_submit():
        new_rating = edit_form.rating.data
        new_review = edit_form.review.data
        if new_rating:
            movie_to_edit.rating = float(new_rating)
        if new_review:
            movie_to_edit.review = new_review
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", edit_form=edit_form, movie=movie_to_edit)


@app.route("/delete/<movie_id>", methods=["POST", "GET"])
def delete(movie_id):
    movie_to_delete = Movies.query.get(movie_id)
    deletion_form = DeletionForm()
    if deletion_form.validate_on_submit():
        if deletion_form.cancel.data:
            return redirect(url_for("home"))
        elif deletion_form.delete.data:
            db.session.delete(movie_to_delete)
            db.session.commit()
            return redirect(url_for("home"))
    return render_template("delete.html", deletion_form=deletion_form, movie=movie_to_delete)


if __name__ == '__main__':
    app.run(debug=True)
