"""
Message sending channel abstract class
"""

from bridge.bridge import Bridge
from bridge.context import Context
from bridge.reply import *


class Channel(object):
    channel_type = ""
    NOT_SUPPORT_REPLYTYPE = [ReplyType.VOICE, ReplyType.IMAGE]

    def startup(self):
        """
        init channel
        """
        raise NotImplementedError

    def handle_text(self, msg):
        """
        process received msg
        :param msg: message object
        """
        raise NotImplementedError

    # 统一的发送函数，每个Channel自行实现，根据reply的type字段发送不同类型的消息
    def send(self, reply: Reply, context: Context):
        """
        send message to user
        :param msg: message content
        :param receiver: receiver channel account
        :return:
        """
        raise NotImplementedError

    def build_reply_content(self, query, context: Context = None) -> Reply:
        # 添加命令处理的优先级检查
        if context and context.get("isgroup", False):
            # 检查是否是点歌命令
            if query.startswith("酷狗点歌") or query.startswith("网易点歌"):
                context["type"] = "music_search"
                return Bridge().fetch_reply_content(query, context)
        
        return Bridge().fetch_reply_content(query, context)

    def build_voice_to_text(self, voice_file) -> Reply:
        return Bridge().fetch_voice_to_text(voice_file)

    def build_text_to_voice(self, text) -> Reply:
        return Bridge().fetch_text_to_voice(text)
