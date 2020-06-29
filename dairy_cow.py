#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
奶牛抢票

@author mybsdc <mybsdc@gmail.com>
@date 2020/6/29
@time 10:28
"""

import os
import time
import random
import json
import re
import sys
import traceback
from urllib.request import urlretrieve
import requests
import pickle
import numpy as np
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import logging
from dotenv import load_dotenv


def catch_exception(origin_func):
    def wrapper(self, *args, **kwargs):
        """
        用于异常捕获的装饰器
        :param origin_func:
        :return:
        """
        try:
            return origin_func(self, *args, **kwargs)
        except AssertionError as ae:
            print('参数错误：{}'.format(str(ae)))
        except NoSuchElementException as nse:
            print('匹配元素超时，超过{}秒依然没有发现元素：{}'.format(DairyCow.timeout, str(nse)))
        except TimeoutException:
            print(f'请求超时：{self.driver.current_url}')
        except UserWarning as uw:
            print('警告：{}'.format(str(uw)))
        except WebDriverException:
            print('未知错误，可能是 chromedriver 与本地谷歌无头浏览器版本不匹配，可检查并前往 https://chromedriver.chromium.org/downloads '
                  '下载匹配的版本，当然也可能不是这个原因:)')
        except Exception as e:
            print('出错：{} 位置：{}'.format(str(e), traceback.format_exc()))
        finally:
            self.driver.quit()
            print('已关闭浏览器，释放资源占用')

    return wrapper


class DairyCow(object):
    # 超时秒数，包括隐式等待和显式等待
    timeout = 33

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'

    # 大麦网登录地址
    login_url = 'https://passport.damai.cn/login'

    def __init__(self):
        # 加载环境变量
        load_dotenv(verbose=True, override=True, encoding='utf-8')

        self.options = webdriver.ChromeOptions()

        self.options.add_argument(f'user-agent={DairyCow.user_agent}')
        self.options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument('--disable-extensions')  # 禁用扩展
        self.options.add_argument('--profile-directory=Default')
        self.options.add_argument('--incognito')  # 隐身模式
        self.options.add_argument('--disable-plugins-discovery')
        self.options.add_argument('--start-maximized')
        # self.options.add_argument('--window-size=1366,768')

        # self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')  # 谷歌官方文档说加上此参数可减少 bug，仅适用于 Windows 系统

        # 解决 unknown error: DevToolsActivePort file doesn't exist
        self.options.add_argument('--no-sandbox')  # 绕过操作系统沙箱环境
        self.options.add_argument('--disable-dev-shm-usage')  # 解决资源限制，仅适用于 Linux 系统

        self.driver = webdriver.Chrome(executable_path=os.getenv('EXECUTABLE_PATH'), options=self.options)
        self.driver.implicitly_wait(DairyCow.timeout)

        # 防止通过 window.navigator.webdriver === true 检测模拟浏览器
        # 参考：
        # https://www.selenium.dev/selenium/docs/api/py/webdriver_chrome/selenium.webdriver.chrome.webdriver.html#selenium.webdriver.chrome.webdriver.WebDriver.execute_cdp_cmd
        # https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-addScriptToEvaluateOnNewDocument
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })

        # 统配显式等待
        self.wait = WebDriverWait(self.driver, timeout=DairyCow.timeout, poll_frequency=0.5)

        self.cookies_file = 'cookies_jar'
        self.cookies = None

        self.username = os.getenv('USERNAME')
        self.password = os.getenv('PASSWORD')

    def __login(self, force=False):
        """
        登录大麦网
        :param force: 是否强制登录，强制登录将忽略已存在的 cookies 文件，走完整登录逻辑
        :return:
        """
        if not force and os.path.exists(self.cookies_file):
            print('发现已存在 cookies 文件，免登录')
            with open(self.cookies_file, 'rb') as f:
                self.cookies = pickle.load(f)

                return self.cookies

        self.driver.get(DairyCow.login_url)

        login_frame = self.driver.find_element_by_id('alibaba-login-box')
        self.driver.switch_to.frame(login_frame)

        u = self.driver.find_element_by_id('fm-login-id')
        u.clear()
        u.send_keys(self.username)

        p = self.driver.find_element_by_id('fm-login-password')
        p.clear()
        p.send_keys(self.password)

        self.__fuck_captcha()

        # self.driver.find_element_by_class_name('password-login').click()

        cookies = {}
        for cookie in self.driver.get_cookies():
            cookies[cookie['name']] = cookie['value']

        # cookies 持久化
        with open(self.cookies_file, 'wb') as f:
            pickle.dump(cookies, f)

        self.cookies = cookies

        return self.cookies

    def __fuck_captcha(self, max_retry_num=6):
        time.sleep(0.2)
        captcha_slider = EC.visibility_of_element_located((By.ID, 'nc_1_n1z'))(self.driver)

        if captcha_slider:
            ActionChains(self.driver).click_and_hold(on_element=captcha_slider).perform()
            ActionChains(self.driver).move_by_offset(xoffset=28, yoffset=0).perform()
            ActionChains(self.driver).release(on_element=captcha_slider).perform()

            # success_icon = EC.presence_of_element_located((By.CLASS_NAME, 'btn_ok'))(self.driver)
            pass


    @staticmethod
    def row_print(string):
        """
        在同一行输出字符
        :param string:
        :return:
        """
        print(string, end='\r')  # 回车将回到文本开始处
        sys.stdout.flush()

        time.sleep(0.02)

    @catch_exception
    def run(self):
        self.__login()
        pass


if __name__ == '__main__':
    dairy_cow = DairyCow()
    dairy_cow.run()
