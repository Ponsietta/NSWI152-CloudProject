import cgi
import datetime
import urllib
import webapp2
import logging
import cloudstorage as gcs
import logging

from google.appengine.api import users
from google.appengine.api import app_identity
from google.appengine.api import taskqueue

import jinja2
import os
import uuid
import json

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class MainPage(webapp2.RequestHandler):
    def get(self):

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'url': url,
            'url_linktext': url_linktext,
        }

        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))

class ConvertImage(webapp2.RequestHandler):
  def post(self):
    newFormat = self.request.get('newFormat')
    img_files = self.request.POST.getall('inputImgs') 
    newWidth = self.request.get('newWidth')
    newHeight = self.request.get('newHeight')

    user = users.get_current_user()
    if user:
        user_email = user.email()
    else:
        user_email = self.request.get('email')

    write_retry_params = gcs.RetryParams(backoff_factor=1.1)

    self.response.headers['Content-Type'] = 'application/json'  

    try:
        for img_f in img_files:       
            
            file_path = "/" + 'toconvert_images' + "/" + str(uuid.uuid4())
            gcs_file = gcs.open(file_path,
                        'w',
                        content_type=img_f.type,
                        retry_params=write_retry_params)

            gcs_file.write(img_f.file.read())
            gcs_file.close()

            #pass conversion task to queue here
            taskqueue.add(
            url='/convert_image',
            method="POST",
            target='worker',
            params={'newFormat': newFormat.encode('utf-8'), 'newWidth': newWidth, 'newHeight': newHeight, 'filePath': file_path.encode('utf-8'), 'user_email': user_email})

        self.response.write(json.dumps({"status": "success", "msg": 'Your request has been recorded. You will receive an email with a link to the converted image once the conversion process is finished.'}))

    except Exception as e:
        logging.exception('Failed: ' + str(e))
        self.response.write(json.dumps({"status": "error", "msg": 'Something went wrong: ' + e.message}))
    

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/convert', ConvertImage)],
                              debug=True)


