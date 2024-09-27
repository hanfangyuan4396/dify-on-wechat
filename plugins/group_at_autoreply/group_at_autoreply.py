import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from plugins import *


@plugins.register(
    name="GroupAtAutoreply",
    desire_priority=900,
    hidden=True,
    enabled=True,
    desc="群聊中出现@某人时，触发某人的自动回复",
    version="0.1",
    author="zexin.li",
)
class GroupAtAutoreply(Plugin):

    def __init__(self):
        super().__init__()
        try:
            self.config = super().load_config()
            logger.info("[GroupAtAutoreply] inited")
            self.handlers[Event.ON_RECEIVE_MESSAGE] = self.on_receive_message
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        except Exception as e:
            logger.error(f"[GroupAtAutoreply]初始化异常：{e}")
            raise "[GroupAtAutoreply] init failed, ignore "

    # 收到消息的时候，直接判断是否需要自动回复，需要的话，直接准备好，放在 context
    def on_receive_message(self, e_context: EventContext):
        context = e_context["context"]
        if context.type != ContextType.TEXT:
            return

        if not context.get("isgroup", False):
            return

        autoreply_members = []
        if isinstance(context["msg"].at_list, list):
            for at in context["msg"].at_list:
                if at in self.config:
                    at_config = self.config[at]
                    if at_config["enabled"]:
                        autoreply_members.append(at)

        if len(autoreply_members) > 0:
            context["autoreply_members"] = autoreply_members
            e_context.action = EventAction.BREAK_PASS

    def include_member(self, member: str):
        if member not in self.config:
            return False
        return self.config[member]["enabled"]

    def cmd_handle(self, cmd: str) -> [bool, str]:
        lines = cmd[1:].split("\n")[1:]

        enabled = None  # 开关
        reply_content = None  # 回复内容

        for line in lines:
            line = line.strip()
            kwarg = line.split(":")
            if len(kwarg) <= 1:
                kwarg = line.split("：")
            key = kwarg[0].strip()
            value = kwarg[1].strip()
            if key == "开关":
                if "打开" == value:
                    enabled = True
                elif "关闭" == value:
                    enabled = False
            elif key == "回复内容":
                reply_content = value

        help_info = """
        参考示例如下：

        #群自动回复
        开关: 打开/关闭
        回复内容: 请稍后联系~
        """
        if enabled is None:
            return False, "指令错误，" + help_info
        if enabled and reply_content is None:
            return False, "缺少回复内容，" + help_info
        if enabled:
            return True, "群自动回复，已开启"
        else:
            return True, "群自动回复，已关闭"

    def on_handle_context(self, e_context: EventContext):
        context = e_context["context"]
        autoreply_members = context["autoreply_members"]
        if autoreply_members is None or len(autoreply_members) == 0:
            return

        reply_text = ""
        for member in autoreply_members:
            member_config = self.config[member]
            if member_config["enabled"]:
                reply_text += f"\n{member}自动回复：{member_config['reply_text']}"

        reply = Reply()
        reply.type = ReplyType.TEXT
        reply.content = reply_text
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS
