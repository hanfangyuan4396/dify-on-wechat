我来完善下 docker-xyb-readme.md 的内容：

```markdown:/usr/docker-xiaoyanbao/dify-on-wechat/docker-xyb-readme.md
```

# 小妍宝 Docker 部署指南

## 一、系统要求
- Docker 版本 >= 20.10.0
- Docker Compose 版本 >= 2.0.0
- 内存 >= 2GB
- 硬盘空间 >= 10GB

## 二、部署步骤

### 1. 创建项目目录
```bash
mkdir -p /usr/docker-xiaoyanbao
cd /usr/docker-xiaoyanbao
```

### 2. 部署 GeWeChat 服务

#### 方式一：直接运行容器
```bash
# 从阿里云镜像仓库拉取(国内)
docker pull registry.cn-chengdu.aliyuncs.com/tu1h/wechotd:alpine
docker tag registry.cn-chengdu.aliyuncs.com/tu1h/wechotd:alpine gewe
```

#### 创建数据目录并启动服务
```bash
mkdir -p gewechat/data  
docker run -itd -v ./gewechat/data:/root/temp -p 2531:2531 -p 2532:2532 --restart=always --name=gewe gewe

```

#### 方式二：使用 docker-compose（推荐）
创建 `gewe-xiaoyanbao.yml` 文件：

```yaml
version: '3'

networks:
  network-xiaoyanbao:
    external: true
    name: network-xiaoyanbao

services:
  gewe03:
    container_name: gewe-xiaoyanbao
    image: gewe
    restart: always
    networks:
      - network-xiaoyanbao
    ports:
      - "32531:2531"  # 映射微信API服务端口
      - "32532:2532"  # 映射微信下载服务端口
    volumes:
      - ./tmp:/var/www/html  # 挂载临时文件目录

```

### 3. 配置文件设置

创建 `config.json` 文件：

```json
{
    "channel_type": "gewechat",
    "character_desc": "你是小妍宝，是小x宝社区的一员，服务乳腺癌患者，提供乳房重建和乳腺癌治疗的AI智能助手，7x24小时专业陪伴，温暖呵护。",
    "gemini_api_key": "your_gemini_key",
    "gewechat_app_id": "",
    "gewechat_base_url": "http://gewe-xiaoyanbao:2531/v2/api",
    "gewechat_callback_url": "http://dow-xyb-test:9919/v2/api/callback/collect",
    "gewechat_download_url": "http://gewe-xiaoyanbao:2532/download",
    "gewechat_token": "",
    "group_chat_in_one_session": [""],
    "group_chat_prefix": [
        "bb",
        "@xybb",
        "@小妍宝宝"
    ],
    "group_chat_suffix": [],
    "group_name_white_list": ["ALL_GROUP"],
    "group_userid_black_list": [],
    "image_recognition": true,
    "model": "gpt-4o-mini",
    "open_ai_api_base": "https://admin.xiaoyibao.com.cn/api/v1",
    "open_ai_api_key": "your_api_key",
    "single_chat_prefix": [
        "xyb",
        "bb",
        "@小妍宝宝",
        ""
    ],
    "single_chat_reply_prefix": "[小妍宝] ",
    "speech_recognition": false,
    "text_to_voice": "",
    "voice_reply_voice": false,
    "voice_to_text": ""
}
```

### 4. 部署 DOW 服务

创建 `dow-xyb-test.yml` 文件：

```yaml
version: '3'

networks:
  network-xiaoyanbao:
    external: true

services:
  dow03:
    container_name: dow-xyb-test
    image: ccr.ccs.tencentyun.com/xiaoyibao/dify-on-wechat-xyb:latest #这是小x宝社区的定制版本
    restart: always
    networks:
      - network-xiaoyanbao
    ports:
      - "39919:9919"  # 映射回调服务端口
    environment:
      TZ: 'Asia/Shanghai'
    volumes:
      - ./config.json:/app/config.json
      - ./tmp:/app/tmp
      - ./run.log:/app/run.log
      - ./plugins:/app/plugins
```

### 5. 启动服务

1. 创建网络：
```bash
docker network create network-xiaoyanbao
```

2. 启动 GeWeChat 服务：
```bash
docker compose -f gewe-xiaoyanbao.yml up -d
```

3. 等待 3-5 分钟后，启动 DOW 服务：
```bash
docker compose -f dow-xyb-test.yml up -d
```

### 6. 验证部署

1. 查看容器状态：
```bash
docker ps | grep -E 'gewe|dow'
```

2. 查看服务日志：
```bash
# 查看 GeWeChat 日志
docker logs -f gewe-xiaoyanbao

# 查看 DOW 日志
docker logs -f dow-xyb-test
```

参考的yml文件看下docker_compose_samples目录

3. 扫码登录：
- 在 DOW 服务日志中会显示二维码链接
- 使用微信扫描二维码进行登录

## 三、常见问题

### 1. 服务无法启动
- 检查端口是否被占用
- 检查配置文件格式是否正确
- 检查网络配置是否正确

### 2. 无法扫码登录
- 确保 GeWeChat 服务已完全启动
- 检查网络连接是否正常
- 查看日志中的具体错误信息

### 3. 消息无法接收
- 检查回调地址配置
- 确认网络连接正常
- 查看 DOW 服务日志

## 四、维护指南

### 1. 日志查看
- 服务日志：`./run.log`
- 容器日志：使用 `docker logs` 命令

### 2. 配置更新
1. 修改 `config.json` 文件
2. 重启 DOW 服务：
```bash
docker compose -f dow-xyb-test.yml restart
```

### 3. 版本更新
1. 拉取新镜像
2. 重新部署服务

### 4. 数据备份
- 定期备份 `tmp` 目录
- 备份 `config.json` 配置文件
- 备份 `run.log` 日志文件
```

##插件说明
本次容器修改，参照社区实际使用，结合其它开源项目如lcard，geminiimg等作者（感谢作者！），提供如下插件功能

## 知识查询增强RAG不足/偏差
- 提供metaso卡片，提问是 “搜索 + （q）”，返回metaso卡片，点击后为搜索结果，非常实用，对于RAG偏差是很方便的补充和校准
- 提供baidu搜索卡片，提问触发“百度+（q）
- 提供药物查询，提问触发词 “用药 + 药品名称”或者 “药品 + 查询药品名称”

## 提供病友生活日常协助
- 音乐点歌：提供搜狗/网易云音乐，通过“随机点歌”，或者“搜狗点歌+歌曲名”，“网易点歌+歌曲名”，触发卡片，让患者家属在音乐中获取片刻轻松和安抚
- 生活查询：
    - 天气：发送“地名+天气”，获得14天预报，方便出行
    - 外卖：发送“美团外卖”
    - 营养：发送“营养视频”，获得复旦肿瘤医院的专业营养指导视频号内容
```

### 后续开发
- [ ] 临床查询助手的卡片增强
- [ ] 其它病友实用小程序，如用药助手，就诊问问等卡片增强
