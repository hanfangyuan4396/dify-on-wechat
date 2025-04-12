import json
import urllib
import requests
import re
from common.log import logger

def get_xml(to_user_id,url,gh_id,username,title,desc,image_url,protocol="gewechat"):
    """
    返回 gewechat 协议的 XML 格式
    """
    # 移除外层 <msg> 标签，直接返回 <appmsg> 开头的 XML
    xml_c = f'''<appmsg appid="" sdkver="0">
    <title>{title}</title>
    <des>{desc}</des>
    <type>5</type>
    <url>{url}</url>
    <thumburl>{image_url}</thumburl>
    <sourceusername>{gh_id}</sourceusername>
    <sourcedisplayname>{username}</sourcedisplayname>
    <appattach>
        <totallen>0</totallen>
        <attachid></attachid>
        <emoticonmd5></emoticonmd5>
        <fileext></fileext>
        <aeskey></aeskey>
    </appattach>
    <weappinfo>
        <pagepath></pagepath>
        <username></username>
        <appid></appid>
        <appservicetype>0</appservicetype>
    </weappinfo>
    <websearch />
</appmsg>'''
    return xml_c

def has_url(content):
    # 定义URL匹配的正则表达式模式
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    # 使用正则表达式模式进行匹配
    urls = re.findall(url_pattern, content)
    # 判断是否存在URL
    if urls:
        return urls
    else:
        return False

def cctv13_live_xml(to_user_id):
    xml_c = f'''<msg>
    <fromusername>{to_user_id}</fromusername>
    <scene>0</scene>
    <commenturl></commenturl>
    <appmsg appid="" sdkver="">
        <title></title>
        <des></des>
        <action>view</action>
        <type>63</type>
        <showtype>0</showtype>
        <content></content>
        <url></url>
        <dataurl></dataurl>
        <lowurl></lowurl>
        <lowdataurl></lowdataurl>
        <recorditem></recorditem>
        <thumburl></thumburl>
        <messageaction></messageaction>
        <extinfo></extinfo>
        <sourceusername></sourceusername>
        <sourcedisplayname></sourcedisplayname>
        <commenturl></commenturl>
        <appattach>
            <totallen>0</totallen>
            <attachid></attachid>
            <emoticonmd5></emoticonmd5>
            <fileext></fileext>
            <aeskey></aeskey>
        </appattach>
        <weappinfo>
            <pagepath></pagepath>
            <username></username>
            <appid></appid>
            <appservicetype>0</appservicetype>
        </weappinfo>
        <websearch />
        <finderLive>
            <finderLiveID>2078689339384988848</finderLiveID>
            <finderUsername>v2_060000231003b20faec8c6e08f1ccad5ca04e930b0772949079bb0975410cd8795a30ecaf182@finder</finderUsername>
            <finderObjectID>14404630107220351100</finderObjectID>
            <nickname>灵绣三都</nickname>
            <desc>24小时新闻直播</desc>
            <finderNonceID>832713670845449450_0_142_0_0</finderNonceID>
            <headUrl>https://wx.qlogo.cn/finderhead/ver_1/3AiczcfQVe2B4p2SCsCMgwTzYeLOeKPPEibh2j1IGRrL8tS32S74gcx4L7iaYCgyAPicpgia1MaxuqNUMgarWPPj0TAnXHz5XiaXRrpkK8Pw2qy28/132</headUrl>
            <liveStatus>1</liveStatus>
            <authIconUrl>https://dldir1v6.qq.com/weixin/checkresupdate/icons_filled_channels_authentication_enterprise_a2658032368245639e666fb11533a600.png</authIconUrl>
            <authIconTypeStr>2</authIconTypeStr>
            <media>
                <thumbUrl>https://finder.video.qq.com/251/20304/stodownload?encfilekey=rjD5jyTuFrIpZ2ibE8T7YmwgiahniaXswqzGnXt0w0XHS7TdmEZUV9W8TIATXiamHeULp88D8Z0Bw9f1EsbbAVodyAQrueN8OFFB9w74SM36eTyW5a1LuZDCMw&amp;bizid=1023&amp;dotrans=0&amp;hy=SH&amp;idx=1&amp;m=&amp;scene=0&amp;picformat=100&amp;token=Cvvj5Ix3eeyD0TVgRZ2eE4bPCBxp7N9elPC46DnibTPoVpOTQGUHuN9FiaGM9zR9vMdYJvBia8UQ1bGdkO52PNbAIQyV5UOkFwBArAFzmMic5FKIuB6SfcVJow&amp;ctsc=1-142</thumbUrl>
                <videoPlayDuration>0</videoPlayDuration>
                <url></url>
                <coverUrl>https://finder.video.qq.com/251/20304/stodownload?encfilekey=rjD5jyTuFrIpZ2ibE8T7YmwgiahniaXswqzGnXt0w0XHS7TdmEZUV9W8TIATXiamHeULp88D8Z0Bw9f1EsbbAVodyAQrueN8OFFB9w74SM36eTyW5a1LuZDCMw&amp;bizid=1023&amp;dotrans=0&amp;hy=SH&amp;idx=1&amp;m=&amp;scene=0&amp;picformat=100&amp;token=Cvvj5Ix3eeyD0TVgRZ2eE4bPCBxp7N9elPC46DnibTPoVpOTQGUHuN9FiaGM9zR9vMdYJvBia8UQ1bGdkO52PNbAIQyV5UOkFwBArAFzmMic5FKIuB6SfcVJow&amp;ctsc=1-142</coverUrl>
                <height>1000</height>
                <width>750</width>
                <mediaType>9</mediaType>
            </media>
        </finderLive>
    </appmsg>
    <appinfo>
        <version>1</version>
        <appname>Window wechat</appname>
    </appinfo>
</msg>'''
    return xml_c

def huochepiao_app(to_user_id,math,toCityName,fromcity,data):
    card_app=f'''<msg>
    <fromusername>{to_user_id}</fromusername>
    <scene>0</scene>
    <commenturl></commenturl>
    <appmsg appid="" sdkver="0">
        <title>{math}</title>
        <des>欢迎使用携程旅行，预定酒店机票火车票汽车票！</des>
        <action>view</action>
        <type>33</type>
        <showtype>0</showtype>
        <content></content>
        <url>https://mp.weixin.qq.com/mp/waerrpage?appid=wx0e6ed4f51db9d078&amp;type=upgrade&amp;upgradetype=3#wechat_redirect</url>
        <dataurl></dataurl>
        <lowurl></lowurl>
        <lowdataurl></lowdataurl>
        <recorditem></recorditem>
        <thumburl></thumburl>
        <messageaction></messageaction>
        <md5>1cecd8508458b4966b0dd0584658405d</md5>
        <extinfo></extinfo>
        <sourceusername>gh_36ada103ba97@app</sourceusername>
        <sourcedisplayname>携程旅行订酒店机票火车汽车门票</sourcedisplayname>
        <commenturl></commenturl>
        <appattach>
            <totallen>0</totallen>
            <attachid></attachid>
            <emoticonmd5></emoticonmd5>
            <fileext>jpg</fileext>
            <filekey>f75426d7c25610ec27c320784b8c143e</filekey>
            <cdnthumburl>3057020100044b3049020100020472901c4e02032f52da0204654aac74020466549b70042437393939323438652d363235312d346261352d383635632d3064623464636663396533300204052408030201000405004c4f2a00</cdnthumburl>
            <aeskey>a3263e3187332a3374bb03ccced259e5</aeskey>
            <cdnthumbaeskey>a3263e3187332a3374bb03ccced259e5</cdnthumbaeskey>
            <encryver>1</encryver>
            <cdnthumblength>116511</cdnthumblength>
            <cdnthumbheight>100</cdnthumbheight>
            <cdnthumbwidth>100</cdnthumbwidth>
        </appattach>
        <weappinfo>
            <pagepath>pages/train/list/list.html?dstation={toCityName}&amp;astation={fromcity}&amp;ddate={data}&amp;departAreaId=undefined&amp;arriveAreaId=undefined</pagepath>
            <username>gh_36ada103ba97@app</username>
            <appid>wx0e6ed4f51db9d078</appid>
            <version>896</version>
            <type>2</type>
            <weappiconurl>http://mmbiz.qpic.cn/mmbiz_png/ZezvdBPFysQ91ncfGDA05ErjTCNmhaLVzwszIkRl4rrdvh997FszfsdS2OFmVKXuIaHFwYvCekDqCvx0ib66edg/640?wx_fmt=png&amp;wxfrom=200</weappiconurl>
            <appservicetype>0</appservicetype>
            <shareId>0_wx0e6ed4f51db9d078_35977f78867055e7dfabcbc3e04a7182_1716820837_0</shareId>
        </weappinfo>
        <websearch />
    </appmsg>
    <appinfo>
        <version>1</version>
        <appname>Window wechat</appname>
    </appinfo>
</msg>'''
    return card_app

def woyaochi_app(to_user_id,content):
    card_app = f'''<?xml version="1.0"?>
    <appmsg appid="wx2c348cf579062e56" sdkver="0">
        <title>美团外卖，送啥都快</title>
        <des>你想吃的，你想喝的：都在美团外卖！赶快下单吧~</des>
        <type>33</type>
        <url>https://mp.weixin.com/mp/waerrpage?appid=wx2c348cf579062e56&amp;type=upgrade&amp;upgradetype=3#wechat_redirect</url>
        <sourceusername>gh_72a4eb2d4324@app</sourceusername>
        <sourcedisplayname>美团外卖丨外卖美食奶茶咖啡水果</sourcedisplayname>
        <appattach>
            <totallen>0</totallen>
            <attachid></attachid>
            <emoticonmd5></emoticonmd5>
            <fileext></fileext>
            <aeskey></aeskey>
            <cdnthumburl>3057020100044b304902010002041c54444e02032f540602041aee903a0204668263d6042466336361363362342d363833652d343034632d386639612d3733623337333635663639370204051808030201000405004c56fa00</cdnthumburl>
            <cdnthumbmd5>9c28705f25887d84f7ffac19e9fcc38c</cdnthumbmd5>
            <cdnthumblength>35122</cdnthumblength>
            <cdnthumbwidth>420</cdnthumbwidth>
            <cdnthumbheight>336</cdnthumbheight>
            <cdnthumbaeskey>c3b2ca749660b8a5cab2ab160e8b8f15</cdnthumbaeskey>
            <encryver>0</encryver>
            <filekey>34631202559@chatroom_1754_1719840815</filekey>
        </appattach>
        <weappinfo>
            <pagepath>pages/index/index.html?redirectUrl=%2Fpackages%2Fsearch-business%2Fsearch%2Findex%3Fkeyword={urllib.parse.quote(content)}&amp;auto_search%3Dtrue%26fromShare%3Dtrue</pagepath>
            <username>gh_72a4eb2d4324@app</username>
            <appid>wx2c348cf579062e56</appid>
            <type>2</type>
            <version>898</version>
            <weappiconurl>http://mmbiz.qpic.cn/sz_mmbiz_png/IXJic6HOb8QQia18XFKQC6YwFLUclBz794p2beQpE1XiaqiaKzvhxfrGIJrhcHPibhR22zRMaG1dcSxic16NkmR2kWMg/640?wx_fmt=png&amp;wxfrom=200</weappiconurl>
            <appservicetype>0</appservicetype>
        </weappinfo>
        <websearch />
    </appmsg>
    <fromusername>{to_user_id}</fromusername>
    <scene>0</scene>
    <appinfo>
        <version>1</version>
        <appname></appname>
    </appinfo>
    <commenturl></commenturl>'''
    return card_app

def mp3_linK(to_user_id,url=None,thumburl=None):
    card_app = f'''<?xml version="1.0"?>
<msg>
    <appmsg appid="wx8dd6ecd81906bf96" sdkver="0">
        <title>云烟成雨</title>
        <des>房东的猫</des>
        <action>view</action>
        <type>3</type>
        <showtype>0</showtype>
        <content></content>
        <url>https://y.qq.com</url>
        <dataurl>http://hm.suol.cc/API/caige/song.mp3</dataurl>
        <lowurl>http://hm.suol.cc/API/caige/song.mp3</lowurl>
        <thumburl>http://y.qq.com/music/photo_new/T002R150x150M000001sKd2l0dVkXa.jpg</thumburl>
        <appattach>
            <totallen>0</totallen>
            <attachid></attachid>
            <emoticonmd5></emoticonmd5>
            <fileext></fileext>
            <aeskey></aeskey>
        </appattach>
        <weappinfo>
            <pagepath></pagepath>
            <username></username>
            <appid></appid>
            <appservicetype>0</appservicetype>
        </weappinfo>
        <websearch />
    </appmsg>
    <fromusername>{to_user_id}</fromusername>
    <scene>0</scene>
    <appinfo>
        <version>1</version>
        <appname>QQ音乐</appname>
    </appinfo>
    <commenturl></commenturl>
</msg>'''
    return card_app

def meituan(to_user_id):
    card_app = f'''
    <appmsg appid="wx2c348cf579062e56" sdkver="0">
        <title>美团外卖，送啥都快</title>
        <des>你想吃的，你想喝的：都在美团外卖！赶快下单吧~</des>
        <type>33</type>
        <url>https://mp.weixin.qq.com/mp/waerrpage?appid=wx2c348cf579062e56&amp;type=upgrade&amp;upgradetype=3#wechat_redirect</url>
        <sourceusername>gh_72a4eb2d4324@app</sourceusername>
        <sourcedisplayname>美团外卖丨外卖美食奶茶咖啡水果</sourcedisplayname>
        <appattach>
            <totallen>0</totallen>
            <attachid></attachid>
            <emoticonmd5></emoticonmd5>
            <fileext></fileext>
            <aeskey></aeskey>
            <cdnthumburl>3057020100044b304902010002041c54444e02032f540602041aee903a0204668263d6042466336361363362342d363833652d343034632d386639612d3733623337333635663639370204051808030201000405004c56fa00</cdnthumburl>
            <cdnthumbmd5>9c28705f25887d84f7ffac19e9fcc38c</cdnthumbmd5>
            <cdnthumblength>35122</cdnthumblength>
            <cdnthumbwidth>420</cdnthumbwidth>
            <cdnthumbheight>336</cdnthumbheight>
            <cdnthumbaeskey>c3b2ca749660b8a5cab2ab160e8b8f15</cdnthumbaeskey>
            <encryver>0</encryver>
            <filekey>34631202559@chatroom_1754_1719840815</filekey>
        </appattach>
        <weappinfo>
            <pagepath>pages/index/index.html?from=from_share_index&amp;</pagepath>
            <username>gh_72a4eb2d4324@app</username>
            <appid>wx2c348cf579062e56</appid>
            <type>2</type>
            <version>905</version>
            <weappiconurl>http://mmbiz.qpic.cn/sz_mmbiz_png/IXJic6HOb8QQia18XFKQC6YwFLUclBz794p2beQpE1XiaqiaKzvhxfrGIJrhcHPibhR22zRMaG1dcSxic16NkmR2kWMg/640?wx_fmt=png&amp;wxfrom=200</weappiconurl>
            <appservicetype>0</appservicetype>
            <shareId>0_wx2c348cf579062e56_35977f78867055e7dfabcbc3e04a7182_1719840814_0</shareId>
            <brandofficialflag>0</brandofficialflag>
            <showRelievedBuyFlag>103967</showRelievedBuyFlag>
            <hasRelievedBuyPlugin>0</hasRelievedBuyPlugin>
            <flagshipflag>0</flagshipflag>
            <subType>0</subType>
            <isprivatemessage>0</isprivatemessage>
            <weapppagethumbrawurl>https://p0.meituan.net/travelcube/f722637dc1686b4cdc27a9614d84863c52486.png@420w_340h_1e_1c_1l</weapppagethumbrawurl>
        </weappinfo>
    </appmsg>
    <fromusername>{to_user_id}</fromusername>
    <scene>0</scene>
    <appinfo>
        <version>1</version>
        <appname>美团外卖</appname>
    </appinfo>
    <commenturl></commenturl>'''
    return card_app

def air_tickets_app(to_user_id,content,departure_code,departure_city,arrive_code,arrive_city,date):
    card_app=f'''
    <appmsg appid="" sdkver="0">
        <title>携程旅行--酒店机票火车票汽车票预订</title>
        <des>{content}</des>
        <action>view</action>
        <type>33</type>
        <showtype>0</showtype>
        <content></content>
        <url>https://mp.weixin.qq.com/mp/waerrpage?appid=wx0e6ed4f51db9d078&amp;type=upgrade&amp;upgradetype=3#wechat_redirect</url>
        <dataurl></dataurl>
        <lowurl></lowurl>
        <lowdataurl></lowdataurl>
        <recorditem></recorditem>
        <thumburl></thumburl>
        <messageaction></messageaction>
        <md5>af1eb5f7dab8374426540687200f7f70</md5>
        <extinfo></extinfo>
        <sourceusername>gh_36ada103ba97@app</sourceusername>
        <sourcedisplayname>携程旅行订酒店机票火车汽车门票</sourcedisplayname>
        <commenturl></commenturl>
        <appattach>
            <totallen>0</totallen>
            <attachid></attachid>
            <emoticonmd5></emoticonmd5>
            <fileext>jpg</fileext>
            <filekey>8ba2ede3252c1517f118d970339e1e29</filekey>
            <cdnthumburl>3052020100044b3049020100020472901c4e02032f5406020476ee903a0204666fca75042462373462623539372d313837352d343562322d386231322d3333666436383139613532360204052808030201000400</cdnthumburl>
            <aeskey>8e209803c9ec5cfaf32d4b37d3163da0</aeskey>
            <cdnthumbaeskey>8e209803c9ec5cfaf32d4b37d3163da0</cdnthumbaeskey>
            <encryver>1</encryver>
            <cdnthumblength>115153</cdnthumblength>
            <cdnthumbheight>100</cdnthumbheight>
            <cdnthumbwidth>100</cdnthumbwidth>
        </appattach>
        <weappinfo>
            <pagepath><![CDATA[pages/flight/pages/list/first.html?tripType=ONE_WAY&dcity={departure_code}&dcityName={departure_city}&acity={arrive_code}&acityName={arrive_city}&ddate={date}&cabin=ECONOMY&from=outer&mktshare=eyhJbGxpYW5jZWlkIjoyNjI2ODQsInNpZCI6NzExNDY1LCJvdWlkIjoiIiwic291cmNlaWQiOjU1NTUyNjg5LCJmcm9tYWxsaWFuY2VpZCI6MCwiZnJvbXNpZCI6MCwiZnJvbW91aWQiOiIiLCJmcm9tc291cmNlaWQiOjAsImZyb21vcGVuaWQiOiJjMzEzYWU0Yi1iYzAxLTRjZDItYjFhZS03NTE3NzlmMGViMzQiLCJpbm5lcnNpZCI6IiIsImlubmVyb3VpZCI6IiIsInB1c2hjb2RlIjoiIn0()CE&mktshare=eyJhbGxpYW5jZ2IjNyojIklWODQsInNpZCI6NzExNDY1LCJvdWlkIjoiIiwic291cmNlaWQiOjU1NTUyNjg5LCJmcm9tYWxsaWFuY2VpZCI6MCwiZnJvbXNpZCI6MCwiZnJvbW91aWQiOiIiLCJmcm9tc291cmNlaWQiOjAsImZyb21vcGVuaWQiOiJjMzEzYWU0Yi1iYzAxLTRjZDItYjFhZS03NTE3NzlmMGViMzQiLCJpbm5lcnNpZCI6IiIsImlubmVyb3VpZCI6IiIsInB1c2hjb2RlIjoiIn0()NY]]></pagepath>
            <username>gh_36ada103ba97@app</username>
            <appid>wx0e6ed4f51db9d078</appid>
            <version>901</version>
            <type>2</type>
            <weappiconurl>http://mmbiz.qpic.cn/mmbiz_png/ZezvdBPFysQ91ncfGDA05ErjTCNmhaLVzwszIkRl4rrdvh997FszfsdS2OFmVKXuIaHFwYvCekDqCvx0ib66edg/640?wx_fmt=png&amp;wxfrom=200</weappiconurl>
            <appservicetype>0</appservicetype>
            <shareId>0_wx0e6ed4f51db9d078_35977f78867055e7dfabcbc3e04a7182_1718601736_0</shareId>
        </weappinfo>
        <websearch />
    </appmsg>
    <appinfo>
        <version>1</version>
        <appname>Window wechat</appname>
    </appinfo>'''
    return card_app

def coupon(to_user_id):
    card_app = f'''
        <appmsg appid="" sdkver="0">
                <title>AI小助手请你干饭</title>
                <type>33</type>
                <action>view</action>
                <url>https://mp.weixin.qq.com/mp/waerrpage?appid=wx0b42a347aafbe0d0&amp;type=upgrade&amp;upgradetype=3#wechat_redirect</url>
                <appattach>
                        <cdnthumburl>thumb_url_placeholder</cdnthumburl>
                        <cdnthumbmd5>md5_placeholder</cdnthumbmd5>
                        <cdnthumblength>37563</cdnthumblength>
                        <cdnthumbwidth>630</cdnthumbwidth>
                        <cdnthumbheight>504</cdnthumbheight>
                        <cdnthumbaeskey>thumbaeskey_placeholder</cdnthumbaeskey>
                        <aeskey>aeskey_placeholder</aeskey>
                        <encryver>0</encryver>
                        <filekey>filekey_placeholder</filekey>
                </appattach>
                <sourceusername>gh_9dda55bf7807@app</sourceusername>
                <sourcedisplayname>惠省 I 吃喝玩乐真会省</sourcedisplayname>
                <md5>md5_placeholder</md5>
                <weappinfo>
                        <username><![CDATA[gh_9dda55bf7807@app]]></username>
                        <appid><![CDATA[wx0b42a347aafbe0d0]]></appid>
                        <type>2</type>
                        <version>35</version>
                        <weappiconurl><![CDATA[icon_url_placeholder]]></weappiconurl>
                        <pagepath><![CDATA[pagepath_placeholder]]></pagepath>
                        <shareId><![CDATA[share_id_placeholder]]></shareId>
                        <appservicetype>0</appservicetype>
                        <brandofficialflag>0</brandofficialflag>
                        <showRelievedBuyFlag>0</showRelievedBuyFlag>
                        <hasRelievedBuyPlugin>0</hasRelievedBuyPlugin>
                        <flagshipflag>0</flagshipflag>
                        <wxaTradeCommentScore>score_placeholder</wxaTradeCommentScore>
                        <subType>0</subType>
                        <isprivatemessage>0</isprivatemessage>
                </weappinfo>
        </appmsg>
        <fromusername>{to_user_id}</fromusername>
        <scene>0</scene>
        <appinfo>
                <version>1</version>
                <appname></appname>
        </appinfo>
        <commenturl></commenturl>'''
    return card_app

def yinyang_xml(to_user_id):
    xml_c = f'''
        <appmsg appid="" sdkver="0">
                <title>当前版本不支持展示该内容，请升级至最新版本。</title>
                <type>51</type>
                <action>view</action>
                <url>https://support.weixin.qq.com/security/readtemplate?t=w_security_center_website/upgrade</url>
                <appattach>
                        <cdnthumbaeskey />
                        <aeskey />
                </appattach>
                <webviewshared>
                        <jsAppId><![CDATA[]]></jsAppId>
                </webviewshared>
                <mpsharetrace>
                        <hasfinderelement>0</hasfinderelement>
                </mpsharetrace>
                <finderFeed>
                        <objectId><![CDATA[14434737134877673966]]></objectId>
                        <feedType><![CDATA[4]]></feedType>
                        <nickname><![CDATA[唐PAN弹]]></nickname>
                        <avatar><![CDATA[https://wx.qlogo.cn/finderhead/ver_1/I5SjfpffIqZzMWTnKaXR7O1Qc9M4xBJaCdC6oYS43YqrakolHEcv1DFWowG4XvzbBV4xsI5098nS8NsVdmLz2yHvVbL4ogabRhaKh3ftnuw/0]]></avatar>
                        <desc><![CDATA[蛋白质是生命的物质基础]]></desc>
                        <mediaCount><![CDATA[1]]></mediaCount>
                        <objectNonceId><![CDATA[4763557173255244036_0_25_0_0]]></objectNonceId>
                        <liveId><![CDATA[]]></liveId>
                        <username><![CDATA[v2_060000231003b20faec8cae1811ecad7ce05eb30b077175b824100eacad7cd817a181294c346@finder]]></username>
                        <authIconUrl><![CDATA[https://dldir1v6.qq.com/weixin/checkresupdate/auth_icon_level1_ba9f2ea346de48a3ae0428273fc48117.png]]></authIconUrl>
                        <authIconType>1</authIconType>
                        <contactJumpInfoStr><![CDATA[]]></contactJumpInfoStr>
                        <sourceCommentScene>25</sourceCommentScene>
                        <mediaList>
                                <media>
                                        <thumbUrl><![CDATA[http://wxapp.tc.qq.com/251/20304/stodownload?encfilekey=oibeqyX228riaCwo9STVsGLPj9UYCicgttvib9PT3htnr3wnxUquufUu4JGBwOlN1qIJib06sxxCgokG9Q84XpHaurkCTNXDbmuqgaibp0O29qqAQnXkrWRlMLvMLeDokAyiaWnFCs5UZI7an4&bizid=1023&dotrans=0&hy=SH&idx=1&m=447bcab08621baa9cf9b5b8fd98e71dc&uzid=2&token=KkOFht0mCXl4P6ZnmgrCxRnC7STlHZKPup41o5qlLE3NrpibkamBLNqib6dEZ5whL5VR4ykES6bOUZrTs2KicTpIiciblotvYKSZs751jgrqXp5k&ctsc=2-25]]></thumbUrl>
                                        <fullCoverUrl><![CDATA[]]></fullCoverUrl>
                                        <videoPlayDuration><![CDATA[77]]></videoPlayDuration>
                                        <url><![CDATA[http://wxapp.tc.qq.com/251/20302/stodownload?encfilekey=Cvvj5Ix3eez3Y79SxtvVL0L7CkPM6dFibFeI6caGYwFFIkPP3XeQ0ic0Jq8z5CkIRvcLeLicMnuyrt1hPC6ZTuIf70NZ9KGfRReVkEjibpngLrMZk5LssatXuzsTlt7kqKrPwficldjjZoiczSqTw8tUQlEA&dotrans=0&hy=SH&idx=1&m=4f592ba31046e1e698fb6bd4df5a5552&uzid=2&token=Cvvj5Ix3eeyQOzDWs0pJalrnqfyo41QvC4LtzTiaZcDEGzpSnR2ibPHDbR7drVwNloZlma7mdXkfFjeTXXB0UngrDH4oJKsTS8BNJbyAB4HK9uN5HM4QVP4CRUbGvlpfyl&ctsc=25&extg=2ab200&ftype=201&svrbypass=AAuL%2FQsFAAABAAAAAACnfgjsQGvQ%2B7bxXaKQZhAAAADnaHZTnGbFfAj9RgZXfw6V7%2BtmjmPo%2BekhsDI8L6LimEvHMm1OAVlZx9hbCXqzt%2BJA2tzR031F0no%3D&svrnonce=1720754781]]></url>
                                        <coverUrl><![CDATA[http://wxapp.tc.qq.com/251/20304/stodownload?encfilekey=oibeqyX228riaCwo9STVsGLPj9UYCicgttvib9PT3htnr3wnxUquufUu4JGBwOlN1qIJib06sxxCgokG9Q84XpHaurkCTNXDbmuqgaibp0O29qqAQnXkrWRlMLvMLeDokAyiaWnFCs5UZI7an4&bizid=1023&dotrans=0&hy=SH&idx=1&m=447bcab08621baa9cf9b5b8fd98e71dc&uzid=2&token=KkOFht0mCXl4P6ZnmgrCxRnC7STlHZKPup41o5qlLE3NrpibkamBLNqib6dEZ5whL5VR4ykES6bOUZrTs2KicTpIiciblotvYKSZs751jgrqXp5k&ctsc=2-25]]></coverUrl>
                                        <height><![CDATA[1920.0]]></height>
                                        <mediaType><![CDATA[4]]></mediaType>
                                        <fullClipInset><![CDATA[]]></fullClipInset>
                                        <width><![CDATA[1080.0]]></width>
                                </media>
                        </mediaList>
                        <megaVideo>
                                <objectId><![CDATA[]]></objectId>
                                <objectNonceId><![CDATA[]]></objectNonceId>
                        </megaVideo>
                        <bizUsername><![CDATA[]]></bizUsername>
                        <bizNickname><![CDATA[]]></bizNickname>
                        <bizAvatar><![CDATA[]]></bizAvatar>
                        <bizUsernameV2><![CDATA[]]></bizUsernameV2>
                        <bizAuthIconUrl><![CDATA[]]></bizAuthIconUrl>
                        <bizAuthIconType>0</bizAuthIconType>
                        <ecSource><![CDATA[]]></ecSource>
                        <lastGMsgID><![CDATA[ChBxaW54aWFvcWlhbmcyMDAyEhN3eGlkX3lqY3liNW1pdHhtODEyIhI4ODc0MTI4OTIwNjkwMzkyODY=]]></lastGMsgID>
                        <shareBypData><![CDATA[]]></shareBypData>
                        <isDebug>0</isDebug>
                        <content_type>0</content_type>
                        <finderForwardSource><![CDATA[]]></finderForwardSource>
                </finderFeed>
                <secretmsg>
                        <isscrectmsg>0</isscrectmsg>
                </secretmsg>
        </appmsg>
        <fromusername>{to_user_id}</fromusername>
        <scene>0</scene>
        <appinfo>
                <version>1</version>
                <appname></appname>
        </appinfo>
        <commenturl></commenturl>'''
    return xml_c

def medsearch(to_user_id, keyword):
    """生成药品搜索小程序卡片
    
    Args:
        to_user_id: 接收者用户ID
        keyword: 药品搜索关键词
    
    Returns:
        str: 药品搜索小程序卡片的XML格式
    """
    # 对关键词进行URL编码
    encoded_keyword = urllib.parse.quote(keyword)
    
    # 生成小程序卡片XML
    card_xml = f"""<appmsg appid="" sdkver="0">
        <title>用药助手 - {keyword}</title>
        <des>搜索药品信息: {keyword}</des>
        <type>33</type>
        <url>https://mp.weixin.qq.com/mp/waerrpage?appid=wx709d9a3862c6fd38&amp;type=upgrade&amp;upgradetype=3#wechat_redirect</url>
        <appattach>
                <cdnthumburl>3057020100044b30490201000204184fbfe702032df7fa020465ebd476020467e8084b042466323066356633612d616262342d346636312d393366322d3830333963646635653238380204051408030201000405004c4c6e00</cdnthumburl>
                <cdnthumbmd5>3b45a13aade85c22c5376941d1d11df5</cdnthumbmd5>
                <cdnthumblength>43454</cdnthumblength>
                <cdnthumbwidth>720</cdnthumbwidth>
                <cdnthumbheight>576</cdnthumbheight>
                <cdnthumbaeskey>9ff79ac75ed344568c9390d5838db058</cdnthumbaeskey>
                <aeskey>9ff79ac75ed344568c9390d5838db058</aeskey>
                <encryver>0</encryver>
                <filekey>wxid_v4cr5q0cdqiu22_8_1743259723</filekey>
        </appattach>
        <sourceusername>gh_465703662041@app</sourceusername>
        <sourcedisplayname>用药助手</sourcedisplayname>
        <md5>3b45a13aade85c22c5376941d1d11df5</md5>
        <weappinfo>
                <username><![CDATA[gh_465703662041@app]]></username>
                <appid><![CDATA[wx709d9a3862c6fd38]]></appid>
                <type>2</type>
                <version>50</version>
                <weappiconurl><![CDATA[http://mmbiz.qpic.cn/mmbiz_png/113OGPNrmMk21vZ5QOJMRKfKwdnnGEvdia1hdbrfY42VDFRLtLxIDnEqxmpFAt483dSpQjz4IZzgqmlg2UJOfkg/640?wx_fmt=png&wxfrom=200]]></weappiconurl>
                <pagepath><![CDATA[pages/search/search.html?keyword={encoded_keyword}]]></pagepath>
                <shareId><![CDATA[0_wx709d9a3862c6fd38_9eb01c8c8135ec467d47fa9c742a07fc_1743259722_0]]></shareId>
                <appservicetype>0</appservicetype>
                <brandofficialflag>0</brandofficialflag>
                <showRelievedBuyFlag>0</showRelievedBuyFlag>
                <hasRelievedBuyPlugin>0</hasRelievedBuyPlugin>
                <flagshipflag>0</flagshipflag>
                <wxaTradeCommentScore>0</wxaTradeCommentScore>
                <subType>0</subType>
                <isprivatemessage>0</isprivatemessage>
        </weappinfo>
</appmsg>
<fromusername>{to_user_id}</fromusername>
<scene>0</scene>
<appinfo>
        <version>1</version>
        <appname />
</appinfo>
<commenturl />"""
    
    logger.info(f"[app_card] 生成药品搜索卡片: {keyword}")
    return card_xml
