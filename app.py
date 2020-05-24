#!/usr/bin/python3
#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import (render_template, request, Response,
                   flash, redirect, url_for, abort)
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime
from sqlalchemy import func
import sys
from models import *
from config import *
from werkzeug.exceptions import *
from sqlalchemy.orm.exc import *
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
    try:
        data = []
        timenow = datetime.now()
        # Query group by city and state
        city_state = db.session.query(Venue.city, Venue.state).group_by(
            Venue.city, Venue.state).all()
        # for each unique (city and state)
        for place in city_state:
            data_entry = {
                "city": place.city,
                "state": place.state,
                "venues": []
            }
            # query all venue data with matched by city and state
            venue_data = Venue.query.filter(
                Venue.city == place.city, Venue.state == place.state).all()

            # get show time data for each venue data
            for vn in venue_data:
                num_upcoming_shows = db.session.query(
                    func.count(Show.id)).filter(
                    Show.start_time > timenow, Show.venue_id == vn.id).all()
                # append each data in data_entry['venues']
                data_entry['venues'].append({
                    "id": vn.id,
                    "name": vn.name,
                    "num_upcoming_shows": num_upcoming_shows,
                })
                # finally apend each venue data in data list
            data.append(data_entry)
    # if any error occured!
    except BadRequest:
        abort(400)
    except Exception as e:
        flash(f'Error: {str(sys.exc_info()[0])}')
    # return venue page with data
    return render_template('pages/venues.html', areas=data)


# search venue
@ app.route('/venues/search', methods=['POST'])
def search_venues():
    try:
        # get value from searchbox
        search_term = request.form.get('search_term', '')
        # current time
        timenow = datetime.now()
        # fetch/search data by user input value
        venues = db.session.query(Venue).filter(Venue.name.ilike(
            '%' + search_term + '%')).all()
        response = {
            "count": 0,
            "data": []
        }
        # for each venue data
        for venue in venues:
            # fetch show time which greater than current time
            num_upcoming_shows = db.session.query(func.count(Show.id)).filter(
                Show.start_time > timenow, Show.venue_id == venue.id).all()
            # in for loop increment respone['count']by 1 and append data
            response['count'] = response.get('count') + 1
            response['data'].append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": num_upcoming_shows,
            })
    # error handling
    # error Method Not Allowed
    except MethodNotAllowed as mt:
        abort(405)
    except BadRequest:
        abort(400)
    except Exception as e:
        flash(f'Error: {str(sys.exc_info()[0])}')
    return render_template('pages/search_venues.html',
                           results=response, search_term=search_term)


# Show Venue data by Id
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    try:
        # shows the venue page with the given venue_id
        venue = Venue.query.filter(Venue.id == venue_id).one()
        # fetch data from Artist, Show using venue_id
        artists = db.session.query(Artist.id, Artist.name, Artist.image_link,
                                   Show.start_time.label('time')).join(
                                       Artist).filter(
                                           Show.venue_id == venue_id).all()
        # store data in dictionary using List Comprehensions
        data = [u.__dict__ for u in [venue]]
        # each data in articles
        for artist in artists:
            # time Compresion
            show = time_comp(datetime.now(), artist.time)
            # append artist data and numbers in datalist
            data[0][show] = data[0].get(show, []) + [{
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": str(artist.time)
            }]
            data[0][show + '_count'] = data[0].get(show + '_count', 0) + 1
    # error handling
    # No Result Found
    except not_found_error:
        abort(404)
    except BadRequest:
        abort(400)
    except Exception as e:
        flash(f'Error: {str(sys.exc_info()[0])}')
    return render_template('pages/show_venue.html', venue=data[0])

#  Create Venue
#  ----------------------------------------------------------------


@ app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()
    error = False
    try:
        # taking input value from Forms for store in database
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
        db.session.add(newVenue)
        db.session.commit()

        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    # Error Handling
    # error Method Not Allowed
    except MethodNotAllowed as mt:
        db.session.rollback()
        abort(405)
    # except
    except BadRequest:
        abort(400)
    except Exception:
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
    try:
        form = VenueForm()
        # Select venue data from db using venue_id and store in list
        venue_query = Venue.query.filter(Venue.id == venue_id).one()
        venue = []
        for u in [venue_query]:
            venue_dict = u.__dict__
            venue_dict.pop('_sa_instance_state', None)
            venue.append(venue_dict)
    # Error Handling
    except NoResultFound:
        abort(404)
    except BadRequest:
        abort(400)
    except Exception as e:
        flash(f'Error: {str(sys.exc_info()[0])}')
    return render_template('forms/edit_venue.html', form=form, venue=venue[0])


@ app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # Select venue data from db using venue_id
    venue = Venue.query.filter(Venue.id == venue_id).one()
    try:
        # taking form values if available and update db
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
        # commit session
        db.session.add(venue)
        db.session.commit()
        flash(f'Venue {request.form["name"]} was successfully updated!')
    # Error Handling
    # error Method Not Allowed
    except MethodNotAllowed as mt:
        db.session.rollback()
        abort(405)
    except BadRequest:
        db.session.rollback()
        abort(400)
    except Exception:
        db.session.rollback()
        flash(f'Error: {str(sys.exc_info()[0])}')
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


# Delete Venue
# ---------------------------------------------
@app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        # delete venue data row using given_id
        Venue.query.filter(Venue.id == venue_id).delete()
        db.session.commit()
        flash(f'Venue id {venue_id} was successfully deleted!')
    # Error Handling
    # error Method Not Allowed
    except MethodNotAllowed as mt:
        db.session.rollback()
        abort(405)
    except BadRequest:
        db.session.rollback()
        abort(400)
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(sys.exc_info()[0])}')
    finally:
        db.session.close()
    return redirect(url_for('index'))


# -----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------

@ app.route('/artists')
def artists():
    # select artist (id, name) data row and store in list
    artists = Artist.query.all()
    data = []
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })
    return render_template('pages/artists.html', artists=data)


# Search Artist
@ app.route('/artists/search', methods=['POST'])
def search_artists():
    try:
        # get value from searchbox
        search_term = request.form.get('search_term', '')
        # current time
        timenow = datetime.now()
        # fetch/search data by user input value
        artists = db.session.query(Artist).filter(Artist.name.ilike(
            '%' + search_term + '%')).all()
        response = {
            "count": 0,
            "data": []
        }
        # for each artist data
        for artist in artists:
            # fetch show time which greater than current time
            num_upcoming_shows = db.session.query(func.count(Show.id)).filter(
                Show.start_time > timenow, Show.artist_id == artist.id).all()
            # in for loop increment respone['count']by 1 and append data
            response['count'] = response.get('count') + 1
            response['data'].append({
                "id": artist.id,
                "name": artist.name,
                "num_upcoming_shows": num_upcoming_shows,
            })
        # error Method Not Allowed
    except MethodNotAllowed as mt:
        abort(405)
    except BadRequest:
        abort(400)
    except Exception as e:
        flash(f'Error: {str(sys.exc_info()[0])}')
    return render_template('pages/search_artists.html',
                           results=response, search_term=search_term)


# Show Artist data by id
@ app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    try:
        artist = Artist.query.filter(Artist.id == artist_id).one()
        # fetch data from Venue, Show using artist_id
        venues = db.session.query(Venue.id, Venue.name, Venue.image_link,
                                  Show.start_time.label('time')).join(
                                      Venue).filter(
                                          Show.artist_id == artist_id).all()
        # store data in dictionary using List Comprehensions
        data = [u.__dict__ for u in [artist]]
        # each data in venues
        for venue in venues:
            # time Compresion
            show = time_comp(datetime.now(), venue.time)
            # append artist data and numbers in datalist
            data[0][show] = data[0].get(show, []) + [{
                "venue_id": venue.id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": str(venue.time)
            }]
            data[0][show + '_count'] = data[0].get(show + '_count', 0) + 1
    # error handling
    except NoResultFound:
        abort(404)
    except BadRequest:
        abort(400)
    except Exception as e:
        flash(f'Error: {str(sys.exc_info()[0])}')
    # return data[0]
    return render_template('pages/show_artist.html', artist=data[0])


# Delete Artist
# ---------------------------------------------------
@app.route('/artists/<artist_id>/delete', methods=['DELETE'])
def delete_artist(artist_id):
    try:
        # delete artist data row using given id
        Artist.query.filter(Artist.id == artist_id).delete()
        db.session.commit()
        flash(f'Artist {artist_id} was successfully deleted!')
    # Error Handling
    # error Method Not Allowed
    except MethodNotAllowed as mt:
        db.session.rollback()
        abort(405)
    except BadRequest:
        db.session.rollback()
        abort(400)
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(sys.exc_info()[0])}')
    finally:
        db.session.close()
    return redirect(url_for('index'))

#  Update Artist
#  ----------------------------------------------------------------


@ app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    # Select artist data from db using artist_id and store in list
    artist_query = Artist.query.filter(Artist.id == artist_id).one()
    artist = []
    for u in [artist_query]:
        artist_dict = u.__dict__
        artist_dict.pop('_sa_instance_state', None)
        artist.append(artist_dict)
    return render_template('forms/edit_artist.html',
                           form=form, artist=artist[0])


@ app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    artist = Artist.query.filter(Artist.id == artist_id).one()
    try:
        # take value and checked if available and then update db
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
        # commit session
        db.session.add(artist)
        db.session.commit()
        flash(f'Artist {request.form["name"]} was successfully updated!')
    # Error Handling
    # error handling
    except NoResultFound:
        b.session.rollback()
        abort(404)
    # error Method Not Allowed
    except MethodNotAllowed as mt:
        db.session.rollback()
        abort(405)
    except BadRequest:
        db.session.rollback()
        abort(400)
    except Exception:
        db.session.rollback()
        flash(f'Error: {str(sys.exc_info()[0])}')
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
        db.session.add(newArtist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    # error Method Not Allowed
    except MethodNotAllowed as mt:
        db.session.rollback()
        abort(405)
    except BadRequest:
        abort(400)
    except Exception:
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
    try:
        # displays list of shows at /shows
        # num_shows should be aggregated based on number
        # of upcoming shows per venue.
        show_query = db.session.query(
            Show, Show.start_time.label('start_time'),
            Venue.id.label('venue_id'), Venue.name.label('venue_name'),
            Artist.id.label('artist_id'), Artist.name.label('artist_name'),
            Artist.image_link.label('image_link')).filter(
                Show.venue_id == Venue.id, Show.artist_id == Artist.id).all()
        # list show data
        data = [
            {
                "venue_id": query.venue_id,
                "venue_name": query.venue_name,
                "artist_id": query.artist_id,
                "artist_name": query.artist_name,
                "artist_image_link": query.image_link,
                "start_time": str(query.start_time)
            }
            for query in show_query
        ]
    except BadRequest:
        abort(400)
    except Exception as e:
        flash(f'Error: {str(sys.exc_info()[0])}')
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
    # called to create new shows in the db, upon
    # submitting new show listing form
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
    # error Method Not Allowed
    except MethodNotAllowed as mt:
        db.session.rollback()
        db.session.close()
        abort(405)
    except BadRequest:
        abort(400)
    except Exception:
        error = True
        db.session.rollback()
        flash(f'An error occurred. Show could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.errorhandler(405)
def method_not_allowed(error):
    return render_template('errors/405.html'), 405


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(400)
def handle_bad_request(error):
    return render_template('errors/400.html'), 400


@ app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
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
