import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_NOTEBOOK_NAME = 'Intro-to-Programming-Notes'

# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent.  However, the write rate should be limited to
# ~1/second.

def notebook_key(notebook_name=DEFAULT_NOTEBOOK_NAME):
    """Constructs a Datastore key for a Notebook entity.

    We use notebook_name as the key.
    """
    return ndb.Key('Notebook', notebook_name)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class Author(ndb.Model):
    """Sub model for representing an author."""
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)


class Greeting(ndb.Model):
    """A main model for representing an individual Notebook entry."""
    author = ndb.StructuredProperty(Author)
    unit = ndb.StringProperty(indexed=True)
    title = ndb.StringProperty(indexed=False)
    description = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)


class MainPage(webapp2.RequestHandler):

    def get(self):
        notebook_name = self.request.get('notebook_name',
                                          DEFAULT_NOTEBOOK_NAME)
        greetings_query = Greeting.query(
            ancestor=notebook_key(notebook_name)).order(Greeting.unit)
        greetings = greetings_query.fetch(10)

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'user': user,
            'greetings': greetings,
            'notebook_name': urllib.quote_plus(notebook_name),
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('mainpage.html')
        self.response.write(template.render(template_values))

class Notebook(webapp2.RequestHandler):
    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each
        # Greeting is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        notebook_name = self.request.get('notebook_name',
                                          DEFAULT_NOTEBOOK_NAME)
        greeting = Greeting(parent=notebook_key(notebook_name))

        if users.get_current_user():
            greeting.author = Author(
                    identity=users.get_current_user().user_id(),
                    email=users.get_current_user().email())

        greeting.description = self.request.get('description')
        greeting.title = self.request.get('title')
        greeting.unit = self.request.get('unit')

        greeting.put()

        # if not (greeting.unit and greeting.title and greeting.description):
        #     self.redirect('/error')
        # else:
        #     greeting.put()

        query_params = {'notebook_name': notebook_name}
        self.redirect('/?' + urllib.urlencode(query_params))

class Error(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('''Some of the data you entered is missing or
                                not valid. To go back to the home page and try
                                again click <a href='/'>here.</a>''')

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', Notebook),
    ('/error', Error),
], debug=True)
