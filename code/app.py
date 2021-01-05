#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for,
    abort
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from config import *
import sys
from sqlalchemy.ext.declarative import declarative_base
import datetime
from models import app, db, Venue, Artist, Show

Base = declarative_base()


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#


moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


############################################################################


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    locals = []
    venues = Venue.query.all()
    for place in Venue.query.distinct(Venue.city, Venue.state).all():
        locals.append({
            'city': place.city,
            'state': place.state,
            'venues': [{
                'id': venue.id,
                'name': venue.name,
            } for venue in venues if
                venue.city == place.city and venue.state == place.state]
        })
    return render_template('pages/venues.html', areas=locals)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    search_term = request.form.get('search_term', '')
    results = Venue.query.filter(Venue.name.ilike('%'+search_term+'%'))
    count = 0
    data = []
    for v in results:
        count += 1
        shows = v.artists    # get all_shows
        upcoming_shows_count = 0
        for s in shows:
            if s.start_time > datetime.datetime.now():  # to get num_upcoming_shows
                upcoming_shows_count += 1
        v_info = {
            "id": v.id,
            "name": v.name,
            "num_upcoming_shows": upcoming_shows_count
        }
        data.append(v_info)

    response = {
        "count": count,
        "data": data
    }
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id

    past_shows = db.session.query(Artist, Show).join(Show).join(Venue).\
        filter(
        Show.venue_id == venue_id,
        Show.artist_id == Artist.id,
        Show.start_time < datetime.datetime.now()
    ).all()

    upcoming_shows = db.session.query(Artist, Show).join(Show).join(Venue).\
        filter(
        Show.venue_id == venue_id,
        Show.artist_id == Artist.id,
        Show.start_time > datetime.datetime.now()
    ).all()

    venue = Venue.query.filter_by(id=venue_id).first_or_404()

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": [],
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        # "seeking_description": required_venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": [{
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
        } for artist, show in past_shows],
        "upcoming_shows": [{
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
        } for artist, show in upcoming_shows],
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }

    # from {g1,g2,..} to ["g1", "g2", ...]
    genres = venue.genres
    genres = genres[1:]  # Removing the fist character
    genres = genres[:-1]  # Removing the last character
    genres = genres.split(',')
    data["genres"] = genres

    if venue.seeking_talent:  # to add seeking_description
        data["seeking_description"] = venue.seeking_description

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    # NOTE:
    # When you validate with FlaskForm.validate, it is necessary to also provideCSRF
    # protection in the forms of the views. To avoid having to implement CSRF inviews,
    # use the attribute: meta={'csrf': False}:

    form = VenueForm(request.form, meta={'csrf': False})
    if form.validate():
        error = False
        try:
            venue = Venue()
            form.populate_obj(venue)
            db.session.add(venue)
            db.session.commit()
            flash('Venue ' + request.form['name']
                  + ' was successfully listed!')
        except ValueError as e:
            db.session.rollback()
            print(e)
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be listed.')
            error = True
        finally:
            db.session.close()

        if error:
            return redirect(url_for('create_venue_submission'))
        else:
            # return render_template('pages/home.html')
            # redirect to the home page
            return redirect('/')
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))
        return redirect(url_for('create_venue_submission'))


@ app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    error = False
    name = ""
    try:
        venue = Venue.query.get(venue_id)
        name = venue.name
        all_shows = Show.query.filter_by(venue_id=venue_id)
        all_shows.delete()
        # db.session.commit()
        db.session.delete(venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + name + ' was successfully deleted!')
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info)
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue ' + name + ' could not be deleted.')
        abort(500)
    else:
        return render_template('pages/home.html')


@ app.route('/artists/<int:artist_id>/delete', methods=['DELETE'])
def delete_artist(artist_id):
    # TODO: Complete this endpoint for taking a artist_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Artist on a Artist Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    error = False
    name = ""
    try:
        artist = Artist.query.get(artist_id)
        name = artist.name
        all_shows = Show.query.filter_by(artist_id=artist_id)
        all_shows.delete()
        # db.session.commit()
        db.session.delete(artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + name + ' was successfully deleted!')
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info)
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist ' + name + ' could not be deleted.')
        abort(500)
    else:
        return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------


@ app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = []
    artists = Artist.query.all()
    for a in artists:
        x = {
            "id": a.id,
            "name": a.name
        }
        data.append(x)
    return render_template('pages/artists.html', artists=data)


@ app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # search for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".

    search_term = request.form.get('search_term', '')
    results = Artist.query.filter(Artist.name.ilike('%'+search_term+'%'))
    count = 0
    data = []
    for a in results:
        count += 1
        shows = a.venues    # get all_shows
        upcoming_shows_count = 0
        for s in shows:
            if s.start_time > datetime.datetime.now():  # to get num_upcoming_shows
                upcoming_shows_count += 1
        a_info = {
            "id": a.id,
            "name": a.name,
            "num_upcoming_shows": upcoming_shows_count
        }
        data.append(a_info)

    response = {
        "count": count,
        "data": data
    }
    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@ app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artists table, using artist_id

    past_shows = db.session.query(Venue, Show).join(Show).join(Artist).\
        filter(
        Show.artist_id == artist_id,
        Show.venue_id == Venue.id,
        Show.start_time < datetime.datetime.now()
    ).all()

    upcoming_shows = db.session.query(Venue, Show).join(Show).join(Artist).\
        filter(
        Show.artist_id == artist_id,
        Show.venue_id == Venue.id,
        Show.start_time > datetime.datetime.now()
    ).all()

    artist = Artist.query.filter_by(id=artist_id).first_or_404()
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": [],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        # "seeking_description": required_artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": [{
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
        } for venue, show in past_shows],
        "upcoming_shows": [{
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": venue.image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
        } for venue, show in upcoming_shows],
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
    }
    # from {g1,g2,..} to ["g1", "g2", ...]
    genres = artist.genres
    genres = genres[1:]  # Removing the fist character
    genres = genres[:-1]  # Removing the last character
    genres = genres.split(',')
    data["genres"] = genres

    if artist.seeking_venue:  # to add seeking_description
        data["seeking_description"] = artist.seeking_description

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------

@ app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@ app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    # NOTE:
    # When you validate with FlaskForm.validate, it is necessary to also provideCSRF
    # protection in the forms of the views. To avoid having to implement CSRF inviews,
    # use the attribute: meta={'csrf': False}:
    print('1111111111111111111111111111111111')
    form = ArtistForm(request.form, meta={'csrf': False})
    if form.validate():
        error = False
        try:
            print('eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeewwwww')
            artist = Artist.query.get_or_404(artist_id)
            form.populate_obj(artist)
            db.session.commit()
            flash('Artist ' + request.form['name']
                  + ' was successfully updated!')
        except ValueError as e:
            db.session.rollback()
            print(e)
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be updated.')
            error = True
        finally:
            db.session.close()

        if error:
            return redirect(url_for('edit_artist_submission', artist_id=artist_id))
        else:
            return redirect(url_for('show_artist', artist_id=artist_id))
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))
        return redirect(url_for('edit_artist_submission', artist_id=artist_id))


@ app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@ app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes

    # NOTE:
    # When you validate with FlaskForm.validate, it is necessary to also provideCSRF
    # protection in the forms of the views. To avoid having to implement CSRF inviews,
    # use the attribute: meta={'csrf': False}:

    form = VenueForm(request.form, meta={'csrf': False})
    if form.validate():
        error = False
        try:
            venue = Venue.query.get_or_404(venue_id)
            form.populate_obj(venue)
            db.session.commit()
            flash('Venue ' + request.form['name']
                  + ' was successfully updated!')
        except ValueError as e:
            db.session.rollback()
            print(e)
            flash('An error occurred. Venue ' +
                  request.form['name'] + ' could not be updated.')
            error = True
        finally:
            db.session.close()

        if error:
            return redirect(url_for('edit_venue_submission', venue_id=venue_id))
        else:
            return redirect(url_for('show_venue', venue_id=venue_id))
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))
        return redirect(url_for('edit_venue_submission', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@ app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@ app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    # NOTE:
    # When you validate with FlaskForm.validate, it is necessary to also provideCSRF
    # protection in the forms of the views. To avoid having to implement CSRF inviews,
    # use the attribute: meta={'csrf': False}:

    form = ArtistForm(request.form, meta={'csrf': False})
    if form.validate():
        error = False
        try:
            artist = Artist()
            form.populate_obj(artist)
            db.session.add(artist)
            db.session.commit()
            flash('Artist ' + request.form['name']
                  + ' was successfully listed!')
        except ValueError as e:
            db.session.rollback()
            print(e)
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be listed.')
            error = True
        finally:
            db.session.close()

        if error:
            return redirect(url_for('create_artist_submission'))
        else:
            # return render_template('pages/home.html')
            # redirect to the home page
            return redirect('/')
    else:
        message = []
        for field, err in form.errors.items():
            message.append(field + ' ' + '|'.join(err))
        flash('Errors ' + str(message))
        return redirect(url_for('create_artist_submission'))


#  Shows
#  ----------------------------------------------------------------

@ app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real shows data.

    data = []
    shows = Show.query.all()
    for s in shows:
        show_info = {
            "venue_id": s.venue_id,
            "venue_name": s.venue.name,
            "artist_id": s.artist_id,
            "artist_name": s.artist.name,
            "artist_image_link": s.artist.image_link,
            "start_time": s.start_time.strftime("%Y/%m/%d, %H:%M:%S")
        }
        data.append(show_info)

    return render_template('pages/shows.html', shows=data)


@ app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@ app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    error = False
    try:
        artist_id = request.form['artist_id']
        venue_id = request.form['venue_id']
        start_time = request.form['start_time']

        artist = Artist.query.get(artist_id)
        venue = Venue.query.get(venue_id)
        if artist == None or venue == None:  # check if artist_id or venue_id doesn't exist
            raise 'error'
        show = Show(start_time=start_time, venue=venue, artist=artist)
        db.session.commit()

        # on successful db insert, flash success
        flash('Show was successfully listed!')

    except:
        db.session.rollback()
        error = True
        print(sys.exc_info)
    finally:
        db.session.close()
    if error:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Show could not be listed.')
        flash('An error occurred. Show could not be listed.')
        abort(500)
    else:
        return redirect('/')  # redirect to the home page
        # return render_template('pages/home.html')


# see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


@ app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@ app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
