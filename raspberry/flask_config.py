import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'guess'
    #BOOTSTRAP_SERVE_LOCAL = True