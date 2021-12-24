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
import json

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
                'window.scrollTo({ top: document.body.scrollHeight, left: 0, behavior: "smooth" });')

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
    chapters_obj_list = []

    click_confirm_button(driver)
    html = driver.page_source
    soup = BeautifulSoup(html, features='html.parser')

    comic_name = soup.select_one('.book-title h1').text

    chapter_list = soup.select('.chapter-list ul')

    # loop through the chapter list
    for chapters in chapter_list:
        for li in chapters.find_all('li'):

            a = li.find('a')

            # check only get 第n卷
            if roll_only and '卷' not in a['title']:
                continue

            details = {
                'url': 'https://www.manhuagui.com/' + a['href'],
                'name': a['title'],
                'total_page': int(li.find('i').text.replace('p', '')),
                'download_page': 0,
                'img_url_list': []
            }
            chapters_obj_list.append(details)

    return comic_name, chapters_obj_list


# Get image from i.harmreus.com and save
def save_img(img_dir_path, chapter):
    Path(img_dir_path).mkdir(parents=True, exist_ok=True)

    headers = {
        'Referer': 'https://www.manhuagui.com',
    }

    download_page = 0
    img_url_list = chapter['img_url_list']
    # pop the third img, becasue it is same as second img
    img_url_list.pop(2)

    for idx, url in enumerate(img_url_list):
        try_again = True
        while try_again:
            try:
                response = requests.get(url, headers=headers, stream=True)
                image = Image.open(io.BytesIO(response.content))
                response.close()

                fname = img_dir_path + str(idx+1) + '.jpg'
                image.save(fname)
                download_page += 1

                print('Img saved:' + str(idx+1) + '/' + str(len(img_url_list)))
                time.sleep(random.uniform(1.5, 3.0))
                try_again = False

            except:
                print('Fail, auto download again')
                try_again = True
                time.sleep(10)

    print('Chapter saving complete!')
    return download_page


# TODO, modify to save from memory
# after all img saved then create
def convert2pdf(img_dir_path, pdf_name_path):
    print('PDF creating...')

    img_path_list = [img_dir_path +
                     img for img in list(os.listdir(img_dir_path))]
    img_path_list = natsorted(img_path_list)

    pdf_padding = 4
    pdf = FPDF()

    for img_path in img_path_list:
        image = Image.open(img_path)

        # dpi to mm
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
        pdf.image(img_path, pdf_padding, pdf_padding,
                  width-pdf_padding*2, height-pdf_padding*2)

    pdf.output(pdf_name_path, 'F')
    print('PDF completed.')


def downlist_update(comic_obj_list=None, replace=False):
    # read existed list
    if not replace:
        try:
            with open('downlist.json', 'r') as f:
                if comic_obj_list != None:
                    comic_obj_list += json.load(f)
                else:
                    comic_obj_list = json.load(f)
        except:
            print('downlist.json not exist, auto create')

    # update list
    with open('downlist.json', 'w') as f:
        json.dump(comic_obj_list, f, ensure_ascii=False, indent=4)

    return comic_obj_list


# setting variable
command_executor = 'http://172.20.0.2:4444/' + 'wd/hub'

try:
    # chrome driver setting
    options = webdriver.ChromeOptions()
    driver = webdriver.Remote(
        command_executor=command_executor,
        options=options
    )

    while(True):
        action = int(input('Input action 1=get url, 2=download, 3=exit: '))

        # getting chapger data
        if action == 1:

            comic_url = input('Input comic url: ')

            roll_only = True if input(
                'Roll only? (True/False) ') == 'True' else False

            # get comic all chapter data
            print('strat getting')
            driver.get(comic_url)
            comic_name, chapters_obj_list = find_chapters_url(
                driver, roll_only=roll_only)

            # print all chapter name
            print('All chapter: ', [chapter['name']
                  for chapter in chapters_obj_list])

            # only append the selected chpater
            input_chapter_list = input(
                'Input the purpose chapter(empty = all)(example: 第05回,第01回): ').split(',')

            chapters_obj_list = chapters_obj_list if input_chapter_list[0] == '' else [
                chapter for chapter in chapters_obj_list if chapter['name'] in input_chapter_list]

            # remove all the skip chapter
            input_chapter_list = input(
                'Input the skipping chapter(example: 第05回,第01回): ').split(',')

            chapters_obj_list = chapters_obj_list if input_chapter_list[0] == '' else [
                chapter for chapter in chapters_obj_list if not chapter['name'] in input_chapter_list]

            # ask create pdf and save to json
            create_pdf = True if input(
                'Create PDF?  (True/False) ') == 'True' else False
            comic_obj_list = [{
                'name': comic_name,
                'create_pdf': create_pdf,
                'url': comic_url,
                'chapter': chapters_obj_list,
            }]
            downlist_update(comic_obj_list)
            print('Adding success!')

        # main of get chpater image url and download
        if action == 2:
            # get teh donwlist data
            comic_obj_list = downlist_update()

            # None = no file
            if comic_obj_list != None:
                for comic_idx, comic in enumerate(comic_obj_list):
                    base_path = comic['name'] + '/'

                    for chapter_idx, chapter in enumerate(comic['chapter']):

                        save_dir_path = base_path + chapter['name'] + '/'
                        
                        print('Getting chapter: ' + chapter['name'])

                        driver.get(chapter['url'])
                        time.sleep(random.uniform(10.0, 15.0))

                        html = find_full_chapter_html(driver)

                        # get chapter image src
                        chapter['img_url_list'] = find_all_img_src(html)
                        comic_obj_list[comic_idx]['chapter'][chapter_idx] = chapter

                        # donwload image and get teh number of downloaded page
                        chapter['download_page'] = save_img(
                            save_dir_path, chapter)
                        comic_obj_list[comic_idx]['chapter'][chapter_idx] = chapter

                        # create pdf
                        if comic['create_pdf']:
                            convert2pdf(save_dir_path, base_path + comic['name'] + ' ' +
                                        chapter['name'] + '.pdf')

                        # update downlist.json
                        downlist_update(comic_obj_list, replace=True)

        if action == 3:
            break

except Exception as e:
    print('Exception:', e)

finally:
    # quit driver
    driver.quit()

    # get teh donwlist data
    comic_obj_list = downlist_update()
    temp_comic_obj_list = []

    # downloaded comic verify
    if comic_obj_list != None:
        for comic_idx, comic in enumerate(comic_obj_list):
            not_finish_chapter_list = []

            print(comic['name'])
            for chapter in comic['chapter']:
                is_complete = True if chapter['download_page'] == chapter['total_page'] else False
                is_complete_message = 'OK!' if is_complete else 'Error, please download again!'

                if not is_complete:
                    not_finish_chapter_list.append(chapter)

                print(chapter['name'] + ': ' + str(chapter['download_page']) +
                      '/' + str(chapter['total_page']) + '\t\t' + is_complete_message)

            # update not download chpater list
            comic_obj_list[comic_idx]['chapter'] = not_finish_chapter_list

            # if chpater list = 0 then remove comic fomr downlist
            if len(comic_obj_list[comic_idx]['chapter']) != 0:
                temp_comic_obj_list.append(comic)

    # update downlist.json
    downlist_update(temp_comic_obj_list, replace=True)
