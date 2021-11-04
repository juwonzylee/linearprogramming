import requests
import pandas
import time
import os
import sys

from multiprocessing import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import *
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup, Comment

DEBUG_MODE = True

# 작업 로그
def line_logging(*messages):
    if DEBUG_MODE:
        import datetime
        import sys
        today = datetime.datetime.today()
        log_time = today.strftime('[%Y/%m/%d %H:%M:%S]')
        log = []
        for message in messages:
            log.append(str(message))
        print(log_time + ':[' + ', '.join(log) + ']')
        sys.stdout.flush()

# sleep 함수
def do_sleep(p_sleep_time):
    time.sleep(p_sleep_time)

# 상품명 크롤링 함수()
def get_product(p_location_F, p_location_T, p_driver_path):
    line_logging(p_location_F, p_location_T)

    list_product = list()
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.80 Safari/537.36")
    driver = webdriver.Chrome(p_driver_path, options=options)

    # 크롬 드라이버로 특정 카테고리 link에 접속
    driver.get('https://map.naver.com/v5/directions/-/-/-/walk?c=14303871.3435609,4276606.0387979,15,0,0,0,dh')

    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "directionStart0"))
    )

    # 출발점 입력 후 엔터 
    inputElementF = driver.find_element_by_id("directionStart0")
    inputElementF.send_keys(p_location_F)
    inputElementF.send_keys(Keys.ENTER)
    time.sleep(3)

    # 도착점 입력 후 엔터 
    inputElementT = driver.find_element_by_id("directionGoal1")
    inputElementT.send_keys(p_location_T)
    inputElementT.send_keys(Keys.ENTER)
    time.sleep(3)

    search_button = driver.find_element_by_class_name("btn_direction")
    actions = ActionChains(driver)
    actions.move_to_element(search_button)
    actions.click(search_button)
    actions.perform()
    time.sleep(3)

    html_tag = driver.page_source

    title = BeautifulSoup(html_tag, "html.parser").find_all('strong', {"class": "summary_title"})
    textname = BeautifulSoup(html_tag, "html.parser").find_all('span', {"class": "summary_text"})
    titlebox = BeautifulSoup(html_tag, "html.parser").find_all('div', {"class": "route_title_box"})
    # print(titlebox)

    if len(title) == 0 or len(textname) == 0 or len(titlebox) == 0:
        return [], False

    summary_title = title[0].text
    summary_text = textname[0].text
    
    if not titlebox[0].text:
        route_title_box = '횡단보도 0회'
    else:
        route_title_box = titlebox[0].text

    res = []
    res.append(summary_title)
    res.append(summary_text)
    res.append(route_title_box)

    return res, True


if __name__ == "__main__":
    driver_path = '/usr/local/bin/chromedriver'
    df = pandas.read_csv('~/desktop/남부구로구.csv')

    addresses_f = []
    addresses_t = []


    for i in range(len(df)):
        addresses_f.append(df['도로명주소'][i])
        addresses_t.append(df['배정 중학교'][i])
    
    res = []
    err_list = []
    current_time = time.time()
    for i in range(len(addresses_f)):
        print("[%04d/%04d] %.2f" % (i, len(addresses_f), time.time()-current_time))
        current_time = time.time()
        # if i > 1:
        #     break # for testing i number of products
        prod, success = get_product(addresses_f[i],addresses_t[i], driver_path)
        if success == False:
            err_list.append([addresses_f[i],addresses_t[i]])

        time.sleep(1)
        res.append(prod)

    # write out to csv file 
    df_res = pandas.DataFrame(res)
    df_res.to_csv('~/desktop/result/남부청/남부구로구result.csv') # store location

    df_error = pandas.DataFrame(err_list)
    df_error.to_csv('~/desktop/result/남부청/남부구로구error.csv')