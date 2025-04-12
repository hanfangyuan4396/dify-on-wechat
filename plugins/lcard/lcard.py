# encoding:utf-8
import datetime
import threading
import time
from datetime import datetime
import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
import plugins.lcard.app_card as fun
from plugins import *
import requests
import json
import re
import urllib.parse  # 添加用于URL编码

@plugins.register(
    name="lcard",
    desire_priority=900,  # 设置更高优先级确保最优先处理点歌命令
    namecn="lcard",
    desc="发送卡片式链接和小程序",
    version="0.3",
    author="sam",
)
class lcard(Plugin):
    def __init__(self):
        super().__init__()
        self.json_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[lcard] inited")

    def on_handle_context(self, e_context: EventContext):
        # 检查消息类型 - 同时处理文本和XML消息
        if e_context["context"].type not in [ContextType.TEXT, ContextType.XML, ContextType.SHARING]:
            logger.debug(f"[lcard] Skipping message type: {e_context['context'].type}")
            return
        context = e_context["context"]
        msg = context.get("msg")
        if not msg:
            logger.warning("[lcard] No message object in context")
            return

        # 获取基本信息
        isgroup = context.get("isgroup", False)
        content = context.content
        _user_id = msg.from_user_id
        to_user_id = msg.to_user_id

        # 记录详细的消息信息
        logger.info(f"[lcard] Processing message: content='{content}', type={e_context['context'].type}, isgroup={isgroup}, from={_user_id}, to={to_user_id}")
        
        content = content.strip()
        
        # 发送各种榜单
        trending_pinyin = {
            "百度热榜": "baidu",
            "今日热榜": "top",
            "今日热文": "top",
            "热门新闻": "top",
            "今日热门新闻": "top",
            "今日的热门新闻": "top",
            "知乎热榜": "zhihu",
            "抖音热榜": "douyin",
            "掘金热榜": "juejin",
            "吴爱热榜": "52pojie",
            "网易热榜": "ne-news",
            "豆瓣热榜": "douban-media",
            "今日头条":"toutiao",
            "github热榜":"github",
            "潘湾新闻":"thepaper",
            "小红书":"xiaohongshu",
            "微博热榜": "weibo",
            "b站热榜": "bilibili",
        }
        
        if content in trending_pinyin:
            trending = trending_pinyin[content]
            url = f"https://rebang.today/home?tab={trending}"
            gh_id = "gh_7d739cf5e919"
            username = "今日热榜"
            title = "今日热榜-全站榜单 🏆"
            desc = "涵盖：今日头条、抖音、Github、吴爱、掘金、bilibili、百度、知乎、网易、微博等热榜"
            image_url = "https://mmbiz.qpic.cn/sz_mmbiz_jpg/RiacFDBX14xAWVSLByXwA4pg6jickFZQT09smokU52wziaZhibhtkSIBll5wKiawKrDmXWwf1YYGq4ZiaJYGfViaDZDrw/300?wxtype=jpeg&amp;wxfrom=401"
            xml_link = fun.get_xml(to_user_id, url, gh_id, username, title, desc, image_url)
            reply = Reply(ReplyType.XML, xml_link)
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS
            e_context['handled'] = True
            logger.info(f"[lcard] Successfully sent trending card for: {content}")
            return
            
        # 新闻直播间
        if content == "新闻直播间":
            try:
                video_mp = fun.cctv13_live_xml(to_user_id)
                reply = Reply(ReplyType.XML, video_mp)
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                e_context['handled'] = True
                logger.info(f"[lcard] Successfully sent CCTV13 live")
                return
            except Exception as e:
                logger.error(f"[lcard] Error processing CCTV13 live request: {e}")
                _set_reply_text(f"新闻直播间请求出错: {e}", e_context, level=ReplyType.TEXT)
                return
                
        # 营养视频
        if content == "营养视频":
            try:
                video_mp = fun.yinyang_xml(to_user_id)
                reply = Reply(ReplyType.XML, video_mp)
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                e_context['handled'] = True
                logger.info(f"[lcard] Successfully sent nutrition video")
                return
            except Exception as e:
                logger.error(f"[lcard] Error processing nutrition video request: {e}")
                _set_reply_text(f"营养视频请求出错: {e}", e_context, level=ReplyType.TEXT)
                return
                
        # 我要吃/我想吃
        if content.startswith("我要吃") or content.startswith("我想吃"):
            try:
                keyword = content[3:].strip()
                xml_app = fun.woyaochi_app(to_user_id, keyword)
                reply = Reply(ReplyType.XML, xml_app)  # 将 MINIAPP 改为 XML 类型
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                e_context['handled'] = True
                logger.info(f"[lcard] Successfully sent food recommendation for: {keyword} as XML")
                return
            except Exception as e:
                logger.error(f"[lcard] Error processing food recommendation request: {e}")
                _set_reply_text(f"美食推荐请求出错: {e}", e_context, level=ReplyType.TEXT)
                return
                
        # 菜品做法
        if content.endswith("怎么做"):
            try:
                dish_name = content[:-3].strip()
                url = f"https://m.xiachufang.com/search/?keyword={dish_name}"
                gh_id = "gh_fbfa5dacde93"
                username = "美食教程"
                title = "美食教程"
                desc = f"🔍️ {dish_name}"
                image_url = "https://mmbiz.qpic.cn/mmbiz_jpg/Uc03FJicJseLq0yQ4JqqiaIIlDB7KuiaNY7ia14ZGCfDeVXktfI9kU6ZGu4659Y3n9CVhP5oKEIYkvXJgDg9WRia5Ng/300?wx_fmt=jpeg&amp;wxfrom=1"
                xml_link = fun.get_xml(to_user_id, url, gh_id, username, title, desc, image_url)
                reply = Reply(ReplyType.XML, xml_link)
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                e_context['handled'] = True
                logger.info(f"[lcard] Successfully sent cooking tutorial for: {dish_name}")
                return
            except Exception as e:
                logger.error(f"[lcard] Error processing cooking tutorial request: {e}")
                _set_reply_text(f"菜谱查询出错: {e}", e_context, level=ReplyType.TEXT)
                return
                
        # 餐券
        elif content == "饭票":
            try:
                xml_app = fun.coupon(to_user_id)
                reply = Reply(ReplyType.XML, xml_app)  # 将 MINIAPP 改为 XML 类型
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                e_context['handled'] = True
                logger.info(f"[lcard] Successfully sent food coupon as XML")
                return
            except Exception as e:
                logger.error(f"[lcard] Error processing food coupon request: {e}")
                _set_reply_text(f"饭票请求出错: {e}", e_context, level=ReplyType.TEXT)
                return
        
        # 处理点歌命令
        elif content.startswith("点歌"):
            keyword = content[2:].replace(" ", "").strip()  
            logger.info(f"[lcard] Processing song request for: {keyword}")
            url = f"https://api.52vmy.cn/api/music/qq?msg={keyword}&n=1"
            try:
                logger.debug(f"[lcard] Requesting song info from: {url}")
                resp1 = requests.get(url)
                data = resp1.json()
                logger.debug(f"[lcard] API response: {data}")
                music_parse = data["data"]
                song_id = music_parse["songid"]
                singer = music_parse["singer"]
                song = music_parse["song"]
                picture = music_parse["picture"]
                logger.info(f"[lcard] Found song: {song} by {singer}")
                
                if song_id:
                    logger.debug(f"[lcard] Generating music card for song: {song}")
                    # 使用QQ音乐原始的链接格式
                    card_app = f"""
<appmsg appid="" sdkver="0">
<title>{song}</title>
<des>{singer}</des>
    <action>view</action>
    <type>3</type>
    <showtype>0</showtype>
    <content></content>
    <url>http://c.y.qq.com/v8/playsong.html?songmid={song_id}</url>
    <dataurl>http://ws.stream.qqmusic.qq.com/C100{song_id}.m4a?fromtag=0&amp;guid=126548448</dataurl>
    <lowurl></lowurl>
    <lowdataurl></lowdataurl>
    <recorditem></recorditem>
    <thumburl>{picture}</thumburl>
    <messageaction></messageaction>
    <md5>fe75b445564bdf938ea28b455f0ccf43</md5>
    <extinfo></extinfo>
    <sourceusername></sourceusername>
    <sourcedisplayname></sourcedisplayname>
    <commenturl></commenturl>
    <appattach>
        <totallen>0</totallen>
        <attachid></attachid>
        <emoticonmd5></emoticonmd5>
        <fileext></fileext>
        <cdnthumburl>{picture}</cdnthumburl>
        <cdnthumbaeskey>766167737676626b706e6b6e6876706d</cdnthumbaeskey>
        <aeskey></aeskey>
        <encryver>1</encryver>
        <cdnthumblength>24237</cdnthumblength>
        <cdnthumbheight>500</cdnthumbheight>
        <cdnthumbwidth>500</cdnthumbwidth>
    </appattach>
    <weappinfo>
        <pagepath></pagepath>
        <username></username>
        <appid></appid>
        <appservicetype>0</appservicetype>
    </weappinfo>
    <websearch />
</appmsg>
<appinfo>
    <version>1</version>
    <appname>QQ音乐</appname>
</appinfo>
    """
                    logger.debug(f"[lcard] Generated music card XML")
                    reply = Reply(ReplyType.XML, card_app)
                    e_context['reply'] = reply
                    # 设置EventAction.BREAK_PASS阻止其他插件处理
                    e_context.action = EventAction.BREAK_PASS
                    e_context['handled'] = True
                    logger.info(f"[lcard] Successfully sent music card for: {song}")
                    return
                else:
                    logger.warning(f"[lcard] Song not found for keyword: {keyword}")
                    _set_reply_text("未找到该歌曲", e_context, level=ReplyType.TEXT)
                    # 设置EventAction.BREAK_PASS阻止其他插件处理
                    e_context.action = EventAction.BREAK_PASS
                    e_context['handled'] = True
                    return
            except Exception as e:
                logger.error(f"[lcard] Error processing song request: {e}")
                _set_reply_text(f"点歌出错: {e}", e_context, level=ReplyType.TEXT)
                # 设置EventAction.BREAK_PASS阻止其他插件处理
                e_context.action = EventAction.BREAK_PASS
                e_context['handled'] = True
                return

        # 处理天气查询
        elif content.endswith("天气"):
            logger.info(f"[lcard] Processing weather request: {content}")
            weather_match = re.search(r"(.+?)(的)?天气", content)
            city_name = weather_match.group(1) if weather_match else "上海"
            logger.debug(f"[lcard] Requesting weather for city: {city_name}")
            try:
                url = f"https://api.pearktrue.cn/api/weather/?city={city_name}&id=1"
                response = requests.get(url)
                if response.status_code == 200:
                    datas = json.loads(response.text)["data"]
                    logger.debug(f"[lcard] Weather API response: {datas}")
                    if all(isinstance(data, dict) for data in datas):
                        first_data_weather = datas[0]['weather']
                        second_data_weather = datas[1]['weather']
                        first_data_temperature = datas[0]['temperature']
                        second_data_temperature = datas[1]['temperature']
                        gh_id = "gh_7d739cf5e919"
                        username = "天气预报"
                        title = f"{city_name}今天 天气：{first_data_weather} 气温：{first_data_temperature}"
                        desc = f"明天：{second_data_weather} 气温：{second_data_temperature}"
                        weather_url = "https://www.msn.cn/zh-cn/weather/"
                        image_url = "https://mmbiz.qpic.cn/mmbiz_jpg/xuic5bNARavt67O3KvoXqjJJanKwRkfIiaJT6Oiavia0icVgC9DWInofCKA655AuicqgdBukd36nFXTqHBUUvfc0uCCQ/300?wxtype=jpeg&amp;wxfrom=401"
                        xml_link = fun.get_xml(to_user_id, weather_url, gh_id, username, title, desc, image_url)
                        reply = Reply(ReplyType.XML, xml_link)
                        e_context['reply'] = reply
                        e_context.action = EventAction.BREAK_PASS
                        e_context['handled'] = True
                        logger.info(f"[lcard] Successfully sent weather card for: {city_name}")
                        return
                    else:
                        logger.warning(f"[lcard] Invalid weather data format for city: {city_name}")
                        _set_reply_text("请按格式输入：城市+天气 例如：北京天气", e_context, level=ReplyType.TEXT)
                        return
                else:
                    logger.error(f"[lcard] Weather API error: {response.status_code}")
                    _set_reply_text("天气查询失败，请稍后再试", e_context, level=ReplyType.TEXT)
                    return
            except Exception as e:
                logger.error(f"[lcard] Error processing weather request: {e}")
                _set_reply_text(f"天气查询出错: {e}", e_context, level=ReplyType.TEXT)
                return
                
        # 处理美团外卖
        elif content == "美团外卖":
            logger.info(f"[lcard] Processing Meituan request")
            try:
                xml_app = fun.meituan(to_user_id)
                reply = Reply(ReplyType.XML, xml_app)  # 将 MINIAPP 改为 XML 类型
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                e_context['handled'] = True
                logger.info(f"[lcard] Successfully sent Meituan mini app as XML")
                return
            except Exception as e:
                logger.error(f"[lcard] Error processing Meituan request: {e}")
                _set_reply_text(f"美团外卖请求出错: {e}", e_context, level=ReplyType.TEXT)
                return

        # 处理药品搜索
        elif content.startswith("用药") or content.startswith("药品"):
            # 提取关键词，移除前缀"用药"或"药品"并清理空格
            if content.startswith("用药"):
                keyword = content[2:].strip()
            else:  # 开头是"药品"
                keyword = content[2:].strip()
                
            if not keyword:
                _set_reply_text("请输入药品关键词，例如：用药 紫杉醇", e_context, level=ReplyType.TEXT)
                return
                
            logger.info(f"[lcard] 执行药品搜索: {keyword}")
            
            try:
                # 使用 app_card.py 中的 medsearch 函数生成卡片
                xml_app = fun.medsearch(to_user_id, keyword)
                reply = Reply(ReplyType.XML, xml_app)
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                e_context['handled'] = True
                logger.info(f"[lcard] 成功发送药品搜索卡片: {keyword}")
                return
            except Exception as e:
                logger.error(f"[lcard] 处理药品搜索请求出错: {e}")
                _set_reply_text(f"药品搜索请求出错: {e}", e_context, level=ReplyType.TEXT)
                return
                
        # 处理秘塔搜索
        elif content.startswith("搜索"):
            # 提取关键词，移除前缀"搜索"并清理空格
            keyword = content[2:].strip()
            if not keyword:
                _set_reply_text("请输入搜索关键词", e_context, level=ReplyType.TEXT)
                return
                
            logger.info(f"[lcard] 执行秘塔搜索: {keyword}")
            
            try:
                # 定义请求头，只保留必要的头信息
                headers = {
                    'Accept': 'application/json, text/plain, */*',
                    'Content-Type': 'application/json',
                    'Origin': 'https://metaso.cn',
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36',
                    'Token': 'wr8+pHu3KYryzz0O2MaBSNUZbVLjLUYC1FR4sKqSW0q7McD9cYp9KtP/JEDdCz85fvC5lkaAZBO4PQuNTExiO6cDNR913DVd0H2pZYy93al/tSOqxwz+wzQAaEEqD2u5LLZMtP9GspxoUWvhjXRyvA=='
                }

                # 设置请求载荷
                payload = {
                    "question": keyword,
                    "mode": "detail",
                    "engineType": "",
                    "scholarSearchDomain": "all"
                }

                # 发起POST请求并设置超时
                response = requests.post(
                    'https://metaso.cn/api/session', 
                    headers=headers, 
                    data=json.dumps(payload),
                    timeout=10  # 设置10秒超时
                )

                # 检查请求是否成功
                if response.status_code == 200:
                    # 解析JSON数据
                    data = response.json()
                    search_id = data['data']['id']
                    
                    # 构建卡片信息
                    gh_id = "gh_d6931e1cbcd9"  # 公众号原始ID
                    username = "秘塔AI搜索"      # 公众号名称
                    title = "秘塔AI搜索"         # 卡片标题
                    desc = f"🔍 {keyword}\n\nmetaso.cn"  # 卡片描述
                    image_url = "https://mmbiz.qpic.cn/mmbiz_jpg/Xc8NsmfSF6wswHSTuUMgIjC6F1SslJ3l4SvZCG7ITURSCQrWfHxIssGI5T7316tibiaCrZRm0sSmLXnQDN088icZg/300?wx_fmt=jpeg&amp;wxfrom=1"  # 卡片图片
                    url = f"https://metaso.cn/search/{search_id}?q={urllib.parse.quote(keyword)}"  # 搜索结果URL，对关键词进行URL编码
                    
                    # 生成XML卡片
                    logger.info(f"[lcard] 开始构建卡片: 标题={title}, URL={url}")
                    xml_link = fun.get_xml(to_user_id, url, gh_id, username, title, desc, image_url)
                    logger.info(f"[lcard] XML卡片生成成功, 长度={len(xml_link)}")
                    
                    # 设置回复内容并发送
                    logger.info(f"[lcard] 准备发送卡片到 {to_user_id}, 类型=ReplyType.XML")
                    _set_reply_text(xml_link, e_context, level=ReplyType.XML)
                    logger.info(f"[lcard] 秘塔搜索卡片发送成功: {keyword}, ID: {search_id}")
                    return
                else:
                    logger.error(f"[lcard] 秘塔搜索请求失败: HTTP {response.status_code}, {response.text}")
                    _set_reply_text(f"抱歉，搜索出错了 (HTTP {response.status_code})", e_context, level=ReplyType.TEXT)
                    return
            except Exception as e:
                logger.error(f"[lcard] 秘塔搜索异常: {str(e)}")
                _set_reply_text(f"抱歉，搜索过程中出现错误: {str(e)}", e_context, level=ReplyType.TEXT)
                return        
                
        # 处理搜索请求
        elif content.startswith("百度"):
            logger.info(f"[lcard] Processing search request: {content}")
            keyword = content[2:].strip()
            try:
                gh_id = "gh_d6931e1cbcd9"
                username = "百度"
                title = "搜索结果"
                desc = f"🔍️ {keyword}"
                search_url = f"https://www.baidu.com/s?wd={keyword}"
                image_url = "https://mmbiz.qpic.cn/mmbiz_png/SP4VXbQ39icVxwCcncW2xJnEr1CdlVeFxUqehnL52AdwOyM0tCvLZJTBibkwEl8GibHTDDiadEgnSib2TIMjJEH3Weg/300?wx_fmt=jpeg&amp;wxfrom=1"
                xml_link = fun.get_xml(to_user_id, search_url, gh_id, username, title, desc, image_url)
                reply = Reply(ReplyType.XML, xml_link)
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                e_context['handled'] = True
                logger.info(f"[lcard] Successfully sent search card for: {keyword}")
                return
            except Exception as e:
                logger.error(f"[lcard] Error processing search request: {e}")
                _set_reply_text(f"搜索出错: {e}", e_context, level=ReplyType.TEXT)
                return
                
        # 处理其他命令
        if content.startswith("小程序"):
            logger.debug(f"[lcard] Processing mini program command: {content}")
            # 处理小程序命令逻辑
            return

        if content.startswith("卡片"):
            logger.debug(f"[lcard] Processing card command: {content}")
            # 处理卡片命令逻辑
            return

        if content.startswith("链接"):
            logger.debug(f"[lcard] Processing link command: {content}")
            # 处理链接命令逻辑
            return

def _set_reply_text(content: str, e_context: EventContext, level: ReplyType = ReplyType.ERROR):
    reply = Reply(level, content)
    e_context["reply"] = reply
    e_context.action = EventAction.BREAK_PASS
    e_context['handled'] = True
