from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.api import app_identity
from google.appengine.api import mail

import cloudstorage as gcs
import webapp2
import os
import logging
import uuid

class ImageConversionHandler(webapp2.RequestHandler):
    def post(self):
        newImgFormat = self.request.get('newFormat')
        imgFilePath = self.request.get('filePath')
        userEmail = self.request.get('user_email') 
        
        if self.request.get('newWidth') is not None and self.request.get('newWidth').isnumeric():
            newWidth = int(self.request.get('newWidth'))
        else:
            newWidth = None

        if self.request.get('newHeight') is not None and self.request.get('newHeight').isnumeric():
            newHeight = int(self.request.get('newHeight'))
        else:
            newHeight = None

        if(newImgFormat == 'jpeg'):
            encoding = images.JPEG
            contentType = 'image/jpeg'
        elif(newImgFormat == 'png'):
            encoding = images.PNG
            contentType = 'image/png'

        def convert_image(blob_key):
            img = images.Image(blob_key=blob_key)         
            img.im_feeling_lucky()
            if newWidth is not None and newHeight is not None:
                img.resize(width=newWidth, height=newHeight)
            #set encoding below based on format chosen
            converted_image = img.execute_transforms(output_encoding=encoding)
            return converted_image         

        def save_converted_image(converted_image):
            write_retry_params = gcs.RetryParams(backoff_factor=1.1)
            file_path = "/converted_images/" + str(uuid.uuid4())
            gcs_file = gcs.open(file_path,
                        'w',
                        content_type=contentType,
                        retry_params=write_retry_params)

            gcs_file.write(converted_image)
            gcs_file.close()
            return file_path

        def send_email_link(blob_key):
            #send email to customer with link to image
            message = mail.EmailMessage(sender="IMG.Convert <ponsietta@gmail.com>",
                            to = userEmail,
                            subject="Your image has been converted")

            #get image serving url, appending '=s0' so image retains the original size
            image_url = images.get_serving_url(blob_key, secure_url=True) + "=s0"

            message.html = """
            <html><head></head><body>
            <p>Hi!</p><p>Your image has been converted and can be downloaded by clicking <a href='""" + image_url +"""' download>HERE</a>.</p><p>The IMG.Convert Team</p>
            </body></html>
            """

            message.send()

        def get_blob_key_for_gcs_file(fileName):
            # In order to use Images API to transform image file, 
            # use the Blobstore API to create a blob_key from the Cloud Storage file name.
            # Blobstore expects the filename to be in the format of:
            # /gs/bucket/object
            blobstore_filename = '/gs{}'.format(fileName)
            blob_key = blobstore.create_gs_key(blobstore_filename)
            return blob_key

        try:
            blob_key = get_blob_key_for_gcs_file(imgFilePath)
            converted_image = convert_image(blob_key)
            newFilePath = save_converted_image(converted_image)
            blob_key = get_blob_key_for_gcs_file(newFilePath)
            send_email_link(blob_key)
            
        except Exception as e:
            logging.exception('Failed: ' + str(e))


app = webapp2.WSGIApplication([
    ('/convert_image', ImageConversionHandler)
], debug=True)