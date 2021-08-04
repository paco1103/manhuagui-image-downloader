import requests
from PIL import Image
import io
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import sys
import random
from pathlib import Path


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


# Get image from i.harmreus.com and save
def save_img(img_dir, img_url_list):
    Path(img_dir).mkdir(parents=True, exist_ok=True)

    headers = {
        'Referer': 'https://www.manhuagui.com',
    }

    for idx, url in enumerate(img_url_list):
        response = requests.get(url, headers=headers, stream=True)
        image = Image.open(io.BytesIO(response.content))
        fname = img_dir + '/' + str(idx+1) + '.jpg'
        image.save(fname)
        print('Img saved:' + str(idx+1) + '/' + str(len(img_url_list)))
        response.close()
        time.sleep(random.uniform(0.5, 3.0))


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

# setting variable
command_executor = 'http://172.20.0.3:4444/wd/hub'
comic_url = 'https://www.manhuagui.com/comic/15761/'
roll_only = True


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
        print('Chapter full html complete!')

        img_url_list = find_all_img_src(html)
        save_img(chapter['name'], img_url_list)
        print('Chapter saving complete!')
except Exception as e:
    print('Exception:', e)

finally:
    # quit driver
    driver.quit()
