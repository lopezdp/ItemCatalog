import sys

# Configuration
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

# ORM defined in terms of a base class which maintains a catalog
# of classes and tables relative to that base
Base = declarative_base()

# Representation of sql tables as a Python class

# User schema and tables
class User(Base):

    # Tables
    __tablename__ = 'users'

    # Mapper: Maps Python Objects to
    # columns in our database
    id = Column (
        Integer,
        primary_key = True
    )

    name = Column(
        String(250),
        nullable=False
    )

    email = Column(
        String(250),
        nullable=False
    )

    picture = Column(
        String(250)
    )


# Catalog schema and tables
class Category(Base):

    # Tables
    __tablename__ = 'category'

    # Mapper: Maps Python Objects to
    # columns in our database

    id = Column (
        Integer,
        primary_key = True
    )

    name = Column (
        String(80),
        nullable = False
    )

    description = Column (
    	String(160)
    )

    # This column maps the category to its owner
    user_id = Column(
        Integer,
        ForeignKey('users.id')
    )

    user = relationship(User)

    @property
    def serialize(self):
        return {
        	'id' : self.id,
            'name' : self.name,
            'description' : self.description
        }

# Item schema and tables
class Item(Base):

    # Tables
    __tablename__ = 'item'

    # Mapper: Maps Python Objects to
    # columns in our database

    id = Column (
        Integer,
        primary_key = True
    )

    name = Column (
        String(80),
        nullable = False
    )

    description = Column (
        String(160)
    )

    price = Column (
        String(10)
    )

    # This column maps the Item to its Category
    categoryid = Column (
        Integer,
        ForeignKey('category.id')
    )

    category = relationship(Category)

    # This column maps the Item to its category owner
    user_id = Column(
        Integer,
        ForeignKey('users.id')
    )

    user = relationship(User)

    @property
    def serialize(self):
        # Returns object data in serialized format
        return {
            'id' : self.id,
            'name' : self.name,
            'description' : self.description,
            'price' : self.price
        }

# Insert at EOF
engine = create_engine('sqlite:///itemCatalog.db')

Base.metadata.create_all(engine)

