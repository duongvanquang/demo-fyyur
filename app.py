import dateutil.parser
import datetime
import babel
import logging
import sqlalchemy
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from logging import Formatter, FileHandler
from sqlalchemy import func, exc
from models import db, Venue, Show, Artist
from formatdatetimes import format_datetime
from forms import *

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)
app.jinja_env.filters['datetime'] = format_datetime

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

@app.route('/')
def index():
    return render_template('pages/home.html')

@app.route('/venues')
def venues():
    data = []
    grouped_venues = Venue.query.with_entities(Venue.city, Venue.state, func.count(Venue.id)).group_by(Venue.city, Venue.state).all()
    
    for city, state, count in grouped_venues:
        venues = Venue.query.filter_by(city=city, state=state).with_entities(Venue.id, Venue.name).all()
        data.append({"city": city, "state": state, "venues": venues})
    
    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_value = request.form.get('search_term', '').lower()
    search_result = Venue.query.filter(func.lower(Venue.name).like(f'%{search_value}%')).with_entities(Venue.id, Venue.name).all()
    response = {"count": len(search_result), "data": search_result}
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue_data = db.session.query(Venue, Artist, Show)\
        .outerjoin(Show, Venue.id == Show.venue_id)\
        .outerjoin(Artist, Artist.id == Show.artist_id)\
        .filter(Venue.id == venue_id)\
        .all()

    if not venue_data:
        return render_template('pages/show_venue.html', venue={})

    venue_info, past_shows, upcoming_shows = None, [], []
    
    for venue_obj, artist_obj, show_obj in venue_data:
        if venue_info is None:
            venue_info = {
                'id': venue_obj.id, 'name': venue_obj.name, 'address': venue_obj.address, 'city': venue_obj.city,
                'state': venue_obj.state, 'phone': venue_obj.phone, 'website_link': venue_obj.website_link,
                'facebook_link': venue_obj.facebook_link, 'seeking_talent': venue_obj.seeking_talent,
                'seeking_description': venue_obj.seeking_description, 'image_link': venue_obj.image_link,
                'genres': venue_obj.genres.strip('{}').split(',')
            }

        if show_obj and artist_obj:
            show_details = {
                'artist_id': artist_obj.id, 'artist_name': artist_obj.name, 
                'artist_image_link': artist_obj.image_link, 'start_time': str(show_obj.start_time)
            }
            if show_obj.start_time < datetime.now():
                past_shows.append(show_details)
            else:
                upcoming_shows.append(show_details)

    venue_info.update({'past_shows': past_shows, 'past_shows_count': len(past_shows), 'upcoming_shows': upcoming_shows, 'upcoming_shows_count': len(upcoming_shows)})
    return render_template('pages/show_venue.html', venue=venue_info)

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    return render_template('forms/new_venue.html', form=VenueForm())

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)
    if form.validate():
        venue = Venue(**form.data)
        try:
            db.session.add(venue)
            db.session.commit()
            flash(f'Venue {venue.name} was successfully listed!')
        except exc.SQLAlchemyError:
            db.session.rollback()
            flash(f'An error occurred. Venue {venue.name} could not be listed.')
    else:
        flash(str(form.errors))
    
    return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue_form(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    form = VenueForm(obj=venue)
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    if form.validate():
        venue = Venue.query.get_or_404(venue_id)
        form.populate_obj(venue)
        try:
            db.session.commit()
            flash(f'Venue {venue.name} was successfully updated!')
        except exc.SQLAlchemyError:
            db.session.rollback()
            flash(f'An error occurred. Venue {venue.name} could not be updated.')
    else:
        flash(str(form.errors))
    
    return redirect(url_for('show_venue', venue_id=venue_id))

@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
        flash(f'Venue id {venue_id} was successfully deleted!')
    except exc.SQLAlchemyError:
        db.session.rollback()
        flash(f'An error occurred. Venue id {venue_id} could not be deleted.')
    return None

# Artists
@app.route('/artists')
def artists():
    artists = Artist.query.with_entities(Artist.id, Artist.name).all()
    return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_value = request.form.get('search_term', '').lower()
    search_result = Artist.query.filter(func.lower(Artist.name).like(f'%{search_value}%')).with_entities(Artist.id, Artist.name).all()
    response = {"count": len(search_result), "data": search_result}
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist_data = db.session.query(Artist, Venue, Show)\
        .outerjoin(Show, Artist.id == Show.artist_id)\
        .outerjoin(Venue, Venue.id == Show.venue_id)\
        .filter(Artist.id == artist_id)\
        .all()

    if not artist_data:
        return render_template('pages/show_artist.html', artist={})

    artist_info, past_shows, upcoming_shows = None, [], []

    for artist_obj, venue_obj, show_obj in artist_data:
        if artist_info is None:
            artist_info = {
                'id': artist_obj.id, 'name': artist_obj.name, 'city': artist_obj.city, 'state': artist_obj.state,
                'phone': artist_obj.phone, 'genres': artist_obj.genres.strip('{}').split(','), 'image_link': artist_obj.image_link,
                'website_link': artist_obj.website_link, 'facebook_link': artist_obj.facebook_link, 
                'seeking_venue': artist_obj.seeking_venue, 'seeking_description': artist_obj.seeking_description
            }

        if show_obj and venue_obj:
            show_details = {
                'venue_id': venue_obj.id, 'venue_name': venue_obj.name, 
                'venue_image_link': venue_obj.image_link, 'start_time': str(show_obj.start_time)
            }
            if show_obj.start_time < datetime.now():
                past_shows.append(show_details)
            else:
                upcoming_shows.append(show_details)

    artist_info.update({'past_shows': past_shows, 'past_shows_count': len(past_shows), 'upcoming_shows': upcoming_shows, 'upcoming_shows_count': len(upcoming_shows)})
    return render_template('pages/show_artist.html', artist=artist_info)

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    return render_template('forms/new_artist.html', form=ArtistForm())

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)
    if form.validate():
        artist = Artist(**form.data)
        try:
            db.session.add(artist)
            db.session.commit()
            flash(f'Artist {form.name.data} was successfully listed!')
        except exc.SQLAlchemyError:
            db.session.rollback()
            flash(f'An error occurred. Artist {form.name.data} could not be listed.')
    else:
        flash(str(form.errors))
    
    return render_template('pages/home.html')

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist_form(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    form = ArtistForm(obj=artist)
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)
    if form.validate():
        artist = Artist.query.get_or_404(artist_id)
        form.populate_obj(artist)
        try:
            db.session.commit()
            flash(f'Artist {artist.name} was successfully updated!')
        except exc.SQLAlchemyError:
            db.session.rollback()
            flash(f'An error occurred. Artist {artist.name} could not be updated.')
    else:
        flash(str(form.errors))
    
    return redirect(url_for('show_artist', artist_id=artist_id))

# Shows
@app.route('/shows')
def shows():
    shows_data = db.session.query(
        Venue.id.label("venue_id"), Venue.name.label("venue_name"),
        Artist.id.label("artist_id"), Artist.name.label("artist_name"),
        Artist.image_link.label("artist_image_link"), func.cast(Show.start_time, sqlalchemy.String).label("start_time")
    ).join(Venue, Show.venue_id == Venue.id).join(Artist, Show.artist_id == Artist.id).all()

    return render_template('pages/shows.html', shows=shows_data)

@app.route('/shows/create')
def create_show_form():
    return render_template('forms/new_show.html', form=ShowForm())

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)
    show = Show(venue_id=form.venue_id.data, artist_id=form.artist_id.data, start_time=form.start_time.data)

    try:
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except exc.SQLAlchemyError as e:
        app.logger.error('Error creating show: %s', repr(e))
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
    
    return render_template('pages/home.html')

if __name__ == '__main__':
    app.run()
