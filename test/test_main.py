import base64
import requests
from PIL import Image
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import sys
import random
from pathlib import Path
from fpdf import FPDF

import base64
import io


class PDF(FPDF):

    def load_resource(self, reason, filename):
        if reason == "image":
            if filename.startswith("http://") or filename.startswith("https://"):
                f = BytesIO(urlopen(filename).read())
            elif filename.startswith("data"):
                f = filename.split('base64,')[1]
                f = base64.b64decode(f)
                f = io.BytesIO(f)
            else:
                f = open(filename, "rb")
            return f
        else:
            self.error("Unknown resource loading reason \"%s\"" % reason)

    def sample_pdf(self, img, path):

        self.image(img, h=70, w=150, x=30, y=100, type="jpg")
        # make sure you use appropriate image format here jpg/png
        pdf.output(path, 'F')




def save_img(img_dir_path, img_url_list):
    Path(img_dir_path).mkdir(parents=True, exist_ok=True)

    headers = {
        'Referer': 'https://www.manhuagui.com',
    }

    for idx, url in enumerate(img_url_list):
        # skip the third img, becasue it is same as second img
        if idx == 2:
            continue

        response = requests.get(url, headers=headers, stream=True)
        image = Image.open(io.BytesIO(response.content))
        response.close()

        image.transpose(Image.ROTATE_90).save('fname.jpg')


        # #px to mm
        # width, height = (i * 0.264583 for i in image.size)
        # print(width, height)

        pdf = PDF()
        pdf.add_page()
        pdf_path = 'test.pdf'
        pdf.sample_pdf(image, pdf_path)









        # fname = img_dir_path + '/' + str(idx+1) + '.jpg'
        # image.save(fname)
        # print('Img saved:' + str(idx+1) + '/' + str(len(img_url_list)))
        # time.sleep(random.uniform(0.5, 3.0))





img_dir = '第02话'
img_url_list = [
    'https://i.hamreus.com/ps3/l/lt-17457/zdxj/第02话/01a.jpg.webp?e=1629366072&m=5rEun6Q1A-Wj_MjOwaZGzA']
save_img(img_dir, img_url_list)
