from bot.session_manager import Session
from common.log import logger
from config import conf


class DeepseekSession(Session):
    def __init__(self, session_id, system_prompt=None):
        super().__init__(session_id, system_prompt)
        self.reset()

    def reset(self):
        self.messages = []
        system_prompt = self.system_prompt
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})
        return self

    def add_query(self, query):
        """添加用户的输入"""
        self.messages.append({"role": "user", "content": query})

    def add_reply(self, reply):
        """添加机器人的回复"""
        if reply and reply.strip():
            self.messages.append({"role": "assistant", "content": reply})

    def discard_exceeding(self, max_tokens=None, cur_tokens=None):
        """丢弃超出最大记忆长度的消息"""
        max_tokens = max_tokens if max_tokens else 4000
        cur_tokens = cur_tokens if cur_tokens else self.calc_tokens()
        if cur_tokens > max_tokens:
            for i in range(0, len(self.messages)):
                if i > 0:
                    if "role" in self.messages[i] and self.messages[i]["role"] == "system":
                        continue
                    self.messages.pop(i)
                    return True
        return False

    def calc_tokens(self):
        """计算当前会话的token数量"""
        return len(str(self.messages))

    def get_messages(self):
        """获取当前会话中的所有消息"""
        return self.messages 