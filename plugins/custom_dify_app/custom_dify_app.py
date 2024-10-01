# encoding:utf-8

import plugins
from plugins import *

class DifyAppConf:
    def __init__(self, app_name, app_type, api_base, api_key):
        self.app_name: str = app_name
        self.app_type: str = app_type
        self.api_base: str = api_base
        self.api_key: str = api_key

@plugins.register(
    name="CustomDifyApp",
    desire_priority=0,
    hidden=True,
    enabled=True,
    desc="根据群聊环境自动选择相应的Dify应用",
    version="0.1",
    author="zexin.li",
)
class CustomDifyApp(Plugin):

    def __init__(self):
        super().__init__()
        try:
            self.config = super().load_config()
            self.dify_app_map: dict[str, DifyAppConf] = {}
            self.single_chat_dify_app = None
            self.group_chat_dify_app: dict[str, str] = {}
            if self.config is None:
                logger.info("[CustomDifyApp] config is None")
                return
            self._parse_config()
            logger.info("[CustomDifyApp] inited")
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        except Exception as e:
            logger.error(f"[CustomDifyApp]初始化异常：{e}")
            raise "[CustomDifyApp] init failed, ignore "

    def _parse_config(self):
        for dify_app_config in self.config:
            dify_app_conf = DifyAppConf(
                app_name=dify_app_config["app_name"], app_type=dify_app_config["app_type"],
                api_base=dify_app_config["api_base"], api_key=dify_app_config["api_key"]
            )
            self.dify_app_map[dify_app_conf.api_key] = dify_app_conf

            if "use_on_single_chat" in dify_app_config and dify_app_config["use_on_single_chat"]:
                self.single_chat_dify_app = dify_app_conf.api_key

            if "group_name_list" not in dify_app_config:
                continue

            group_name_list = dify_app_config["group_name_list"]
            for group_name in group_name_list:
                self._add_group_chat_config(group_name, dify_app_conf.api_key)

    def _add_group_chat_config(self, group_name, api_key):
        if isinstance(group_name, str):
            self.group_chat_dify_app[group_name] = api_key
        elif isinstance(group_name, dict):
            keyword = group_name.get("keyword")
            if keyword:
                for existing_group in list(self.group_chat_dify_app.keys()):
                    if keyword in existing_group:
                        self.group_chat_dify_app[existing_group] = api_key
            exact_name = group_name.get("name")
            if exact_name:
                self.group_chat_dify_app[exact_name] = api_key

    def on_handle_context(self, e_context: EventContext):
        if self.config is None:
            return

        context = e_context["context"]
        try:
            if context.get("isgroup", False):
                group_name = context["group_name"]
                dify_app_key = self.group_chat_dify_app[group_name]
                dify_app_conf = self.dify_app_map[dify_app_key]
            else:
                dify_app_conf = self.dify_app_map[self.single_chat_dify_app]
        except:
            dify_app_conf = None

        if dify_app_conf is None:
            return

        logger.info(f"use dify app: {dify_app_conf.app_name}")
        context["dify_app_type"] = dify_app_conf.app_type
        context["dify_api_base"] = dify_app_conf.api_base
        context["dify_api_key"] = dify_app_conf.api_key
