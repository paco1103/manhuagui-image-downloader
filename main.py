#Only support 3.7 version

import requests
from PIL import Image
import io
from bs4 import BeautifulSoup
import time
import sys
import os
import random
from pathlib import Path
from fpdf import FPDF
from natsort import natsorted
import json
from requests_html import HTMLSession


#Step 1: Get comic all charpter url
def find_chapters_url(comic_url, roll_only=False):
    chapters_obj_list = []
    isAdult = False

    response = requests.get(comic_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    response.close()

    comic_name = soup.select_one('.book-title h1').text
    chapter_list = soup.select('.chapter-list ul')

    if len(chapter_list) == 0:
        isAdult = True
        chapter_list = get_from_audit(comic_url).select('.chapter-list ul')

    # loop through the chapter list
    for chapters in chapter_list:
        for li in chapters.find_all('li'):

            a = li.find('a')

            # check only get 第n卷
            if roll_only and '卷' not in a['title']:
                continue

            details = {
                'url': 'https://tw.manhuagui.com' + a['href'],
                'name': a['title'],
                'total_page': int(li.find('i').text.replace('p', '')),
                'download_page': 0,
                'img_url_list': []
            }
            chapters_obj_list.append(details)
    return comic_name, isAdult, chapters_obj_list


#Step 2: find the chapter image url
def find_chapter_img_src(isAdult, url, num_page):
    img_url_list = []
    session = HTMLSession()
    for image_idx in range(1, num_page + 1):
        image_url = url + '#p=' + str(image_idx)
        #must use requests_html because of the ajax
        if isAdult:
            soup = get_from_audit(image_url)
            sleep_time = random.uniform(20.0, 60.0)
        else:
            response = session.get(image_url)
            response.html.render()
            soup = BeautifulSoup(response.html.html, features='html.parser')
            response.close()
            sleep_time = random.uniform(0.5, 2.0)

        img_tag = soup.select('#mangaBox img')
        img_url_list.append(img_tag[0]['src'])
        print('Image url:' + str(image_idx) + '/' + str(num_page))
        time.sleep(sleep_time)
    
    session.close()
    return img_url_list


#Step 3: Get image from i.harmreus.com and save
def save_img(img_dir_path, chapter):
    Path(img_dir_path).mkdir(parents=True, exist_ok=True)

    headers = {
        'Referer': 'https://tw.manhuagui.com',
    }

    download_page = 0
    img_url_list = chapter['img_url_list']
    print(img_url_list)
    for idx, url in enumerate(img_url_list):
        try_again = True
        while try_again:
            try:
                response = requests.get(url, headers=headers, stream=True)
                image = Image.open(io.BytesIO(response.content))
                response.close()

                fname = img_dir_path + str(idx + 1) + '.jpg'
                image.save(fname)
                download_page += 1

                print('Img saved:' + str(idx + 1) + '/' +
                      str(len(img_url_list)))
                time.sleep(random.uniform(0.5, 2.0))
                try_again = False

            except:
                print('Fail, auto download again')
                try_again = True
                time.sleep(random.uniform(10.0, 20.0))

    print('Chapter saving complete!')
    return download_page


def get_from_audit(url):
    session = HTMLSession()
    response = session.get(url)
    script = """
        try {
            document.getElementById('checkAdult').click();
        } catch (error) {
        }
    """
    response.html.render(script=script, reload=True)
    soup = BeautifulSoup(response.html.html, features='html.parser')
    response.close()
    session.close()
    return soup


# TODO, modify to save from memory
# after all img saved then create
def convert2pdf(img_dir_path, pdf_name_path):
    print('PDF creating...')

    img_path_list = [
        img_dir_path + img for img in list(os.listdir(img_dir_path))
    ]
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

        width = width if width < pdf_size[orientation]['w'] else pdf_size[
            orientation]['w']
        height = height if height < pdf_size[orientation]['h'] else pdf_size[
            orientation]['h']

        pdf.image(img_path, pdf_padding, pdf_padding, width - pdf_padding * 2,
                  height - pdf_padding * 2)

    pdf.output(pdf_name_path, 'F')
    print('PDF completed.')


#update the downlist.json and return the data from downlist.json
def downlist_update(comic_obj_list=None, replace=False):
    # read existed list
    if not replace:
        try:
            with open('data/downlist.json', 'r', encoding="utf-8") as f:
                if comic_obj_list != None:
                    comic_obj_list += json.load(f)
                else:
                    comic_obj_list = json.load(f)
        except:
            print('downlist.json not exist, auto create')

    # update list
    with open('data/downlist.json', 'w', encoding="utf-8") as f:
        json.dump(comic_obj_list, f, ensure_ascii=False, indent=4)

    return comic_obj_list


#verify the downlist data and remove the completed comic from downlist
def downlist_verify():
    # get teh donwlist data
    comic_obj_list = downlist_update()
    temp_comic_obj_list = []

    # downloaded comic verify
    if comic_obj_list != None:
        for comic_idx, comic in enumerate(comic_obj_list):
            not_finish_chapter_list = []

            print(comic['name'])
            for chapter in comic['chapter']:
                is_complete = True if chapter['download_page'] == chapter[
                    'total_page'] else False
                is_complete_message = 'OK!' if is_complete else 'Error, please download again!'

                if not is_complete:
                    not_finish_chapter_list.append(chapter)

                print(chapter['name'] + ': ' + str(chapter['download_page']) +
                    '/' + str(chapter['total_page']) + '\t\t' +
                    is_complete_message)

            # update not download chpater list
            comic_obj_list[comic_idx]['chapter'] = not_finish_chapter_list

            # if chpater list = 0 then remove comic fomr downlist
            if len(comic_obj_list[comic_idx]['chapter']) != 0:
                temp_comic_obj_list.append(comic)
    # update downlist.json
    downlist_update(temp_comic_obj_list, replace=True)





try:
    while (True):
        action = int(input('Input action 1=get url, 2=download, 3=exit: '))

        # getting chapger data
        if action == 1:

            comic_url = input('Input comic url: ')

            roll_only = True if input(
                'Roll only? (True/False) ') == 'True' else False

            # get comic all chapter data
            print('start getting')
            comic_name, isAdult, chapters_obj_list = find_chapters_url(comic_url,
                                                            roll_only=roll_only)

            # print all chapter name
            print('All chapter: ',
                [chapter['name'] for chapter in chapters_obj_list])

            # only append the selected chpater
            input_chapter_list = input(
                'Input the purpose chapter(empty = all)(example: 第05回,第01回): '
            ).split(',')

            chapters_obj_list = chapters_obj_list if input_chapter_list[
                0] == '' else [
                    chapter for chapter in chapters_obj_list
                    if chapter['name'] in input_chapter_list
                ]

            # remove all the skip chapter
            input_chapter_list = input(
                'Input the skipping chapter(example: 第05回,第01回): ').split(',')

            chapters_obj_list = chapters_obj_list if input_chapter_list[
                0] == '' else [
                    chapter for chapter in chapters_obj_list
                    if not chapter['name'] in input_chapter_list
                ]

            # ask create pdf and save to json
            create_pdf = False if input(
                'Create PDF?  (True/False) ') == 'False' else True
            comic_obj_list = [{
                'name': comic_name,
                'isAdult': isAdult,
                'create_pdf': create_pdf,
                'url': comic_url,
                'chapter': chapters_obj_list
            }]
            downlist_update(comic_obj_list)
            print('Adding success!')

        # main of get chapters image url and download
        if action == 2:
            # get teh donwlist data
            comic_obj_list = downlist_update()

            # None = no file
            if comic_obj_list != None:
                for comic_idx, comic in enumerate(comic_obj_list):
                    base_path = 'data/' + comic['name'] + '/'

                    for chapter_idx, chapter in enumerate(comic['chapter']):

                        save_dir_path = base_path + chapter['name'] + '/'

                        print('Getting chapter: ', comic['name'], chapter['name'])
                        #wait until next chapter scraping
                        time.sleep(random.uniform(5.0, 10.0))

                        # get chapter image src
                        chapter['img_url_list'] = find_chapter_img_src(comic['isAdult'], comic_obj_list[comic_idx]['chapter'][chapter_idx]
                            ['url'], comic_obj_list[comic_idx]['chapter']
                            [chapter_idx]['total_page'])

                        comic_obj_list[comic_idx]['chapter'][chapter_idx] = chapter

                        # donwload image and get teh number of downloaded page
                        chapter['download_page'] = save_img(save_dir_path, chapter)
                        comic_obj_list[comic_idx]['chapter'][chapter_idx] = chapter

                        # create pdf
                        if comic['create_pdf']:
                            convert2pdf(
                                save_dir_path, base_path + comic['name'] + ' ' +
                                chapter['name'] + '.pdf')

                        # update downlist.json
                        downlist_update(comic_obj_list, replace=True)
                
                downlist_verify()

        if action == 3:
            break
        
except Exception as e:
    import traceback
    traceback.print_exc()
    print('Exception:', e)

finally:
    downlist_verify()
