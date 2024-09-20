from flask import Flask
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

db = SQLAlchemy()


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#
class Venue(db.Model):
    __tablename__ = "venues"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column("genres", db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))

    def __repr__(self):
        return f"<Venue: {self.id}:  {self.name}>"


class Artist(db.Model):
    __tablename__ = "artists"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_description = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)

    def __repr__(self):
        return f"<Artist: {self.id}:  {self.name}>"


class Show(db.Model):
    __tablename__ = "shows"

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id"))
    venue_id = db.Column(db.Integer, db.ForeignKey("venues.id"))
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    artist = db.relationship(
        "Artist", backref=db.backref("shows", cascade="all, delete-orphan")
    )
    venue = db.relationship(
        "Venue", backref=db.backref("shows", cascade="all, delete-orphan")
    )

    def __repr__(self):
        return f"<Show: {self.id}"


