# encoding:utf-8
import json
import os
import html
from urllib.parse import urlparse

import requests

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from plugins import *

@plugins.register(
    name="TransformSharing",
    desire_priority=5,
    hidden=False,
    desc="转换分享链接",
    version="0.0.1",
    author="gadzan",
)
class TransformSharing(Plugin):

    white_url_list = []
    black_url_list = [
        "https://support.weixin.qq.com", # 视频号视频
        "https://channels-aladin.wxqcloud.qq.com", # 视频号音乐
        "https://mp.weixin.qq.com/mp/waerrpage" # 小程序
    ]

    def __init__(self):
        super().__init__()
        try:
            self.config = super().load_config()
            if not self.config:
                self.config = self._load_config_template()
            self.white_url_list = self.config.get("white_url_list", self.white_url_list)
            self.black_url_list = self.config.get("black_url_list", self.black_url_list)
            logger.info(f"[TransformSharing] inited, config={self.config}")
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        except Exception as e:
            logger.error(f"[TransformSharing] 初始化异常：{e}")
            raise "[TransformSharing] init failed, ignore "

    def on_handle_context(self, e_context: EventContext):
        try:
            context = e_context["context"]
            content = context.content
            if context.type != ContextType.SHARING:
                return
            if not self._check_url(content):
                logger.debug(f"[TransformSharing] {content} is not a valid url, skip")
                e_context.action = EventAction.BREAK_PASS
                return
            logger.debug("[TransformSharing] on_handle_context. content: %s" % content)
            reply = Reply(ReplyType.TEXT, "🧐正在阅读您的分享，请稍候...")
            channel = e_context["channel"]
            channel.send(reply, context)

            target_url = html.unescape(content) # 解决公众号卡片链接校验问题，参考 https://github.com/fatwang2/sum4all/commit/b983c49473fc55f13ba2c44e4d8b226db3517c45
            context.content = target_url
            logger.debug(f"[TransformSharing] 转换分享为链接: {context.content}")
        except Exception as e:
            logger.exception(f"[TransformSharing] {str(e)}")
            reply = Reply(ReplyType.ERROR, "我暂时无法处理分享内容，请稍后再试")
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS

    def _load_config_template(self):
        logger.debug("No plugin config.json, use plugins/transform_sharing/config.json.template")
        try:
            plugin_config_path = os.path.join(self.path, "config.json.template")
            if os.path.exists(plugin_config_path):
                with open(plugin_config_path, "r", encoding="utf-8") as f:
                    plugin_conf = json.load(f)
                    return plugin_conf
        except Exception as e:
            logger.exception(e)

    def _check_url(self, target_url: str):
        stripped_url = target_url.strip()
        # 简单校验是否是url
        if not stripped_url.startswith("http://") and not stripped_url.startswith("https://"):
            return False

        # 检查白名单
        if len(self.white_url_list):
            if not any(stripped_url.startswith(white_url) for white_url in self.white_url_list):
                return False

        # 排除黑名单，黑名单优先级>白名单
        for black_url in self.black_url_list:
            if stripped_url.startswith(black_url):
                return False

        return True