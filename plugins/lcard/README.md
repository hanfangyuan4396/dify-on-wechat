## 插件描述

#### 如何查看发送卡片类型的xml参数？

 `打开 ntchat_channel.py`

- 群聊下开启监听：

      def handle_group(self, cmsg: ChatMessage):         # 此函数下取消注释print(cmsg)

- 私聊下开启监听：

      def handle_single(self, cmsg: ChatMessage):        # 此函数下取消注释print(cmsg)

- 如何知道某个卡片类型的xml结构是什么样子？
         
      取消以上注释后，即可开启监听日志，使用bot账号转发一下你想发送的卡片类型到群聊或者私聊，即可在日志看到相关xml（必须是bot账号转发卡片）
 已知直播，视频号，链接卡片，小程序，聊天记录，音乐卡片类型全是xml结构，自己转发你想要发送的卡片类型，即可获得该卡片的xml，替换xml里相关参数，ReplyType.LINK发送xml即可实现发送该卡片


- 小程序没有图片？

        小程序的图片有时效性，需要定期更换图片的url，觉得麻烦可以不换，不影响小程序打开。


- 默认使用官方QQ音乐的卡片播放！这个卡片类型只能播放官方的QQ音乐歌曲，也可以使用app_card.py下的`def mp3_linK()xml`
这个xml结构可播放第三方音乐url，即卡片式mp3,不过样式不如官方的好看。
        