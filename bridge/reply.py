# encoding:utf-8

from enum import Enum


class ReplyType(Enum):

    TEXT = 1  # 文本
    VOICE = 2  # 音频文件
    IMAGE = 3  # 图片文件
    IMAGE_URL = 4  # 图片URL
    VIDEO_URL = 5  # 视频URL
    FILE = 6  # 文件
    CARD = 7  # 微信名片
    InviteRoom = 8  # 邀请好友进群
    INFO = 9  #提示信息
    ERROR = 10  #错误信息
    TEXT_ = 11  # 强制文本
    VIDEO = 12  #视频
    MINIAPP = 13  # 小程序
    LINK = 14  #链接
    ACCEPT_FRIEND = 15  # 接受好友请求
    CALL_UP = 16  #打电话
    GIF = 17  #动图
    XML = 18 #卡片
    APP = 19 #APP配合SearchMusic

    def __str__(self):
        return self.name

    def is_xml_type(self):
        return self in [ReplyType.CARD, ReplyType.MINIAPP, ReplyType.LINK, ReplyType.XML]


class Reply:
    def __init__(self, type: ReplyType = None, content=None):
        self.type = type
        self.content = content

    def __str__(self):
        return "Reply(type={}, content={})".format(self.type, self.content)
