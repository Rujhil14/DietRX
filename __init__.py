from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config
from elasticsearch import Elasticsearch
import pickle as pkl


app = Flask(__name__, static_url_path='/dietrx/static', static_folder='static')
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
    if app.config['ELASTICSEARCH_URL'] else None

# Mapping from id to functional group
fgid2name = pkl.load(open('dietrx/static/fgid2name.p', 'rb'))
fgname2id = pkl.load(open('dietrx/static/fgname2id.p', 'rb'))
fglist = list(fgname2id.keys())

from dietrx import routes, models