import requests
from PIL import Image
import io
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import sys
import os
import random
from pathlib import Path
from fpdf import FPDF
from natsort import natsorted


# check if the button is exist, return true false
def click_confirm_button(driver):
    try:
        driver.find_element_by_id('checkAdult')
    except Exception as e:
        return
    confirm_btn = driver.find_element_by_id('checkAdult')
    confirm_btn.click()
    return


# get full HTML code, return html
def find_full_chapter_html(driver):
    html = ''

    try:
        click_confirm_button(driver)

        scorll_down_btn = driver.find_element_by_xpath(
            "//a[contains(@onclick,'SMH.setFunc(3)')]")
        scorll_down_btn.click()

        time.sleep(5)

        last_height = driver.execute_script(
            'return document.body.scrollHeight')
        while True:
            driver.execute_script(
                'window.scrollTo(0, document.body.scrollHeight);')

            time.sleep(random.uniform(8.0, 12.0))

            new_height = driver.execute_script(
                'return document.body.scrollHeight')
            if new_height == last_height:
                break
            last_height = new_height

        html = driver.page_source
        print('Chapter full html complete!')

    except Exception as e:
        print(e)

    return html


# Get all image url from html, return list of img url
def find_all_img_src(html):
    img_url_list = []
    soup = BeautifulSoup(html, features='html.parser')

    for img_tag in soup.find_all('img'):
        if 'https://i.hamreus.com' in img_tag['src']:
            img_url_list.append(img_tag['src'])

    return img_url_list


def find_chapters_url(driver, roll_only=False):
    chapters_url_name_list = []

    click_confirm_button(driver)
    html = driver.page_source
    soup = BeautifulSoup(html, features='html.parser')

    chapter_list = soup.find_all("div", {"class": "chapter-list"})

    # loop through the chapter list
    for chapters in chapter_list:
        for chapter in chapters.find_all('a'):
            # check only get 第n卷
            if roll_only and '卷' not in chapter['title']:
                continue

            url_name_dict = {
                'url': 'https://www.manhuagui.com/' + chapter['href'],
                'name': chapter['title']
            }
            chapters_url_name_list.append(url_name_dict)

    return chapters_url_name_list


# Get image from i.harmreus.com and save
def save_img(img_dir_path, img_url_list):
    Path(img_dir_path).mkdir(parents=True, exist_ok=True)

    headers = {
        'Referer': 'https://www.manhuagui.com',
    }

    # pop the third img, becasue it is same as second img
    img_url_list.pop(2)

    for idx, url in enumerate(img_url_list):
        response = requests.get(url, headers=headers, stream=True)
        image = Image.open(io.BytesIO(response.content))
        response.close()

        fname = img_dir_path + str(idx+1) + '.jpg'
        image.save(fname)
        print('Img saved:' + str(idx+1) + '/' + str(len(img_url_list)))
        time.sleep(random.uniform(0.5, 3.0))

    print('Chapter saving complete!')


# TODO, modify to save from memory
# after all img saved then create
def convert2pdf(img_dir_path, pdf_name_path):
    print('PDF creating...')

    img_path_list = [img_dir_path + img for img in list(os.listdir(img_dir_path))]
    img_path_list = natsorted(img_path_list)

    print(img_path_list)

    pdf_padding = 4
    pdf = FPDF()

    for img_path in img_path_list:
        image = Image.open(img_path)

        #dpi to mm
        width, height = (i * 0.264583 for i in image.size)

        # given we are working with A4 format size 
        pdf_size = {'P': {'w': 210, 'h': 297}, 'L': {'w': 297, 'h': 210}}

        # get page orientation from image size 
        orientation = 'P' if width < height else 'L'
        pdf.add_page(orientation=orientation)

        width = width if width < pdf_size[orientation]['w'] else pdf_size[orientation]['w']
        height = height if height < pdf_size[orientation]['h'] else pdf_size[orientation]['h']

        # if orientation == 'P':
        #     # make sure image size is not greater than the pdf format size
        #     width = width if width < pdf_size[orientation]['w'] else pdf_size[orientation]['w']
        #     height = height if height < pdf_size[orientation]['h'] else pdf_size[orientation]['h']
        # else:
        #     resize = True if width > pdf_size[orientation]['w'] or height > pdf_size[orientation]['h'] else False
            
        #     if resize:
        #         width_resize_percent = (width - pdf_size[orientation]['w']) / width
        #         height_resize_percent = (height - pdf_size[orientation]['h']) / height

        #         resize_percent = width_resize_percent if width_resize_percent > height_resize_percent else height_resize_percent
                
        #         width = width * resize_percent
        #         height = height * resize_percent
            
        # TODO image rotate and save by image type
        pdf.image(img_path, pdf_padding, pdf_padding, width-pdf_padding*2, height-pdf_padding*2)

    pdf.output(pdf_name_path, 'F')
    print('PDF completed.')


# setting variable
command_executor = 'http://172.20.0.3:4444/wd/hub'
comic_url = 'https://www.manhuagui.com/comic/41237/'
roll_only = False
create_pdf = True

try:
    # chrome driver setting
    options = webdriver.ChromeOptions()
    driver = webdriver.Remote(
        command_executor=command_executor,
        options=options
    )

    driver.get(comic_url)
    chapters_url_name_list = find_chapters_url(driver, roll_only=roll_only)

    print('Chapters list: ', chapters_url_name_list)

    for chapter in chapters_url_name_list:
        driver.get(chapter['url'])
        print('Getting chapter: ' + chapter['name'])

        time.sleep(random.uniform(10.0, 15.0))
        html = find_full_chapter_html(driver)

        img_url_list = find_all_img_src(html)
        
        save_img(chapter['name'] + '/', img_url_list)

        if create_pdf:
            convert2pdf(chapter['name'] + '/', chapter['name'] + '.pdf')

except Exception as e:
    print('Exception:', e)

finally:
    # quit driver
    driver.quit()
