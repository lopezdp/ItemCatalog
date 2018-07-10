# Item Catalog

A generic implementation of an item catalog that can be used to build dynamic web applications that can persist data to a hosted cloud store or a database, with the goal of this project being used as a quick start up framework.

A user can view different categories and items to add, edit, or delete items and categories as needed. There is functionality for the user be able to authenitcate themself within the application in order to add new, edit, and delete custom items from the database. The project is built using Python3 to create the _Route Handlers_ in _Flask_ implemented using a ReSTful web architecture.


## Installation
1. Python 3.6.x is needed to run the back end of this Flask application
2. *Flask* and *SQLAlchemy* are needed to run this application
3. From a Terminal Run: `pip install Flask`
4. From a Terminal Run: `pip install SQLAlchemy`

## Documentation & Additional Information
1. The documentation will include instructions and examples on how to use this application

## Issues, Current, & Future Functionality
[ ] Users can Add New, Edit, & Delete Items.
[ ] Users can Add New Menu Items for each category available in the catalog.
[ ] Users can Edit & Delete Items for each category available in the catalog.
[ ] Users can view items from a categorical List.
[ ] Data Driven Application Using SQLite3.
[ ] Application provides JSON API Endpoints for the following:
	* showCategories: `/categories/JSON`
	* showItem: `/categories/category_id/item/item_id/JSON`
[ ] Need to Style the page using Jinja templates & CSS.
[ ] Users can login and register using Google+ API.
[ ] Local Permission System to allow users private access to user content.
[ ] Users can login and register using Facebook Login API

## License
The content of this repository is licensed under a [**GNU General Public License v3.0**](https://choosealicense.com/licenses/gpl-3.0)