import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
class DatabaseURI:
    DATABASE_NAME = "fyyurdb"
    SQLALCHEMY_DATABASE_URI = "postgres:///{}".format(
        DATABASE_NAME)

# sqlalchemy track modification
class SQLALCHEMY_TRACK_MODIFICATIONS:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
