#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
from array import array

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# DONE: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mykecampbell@localhost:5432/fyyur'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    website = db.Column(db.String())
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String())
    artists = db.relationship('Show', backref='venues', lazy=True)
    # DONE implement any missing fields, as a database migration using Flask-Migrate

    def __repr__(self):
        return f'<Venue {self.name} {self.city} {self.state}>'


class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String())
    seeking_venue = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String())
    venues = db.relationship('Show', backref='artists', lazy=True)

    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'

    # DONE implement any missing fields, as a database migration using Flask-Migrate


# DONE Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = 'show'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'venue.id'), primary_key=True, unique=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'artist.id'), primary_key=True, unique=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Show {self.venue_id} artistId: {self.artist_id} time: {self.start_time}'


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
    # DONE return duplicated
    now = datetime.utcnow()
    data = []
    venue_location = Venue.query.with_entities(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()

    for area in venue_location:
        venue_area = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
        venue_detail = []
        for venue in venue_area:
            venue_detail.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_show': db.session.query(Show).filter(Show.venue_id == venue.id).filter(Show.start_time < now).count()
            })
        data.append({
            'city': area.city,
            'state': area.state,
            'venues': venue_detail
        })
    return render_template('pages/venues.html', areas=data)
    

@app.route('/venues/search', methods=['POST'])
def search_venues():
    search = request.form.get('search_term', '')
    search_results = Venue.query.with_entities(Venue.id, Venue.name).filter(
        Venue.name.ilike('%' + search + '%')).all()
    response = {'data': search_results, 'count': len(search_results)}
    return render_template('pages/search_venues.html', results=response, search_term=search)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    past_shows = []
    upcoming_shows = []
    now = datetime.utcnow() 
    venue = Venue.query.get(venue_id)

    past_shows_data = db.session.query(Artist.id, Artist.name, Artist.image_link, Show.start_time)\
        .join(Show, Artist.id == Show.artist_id)\
        .filter(Show.venue_id == venue_id).filter(Show.start_time > now).all()
    upcoming_shows_data = db.session.query(Artist.id, Artist.name, Artist.image_link, Show.start_time) \
        .join(Show, Artist.id == Show.artist_id) \
        .filter(Show.venue_id == venue_id).filter(Show.start_time < now).all()

    for past_show in past_shows_data:
        past_shows.append({
            'artist_id': past_show.id,
            'artist_name': past_show.name,
            'artist_image_link': past_show.image_link,
            'start_time': past_show.start_time.strftime('%A %B %d %Y %I:%M %p')
        })
    for upcoming_show in upcoming_shows_data:
        upcoming_shows.append({
            'artist_id': upcoming_show.id,
            'artist_name': upcoming_show.name,
            'artist_image_link': upcoming_show.image_link,
            'start_time': upcoming_show.start_time.strftime('%A %B %d, %Y %I:%M %p')
        })

    data = {
        'id': venue_id,
        'name': venue.name,
        'genres': ''.join(venue.genres[1:-1]).split(','),
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website': venue.website,
        'facebook_link': venue.facebook_link,
        'image_link': venue.image_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'upcoming_shows': upcoming_shows,
        'past_shows': past_shows,
        'upcoming_shows_count': len(upcoming_shows),
        'past_shows_count': len(past_shows)
    }
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    print('Genres: ', genres)
    facebook_link = request.form['facebook_link']
    website = request.form['website']
    image_link = request.form['image_link']
    seeking_talent = True if request.form.get('seekign_description') == 'y' else False
    seeking_description = request.form['seeking_description'] if seeking_talent == True else None
    
    try:
        new_venue = Venue(name=name, city=city, address=address,state=state, phone=phone, genres=genres, facebook_link=facebook_link, website=website, image_link=image_link, seeking_description=seeking_description, seeking_talent=seeking_talent)
        db.session.add(new_venue)
        db.session.commit()
    # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully created!')
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
        flash('An error occurred. Venue ' + name + ' could not be listed.')
    finally:
        db.session.close()
        return redirect(url_for('venues'))


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try: 
        venue = Venue.query.get(venue_id)
        name = venue.name
        db.session.delete(venue)
        db.session.commit()
        flash('Venue ' + name + ' was successfully deleted')
    except:
        db.session.rollback()
        flash('Oh no something went wrong. Please try again later')
    finally:
        db.session.close()
        return redirect(url_for('index'))




        
   

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # DONE: replace with real data returned from querying the database
    return render_template('pages/artists.html', artists=Artist.query.with_entities(Artist.id, Artist.name).order_by('id').all())


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search = request.form.get('search_term', '')
    search_result = Artist.query.with_entities(Artist.id, Artist.name).filter(
        Artist.name.ilike('%' + search + '%')).all()
    response = {'count': len(search_result), 'data': search_result}
    return render_template('pages/search_artists.html', results=response, search_term=search)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    upcoming_shows = []
    past_shows = []
    today = datetime.utcnow()
    artist = Artist.query.get(artist_id)
    
    past_shows_data = db.session.query(Venue.id, Venue.name, Venue.image_link, Show.start_time)\
        .join(Show, Venue.id == Show.venue_id)\
            .filter(Show.artist_id == artist_id).filter(Show.start_time < today).all()
            
    upcoming_shows_data = db.session.query(Venue.id, Venue.name, Venue.image_link, Show.start_time)\
        .join(Show, Venue.id == Show.venue_id)\
            .filter(Show.artist_id == artist_id).filter(Show.start_time > today).all()
            
    for past_show in past_shows_data:
        past_shows.append({
            'venue_id': past_show.id,
            'venue_name': past_show.name,
            'venue_image_link': past_show.image_link,
            'start_time': past_show.start_time.strftime('%A %B, %d %Y %I:%M %p')
        })
        for upcoming_show in upcoming_shows_data:
            upcoming_shows.append({
                'venue_id': upcoming_show.id,
                'venue_name': upcoming_show.name,
                'venue_image_link': upcoming_show.image_link,
                'start_time': upcoming_show.start_time.strftime('%A %B, %d %Y %I:%M %p')
            })

    data = {
        'id': artist_id,
        'name': artist.name,
        'genres': ''.join(artist.genres[1:-1]).split(','),
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website,
        'facebook_link': artist.facebook_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    }
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    # DONE 
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.image_link.data = artist.image_link
    form.facebook_link.data = artist.facebook_link
    form.website.data = artist.website
    form.genres.data = request.form.getlist('genres')
    form.seeking_venue.data = artist.seeking_venue,
    form.seeking_description.data = artist.seeking_description
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # DONE: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    error = False
    artist = Artist.query.get(artist_id)
    seeking_venue = True if request.form.get('seeking_venue') == 'y' else False
    seeking_description = request.form['seeking_description'] if seeking_venue == True else None
    try:
         artist.name = request.form['name']
         artist.city = request.form['city']
         artist.state = request.form['state']
         artist.phone = request.form['phone']
         artist.genres = request.form.getlist('genres')
         artist.website = request.form['website']
         artist.facebook_link = request.form['facebook_link']
         artist.image_link = request.form['image_link']
         artist.seeking_venue = seeking_venue
         artist.seeking_description = seeking_description
         print('Artist: ', artist)
         db.session.add(artist)
         db.session.commit()
         flash('Artist ' + request.form['name'] + 'successfully updated 🚀 ')
    except:
        db.session.rollback()
        flash('Artist ' + request.form['name'] + ' cannot be updated! 😞')
    finally:
        db.session.close()
        return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    # DONE the edit form need to add website, seeking_talent, seeking_description, image_link
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.seeking_description.data = venue.seeking_description
    form.seeking_talent.data = venue.seeking_talent
    form.image_link.data = venue.image_link
    form.website.data = venue.website

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # DONE take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.get(venue_id)
    seeking_talent = True if request.form.get('seeking_talent') == 'y' else False
    seeking_description = request.form['seeking_description'] if seeking_talent == True else None
    try:
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        print('Venue: ', venue.city)
        venue.genres = request.form.getlist('genres')
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.facebook_link = request.form['facebook_link']
        venue.seeking_description = seeking_description
        venue.seeking_talent = seeking_talent
        venue.image_link = request.form['image_link']
        venue.website = request.form['website']
        
        db.session.commit()
        flash('Venue ' +  request.form['name'] + ' was successfully updated 🚀')
    except:
        db.session.rollback()
        error = True
        flash('Something went wrong. Please try again later 😞')
    finally:
        db.session.close()
        return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # DONE: insert form data as a new Venue record in the db, instead
    # DONE: modify data to be the data object returned from db insertion
    # DONE: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    error = False
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form['genres']
    facebook_link = request.form['facebook_link']
    
    try:
        new_artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link)
        db.session.add(new_artist)
        db.session.commit()
        flash('Artist ' + name + ' was successfully created! 🚀 ')
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
        flash('Artist ' + name + ' could not be created at this time. Please try again later 😞')
    finally:
        db.session.close()
        return redirect(url_for('index'))

@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        name = artist.name
        db.session.delete(artist)
        db.session.commit()
        flash('Artist ' + name + ' successfully deleted!')
    except:
        db.session.rollback()
        flash('Artist ' + name + 'could not be deleted at this time. Plese try again later')
    finally:
        db.session.close()
        return redirect(url_for('index'))

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # DONE: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    data = []
    now = datetime.utcnow()
    shows = db.session.query(Show.venue_id, Show.artist_id, Show.start_time, Venue.name.label('venue_name'), Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link'))\
        .join(Artist, Artist.id == Show.artist_id).join(Venue, Venue.id == Show.venue_id).all()
    
    for show in shows:
        data.append({
            'venue_id': show.venue_id,
            'venue_name': show.venue_name,
            'artist_id': show.artist_id,
            'artist_name': show.artist_name,
            'artist_image_link': show.artist_image_link,
            'start_time': show.start_time.strftime("%A %B %d %Y %I:%M %p")
        })
    return render_template('pages/shows.html', shows=data)
 



@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # DONE: insert form data as a new Show record in the db, instead
    error = False
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
    
    try:
        new_show = Show(venue_id = venue_id, artist_id = artist_id, start_time = start_time)
        db.session.add(new_show)
        db.session.commit()
        flash('Show was successfully created! 🚀')
    except:
        db.session.rollback()
        error = True
        flash('Oh no something went wrong')
    finally:
        db.session.close()
        return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
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
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
