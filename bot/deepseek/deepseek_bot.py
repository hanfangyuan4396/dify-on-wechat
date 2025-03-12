# encoding:utf-8

import time
import openai

from bot.bot import Bot
from bot.deepseek.deepseek_session import DeepseekSession
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf

user_session = dict()


# Deepseek对话模型API
class DeepseekBot(Bot):
    def __init__(self):
        super().__init__()
        openai.api_key = conf().get("open_ai_api_key")
        openai.api_base = conf().get("open_ai_api_base", "https://api.deepseek.com/v1")
        
        # 配置代理
        proxy = conf().get("proxy")
        if proxy:
            openai.proxy = proxy
            
        self.sessions = SessionManager(DeepseekSession)
        
        # Deepseek API参数
        self.args = {
            "model": conf().get("model", "deepseek-chat"),
            "temperature": conf().get("temperature", 0.7),
            "max_tokens": conf().get("conversation_max_tokens", 4000),
            "top_p": conf().get("top_p", 1),
            "frequency_penalty": conf().get("frequency_penalty", 0.0),
            "presence_penalty": conf().get("presence_penalty", 0.0),
            "request_timeout": conf().get("request_timeout", 180),
        }

    def reply(self, query, context=None):
        # 处理查询请求
        if context and context.type:
            if context.type == ContextType.TEXT:
                logger.info("[DEEPSEEK] query={}".format(query))
                session_id = context["session_id"]
                reply = None
                
                if query == "#清除记忆":
                    self.sessions.clear_session(session_id)
                    reply = Reply(ReplyType.INFO, "记忆已清除")
                    return reply
                    
                session = self.sessions.session_query(query, session_id)
                
                reply_content = self.reply_text(session)
                
                if reply_content:
                    # 将回复添加到会话中
                    session.add_reply(reply_content)
                    
                    logger.info("[DEEPSEEK] new reply={}".format(reply_content))
                    reply = Reply(ReplyType.TEXT, reply_content)
                else:
                    logger.error("[DEEPSEEK] reply content is empty")
                    reply = Reply(ReplyType.ERROR, "对不起，我没有得到有效的回复。")
                    
                return reply
            elif context.type == ContextType.IMAGE_CREATE:
                # 不支持图像创建
                reply = Reply(ReplyType.ERROR, "抱歉，Deepseek模型暂不支持图像创建。")
                return reply
        return Reply(ReplyType.ERROR, "处理消息失败")

    def reply_text(self, session: DeepseekSession, retry_count=0):
        """使用Deepseek API生成回复"""
        try:
            messages = session.get_messages()
            logger.debug("[DEEPSEEK] session messages={}".format(messages))
            
            # 调用API获取回复 - 使用旧版本OpenAI API格式
            response = openai.ChatCompletion.create(
                model=self.args["model"],
                messages=messages,
                temperature=self.args["temperature"],
                max_tokens=self.args["max_tokens"],
                top_p=self.args["top_p"],
                frequency_penalty=self.args["frequency_penalty"],
                presence_penalty=self.args["presence_penalty"],
                request_timeout=self.args["request_timeout"]
            )
            
            # 提取回复内容
            reply_content = response.choices[0].message.content
            return reply_content
            
        except Exception as e:
            # 处理异常情况
            logger.error("[DEEPSEEK] Exception: {}".format(e))
            if retry_count < 2:
                logger.warn("[DEEPSEEK] 第{}次重试".format(retry_count + 1))
                time.sleep(3)
                return self.reply_text(session, retry_count + 1)
            else:
                return "抱歉，我遇到了问题，请稍后再试。" 