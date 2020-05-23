#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
from sqlalchemy import func
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    genres = db.Column(db.ARRAY(db.String(120)), nullable=False)
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='venue')

    def __repr__(self):
        return f'<Venue {self.id} {self.city} {self.state}>'


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String(120)), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(300))
    shows = db.relationship('Show', backref='artist')


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'venues.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'artists.id'), nullable=False)

    def __repr__(self):
        return f'<Show {self.id} {self.start_time}>'


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

#----------------------------------------------------------------------------#
# Time Compare
#----------------------------------------------------------------------------#


def time_comp(timenow, time):
    return 'upcoming_shows' if time >= timenow else 'past_shows'


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    try:
        data = []
        timenow = datetime.now()
        city_state = db.session.query(Venue.city, Venue.state).group_by(
            Venue.city, Venue.state).all()

        for place in city_state:
            data_entry = {
                "city": place.city,
                "state": place.state,
                "venues": []
            }
            venue_data = Venue.query.filter(
                Venue.city == place.city, Venue.state == place.state).all()

            for vn in venue_data:
                num_upcoming_shows = db.session.query(func.count(Show.id)).filter(
                    Show.start_time > timenow, Show.venue_id == vn.id).all()
                data_entry['venues'].append({
                    "id": vn.id,
                    "name": vn.name,
                    "num_upcoming_shows": num_upcoming_shows,
                })
            data.append(data_entry)
    except:
        print(f'Error: {str(sys.exc_info())}')
        abort(500)
    return render_template('pages/venues.html', areas=data)


# search venue
@ app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    try:
        search_term = request.form.get('search_term', '')
        timenow = datetime.now()
        venues = db.session.query(Venue).filter(Venue.name.ilike(
            '%' + search_term + '%')).all()
        response = {
            "count": 0,
            "data": []
        }

        for venue in venues:
            num_upcoming_shows = db.session.query(func.count(Show.id)).filter(
                Show.start_time > timenow, Show.venue_id == venue.id).all()
            response['count'] = response.get('count') + 1
            response['data'].append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": num_upcoming_shows,
            })
    except:
        abort(500)
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


# Show Venue data by Id
@ app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    try:
        venue = Venue.query.filter(Venue.id == venue_id).one()
        data = {
            "id": venue_id,
            "name": venue.name,
            "genres": venue.genres,
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "website": venue.website,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description,
            "image_link": venue.image_link,
            "past_shows": [],
            "upcoming_shows": [],
            "past_shows_count": 0,
            "upcoming_shows_count": 0,
        }
        timenow = datetime.now()
        artists = db.session.query(Artist.id, Artist.name, Artist.image_link, Show.start_time.label(
            'time')).filter(Show.venue_id == venue.id).all()
        for artist in artists:
            show = time_comp(timenow, artist.time)
            data[show].append({
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": str(artist.time)
            })
            data[show + '_count'] = data.get(show + '_count') + 1
    except:
        flash(f'{str(sys.exc_info())}')
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@ app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    form = VenueForm()
    error = False
    try:
        newVenue = Venue(name=request.form['name'],
                         city=request.form['city'],
                         state=request.form['state'],
                         address=request.form['address'],
                         phone=request.form['phone'],
                         image_link=request.form['image_link'],
                         facebook_link=request.form['facebook_link'],
                         genres=request.form['genres'],
                         website=request.form['website'],
                         seeking_talent=True if "request.form['seeking_description']" != '' else False,
                         seeking_description=request.form['seeking_description']
                         )
        # TODO: modify data to be the data object returned from db insertion
        db.session.add(newVenue)
        db.session.commit()

        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    except:
        error = True
        db.session.rollback()
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')
    finally:
        # Always Close the session.
        db.session.close()
    return render_template('pages/home.html')

# Update Venue
# ----------------------------------------------


@ app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue_query = Venue.query.filter(Venue.id == venue_id).one()
    # # TODO: populate form with values from venue with ID <venue_id>
    venue = []
    for u in [venue_query]:
        venue_dict = u.__dict__
        venue_dict.pop('_sa_instance_state', None)
        venue.append(venue_dict)
    return render_template('forms/edit_venue.html', form=form, venue=venue[0])


@ app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.filter(Venue.id == venue_id).one()
    try:
        if request.form['name']:
            venue.name = request.form['name']
        if request.form['city']:
            venue.city = request.form['city']
        if request.form['state']:
            venue.state = request.form['state']
        if request.form['address']:
            venue.address = request.form['address']
        if request.form['phone']:
            venue.phone = request.form['phone']
        if request.form['image_link']:
            venue.image_link = request.form['image_link']
        if request.form['facebook_link']:
            venue.facebook_link = request.form['facebook_link']
        if request.form['genres']:
            venue.genres = request.form['genres']
        if request.form['website']:
            venue.website = request.form['website']
        if request.form['seeking_description']:
            venue.seeking_description = request.form['seeking_description']
        if request.form['seeking_description'] != '':
            venue.seeking_talent = True
        else:
            venue.seeking_talent = False

        db.session.add(venue)
        db.session.commit()
        flash(f'Venue {request.form["name"]} was successfully updated!')
    except:
        db.session.rollback()
        flash(f'Error: {str(sys.exc_info())}')
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


# Delete Venue
# ---------------------------------------------
@app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        Venue.query.filter(Venue.id == venue_id).delete()
        db.session.commit()
        flash(f'Venue id {venue_id} was successfully deleted!')
    except:
        db.session.rollback()
        flash(f'Error: {str(sys.exc_info())}')
    finally:
        db.session.close()

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return redirect(url_for('/'))


# -----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------

@ app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    artists = Artist.query.all()
    data = []
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })
    return render_template('pages/artists.html', artists=data)


@ app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    timenow = datetime.now()
    artists = db.session.query(Artist).filter(Artist.name.ilike(
        '%' + search_term + '%')).all()
    response = {
        "count": 0,
        "data": []
    }
    for artist in artists:
        num_upcoming_shows = db.session.query(func.count(Show.id)).filter(
            Show.start_time > timenow, Show.artist_id == artist.id).all()
        response['count'] = response.get('count') + 1
        response['data'].append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": num_upcoming_shows,
        })
    return render_template('pages/search_artists.html', results=response, search_term=search_term)


# Show Artist data by id
@ app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    try:
        artist = Artist.query.filter(Artist.id == artist_id).one()
        data = {
            "id": artist_id,
            "name": artist.name,
            "genres": artist.genres,
            "city": artist.city,
            "state": artist.state,
            "phone": artist.phone,
            "website": artist.website,
            "facebook_link": artist.facebook_link,
            "seeking_venue": artist.seeking_venue,
            "seeking_description": artist.seeking_description,
            "image_link": artist.image_link,
            "past_shows": [],
            "upcoming_shows": [],
            "past_shows_count": 0,
            "upcoming_shows_count": 0,
        }
        timenow = datetime.now()
        venues = db.session.query(Venue.id, Venue.name, Venue.image_link, Show.start_time.label(
            'time')).filter(Show.artist_id == artist.id).all()
        for venue in venues:
            show = time_comp(timenow, venue.time)
            data[show].append({
                "venue_id": venue.id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": str(venue.time)
            })
            data[show + '_count'] = data.get(show + '_count') + 1
    except:
        abort(404)

    return render_template('pages/show_artist.html', artist=data)


# Delete Artist
# ---------------------------------------------------
@app.route('/artists/<artist_id>/delete', methods=['DELETE'])
def delete_artist(artist_id):
    # TODO: Complete this endpoint for taking a artist_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        Artist.query.filter(Artist.id == artist_id).delete()
        db.session.commit()
        flash(f'Artist {artist_id} was successfully deleted!')
    except:
        db.session.rollback()
        flash(f'Error: {str(sys.exc_info())}')
    finally:
        db.session.close()

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return redirect(url_for('/'))

#  Update Artist
#  ----------------------------------------------------------------


@ app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    # # TODO: populate form with fields from artist with ID <artist_id>
    artist_query = Artist.query.filter(Artist.id == artist_id).one()
    artist = []
    for u in [artist_query]:
        artist_dict = u.__dict__
        artist_dict.pop('_sa_instance_state', None)
        artist.append(artist_dict)
    return render_template('forms/edit_artist.html', form=form, artist=artist[0])


@ app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    artist = Artist.query.filter(Artist.id == artist_id).one()
    try:
        if request.form['name']:
            artist.name = request.form['name']
        if request.form['city']:
            artist.city = request.form['city']
        if request.form['state']:
            artist.state = request.form['state']
        if request.form['phone']:
            artist.phone = request.form['phone']
        if request.form['image_link']:
            artist.image_link = request.form['image_link']
        if request.form['facebook_link']:
            artist.facebook_link = request.form['facebook_link']
        if request.form['genres']:
            artist.genres = request.form['genres']
        if request.form['website']:
            artist.website = request.form['website']
        if request.form['seeking_description']:
            artist.seeking_description = request.form['seeking_description']
        if request.form['seeking_description'] != '':
            artist.seeking_venue = True
        else:
            artist.seeking_venue = False

        db.session.add(artist)
        db.session.commit()
        flash(f'Artist {request.form["name"]} was successfully updated!')
    except:
        db.session.rollback()
        flash(f'Error: {str(sys.exc_info())}')
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


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
    form = ArtistForm()
    error = False
    try:
        newArtist = Artist(name=request.form['name'],
                           city=request.form['city'],
                           state=request.form['state'],
                           phone=request.form['phone'],
                           image_link=request.form['image_link'],
                           facebook_link=request.form['facebook_link'],
                           genres=request.form['genres'],
                           website=request.form['website'],
                           seeking_venue=True if "request.form['seeking_description']" != '' else False,
                           seeking_description=request.form['seeking_description'])
        # TODO: modify data to be the data object returned from db insertion
        db.session.add(newArtist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    except:
        error = True
        db.session.rollback()
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')
    finally:
        # Always Close the session.
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@ app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    show_query = db.session.query(Show, Show.start_time.label('start_time'), Venue.id.label('venue_id'), Venue.name.label('venue_name'), Artist.id.label(
        'artist_id'), Artist.name.label('artist_name'), Artist.image_link.label('image_link')).filter(Show.venue_id == Venue.id, Show.artist_id == Artist.id).all()
    data = []
    for query in show_query:
        data.append({
            "venue_id": query.venue_id,
            "venue_name": query.venue_name,
            "artist_id": query.artist_id,
            "artist_name": query.artist_name,
            "artist_image_link": query.image_link,
            "start_time": str(query.start_time)
        })
    return render_template('pages/shows.html', shows=data)


# Create Shows
# --------------------------------------------------------------
@ app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@ app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    form = ShowForm()
    error = False
    try:
        newShow = Show(start_time=request.form['start_time'],
                       venue_id=request.form['venue_id'],
                       artist_id=request.form['artist_id'])
        # on successful db insert, flash success
        db.session.add(newShow)
        db.session.commit()
        flash('Show was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    except:
        error = True
        db.session.rollback()
        flash(f'An error occurred. Show could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


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
