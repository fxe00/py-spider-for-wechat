#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
微信公众号ID获取模块
==================

模块功能:
    通过微信公众平台的搜索接口，根据公众号名称关键词搜索匹配的公众号，
    并返回公众号的基本信息（名称和fakeid）。fakeid是微信公众平台内部
    用于标识公众号的唯一ID，是后续获取文章列表的必要参数。

主要功能:
    1. 公众号搜索 - 根据关键词搜索公众号
    2. 结果解析 - 解析搜索结果并提取公众号信息
    3. 数据格式化 - 将结果格式化为标准的字典列表

API接口说明:
    - 接口地址: https://mp.weixin.qq.com/cgi-bin/searchbiz
    - 请求方式: GET
    - 认证方式: 通过token和cookie进行身份验证
    - 返回格式: JSON

参数说明:
    - headers: HTTP请求头，包含cookie等认证信息
    - tok: 微信公众平台的访问token
    - query: 搜索关键词（公众号名称）

返回值格式:
    返回包含公众号信息的字典列表，每个字典包含：
    - wpub_name: 公众号显示名称
    - wpub_fakid: 公众号的内部ID（用于后续API调用）

使用示例:
    headers = {'cookie': 'your_cookie_here', ...}
    token = 'your_token_here'
    query = '公众号名称'
    result = get_fakid(headers, token, query)
    # result: [{'wpub_name': '公众号1', 'wpub_fakid': 'fakeid1'}, ...]

注意事项:
    - 需要有效的微信公众平台登录状态
    - token和cookie必须匹配且在有效期内
    - 搜索结果最多返回10个匹配的公众号
    - 请求频率不宜过高，避免被限制访问

作者: 王思哲
创建时间: 2022/12/20
版本: 1.0
"""

# coding=utf-8
# @Time : 2022/12/20 11:55 AM
# @Author : 王思哲
# @File : getFakId.py
# @Software: PyCharm

import logging
import time
import requests

# 频率限制错误码
FREQ_CONTROL_RET = 200013
# 频率限制等待时间（秒）
FREQ_CONTROL_WAIT = 60
# 最大重试次数
MAX_RETRIES = 3


def get_fakid(headers, tok, query, retries=MAX_RETRIES):
    '''
    :param headers: 请求头
    :param tok: token
    :param query: 查询名称
    :param retries: 遇到频率限制时的最大重试次数
    :return: 公众号列表
    '''
    url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz'
    data = {
        'action': 'search_biz',
        'scene': 1,  # 页数
        'begin': 0,
        'count': 10,
        'query': query,
        'token': tok,
        'lang': 'zh_CN',
        'f': 'json',
        'ajax': '1',
    }

    for attempt in range(retries):
        # 发送请求
        r = requests.get(url, headers=headers, params=data)
        # 解析json
        dic = r.json()

        # 检查响应是否包含错误
        if 'ret' in dic and dic['ret'] != 0:
            ret = dic['ret']
            error_msg = dic.get('errmsg', '未知错误')

            # 如果是频率限制，等待后重试
            if ret == FREQ_CONTROL_RET:
                if attempt < retries - 1:
                    logging.warning(
                        f"wechat returned freq control (ret={ret}), waiting {FREQ_CONTROL_WAIT}s before retry ({attempt + 1}/{retries})")
                    time.sleep(FREQ_CONTROL_WAIT)
                    continue
                else:
                    logging.error(f"wechat returned freq control (ret={ret}) after {retries} attempts, giving up")
                    return []
            else:
                logging.warning(f"wechat returned error ret={ret}, msg={error_msg}")
                return []

        # 检查响应中是否包含 list 字段
        if 'list' not in dic:
            logging.warning(f"wechat response missing 'list' field: {dic}")
            return []

        # 获取公众号名称、fakeid、头像
        wpub_list = []
        for item in dic['list']:
            wpub_info = {
                'wpub_name': item['nickname'],
                'wpub_fakid': item['fakeid']
            }
            # 记录所有可用字段（用于调试）
            available_fields = [k for k in item.keys() if 'img' in k.lower()
                                or 'avatar' in k.lower() or 'head' in k.lower()]
            if available_fields:
                logging.info(f"Available image fields for {item['nickname']}: {available_fields}")

            # 尝试获取头像URL（微信API可能返回的字段名，按优先级尝试）
            avatar_found = False
            for field_name in ['round_head_img', 'headimg', 'avatar', 'head_img', 'round_headimg', 'logo_url']:
                if field_name in item and item[field_name]:
                    wpub_info['wpub_avatar'] = item[field_name]
                    avatar_found = True
                    logging.info(f"Found avatar for {item['nickname']} in field '{field_name}'")
                    break

            if not avatar_found:
                logging.warning(f"No avatar field found for {item['nickname']}. All fields: {list(item.keys())}")

            # 保存其他可能有用的字段
            if 'alias' in item:
                wpub_info['alias'] = item['alias']  # 公众号别名
            if 'service_type' in item:
                wpub_info['service_type'] = item['service_type']  # 服务类型
            if 'verify_type' in item:
                wpub_info['verify_type'] = item['verify_type']  # 认证类型
            if 'signature' in item:
                wpub_info['signature'] = item['signature']  # 简介/签名
            if 'user_name' in item:
                wpub_info['user_name'] = item['user_name']  # 用户名（可能是原始ID）

            # 保存原始数据用于调试（仅包含关键字段）
            wpub_info['_raw_data'] = {
                k: v for k, v in item.items()
                if k not in ['nickname', 'fakeid'] and v is not None
            }
            wpub_list.append(wpub_info)

        return wpub_list

    return []
