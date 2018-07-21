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
from itemCatalogSchema import Base, Category, Item, User

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
#APPLICATION_NAME = "Item Catalog Application"

app = Flask(__name__)

# Create Session and connect to SQLite db
engine = create_engine('sqlite:///itemCatalogSchema.db')
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

# Create anti-forgery state token
#################################
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
        for x in range(32)
    )

    login_session['state'] = state
    #return "The current session state is %s" % login_session['state']
    # RENDER the LOGIN.HTML TEMPLATE
    return render_template('login.html', STATE=state)



# Building Endpoints/Route Handlers "Local Routing" (GET Request)
# Root Catalog Directory
#################################################################
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    # query db and assign to categories variable
    categories = session.query(Category).order_by(Category.id.asc()).all()

    # Check if user credential match data in login_session
    # Check if username data in login_session
    if 'username' not in login_session:
        # This page will redirect user to Google login page
        return render_template('publicCategories.html', categories = categories, title = "Item Categories")
    else:
        # return "This page will show all categories"
        return render_template('categories.html', categories = categories, title = "Item Categories")

# Create a New Category
#########################
@app.route('/category/new/', methods = ['GET', 'POST'])
# Method to create newCategory
def newCategory():
    # Check to see if a user is logged in.
    if 'username' not in login_session:
        return redirect('/login')

    # If user is logged in then access newCategory page
    if request.method == 'POST':
        # Store category input from form into newCategory
        newCategory = Category(
            name = request.form['name'].strip(),
            description = request.form['description'].strip(),
            user_id = login_session['user_id']
        )
        # add newCategory item to db stage
        session.add(newCategory)
        # commit newCategory item to db
        session.commit()

        # flash message to indicate success
        flash("New Category: " + newCategory.name + " ==> Created!")

        # redirect user to updated list of categories
        return redirect(url_for('newCategory'))
    else:
        return render_template('newCategory.html', title = "New Category Input")

# Edit a Category
#########################
@app.route('/category/<int:category_id>/edit/', methods = ['GET', 'POST'])
def editCategory(category_id):

    # query db by category_id and assign to category variable
    category = session.query(Category).filter_by(id = category_id).one()

    # Check to see if a user is logged in.
    if 'username' not in login_session:
        return redirect('/login')

    # Check if user_id matches the user_id stored in login_session
    if category.user_id != login_session['user_id']:
        return authorizationAlert("Edit")

    # If user is logged in then access editCategory page
    if request.method == 'POST':
        if request.form:
            # Store edited field data and POST to db
            category.name = request.form['name'].strip()
            category.description = request.form['description'].strip()
        # add editCategory data to db stage
        session.add(restaurant)
        # commit editCategory data to db
        session.commit()

        # flash msg to indicate success
        flash("Edited Category: " + category.name + " ==> Updated!")

        # redirect user to updated list of categories in Catalog
        return redirect(url_for('showCatalog'))
    else:
        # Render the html needed to edit the category.
        return render_template('editCategory.html', title = 'Edit Category', category = category)

# Delete a Category
#########################
@app.route('/category/<int:category_id>/delete/', methods = ['GET', 'POST'])
def deleteCategory(category_id):

    # query db by category_id and assign to category variable
    category = session.query(Category).filter_by(id=category_id).one()

    # Check to see if a user is logged in.
    if 'username' not in login_session:
        return redirect('/login')

    # Check if user_id matches the user_id stored in login_session
    if category.user_id != login_session['user_id']:
        return authorizationAlert("Delete")

    # If user is logged in then access deleteCategory page
    if request.method == 'POST':
        # delete category object obtained from db query
        session.delete(category)
        # commit delete to db
        session.commit()

        # flash msg to indicate success
        flash("Deleted Category: " + category.name + " ==> Deleted!")

        # redirect user to updated list of categories
        return redirect(url_for('showCatalog'))
    else:
        # Render the html needed to delete the category.
        return render_template('deleteCategory.html', title = 'Confirm Delete Category', category = category)

# Show Category
#########################
@app.route('/category/<int:category_id>/menu/')
@app.route('/category/<int:category_id>/')
def showCategory(category_id):

    # query db to find category
    category = session.query(Category).filter_by(id = category_id).one()

    # getUserInfo()
    creator = getUserInfo(category.user_id)

    # query db to find items for category
    items = session.query(Item).filter_by(categoryid = category_id).order_by(Item.id.asc()).all()

    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicCategory.html', items=items, category=category, creator=creator)
    else:
        # return "This page are the items for category %s" % category_id
        return render_template('Category.html', category = category, items = items, creator=creator)

# New Item
#########################
@app.route('/category/<int:category_id>/new/', methods = ['GET', 'POST'])
def newItem(category_id):
    # Check to see if a user is logged in.
    if 'username' not in login_session:
        return redirect('/login')

    # If user is logged in then access newItem page
    # query db to find Category
    category = session.query(Category).filter_by(id = category_id).one()

    # Check if user_id matches the user_id stored in login_session
    if category.user_id != login_session['user_id']:
        return authorizationAlert("Add")

    if request.method == 'POST':
        # Store item input from form into newItem
        newItem = Item(
            name = request.form['name'].strip(),
            description = request.form['description'].strip(),
            price = request.form['price'].strip(),
            categoryid = category_id,
            user_id = category.user_id
        )
        # add newItem to db stage
        session.add(newItem)
        # commit newItem to db
        session.commit()

        # flash message to indicate success
        flash("New Item: " + newItem.name + " ==> Created!")

        # redirect user to updated list of Items for chosen category
        return redirect(url_for('showCategory', category_id = category_id))
    else:
        return render_template('newItem.html', title = "New Item Input", category = category)

# Edit Item
#########################
@app.route('/category/<int:category_id>/item/<int:item_id>/edit/', methods = ['GET', 'POST'])
def editItem(category_id, item_id):
    # Check to see if a user is logged in.
    if 'username' not in login_session:
        return redirect('/login')

    # If user is logged in then access editItem page
    # query db by category_id and item_id and assign to category and item variables
    category = session.query(Category).filter_by(id = category_id).one()
    item = session.query(Item).filter_by(id = item_id).one()

    # Check if user_id matches the user_id stored in login_session
    if category.user_id != login_session['user_id']:
        return authorizationAlert("Edit")

    if request.method == 'POST':
        if request.form:
            # Store edited field data and POST to db
            item.name = request.form['name'].strip()
            item.description = request.form['description'].strip()
            item.price = request.form['price'].strip()
            #item.categoryid = category_id

        # add editItem data to db stage
        session.add(item)
        # commit editItem data to db
        session.commit()

        # flash msg to indicate success
        flash("Edit Item: " + item.name + " ==> Updated!")
        # redirect user to updated list of items
        return redirect(url_for('showCategory', category_id = category_id))
    else:
        category = session.query(Category).filter_by(id = category_id).one()
        return render_template('editItem.html', title = 'Edit Item', category = category, item = item)
