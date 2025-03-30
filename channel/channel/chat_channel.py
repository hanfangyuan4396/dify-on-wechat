import os
import random
import re
import threading
import time
from asyncio import CancelledError
from concurrent.futures import Future, ThreadPoolExecutor

from bridge.context import *
from bridge.reply import *
from channel.channel import Channel
from common.dequeue import Dequeue
from config import conf, config
from plugins import *

try:
    from voice.audio_convert import any_to_wav
except Exception as e:
    pass


# 抽象类, 它包含了与消息通道无关的通用处理逻辑
class ChatChannel(Channel):
    name = None  # 登录的用户名
    user_id = None  # 登录的用户id
    futures = {}  # 记录每个session_id提交到线程池的future对象, 用于重置会话时把没执行的future取消掉，正在执行的不会被取消
    sessions = {}  # 用于控制并发，每个session_id同时只能有一个context在处理
    lock = threading.Lock()  # 用于控制对sessions的访问
    handler_pool = ThreadPoolExecutor(max_workers=8)  # 处理消息的线程池

    def __init__(self):
        self.should_stop = False
        _thread = threading.Thread(target=self.consume)
        _thread.setDaemon(True)
        _thread.start()

    # 根据消息构造context，消息内容相关的触发项写在这里
    def _compose_context(self, ctype: ContextType, content, **kwargs):
        config = conf()
        context = Context(ctype, content)
        context.kwargs = kwargs
        # context首次传入时，origin_ctype是None,
        # 引入的起因是：当输入语音时，会嵌套生成两个context，第一步语音转文本，第二步通过文本生成文字回复。
        # origin_ctype用于第二步文本回复时，判断是否需要匹配前缀，如果是私聊的语音，就不需要匹配前缀
        if "origin_ctype" not in context:
            context["origin_ctype"] = ctype
        # context首次传入时，receiver是None，根据类型设置receiver
        first_in = "receiver" not in context
        # 群名匹配过程，设置session_id和receiver
        if first_in:  # context首次传入时，receiver是None，根据类型设置receiver
            config = conf()
            cmsg = context["msg"]
            user_data = conf().get_user_data(cmsg.from_user_id)
            context["openai_api_key"] = user_data.get("openai_api_key")
            context["gpt_model"] = user_data.get("gpt_model")
            if context.get("isgroup", False):
                group_name = cmsg.other_user_nickname
                group_id = cmsg.other_user_id
                logger.debug(f"正在处理群组消息，群名：{group_name}, 群ID：{group_id}")
                # print(f"正在处理群组消息，群名：{group_name}, 群ID：{group_id}")
                group_name_white_list = config.get("group_name_white_list", [])
                group_name_keyword_white_list = config.get("group_name_keyword_white_list", [])

                if any(
                        [
                            group_name in group_name_white_list,
                            "ALL_GROUP" in group_name_white_list,
                            check_contain(group_name, group_name_keyword_white_list),
                        ]
                ):
                    group_chat_in_one_session = conf().get("group_chat_in_one_session", [])
                    session_id = cmsg.actual_user_id
                    if session_id is None or session_id == "":
                        session_id = group_id
                    if any(
                            [
                                group_name in group_chat_in_one_session,
                                "ALL_GROUP" in group_chat_in_one_session,
                            ]
                    ):
                        session_id = group_id

                else:
                    return None
                context["session_id"] = session_id
                context["receiver"] = group_id
            else:
                context["session_id"] = cmsg.other_user_id
                context["receiver"] = cmsg.other_user_id

            logger.debug(f"最终的会话ID：{context['session_id']}")
            logger.debug(f"最终的接收者ID：{context['receiver']}")
            e_context = PluginManager().emit_event(
                EventContext(Event.ON_RECEIVE_MESSAGE, {"channel": self, "context": context}))
            context = e_context["context"]
            if e_context.is_pass() or context is None:
                return context

            if cmsg.from_user_id == self.user_id and not config.get("trigger_by_self", False):
                logger.debug("[WX]self message skipped")
                return None

        # 消息内容匹配过程，并处理content
        if ctype == ContextType.TEXT:
            # if first_in and "」\n- - - - - - -" in content:  # 初次匹配 过滤引用消息
            #     start_idx = content.find("「") + 1  # 找到「的位置
            #     end_idx = content.find("：", start_idx)  # 找到：的位置
            #     result = content[:start_idx] + content[end_idx+1:]  # 将两部分字符串拼接起来
            #     content=result
                #print(content)  # 输出结果

            if context.get("isgroup", False):  # 群聊
                match_prefix = check_prefix(content, conf().get("group_chat_prefix"))
                match_suffix = check_suffix(content, conf().get("group_chat_suffix"))
                match_contain = check_contain(content, conf().get("group_chat_keyword"))
                group_userid_black_list = config.get("group_userid_black_list", [])
                flag = False
                if match_prefix is not None or match_contain is not None or match_suffix is not None :
                    flag = True
                    if match_prefix:
                        content = content.replace(match_prefix, "", 1).strip()
                if context["msg"].is_at:
                    logger.info("[WX]receive group at")
                    # 群用户ID黑名单
                    if context["msg"].actual_user_id in group_userid_black_list:
                        logger.info("[WX]该用户在黑名单中，不作回复")
                        return None
                    if not conf().get("group_at_off", False):
                        flag = True
                    # 确保self.name不为None，避免re.escape出错
                    if self.name is not None:
                        pattern = f"@{re.escape(self.name)}(\u2005|\u0020)"
                    else:
                        pattern = "@(\u2005|\u0020)"  # 如果self.name为None，使用一个通用模式
                    subtract_res = re.sub(pattern, r"", content)
                    if subtract_res == content and context["msg"].self_display_name:
                        pattern = f"@{re.escape(context['msg'].self_display_name)}(\u2005|\u0020)"
                        subtract_res = re.sub(pattern, r"", subtract_res)
                    if subtract_res == content and context["msg"].self_display_name:
                        # 前缀移除后没有变化，使用群昵称再次移除
                        pattern = f"@{re.escape(context['msg'].self_display_name)}(\u2005|\u0020)"
                        subtract_res = re.sub(pattern, r"", content)
                    content = subtract_res
                if not flag:
                    if context["origin_ctype"] == ContextType.VOICE:
                        logger.info("[WX]发现群内语音, 但无触发前缀，bot不回复")
                    return None

            else:  # 单聊
                match_prefix = check_prefix(content, conf().get("single_chat_prefix", [""]))
                if match_prefix is not None:  # 判断如果匹配到自定义前缀，则返回过滤掉前缀+空格后的内容
                    content = content.replace(match_prefix, "", 1).strip()
                elif context["origin_ctype"] == ContextType.VOICE:  # 如果源消息是私聊的语音消息，允许不匹配前缀，放宽条件
                    pass
                else:
                    return None
            content = content.strip()
            img_match_prefix = check_prefix(content, conf().get("image_create_prefix"))
            if img_match_prefix:
                content = content.replace(img_match_prefix, "", 1)
                context.type = ContextType.IMAGE_CREATE
            else:
                context.type = ContextType.TEXT
            context.content = content.strip()
            if "desire_rtype" not in context and conf().get(
                    "always_reply_voice") and ReplyType.VOICE not in self.NOT_SUPPORT_REPLYTYPE:
                context["desire_rtype"] = ReplyType.VOICE
        elif ctype == ContextType.QUOTE:
            cmsg = context["msg"]
            refname_text = cmsg.to_user_id
            msg_text = content
            if refname_text == self.user_id:
                context.content = msg_text
                context.type = ContextType.TEXT
            else:
                # 如果不是AI，则可能忽略这条消息或使用不同的逻辑处理
                return None  # 忽略或替换为其他处理逻辑
        elif ctype == ContextType.WCPAY:
            pass
            # msg_text = content
        elif ctype == ContextType.MP:
            return
        elif ctype == ContextType.LEAVE_GROUP:
            pass
        elif ctype == ContextType.EXIT_GROUP:
            pass
        elif context.type == ContextType.VOICE:
            if "desire_rtype" not in context and conf().get(
                    "voice_reply_voice") and ReplyType.VOICE not in self.NOT_SUPPORT_REPLYTYPE:
                context["desire_rtype"] = ReplyType.VOICE

        return context

    def _handle(self, context: Context):
        if context is None or not context.content:
            return
        logger.debug("[WX] ready to handle context: {}".format(context))
        # reply的构建步骤
        reply = self._generate_reply(context)

        logger.debug("[WX] ready to decorate reply: {}".format(reply))
        # reply的包装步骤
        reply = self._decorate_reply(context, reply)

        # reply的发送步骤
        self._send_reply(context, reply)

    def _generate_reply(self, context: Context, reply: Reply = Reply()) -> Reply:
        e_context = PluginManager().emit_event(
            EventContext(
                Event.ON_HANDLE_CONTEXT,
                {"channel": self, "context": context, "reply": reply},
            )
        )
        reply = e_context["reply"]
        if not e_context.is_pass():
            logger.debug("[WX] ready to handle context: type={}, content={}".format(context.type, context.content))
            if e_context.is_break():
                context["generate_breaked_by"] = e_context["breaked_by"]
            if context.type == ContextType.TEXT or context.type == ContextType.IMAGE_CREATE:  # 文字和图片消息
                reply = super().build_reply_content(context.content, context)
            elif context.type == ContextType.VOICE:  # 语音消息
                cmsg = context["msg"]
                cmsg.prepare()
                file_path = context.content
                wav_path = os.path.splitext(file_path)[0] + ".wav"
                try:
                    any_to_wav(file_path, wav_path)
                except Exception as e:  # 转换失败，直接使用mp3，对于某些api，mp3也可以识别
                    logger.warning("[WX]any to wav error, use raw path. " + str(e))
                    wav_path = file_path
                # 语音识别
                reply = super().build_voice_to_text(wav_path)
                # 删除临时文件
                try:
                    os.remove(file_path)
                    if wav_path != file_path:
                        os.remove(wav_path)
                except Exception as e:
                    pass
                    # logger.warning("[WX]delete temp file error: " + str(e))

                if reply.type == ReplyType.TEXT:
                    new_context = self._compose_context(ContextType.TEXT, reply.content, **context.kwargs)
                    if new_context:
                        reply = self._generate_reply(new_context)
                    else:
                        return
            elif context.type == ContextType.IMAGE:
                cmsg = context["msg"]
                cmsg.prepare()
            elif context.type == ContextType.LEAVE_GROUP:
                if config.get("group_chat_exit_group"):
                    reply = Reply()
                    reply.type = ReplyType.INFO
                    reply.content = context.content
                else:
                    pass
            elif context.type == ContextType.FUNCTION or context.type == ContextType.FILE:  # 文件消息及函数调用等，当前无默认逻辑
                pass
            # 未来可自定义逻辑
            elif context.type == ContextType.XML:
                pass
            elif context.type == ContextType.SHARING:
                pass
            elif context.type == ContextType.CARD:
                pass
            elif context.type == ContextType.VIDEO:
                pass
            elif context.type == ContextType.EMOJI:
                pass
            elif context.type == ContextType.PATPAT:
                pass
            elif context.type == ContextType.QUOTE:
                pass
            elif context.type == ContextType.MINIAPP:
                pass
            elif context.type == ContextType.JOIN_GROUP:
                pass
            elif context.type == ContextType.EXIT_GROUP:
                pass
            elif context.type == ContextType.SYSTEM:
                pass
            elif context.type == ContextType.WCPAY:
                pass
            elif context.type == ContextType.WECHAT_VIDEO:
                pass
            elif context.type == ContextType.MP:
                pass
            elif context.type == ContextType.MP_LINK:
                pass
            else:
                logger.error("[WX] unknown context type: {}".format(context.type))
                return
        return reply

    def _decorate_reply(self, context: Context, reply: Reply) -> Reply:
        if reply and reply.type:
            e_context = PluginManager().emit_event(
                EventContext(
                    Event.ON_DECORATE_REPLY,
                    {"channel": self, "context": context, "reply": reply},
                )
            )
            reply = e_context["reply"]
            desire_rtype = context.get("desire_rtype")
            logger.debug(f"context:{context}")
            if not e_context.is_pass() and reply and reply.type:
                if reply.type in self.NOT_SUPPORT_REPLYTYPE:
                    logger.error("[WX]reply type not support: " + str(reply.type))
                    reply.type = ReplyType.ERROR
                    reply.content = "不支持发送的消息类型: " + str(reply.type)

                if reply.type == ReplyType.TEXT:
                    reply_text = reply.content
                    if desire_rtype == ReplyType.VOICE and ReplyType.VOICE not in self.NOT_SUPPORT_REPLYTYPE:
                        reply = super().build_text_to_voice(reply.content)
                        return self._decorate_reply(context, reply)
                    if context.get("isgroup", False):
                        nickname = context["msg"].actual_user_nickname if context["msg"].actual_user_nickname is not None else "提问用户"
                        reply_text = "@" + context["msg"].actual_user_nickname + "\n" + reply_text.strip()
                        reply_text = conf().get("group_chat_reply_prefix", "") + reply_text + conf().get(
                            "group_chat_reply_suffix", "")
                    else:
                        reply_text = conf().get("single_chat_reply_prefix", "") + reply_text + conf().get(
                            "single_chat_reply_suffix", "")
                    reply.content = reply_text

                elif reply.type == ReplyType.ERROR or reply.type == ReplyType.INFO:
                    reply.content = "[" + str(reply.type) + "]\n" + reply.content
                elif reply.type == ReplyType.IMAGE_URL or reply.type == ReplyType.VOICE or reply.type == ReplyType.IMAGE:
                    pass
                elif reply.type == ReplyType.VIDEO_URL:
                    pass
                elif reply.type == ReplyType.CARD:
                    pass
                elif reply.type == ReplyType.InviteRoom:
                    pass
                elif reply.type == ReplyType.TEXT_:
                    pass
                elif reply.type == ReplyType.FILE:
                    pass
                elif reply.type == ReplyType.MINIAPP:
                    pass
                elif reply.type == ReplyType.LINK:
                    pass
                elif reply.type == ReplyType.CALL_UP:
                    pass
                elif reply.type == ReplyType.GIF:
                    pass
                elif reply.type == ReplyType.XML:
                    # XML 类型回复不需要额外处理，直接传递给发送方法
                    pass
                else:
                    logger.error("[WX] unknown reply type: {}".format(reply.type))
                    return
            if desire_rtype and desire_rtype != reply.type and reply.type not in [ReplyType.ERROR, ReplyType.INFO]:
                logger.warning(
                    "[WX] desire_rtype: {}, but reply type: {}".format(context.get("desire_rtype"), reply.type))
            return reply

    def _send_reply(self, context: Context, reply: Reply):
        if reply and reply.type:
            e_context = PluginManager().emit_event(
                EventContext(
                    Event.ON_SEND_REPLY,
                    {"channel": self, "context": context, "reply": reply},
                )
            )
            reply = e_context["reply"]
            if not e_context.is_pass() and reply and reply.type:
                logger.debug("[WX] ready to send reply: {}, context: {}".format(reply, context))
                self._send(reply, context)

    def _send(self, reply: Reply, context: Context, retry_cnt=0):
        try:
            self.send(reply, context)
        except Exception as e:
            logger.error("[WX] sendMsg error: {}".format(str(e)))
            if isinstance(e, NotImplementedError):
                return
            logger.exception(e)
            if retry_cnt < 2:
                time.sleep(3 + 3 * retry_cnt)
                self._send(reply, context, retry_cnt + 1)

    def _success_callback(self, session_id, **kwargs):  # 线程正常结束时的回调函数
        logger.debug("Worker return success, session_id = {}".format(session_id))

    def _fail_callback(self, session_id, exception, **kwargs):  # 线程异常结束时的回调函数
        logger.exception("Worker return exception: {}".format(exception))

    def _thread_pool_callback(self, session_id, **kwargs):
        def func(worker: Future):
            try:
                worker_exception = worker.exception()
                if worker_exception:
                    self._fail_callback(session_id, exception=worker_exception, **kwargs)
                else:
                    self._success_callback(session_id, **kwargs)
            except CancelledError as e:
                logger.info("Worker cancelled, session_id = {}".format(session_id))
            except Exception as e:
                logger.exception("Worker raise exception: {}".format(e))
            with self.lock:
                self.sessions[session_id][1].release()
            ###

        return func

    def produce(self, context: Context):
        session_id = context["session_id"]
        # print(self.sessions)
        with self.lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = [
                    Dequeue(),
                    threading.BoundedSemaphore(conf().get("concurrency_in_session", 4)),
                ]
            if context.type == ContextType.TEXT and context.content.startswith("#"):
                self.sessions[session_id][0].putleft(context)  # 优先处理管理命令
            else:
                self.sessions[session_id][0].put(context)

    # 消费者函数，单独线程，用于从消息队列中取出消息并处理
    def consume(self):
        logger.debug("[ChatChannel] consume method started.")
        while True:
            with self.lock:
                session_ids = list(self.sessions.keys())
                for session_id in session_ids:
                    context_queue, semaphore = self.sessions[session_id]
                    if semaphore.acquire(blocking=False):  # 等线程处理完毕才能删除
                        if not context_queue.empty():
                            context = context_queue.get()
                            future: Future = self.handler_pool.submit(self._handle, context)
                            future.add_done_callback(self._thread_pool_callback(session_id, context=context))
                            if session_id not in self.futures:
                                self.futures[session_id] = []
                            self.futures[session_id].append(future)
                        elif semaphore._initial_value == semaphore._value + 1:  # 除了当前，没有任务再申请到信号量，说明所有任务都处理完毕
                            self.futures[session_id] = [t for t in self.futures[session_id] if not t.done()]
                            assert len(self.futures[session_id]) == 0, "thread pool error"
                            del self.sessions[session_id]
                        else:
                            semaphore.release()
            time.sleep(0.1)

    # 取消session_id对应的所有任务，只能取消排队的消息和已提交线程池但未执行的任务
    def cancel_session(self, session_id):
        with self.lock:
            if session_id in self.sessions:
                for future in self.futures[session_id]:
                    future.cancel()
                cnt = self.sessions[session_id][0].qsize()
                if cnt > 0:
                    logger.info("Cancel {} messages in session {}".format(cnt, session_id))
                self.sessions[session_id][0] = Dequeue()

    def cancel_all_session(self):
        with self.lock:
            for session_id in self.sessions:
                for future in self.futures[session_id]:
                    future.cancel()
                cnt = self.sessions[session_id][0].qsize()
                if cnt > 0:
                    logger.info("Cancel {} messages in session {}".format(cnt, session_id))
                self.sessions[session_id][0] = Dequeue()

    def stop(self):
        self.should_stop = True


def check_prefix(content, prefix_list):
    if not prefix_list:
        return None
    for prefix in prefix_list:
        if content.lower().startswith(prefix):
            return prefix
    return None
def check_suffix(content, prefix_list):
    if not prefix_list:
        return None
    for prefix in prefix_list:
        if content.lower().endswith(prefix):
            return prefix
    return None

def check_contain(content, keyword_list):
    if not keyword_list:
        return None
    for ky in keyword_list:
        if content.find(ky) != -1:
            return True
    return None
