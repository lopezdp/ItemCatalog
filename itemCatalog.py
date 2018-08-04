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

# GConnect
# Route handler to accept client-side calls from signInCallBack()
#################################################################
@app.route('/gconnect', methods = ['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        # if state tokens do not match then return 401
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # save request data in code variable
    code = request.data

    try:
        #Upgrade the auth code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope = '')
        oauth_flow.redirect_uri = 'postmessage'
        # credentials variable holds the request data
        credentials = oauth_flow.step2_exchange(code)

    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check to be sure the access token is valid
    access_token = credentials.access_token

    url = ("https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s" % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # Abort if there is an error with the access token
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        # Debug
        print("500 error print: " + result)
        return response

    # Ensure that the access_token is used by the intended person
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps('Token client ID does not match user ID'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is good for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check to see if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current User is already Signed In'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Save the access_token for later use dude
    login_session['provider'] = 'google'
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    # Store data params into login_session params
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Check for user in db, if not then INSERT
    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    # Format output
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print("Done!")

    # Return output
    return output

# FB Connect
##############################
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    # Check if user has login['state'] granted
    # if tokenstate null, then return 401
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid State Parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # On connect store the access_token
    access_token = request.data

    # Read json file in dir to obtain API credentials
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']

    # Access Endpoint for API
    url = 'https"//graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)

    # Init an Http object and create an http GET request to API URL
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use the access_token to obtain user_info
    userinfo_url = 'https://graph.facebook.com/v2.2/me'
    # strip expire tag from access_token
    token = result.split('&')[0]

    # Init an Http object and create an http GET request to API URL
    url = 'https://graph.facebook.com/v2.2/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Capture data from http request
    data = json.loads(result)

    # Obtain FB User Data
    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    # Get User picture
    url = 'https://graph.facebook.com/v2.2/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Capture data from http request
    data = json.loads(result)

    login_session['picture'] = data['data']['url']

    # Check if user exists
    user_id = getUserId(login_session['email'])

    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    # Format output
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print("Done!")

    # Return output
    return output

# Abstract DisConnect
##############################
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['access_token']
            del login_session['gplus_id']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You've been Logged out!")
        return redirect(url_for('showRestaurants'))
    else:
        flash("You've were never logged in!")
        return redirect(url_for('showRestaurants'))

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
        session.add(category)
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

# Delete Item
#########################
@app.route('/category/<int:category_id>/item/<int:item_id>/delete/', methods = ['GET', 'POST'])
def deleteItem(category_id, item_id):
    # Check to see if a user is logged in.
    if 'username' not in login_session:
        return redirect('/login')

    # If user is logged in then access deleteItem page
    # query db by category_id and item_id and assign to category and item variables
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id = item_id).one()

    # Check if user_id matches the user_id stored in login_session
    if category.user_id != login_session['user_id']:
        return authorizationAlert("Delete")

    if request.method == 'POST':
        # delete category object obtained from db query
        session.delete(item)
        # commit delete to db
        session.commit()
        flash("Deleted item: " + item.name + " ==> Deleted!")
        # redirect user to updated list of category
        return redirect(url_for('showItem', category_id = category_id))
    else:
        return render_template('deleteItem.html', title = 'Confirm Delete Item', category = category, item = item)

# EXPOSE API Endpoints in JSON
#/catalog/JSON
##############################
@app.route('/catalog/JSON')
def showCatalogJSON():
    # query db for all Categories to jsonify
    categories = session.query(Category).all()
    # create json object of list of all Categories
    json = jsonify(categories=[category.serialize for category in categories])
    # create a response object using flask make_response(responseObj, status)
    res = make_response(json, 200)
    # Change value of 'Content-Type' header as required
    res.headers['Content-Type'] = 'application/json'
    # return the response
    return res





if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)