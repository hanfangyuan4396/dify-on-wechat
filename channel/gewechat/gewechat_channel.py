import os
import time
import json
import web
from urllib.parse import urlparse

from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel
from channel.gewechat.gewechat_message import GeWeChatMessage
from common.log import logger
from common.singleton import singleton
from common.tmp_dir import TmpDir
from config import conf, save_config
from lib.gewechat import GewechatClient
from voice.audio_convert import mp3_to_silk
import uuid


MAX_UTF8_LEN = 2048

@singleton
class GeWeChatChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()

        self.base_url = conf().get("gewechat_base_url")
        if not self.base_url:
            logger.error("[gewechat] base_url is not set")
            return
        self.token = conf().get("gewechat_token")
        self.client = GewechatClient(self.base_url, self.token)

        # 如果token为空，尝试获取token
        if not self.token:
            logger.warning("[gewechat] token is not set，trying to get token")
            token_resp = self.client.get_token()
            # {'ret': 200, 'msg': '执行成功', 'data': 'tokenxxx'}
            if token_resp.get("ret") != 200:
                logger.error(f"[gewechat] get token failed: {token_resp}")
                return
            self.token = token_resp.get("data")
            conf().set("gewechat_token", self.token)
            save_config()
            logger.info(f"[gewechat] new token saved: {self.token}")
            self.client = GewechatClient(self.base_url, self.token)

        self.app_id = conf().get("gewechat_app_id")
        if not self.app_id:
            logger.warning("[gewechat] app_id is not set，trying to get new app_id when login")

        self.download_url = conf().get("gewechat_download_url")
        if not self.download_url:
            logger.warning("[gewechat] download_url is not set, unable to download image")

        logger.info(f"[gewechat] init: base_url: {self.base_url}, token: {self.token}, app_id: {self.app_id}, download_url: {self.download_url}")

    def startup(self):
        # 如果app_id为空或登录后获取到新的app_id，保存配置
        app_id, error_msg = self.client.login(self.app_id)
        if error_msg:
            logger.error(f"[gewechat] login failed: {error_msg}")
            return

        # 如果原来的self.app_id为空或登录后获取到新的app_id，保存配置
        if not self.app_id or self.app_id != app_id:
            conf().set("gewechat_app_id", app_id)
            save_config()
            logger.info(f"[gewechat] new app_id saved: {app_id}")
            self.app_id = app_id

        # 获取回调地址，示例地址：http://172.17.0.1:9919/v2/api/callback/collect  
        callback_url = conf().get("gewechat_callback_url")
        if not callback_url:
            logger.error("[gewechat] callback_url is not set, unable to start callback server")
            return

        # 创建新线程设置回调地址
        import threading
        def set_callback():
            # 等待服务器启动（给予适当的启动时间）
            import time
            logger.info("[gewechat] sleep 3 seconds waiting for server to start, then set callback")
            time.sleep(3)

            # 设置回调地址，{ "ret": 200, "msg": "操作成功" }
            callback_resp = self.client.set_callback(self.token, callback_url)
            if callback_resp.get("ret") != 200:
                logger.error(f"[gewechat] set callback failed: {callback_resp}")
                return
            logger.info("[gewechat] callback set successfully")

        callback_thread = threading.Thread(target=set_callback, daemon=True)
        callback_thread.start()

        # 从回调地址中解析出端口与url path，启动回调服务器  
        parsed_url = urlparse(callback_url)
        path = parsed_url.path
        # 如果没有指定端口，使用默认端口80
        port = parsed_url.port or 80
        logger.info(f"[gewechat] start callback server: {callback_url}, using port {port}")
        urls = (path, "channel.gewechat.gewechat_channel.Query")
        app = web.application(urls, globals(), autoreload=False)
        web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))

    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        gewechat_message = context.get("msg")
        if reply.type in [ReplyType.TEXT, ReplyType.ERROR, ReplyType.INFO]:
            reply_text = reply.content
            ats = ""
            if gewechat_message and gewechat_message.is_group:
                ats = gewechat_message.actual_user_id
            self.client.post_text(self.app_id, receiver, reply_text, ats)
            logger.info("[gewechat] Do send text to {}: {}".format(receiver, reply_text))
        elif reply.type == ReplyType.VOICE:
            try:
                content = reply.content
                if content.endswith('.mp3'):
                    # 如果是mp3文件，转换为silk格式
                    silk_path = content + '.silk'
                    duration = mp3_to_silk(content, silk_path)
                    callback_url = conf().get("gewechat_callback_url")
                    silk_url = callback_url + "?file=" + silk_path
                    self.client.post_voice(self.app_id, receiver, silk_url, duration)
                    logger.info(f"[gewechat] Do send voice to {receiver}: {silk_url}, duration: {duration/1000.0} seconds")
                    return
                else:
                    logger.error(f"[gewechat] voice file is not mp3, path: {content}, only support mp3")
            except Exception as e:
                logger.error(f"[gewechat] send voice failed: {e}")
        #增加SearchMusic配套代码133-155
        elif reply.type == ReplyType.APP:
            try:
                logger.info("[gewechat] APP message raw content type: {}, content: {}".format(type(reply.content), reply.content))
                
                # 直接使用 XML 内容
                if not isinstance(reply.content, str):
                    logger.error(f"[gewechat] send app message failed: content must be XML string, got type={type(reply.content)}")
                    return
                
                if not reply.content.strip():
                    logger.error("[gewechat] send app message failed: content is empty string")
                    return
                
                # 直接发送 appmsg 内容
                result = self.client.post_app_msg(self.app_id, receiver, reply.content)
                logger.info("[gewechat] sendApp, receiver={}, content={}, result={}".format(
                    receiver, reply.content, result))
                return result
                
            except Exception as e:
                logger.error(f"[gewechat] send app message failed: {str(e)}")
                return             
               
        elif reply.type == ReplyType.IMAGE_URL or reply.type == ReplyType.IMAGE:
            image_storage = reply.content
            if reply.type == ReplyType.IMAGE_URL:
                import requests
                import io
                img_url = reply.content
                logger.debug(f"[gewechat]sendImage, download image start, img_url={img_url}")
                pic_res = requests.get(img_url, stream=True)
                image_storage = io.BytesIO()
                size = 0
                for block in pic_res.iter_content(1024):
                    size += len(block)
                    image_storage.write(block)
                logger.debug(f"[gewechat]sendImage, download image success, size={size}, img_url={img_url}")
                image_storage.seek(0)
                if ".webp" in img_url:
                    try:
                        from common.utils import convert_webp_to_png
                        image_storage = convert_webp_to_png(image_storage)
                    except Exception as e:
                        logger.error(f"[gewechat]sendImage, failed to convert image: {e}")
                        return
            # Save image to tmp directory
            image_storage.seek(0)
            header = image_storage.read(6)
            image_storage.seek(0)
            img_data = image_storage.read()
            image_storage.seek(0)
            extension = ".gif" if header.startswith((b'GIF87a', b'GIF89a')) else ".png"
            img_file_name = f"img_{str(uuid.uuid4())}{extension}"
            img_file_path = TmpDir().path() + img_file_name
            with open(img_file_path, "wb") as f:
                f.write(img_data)
            # Construct callback URL
            callback_url = conf().get("gewechat_callback_url")
            img_url = callback_url + "?file=" + img_file_path
            if extension == ".gif":
                result = self.client.post_file(self.app_id, receiver, file_url=img_url, file_name=img_file_name)
                logger.info("[gewechat] sendGifAsFile, receiver={}, file_url={}, file_name={}, result={}".format(
                    receiver, img_url, img_file_name, result))
            else:
                result = self.client.post_image(self.app_id, receiver, img_url)
                logger.info("[gewechat] sendImage, receiver={}, url={}, result={}".format(receiver, img_url, result))
            if result.get('ret') == 200:
                newMsgId = result['data'].get('newMsgId')
                new_img_file_path = TmpDir().path() + str(newMsgId) + extension
                os.rename(img_file_path, new_img_file_path)
                logger.info("[gewechat] sendImage rename to {}".format(new_img_file_path))
        elif reply.type == ReplyType.XML:
            # XML 类型回复处理
            xml_content = reply.content
            
            # 使用 appmsg.py 中的方法发送卡片消息
            try:
                # 确保 XML 内容格式正确
                # 如果是音乐卡片，将 appid 属性替换为空
                if "<appmsg appid=\"wx5aa333606550dfd5\"" in xml_content:
                    xml_content = xml_content.replace("<appmsg appid=\"wx5aa333606550dfd5\"", "<appmsg appid=\"\"")
                
                # 使用 requests 库发送卡片消息
                import requests
                import json
                
                # 构建完整的 URL
                url = f"{self.base_url}/message/postAppMsg"
                logger.info(f"[gewechat] Sending appmsg to URL: {url}")
                
                # 构建请求数据
                payload = json.dumps({
                    "appId": self.app_id,
                    "toWxid": receiver,
                    "appmsg": xml_content
                })
                
                # 构建请求头
                headers = {
                    'X-GEWE-TOKEN': self.token,
                    'Content-Type': 'application/json'
                }
                
                # 发送请求
                response = requests.post(url, headers=headers, data=payload)
                response_text = response.text
                
                logger.info(f"[gewechat] Do send XML as appmsg to {receiver}, response: {response_text}")
                
                # 如果发送失败，尝试发送文本消息作为备选
                response_json = json.loads(response_text)
                if response_json.get('ret') != 200:
                    raise Exception(f"Failed to send appmsg: {response_text}")
                    
            except Exception as e:
                logger.error(f"[gewechat] Failed to send XML as appmsg: {e}")
                
                # 对于所有类型的 XML，发送通用提示消息
                self.client.post_text(self.app_id, receiver, "[卡片消息] 您的设备不支持显示此类型的消息", "")
                logger.info(f"[gewechat] Do send XML as text to {receiver}: [卡片消息]")

class Query:
    def GET(self):
        # 搭建简单的文件服务器，用于向gewechat服务传输语音等文件，但只允许访问tmp目录下的文件
        params = web.input(file="")
        file_path = params.file
        if file_path:
            # 使用os.path.abspath清理路径
            clean_path = os.path.abspath(file_path)
            # 获取tmp目录的绝对路径
            tmp_dir = os.path.abspath("tmp")
            # 检查文件路径是否在tmp目录下
            if not clean_path.startswith(tmp_dir):
                logger.error(f"[gewechat] Forbidden access to file outside tmp directory: file_path={file_path}, clean_path={clean_path}, tmp_dir={tmp_dir}")
                raise web.forbidden()

            if os.path.exists(clean_path):
                with open(clean_path, 'rb') as f:
                    return f.read()
            else:
                logger.error(f"[gewechat] File not found: {clean_path}")
                raise web.notfound()
        return "gewechat callback server is running"

    def POST(self):
        channel = GeWeChatChannel()
        web_data = web.data()
        logger.debug("[gewechat] receive data: {}".format(web_data))
        data = json.loads(web_data)
        
        # gewechat服务发送的回调测试消息
        if isinstance(data, dict) and 'testMsg' in data and 'token' in data:
            logger.debug(f"[gewechat] 收到gewechat服务发送的回调测试消息")
            return "success"

        gewechat_msg = GeWeChatMessage(data, channel.client)
        
        # 微信客户端的状态同步消息
        if gewechat_msg.ctype == ContextType.STATUS_SYNC:
            logger.debug(f"[gewechat] ignore status sync message: {gewechat_msg.content}")
            return "success"

        # 忽略非用户消息（如公众号、系统通知等）
        if gewechat_msg.ctype == ContextType.NON_USER_MSG:
            logger.debug(f"[gewechat] ignore non-user message from {gewechat_msg.from_user_id}: {gewechat_msg.content}")
            return "success"

        # 判断是否需要忽略语音消息
        if gewechat_msg.ctype == ContextType.VOICE:
            if conf().get("speech_recognition") != True:
                return "success"

        # 忽略来自自己的消息
        if gewechat_msg.my_msg:
            logger.debug(f"[gewechat] ignore message from myself: {gewechat_msg.actual_user_id}: {gewechat_msg.content}")
            return "success"

        # 忽略过期的消息
        if int(gewechat_msg.create_time) < int(time.time()) - 60 * 5: # 跳过5分钟前的历史消息
            logger.debug(f"[gewechat] ignore expired message from {gewechat_msg.actual_user_id}: {gewechat_msg.content}")
            return "success"

        context = channel._compose_context(
            gewechat_msg.ctype,
            gewechat_msg.content,
            isgroup=gewechat_msg.is_group,
            msg=gewechat_msg,
        )
        if context:
            channel.produce(context)
        return "success"
