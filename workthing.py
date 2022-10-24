"""
The flask application package.
"""

from flask import Flask
import utils
import flask_login
import logging
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['UPLOADED_PHOTOS'] = 'PDFs'

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.DEBUG)
app.logger.debug('Something')

app.secret_key = 'idkwhatthisisyet'

import views#WorkThing.views
import utils#WorkThing.utils
