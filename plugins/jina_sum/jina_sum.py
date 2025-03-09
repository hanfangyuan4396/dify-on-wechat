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
    name="JinaSum",
    desire_priority=10,
    hidden=False,
    enabled=False,
    desc="Sum url link content with jina reader and llm",
    version="0.0.1",
    author="hanfangyuan",
)
class JinaSum(Plugin):
    """使用 Jina Reader 和 LLM 模型对网页内容进行智能总结的插件
    
    功能特点:
    1. 支持处理微信公众号文章、普通网页等多种链接
    2. 使用 Jina Reader 提取网页内容
    3. 使用 LLM 模型生成结构化的总结
    4. 支持白名单和黑名单过滤
    """

    # Jina Reader API 基础URL
    jina_reader_base = "https://r.jina.ai"
    
    # OpenAI API 配置
    open_ai_api_base = "https://api.openai.com/v1"
    open_ai_model = "gpt-3.5-turbo"
    
    # 文本处理配置
    max_words = 8000  # 最大处理字数
    
    # 总结提示词
    prompt = "我需要对下面引号内文档进行总结，总结输出包括以下三个部分：\n"\
            "📖 一句话总结\n"\
            "🔑 关键要点,用数字序号列出3-5个文章的核心内容\n"\
            "🏷 标签: #xx #xx\n"\
            "请使用emoji让你的表达更生动\n\n"
    
    # URL过滤配置
    white_url_list = []  # 白名单，为空表示不启用
    black_url_list = [  # 黑名单，优先级高于白名单
        "https://support.weixin.qq.com",      # 视频号视频
        "https://channels-aladin.wxqcloud.qq.com",  # 视频号音乐
    ]

    def __init__(self):
        """初始化JinaSum插件
        
        加载配置文件，设置必要的API参数和处理函数
        """
        super().__init__()
        try:
            # 加载配置文件
            self.config = super().load_config()
            if not self.config:
                self.config = self._load_config_template()
                
            # 从配置文件中读取各项设置，如果不存在则使用默认值
            self.jina_reader_base = self.config.get("jina_reader_base", self.jina_reader_base)
            self.open_ai_api_base = self.config.get("open_ai_api_base", self.open_ai_api_base)
            self.open_ai_api_key = self.config.get("open_ai_api_key", "")  # API密钥必须在配置文件中指定
            self.open_ai_model = self.config.get("open_ai_model", self.open_ai_model)
            self.max_words = self.config.get("max_words", self.max_words)
            self.prompt = self.config.get("prompt", self.prompt)
            self.white_url_list = self.config.get("white_url_list", self.white_url_list)
            self.black_url_list = self.config.get("black_url_list", self.black_url_list)
            
            # 记录配置信息
            logger.info(f"[JinaSum] 初始化完成，配置信息: {self.config}")
            
            # 注册消息处理函数
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            
        except Exception as e:
            logger.error(f"[JinaSum] 初始化异常：{e}")
            raise Exception("[JinaSum] 初始化失败，跳过此插件")

    def on_handle_context(self, e_context: EventContext, retry_count: int = 0):
        """处理收到的消息事件
        
        Args:
            e_context: 事件上下文，包含消息内容和相关信息
            retry_count: 重试次数，默认为0
        """
        try:
            # 获取消息内容
            context = e_context["context"]
            content = context.content
            
            # 只处理分享类型和文本类型的消息
            if context.type != ContextType.SHARING and context.type != ContextType.TEXT:
                logger.debug(f"[JinaSum] 不支持的消息类型: {context.type}")
                return
                
            # 检查URL是否有效且允许被处理
            if not self._check_url(content):
                logger.debug(f"[JinaSum] 无效或不允许的URL: {content}")
                return
                
            # 首次处理时发送等待提示
            if retry_count == 0:
                logger.debug(f"[JinaSum] 开始处理链接: {content}")
                reply = Reply(ReplyType.TEXT, "🎉正在为您生成总结，请稍候...")
                channel = e_context["channel"]
                channel.send(reply, context)

            # 解决公众号卡片链接中的HTML转义字符问题
            target_url = html.unescape(content)
            
            # 构建Jina Reader的请求URL和参数
            jina_url = self._get_jina_url(target_url)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Content-Type": "application/json"  # Jina Reader现在需要JSON格式的请求体
            }
            # 将目标URL放在请求体中发送
            payload = {"url": target_url}
            
            logger.debug(f"[JinaSum] 发送请求到Jina Reader: {jina_url}")
            try:
                # 发送POST请求到Jina Reader服务
                response = requests.post(jina_url, headers=headers, json=payload, timeout=60)
                
                # 检查HTTP响应状态
                if response.status_code == 404:
                    logger.error(f"[JinaSum] 目标网页不存在: {target_url}")
                    raise requests.exceptions.HTTPError("目标网页不存在或无法访问")
                elif response.status_code == 403:
                    logger.error(f"[JinaSum] 无权访问目标网页: {target_url}")
                    raise requests.exceptions.HTTPError("无权访问目标网页")
                elif response.status_code >= 500:
                    logger.error(f"[JinaSum] Jina Reader服务器错误: {response.status_code}")
                    raise requests.exceptions.HTTPError("Jina Reader服务器内部错误")
                
                response.raise_for_status()  # 处理其他HTTP错误
                
                try:
                    # 解析JSON响应
                    response_json = response.json()
                    target_url_content = response_json.get('text', '')
                    
                    # 验证响应内容
                    if not target_url_content:
                        logger.warning(f"[JinaSum] Jina Reader返回的文本为空: {response_json}")
                        raise ValueError("无法从网页提取有效内容")
                    
                    # 检查文本长度
                    if len(target_url_content.strip()) < 10:  # 假设有效文本至少需要 10 个字符
                        logger.warning(f"[JinaSum] 提取的文本内容过短: {target_url_content}")
                        raise ValueError("网页内容过少，无法生成有效总结")
                        
                    logger.debug(f"[JinaSum] 成功提取网页内容，长度: {len(target_url_content)}")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"[JinaSum] 响应数据不是有效的JSON格式: {str(e)}")
                    raise
                    
            except requests.exceptions.Timeout:
                logger.error(f"[JinaSum] 请求Jina Reader超时: {jina_url}")
                raise
            except requests.exceptions.ConnectionError as e:
                logger.error(f"[JinaSum] 无法连接到Jina Reader服务: {str(e)}")
                raise
            except requests.exceptions.RequestException as e:
                logger.error(f"[JinaSum] Jina Reader请求失败: {str(e)}")
                raise

            # 准备OpenAI API请求
            openai_chat_url = self._get_openai_chat_url()
            openai_headers = self._get_openai_headers()
            openai_payload = self._get_openai_payload(target_url_content)
            logger.debug(f"[JinaSum] 准备发送到OpenAI: URL={openai_chat_url}, 模型={self.open_ai_model}")
            
            try:
                # 检查API密钥是否配置
                if not self.open_ai_api_key:
                    logger.error("[JinaSum] 未配置OpenAI API密钥")
                    raise ValueError("未配置OpenAI API密钥，请先配置")
                
                # 发送请求到OpenAI生成总结
                logger.debug(f"[JinaSum] 发送请求到OpenAI，模型: {self.open_ai_model}, 文本长度: {len(target_url_content)}")
                response = requests.post(
                    openai_chat_url, 
                    headers={**openai_headers, **headers}, 
                    json=openai_payload, 
                    timeout=60
                )
                
                # 检查HTTP响应状态
                if response.status_code == 401:
                    logger.error("[JinaSum] OpenAI API密钥无效")
                    raise requests.exceptions.HTTPError("OpenAI API密钥无效")
                elif response.status_code == 429:
                    logger.error("[JinaSum] OpenAI API请求超过限制")
                    raise requests.exceptions.HTTPError("OpenAI API请求超过限制，请稍后再试")
                elif response.status_code >= 500:
                    logger.error(f"[JinaSum] OpenAI服务器错误: {response.status_code}")
                    raise requests.exceptions.HTTPError("OpenAI服务器内部错误")
                
                response.raise_for_status()  # 处理其他HTTP错误
                
                try:
                    # 解析JSON响应
                    response_json = response.json()
                    
                    # 检查是否存在错误信息
                    if 'error' in response_json:
                        error_msg = response_json['error'].get('message', '未知错误')
                        logger.error(f"[JinaSum] OpenAI API返回错误: {error_msg}")
                        raise ValueError(f"OpenAI API错误: {error_msg}")
                    
                    # 提取总结内容
                    result = response_json['choices'][0]['message']['content']
                    
                    # 验证总结内容
                    if not result or len(result.strip()) < 10:
                        logger.warning(f"[JinaSum] OpenAI返回的总结内容过短: {result}")
                        raise ValueError("生成的总结内容过短，请重试")
                    
                    logger.debug(f"[JinaSum] 成功生成总结，长度: {len(result)}")
                    
                    # 设置回复
                    reply = Reply(ReplyType.TEXT, result)
                    e_context["reply"] = reply
                    e_context.action = EventAction.BREAK_PASS
                    
                except json.JSONDecodeError as e:
                    logger.error(f"[JinaSum] OpenAI响应不是有效的JSON格式: {str(e)}")
                    raise
                except (KeyError, IndexError) as e:
                    logger.error(f"[JinaSum] OpenAI响应格式错误: {str(e)}")
                    raise ValueError("OpenAI响应格式错误")
                    
            except requests.exceptions.Timeout:
                logger.error(f"[JinaSum] 请求OpenAI超时: {openai_chat_url}")
                raise
            except requests.exceptions.ConnectionError as e:
                logger.error(f"[JinaSum] 无法连接到OpenAI服务: {str(e)}")
                raise
            except requests.exceptions.RequestException as e:
                logger.error(f"[JinaSum] OpenAI API请求失败: {str(e)}")
                raise

        except Exception as e:
            # 当重试次数小于3次时，判断是否需要重试
            if retry_count < 3:
                # 某些错误不需要重试
                if isinstance(e, (ValueError, json.JSONDecodeError)):
                    logger.warning(f"[JinaSum] 遇到不需要重试的错误: {str(e)}")
                else:
                    logger.warning(f"[JinaSum] 处理失败，准备第{retry_count + 1}次重试: {str(e)}")
                    self.on_handle_context(e_context, retry_count + 1)
                    return

            # 超过最大重试次数或不需要重试，记录错误并返回错误信息
            logger.exception(f"[JinaSum] 处理失败: {str(e)}")
            
            # 根据错误类型返回不同的错误信息
            error_message = "我暂时无法总结链接"
            retry_suggestion = "，请稍后再试"
            
            if isinstance(e, requests.exceptions.Timeout):
                error_message += "，请求超时了" + retry_suggestion
            elif isinstance(e, requests.exceptions.ConnectionError):
                error_message += "，网络连接出现问题" + retry_suggestion
            elif isinstance(e, requests.exceptions.HTTPError):
                if "401" in str(e):
                    error_message += "，API密钥无效，请联系管理员检查配置"
                elif "429" in str(e):
                    error_message += "，请求频率超过限制，请稍后再试"
                elif "500" in str(e):
                    error_message += "，服务器内部错误" + retry_suggestion
                else:
                    error_message += "，服务器响应异常" + retry_suggestion
            elif isinstance(e, (KeyError, IndexError)):
                error_message += "，服务器响应格式不符合预期" + retry_suggestion
            elif isinstance(e, json.JSONDecodeError):
                error_message += "，服务器响应数据格式错误" + retry_suggestion
            elif isinstance(e, ValueError):
                if "未配置OpenAI API密钥" in str(e):
                    error_message += "，请先配置OpenAI API密钥"
                elif "无法提取网页内容" in str(e):
                    error_message += "，无法从目标网页提取有效内容，请检查链接是否有效"
                elif "网页内容过少" in str(e):
                    error_message += "，网页内容太少，无法生成有效总结"
                else:
                    error_message += "，" + str(e)
            else:
                error_message += "，发生未知错误" + retry_suggestion
            
            reply = Reply(ReplyType.ERROR, error_message)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS

    def get_help_text(self, verbose, **kwargs):
        """获取插件的帮助文本
        
        Args:
            verbose: 是否显示详细信息
            **kwargs: 额外的参数
            
        Returns:
            str: 插件的功能描述
        """
        return f'使用jina reader和ChatGPT总结网页链接内容'

    def _load_config_template(self) -> dict:
        """加载插件的配置模板
        
        当插件没有config.json文件时，尝试从 config.json.template 加载默认配置
        
        Returns:
            dict: 插件的配置字典，如果加载失败则返回空字典
        """
        logger.debug("[JinaSum] 未找到config.json，尝试加载 config.json.template")
        
        try:
            # 构建模板文件路径
            plugin_config_path = os.path.join(self.path, "config.json.template")
            
            # 检查模板文件是否存在
            if os.path.exists(plugin_config_path):
                logger.debug(f"[JinaSum] 找到配置模板文件: {plugin_config_path}")
                
                # 读取并解析JSON文件
                with open(plugin_config_path, "r", encoding="utf-8") as f:
                    plugin_conf = json.load(f)
                    logger.debug(f"[JinaSum] 成功加载配置模板: {plugin_conf}")
                    return plugin_conf
            else:
                logger.warning(f"[JinaSum] 未找到配置模板文件: {plugin_config_path}")
                
        except json.JSONDecodeError as e:
            logger.error(f"[JinaSum] 配置模板文件JSON格式错误: {str(e)}")
        except Exception as e:
            logger.exception(f"[JinaSum] 加载配置模板失败: {str(e)}")
            
        # 如果加载失败，返回空字典
        return {}

    def _get_jina_url(self, target_url):
        """构建Jina Reader的URL
        Args:
            target_url: 需要解析的目标URL
        Returns:
            完整的Jina Reader请求URL
        """
        return self.jina_reader_base + "/" + target_url

    def _get_openai_chat_url(self):
        """构建OpenAI聊天请求的URL
        Returns:
            str: OpenAI API的完整URL
        """
        return self.open_ai_api_base + "/chat/completions"

    def _get_openai_headers(self):
        """构建OpenAI API请求所需的头部
        Returns:
            dict: 包含认证信息和主机信息的头部字典
        """
        return {
            'Authorization': f"Bearer {self.open_ai_api_key}",  # OpenAI认证令牌
            'Host': urlparse(self.open_ai_api_base).netloc  # 从基础URL中提取主机名
        }

    def _get_openai_payload(self, target_url_content):
        """构建OpenAI API的请求载荷
        
        Args:
            target_url_content: 需要总结的文本内容
            
        Returns:
            dict: OpenAI API请求的参数字典
        """
        # 限制文本长度，防止超过API限制
        target_url_content = target_url_content[:self.max_words]
        
        # 构建提示词和文本内容
        sum_prompt = f"{self.prompt}\n\n'''{target_url_content}'''"
        messages = [{"role": "user", "content": sum_prompt}]
        
        # 组装API请求参数
        payload = {
            'model': self.open_ai_model,  # 使用配置的模型
            'messages': messages  # 对话历史
        }
        return payload

    def _check_url(self, target_url: str):
        """检查URL是否有效且允许被处理
        
        Args:
            target_url: 待检查的URL字符串
            
        Returns:
            bool: URL是否可以被处理
        """
        stripped_url = target_url.strip()
        
        # 基本URL格式检查
        if not stripped_url.startswith("http://") and not stripped_url.startswith("https://"):
            return False

        # 白名单检查：如果设置了白名单，URL必须在白名单中
        if len(self.white_url_list):
            if not any(stripped_url.startswith(white_url) for white_url in self.white_url_list):
                return False

        # 黑名单检查：黑名单优先级高于白名单
        # 如果URL在黑名单中，直接拒绝处理
        for black_url in self.black_url_list:
            if stripped_url.startswith(black_url):
                return False

        return True
