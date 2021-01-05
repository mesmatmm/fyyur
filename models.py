from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app = Flask(__name__)
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # link to the Flask app models and database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


class Show(db.Model):  # Association Table
    """
    many-to-many relationship becuase an artist (or a group of artists) can present shows in many venues
                                and a venue can be used by many artists to present shows.
    In this table, I made both artist_id and start_time as primary key for that table:
                    1- to enable artists to present shows in the same venue at different times
                    2- prevent the same artist to present shows at the same time in different venues
                    3- also enable different artists to present shows in the same venue at the same time (working as a group)
    """
    __tablename__ = 'Show'
    # parent id
    artist_id = db.Column(db.Integer, db.ForeignKey
                          ('Artist.id'), primary_key=True)
    # child id
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    # extra_data
    start_time = db.Column(db.DateTime, primary_key=True)
    # child
    venue = db.relationship("Venue", back_populates="artists")
    # parent
    artist = db.relationship("Artist", back_populates="venues")


class Artist(db.Model):  # Parent Table
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(300))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String())

    venues = db.relationship("Show", back_populates="artist")


class Venue(db.Model):  # Child Table
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(300))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(120))
    seeking_talent = db.Column(
        db.Boolean, default=False, server_default="false")
    seeking_description = db.Column(db.String())

    # parents
    artists = db.relationship("Show", back_populates="venue")
