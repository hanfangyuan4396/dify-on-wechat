# encoding:utf-8

import plugins
from plugins import *

@plugins.register(
    name="CustomDifyApp",
    desire_priority=0,
    hidden=True,
    enabled=True,
    desc="根据群聊环境自动选择相应的Dify应用",
    version="0.2",
    author="zexin.li, hanfangyuan",
)
class CustomDifyApp(Plugin):

    def __init__(self):
        super().__init__()
        try:
            self.config = super().load_config()
            self.single_chat_conf = None
            if self.config is None:
                logger.info("[CustomDifyApp] config is None")
                return
            self._init_single_chat_conf()
            logger.info("[CustomDifyApp] inited")
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        except Exception as e:
            logger.error(f"[CustomDifyApp]初始化异常：{e}")
            raise "[CustomDifyApp] init failed, ignore "

    def _init_single_chat_conf(self):
        for dify_app_dict in self.config:
            if "use_on_single_chat" in dify_app_dict and dify_app_dict["use_on_single_chat"]:
                self.single_chat_conf = dify_app_dict
                break

    def on_handle_context(self, e_context: EventContext):
        try:
            if self.config is None:
                return

            context = e_context["context"]
            dify_app_conf = None
            if context.get("isgroup", False):
                group_name = context["group_name"]
                for conf in self.config:
                    if "group_name_keywords" in conf:
                        if any(keyword in group_name for keyword in conf["group_name_keywords"]):
                            dify_app_conf = conf
                            break
            else:
                dify_app_conf = self.single_chat_conf

            if dify_app_conf is None:
                return
            if not (dify_app_conf.get("app_type") and dify_app_conf.get("api_base") and dify_app_conf.get("api_key")):
                logger.warning(f"[CustomDifyApp] dify app config is invalid: {dify_app_conf}")
                return

            logger.debug(f"use dify app: {dify_app_conf['app_name']}")
            context["dify_app_type"] = dify_app_conf["app_type"]
            context["dify_api_base"] = dify_app_conf["api_base"]
            context["dify_api_key"] = dify_app_conf["api_key"]
        except Exception as e:
            logger.error(f"[CustomDifyApp] on_handle_context error: {e}")
