'''
    David P. Lopez
    Item Catalog

    A generic implementation of an item catalog that can be used for different projects

'''

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response

# import CRUD operations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# This imports the data model designed in the schema: itemCatalogSchema.py
from restaurantMenuSchema import Base, Restaurant, MenuItem, User

# New Imports for Google Oauth Login functionality
from flask import session as login_session
import random
import string

# OAUTH IMPORTS
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests


######## Follow Up with Auth!!!
# Read & store the client_id from the client_secrets.json file
#CLIENT_ID = json.loads(
#    open('client_secrets.json','r').read())['web']['client_id']
#APPLICATION_NAME = "Restaurant Menu Application"

app = Flask(__name__)

# Create Session and connect to SQLite db
engine = create_engine('sqlite:///restaurantMenus.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()