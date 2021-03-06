# -*- coding: utf-8 -*-
import datetime
import logging
import os
import unittest
import mysql.connector
import redis
from time import sleep
from selenium import webdriver
from os import path

import lib.Properties

logger = logging.getLogger('test_login')
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setFormatter(
    logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] [%(process)d]- %(levelname)s: %(message)s'))
logger.addHandler(sh)
"""
获取cookie里的yunsid
"""


def get_yun_sid(browers):
    cookies = browers.get_cookies()
    for cookie_dict in cookies:
        if cookie_dict['name'] == 'yunsid':
            return cookie_dict['value']
    logger.error('该页面cookie不包含yunsid')
    return ''


cwd = path.dirname(__file__)


# 获取redis中验证码
def get_redis_validcode(browers, redis, config):
    # 获取cookie中的sid，并获取redis中的图片验证码
    yunsid = get_yun_sid(browers)
    logger.info('获得yunsid:{}'.format(yunsid))
    valied_code = redis.hget((config.get('session.prefix') + yunsid), config.get('valid.code.key'))
    return valied_code


# 获取数据库中的手机验证码
def get_phone_validcode(jdbc, phone, config):
    verify_phone_code = ''
    i = 1
    while i < 6 and verify_phone_code == '':
        sleep(2)
        logger.info('当前手机验证码为空，第{}次查询数据库……'.format(i))
        cursor = jdbc.cursor()
        query_sql = str(config.get('jdbc.query')).replace('$equals$', '=').format(phone)
        cursor.execute(query_sql)
        logger.info('查询数据库：{}'.format(query_sql))
        jdbc_result = cursor.fetchall()
        logger.info('查询结果为：{}'.format(jdbc_result))
        if type(jdbc_result) == list:
            for rows in jdbc_result:
                if rows[0] is not None:
                    verify_phone_code = rows[0]
                    break
        i += 1
    logger.info('短信验证码为:{}'.format(verify_phone_code))
    return verify_phone_code


# 输入用户名和密码
def input_uname(browers, config, element, username, password, valied_code):
    browers.find_element_by_xpath(element.get('login.page.prompt')).click()
    browers.find_element_by_id(element.get('login.username.id')).send_keys(username)
    browers.find_element_by_id(element.get('login.pwd.id')).send_keys(password)
    logger.info('从redis中获取图片验证码为:{}'.format(valied_code))
    browers.find_element_by_id(element.get('login.valid.id')).send_keys(str(valied_code))
    browers.find_element_by_xpath(element.get('login.button')).click()
    sleep(1)
    return get_dialog(browers, element)


# 输入税号和密码
def input_nsrsbh(browers, config, element, nsrsbh, password, valied_code):
    browers.get(config.get('login.url'))
    browers.find_element_by_xpath(element.get('login.page.prompt')).click()
    sleep(1)
    browers.find_element_by_xpath(element.get('login.tax')).click()
    browers.find_element_by_id(element.get('login.username.tax.id')).send_keys(nsrsbh)
    browers.find_element_by_id(element.get('login.pwd.tax.id')).send_keys(password)
    logger.info('从redis中获取图片验证码为:{}'.format(valied_code))
    browers.find_element_by_id(element.get('login.valid.tax.id')).send_keys(str(valied_code))
    browers.find_element_by_xpath(element.get('login.button.tax')).click()
    sleep(1)
    return get_dialog(browers, element)


# 输入验证码
def phone_varify(browers, element, verify_phone_code):
    browers.find_element_by_id(element.get('verify.phone.sender')).click()
    logger.info('发送验证码中')
    browers.find_element_by_id(element.get('yzm.input.id')).send_keys(verify_phone_code)
    browers.find_element_by_xpath(element.get('yzm.button')).click()
    sleep(1)
    return get_dialog(browers, element)


# 获取页面提示的dialog
def get_dialog(browers, element):
    dialog_element = None
    # 如果登录失败，页面有弹出框提示，则测试通过
    try:
        dialog_element = browers.find_element_by_xpath(element.get('login.page.dialog'))
        dialog_element_msg = dialog_element.text
        logger.info(dialog_element_msg)
        browers.save_screenshot(
            'test_login_' + datetime.datetime.now().strftime('%Y-%m-%d %H_%M_%S') + '.png')
    except:
        pass
    return dialog_element


class LoginTest(unittest.TestCase):

    def setUp(self):
        self.config = lib.Properties.parse(cwd + os.sep + 'config.properties')
        self.element = lib.Properties.parse(cwd + os.sep + 'element.properties')
        self.input = lib.Properties.parse(cwd + os.sep + 'input.properties')
        self.redis = redis.Redis(
            host=self.config.get('redis.host'),
            password=self.config.get('redis.password'),
            port=self.config.get('redis.port')
        )
        self.jdbc = mysql.connector.connect(
            host=self.config.get('jdbc.host'),
            user=self.config.get('jdbc.username'),
            password=self.config.get('jdbc.password'),
            database=self.config.get('jdbc.database')
        )
        chrome_driver = self.config.contains('chrome.driver.path')
        ie_driver = self.config.contains('ie.driver.path')
        if chrome_driver is True:
            chrome_driver_path = self.config.get('chrome.driver.path')
            logger.info('获取到chrome驱动路径为:{}'.format(chrome_driver_path))
            self.browers = webdriver.Chrome(chrome_driver_path)
        if ie_driver is True:
            ie_driver_path = self.config.get('ie.driver.path')
            logger.info('获取到IE驱动路径为:{}'.format(ie_driver_path))
            self.browers = webdriver.Ie(ie_driver_path)

    """测试用例01-手机号+密码登录成功"""

    def test_login_001(self):
        browers = self.browers
        config = self.config
        input = self.input
        element = self.element
        browers.implicitly_wait(5)
        browers.get(config.get('login.url'))
        valid_code = get_redis_validcode(browers, self.redis, config)
        dialog_element = input_uname(browers, config, element, input.get('test.case1.username'),
                                     input.get('test.case1.pwd'), valid_code)
        dialog_msg = dialog_element.text if dialog_element is not None else ''
        self.assertIsNone(dialog_element, '登录失败:{}'.format(dialog_msg))
        title = browers.title
        if title == config.get('success.title'):
            self.assertEqual(title, config.get('success.title'))
        verify_phone = browers.find_element_by_id(element.get('verify.phone.id')).get_attribute('value')
        logger.info('当前登录用户手机号码为：{}'.format(verify_phone))
        verify_phone_code = get_phone_validcode(self.jdbc, verify_phone, config)
        dialog_element = phone_varify(browers, element, verify_phone_code)
        dialog_msg = dialog_element.text if dialog_element is not None else ''
        self.assertIsNone(dialog_element, '登录失败:{}'.format(dialog_msg))
        title = browers.title
        self.assertEqual(title, config.get('success.title'))

    """测试用例02-用户名+密码登录成功"""

    def test_login_002(self):
        browers = self.browers
        config = self.config
        input = self.input
        element = self.element
        browers.implicitly_wait(5)
        browers.get(config.get('login.url'))
        valid_code = get_redis_validcode(browers, self.redis, config)
        dialog_element = input_uname(browers, config, element, input.get('test.case2.username'),
                                     input.get('test.case2.pwd'), valid_code)
        dialog_msg = dialog_element.text if dialog_element is not None else ''
        self.assertIsNone(dialog_element, '登录失败:{}'.format(dialog_msg))
        title = browers.title
        if title == config.get('success.title'):
            self.assertEqual(title, config.get('success.title'))
        verify_phone = browers.find_element_by_id(element.get('verify.phone.id')).get_attribute('value')
        logger.info('当前登录用户手机号码为：{}'.format(verify_phone))
        verify_phone_code = get_phone_validcode(self.jdbc, verify_phone, config)
        dialog_element = phone_varify(browers, element, verify_phone_code)
        self.assertIsNone(dialog_element, '登录失败:{}'.format(dialog_msg))
        title = browers.title
        self.assertEqual(title, config.get('success.title'))

    """测试用例03-税号+密码登录成功"""

    def test_login_003(self):
        browers = self.browers
        config = self.config
        input = self.input
        element = self.element
        browers.implicitly_wait(5)
        browers.get(config.get('login.url'))
        valid_code = get_redis_validcode(browers, self.redis, config)
        dialog_element = input_nsrsbh(browers, config, element, input.get('test.case1.username'),
                                      input.get('test.case3.pwd'), valid_code)
        dialog_msg = dialog_element.text if dialog_element is not None else ''
        self.assertIsNone(dialog_element, '登录失败:{}'.format(dialog_msg))
        title = browers.title
        if title == config.get('success.title'):
            self.assertEqual(title, config.get('success.title'))
        verify_phone = browers.find_element_by_id(element.get('verify.phone.id')).get_attribute('value')
        logger.info('当前登录用户手机号码为：{}'.format(verify_phone))
        verify_phone_code = get_phone_validcode(self.jdbc, verify_phone, config)
        dialog_element = phone_varify(browers, element, verify_phone_code)
        self.assertIsNone(dialog_element, '登录失败:{}'.format(dialog_msg))
        title = browers.title
        self.assertEqual(title, config.get('success.title'))

    """测试用例004-手机号+错误密码登录失败"""

    def test_login_004(self):
        browers = self.browers
        config = self.config
        input = self.input
        element = self.element
        browers.implicitly_wait(5)
        browers.get(config.get('login.url'))
        valid_code = get_redis_validcode(browers, self.redis, config)
        dialog_element = input_nsrsbh(browers, config, element, input.get('test.case4.username'),
                                      input.get('test.case4.pwd'), valid_code)
        self.assertIsNotNone(dialog_element, '错误密码不应该登录成功')

    """测试用例005-用户名为中文，登录失败"""

    def test_login_005(self):
        browers = self.browers
        config = self.config
        input = self.input
        element = self.element
        browers.implicitly_wait(5)
        browers.get(config.get('login.url'))
        valid_code = get_redis_validcode(browers, self.redis, config)
        dialog_element = input_nsrsbh(browers, config, element, input.get('test.case5.username'),
                                      input.get('test.case5.pwd'), valid_code)
        self.assertIsNotNone(dialog_element, '中文用户名不应该登录成功')

    """测试用例006-密码为纯数字登录失败"""

    def test_login_006(self):
        browers = self.browers
        config = self.config
        input = self.input
        element = self.element
        browers.implicitly_wait(5)
        browers.get(config.get('login.url'))
        valid_code = get_redis_validcode(browers, self.redis, config)
        dialog_element = input_nsrsbh(browers, config, element, input.get('test.case6.username'),
                                      input.get('test.case6.pwd'), valid_code)
        self.assertIsNotNone(dialog_element, '纯数字密码不应该登录成功')

    """测试用例007-图形验证码为空登录失败"""

    def test_login_007(self):
        browers = self.browers
        config = self.config
        input = self.input
        element = self.element
        browers.implicitly_wait(5)
        browers.get(config.get('login.url'))
        dialog_element = input_nsrsbh(browers, config, element, input.get('test.case7.username'),
                                      input.get('test.case7.pwd'), '')
        self.assertIsNotNone(dialog_element, '验证码为空不应该登录成功')

    """测试用例008-税号有特殊字符登录失败"""

    def test_login_008(self):
        browers = self.browers
        config = self.config
        input = self.input
        element = self.element
        browers.implicitly_wait(5)
        browers.get(config.get('login.url'))
        dialog_element = input_nsrsbh(browers, config, element, input.get('test.case8.username'),
                                      input.get('test.case8.pwd'), '')
        self.assertIsNotNone(dialog_element, '税号有特殊字符不应该登录成功')

    """测试用例009-密码为空登录失败"""

    def test_login_009(self):
        browers = self.browers
        config = self.config
        input = self.input
        element = self.element
        browers.implicitly_wait(5)
        browers.get(config.get('login.url'))
        valid_code = get_redis_validcode(browers, self.redis, config)
        dialog_element = input_nsrsbh(browers, config, element, input.get('test.case9.username'),
                                      input.get('test.case9.pwd'), valid_code)
        self.assertIsNotNone(dialog_element, '空密码不应该登录成功')

    def tearDown(self):
        self.browers.quit()


if __name__ == '__main__':
    unittest.main()
