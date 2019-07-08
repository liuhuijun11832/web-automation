# -*-encoding: utf-8 -*-
import datetime
import logging
import os
import unittest

import lib.HTMLTestRunner as HTMLTestRunner
import lib.Properties as Properties

logger = logging.getLogger('html_report')
logger.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setFormatter(
    logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] [%(process)d]- %(levelname)s: %(message)s'))
logger.addHandler(sh)

if __name__ == '__main__':
    suite = unittest.TestSuite()
    bootstrap = Properties.parse(r'bootstrap.properties')
    current_file = os.path.split(__file__)[-1]
    pid = os.getpid()
    logger.info('开始读取配置文件')
    # 包含测试用例的目录必须是python package，否则无法递归匹配
    discover = unittest.defaultTestLoader.discover(bootstrap.get('test.case.dir'),
                                                   pattern=bootstrap.get('test.file.pattern'),
                                                   top_level_dir=None)
    for test_suite in discover:
        for test_case in test_suite:
            suite.addTests(test_case)
    now = datetime.datetime.now().strftime('%Y-%m-%d %H_%M_%S')
    filename = now + '.html'
    if bootstrap.contains('report.result.dir'):
        filename = bootstrap.get('report.result.dir') + now + '_result.html'
    fp = open(filename, 'wb')
    runner = HTMLTestRunner.HTMLTestRunner(
        stream=fp,
        title=bootstrap.get('repost.result.title'),
        description=bootstrap.get('report.result.desc'),
        verbosity=int(bootstrap.get('report.result.verbosity')),
        logger=logger
    )
    runner.run(suite)
    fp.close()
