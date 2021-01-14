#!/usr/bin/env python
# -*- encoding=utf8 -*-

import time
import requests
import json

from datetime import datetime

from .jd_logger import logger
from .config import global_config

MAX_COUNT = 5
DEBUG = True

class Timer(object):
    def __init__(self, sleep_interval=0.5):
        # '2018-09-28 22:45:50.000'
        self.buy_time = datetime.strptime(global_config.getRaw('config', 'buy_time'), "%Y-%m-%d %H:%M:%S.%f")
        self.buy_time_ms = int(time.mktime(self.buy_time.timetuple()) * 1000.0 + self.buy_time.microsecond / 1000)
        self.sleep_interval = sleep_interval

        self.diff_time = self.local_jd_time_diff()

    def jd_time(self):
        """
        从京东服务器获取时间毫秒
        :return:
        """
        url = 'https://a.jd.com//ajax/queryServerData.html'
        ret = requests.get(url).text
        js = json.loads(ret)
        return int(js["serverTime"])

    def local_time(self):
        """
        获取本地毫秒时间
        :return:
        """
        return int(round(time.time() * 1000))

    def local_jd_time_diff(self):
        """
        计算本地与京东服务器时间差
        :return:
        """
        logger.info("开始计算服务器与本地时间平均差， 为精确需要一点时间")
        if DEBUG:
            default_time = self.local_time() - self.jd_time()
            return default_time
        max_diff_time = 0
        mini_diff_time = 0
        sum_diff_time = 0
        count = 0
        while count < MAX_COUNT:
            count = count + 1
            diff_time = self.local_time() - self.jd_time()
            logger.info('开始计算第{}/{}次时间差:{}'.format(count, MAX_COUNT, diff_time))
            if count == 1:
                max_diff_time = diff_time
                mini_diff_time = diff_time
                sum_diff_time = diff_time
                continue
            if diff_time > max_diff_time:
                max_diff_time = diff_time
            elif diff_time < mini_diff_time:
                mini_diff_time = diff_time
            sum_diff_time = sum_diff_time + diff_time
            time.sleep(self.sleep_interval)
        result = (sum_diff_time - max_diff_time - mini_diff_time) / (MAX_COUNT - 2)
        logger.info('最大时间差:{}'.format(max_diff_time))
        logger.info('最小时间差:{}'.format(mini_diff_time))
        logger.info("平均时间差：{}".format(result))
        logger.info("开始计算服务器与本地时间差结束")
        return result

    def start(self):
        logger.info('正在等待到达设定时间:{}，检测本地时间与京东服务器时间误差为【{}】毫秒'.format(self.buy_time, self.diff_time))
        if self.local_time() - self.diff_time >= (self.buy_time_ms - 5*60*1000):
            need_re_check_local_jd_time_diff = True
        else:
            need_re_check_local_jd_time_diff = False
        while True:
            # 本地时间减去与京东的时间差，能够将时间误差提升到0.1秒附近
            # 具体精度依赖获取京东服务器时间的网络时间损耗
            if need_re_check_local_jd_time_diff and self.local_time() - self.diff_time >= (self.buy_time_ms - 5*60*1000):
                self.diff_time = self.local_jd_time_diff()
                logger.info("现在是抢购5分钟前,重新校验diff time " + str(self.diff_time))
                need_re_check_local_jd_time_diff = False
            if self.local_time() - self.diff_time >= self.buy_time_ms:
                logger.info('时间到达，开始执行……')
                break
            else:
                time.sleep(self.sleep_interval)

    def buytime_get(self):
        """获取开始抢购的时间"""
        return self.buy_time