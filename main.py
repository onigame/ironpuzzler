from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.out.write(template.render("main.dj.html", {}))

app = webapp.WSGIApplication([('/', MainPage)], debug=True)
if __name__ == "__main__": run_wsgi_app(app)
