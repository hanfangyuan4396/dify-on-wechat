
import requests
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from voice.voice import Voice
import datetime
import random

class DifyVoice(Voice):
    def __init__(self):
        self.api_key = conf().get("dify_api_key")
        self.api_base = conf().get("dify_api_base") or "http://dify.hanfangyuan.cn/v1"

    def voiceToText(self, voice_file):
        logger.debug("[Dify] voice file name={}".format(voice_file))
        try:
            files = {
                'file': open(voice_file, 'rb')
            }
            data = {
                'user': 'user_id'  # 请根据实际情况替换为正确的用户标识
            }
            headers = {
                'Authorization': 'Bearer ' + self.api_key
            }
            response = requests.post(
                f'{self.api_base}/audio-to-text',
                headers=headers,
                files=files,
                data=data
            )
            response_data = response.json()
            text = response_data['text']
            reply = Reply(ReplyType.TEXT, text)
            logger.info("[Dify] voiceToText text={} voice file name={}".format(text, voice_file))
        except Exception as e:
            logger.error(e)
            reply = Reply(ReplyType.ERROR, "我暂时还无法听清您的语音，请稍后再试吧~")
        return reply

    def textToVoice(self, text):
        logger.debug("[Dify] text={}".format(text))
        try:
            data = {
                'text': text,
                'user': 'user_id'  # 请根据实际情况替换为正确的用户标识
            }
            headers = {
                'Authorization': 'Bearer ' + self.api_key,
                'Content-Type': 'application/json'
            }
            response = requests.post(
                f'{self.api_base}/text-to-audio',
                headers=headers,
                json=data
            )
            file_name = "tmp/" + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(0, 1000)) + ".wav"
            with open(file_name, 'wb') as f:
                f.write(response.content)
            logger.info("[Dify] textToVoice success, file_name={}".format(file_name))
            reply = Reply(ReplyType.VOICE, file_name)
        except Exception as e:
            logger.error(e)
            reply = Reply(ReplyType.ERROR, "遇到了一点小问题，请稍后再问我吧")
        return reply