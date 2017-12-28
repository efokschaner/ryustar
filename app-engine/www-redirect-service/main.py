import webapp2

class MainPage(webapp2.RequestHandler):
    def get(self):
        url = self.request.url.replace(self.request.host, 'www.ryustar.io')
        return self.redirect(url, True)

app = webapp2.WSGIApplication([
    ('/.*', MainPage),
], debug=False)