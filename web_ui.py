import os
from multiprocessing import Process
import signal
import time
import requests
from logging import getLogger

import gradio as gr

from channel import channel_factory
from common import const
from config import load_config, conf
from plugins import *

logger = getLogger(__name__)
current_process_instance = None

def check_gewechat_online():
    """检查gewechat用户是否在线
    Returns:
        tuple: (是否在线, 错误信息)
    """
    try:
        from lib.gewechat.client import GewechatClient
        base_url = conf().get("gewechat_base_url")
        token = conf().get("gewechat_token")
        app_id = conf().get("gewechat_app_id")
        
        client = GewechatClient(base_url, token)
        online_status = client.check_online(app_id)
        
        if not online_status:
            return False, "获取在线状态失败"
            
        if not online_status.get('data', False):
            logger.info("Gewechat用户未在线")
            return False, "用户未登录"
            
        return True, None
        
    except Exception as e:
        logger.error(f"检查gewechat在线状态失败: {str(e)}")
        return False, f"检查在线状态出错: {str(e)}"

def get_gewechat_profile():
    """获取gewechat用户信息并下载头像，仅在用户在线时返回信息"""
    try:
        is_online, error_msg = check_gewechat_online()
        if not is_online:
            logger.info(f"Gewechat状态检查: {error_msg}")
            return None, None
            
        from lib.gewechat.client import GewechatClient
        base_url = conf().get("gewechat_base_url")
        token = conf().get("gewechat_token")
        app_id = conf().get("gewechat_app_id")
        
        client = GewechatClient(base_url, token)
        profile = client.get_profile(app_id)
        
        if not profile or 'data' not in profile:
            return None, None
            
        user_info = profile['data']
        nickname = user_info.get('nickName', '未知')
        
        # 下载头像
        avatar_url = user_info.get('bigHeadImgUrl')
        avatar_path = None
        
        if avatar_url:
            try:
                avatar_path = 'tmp/avatar.png'
                os.makedirs('tmp', exist_ok=True)
                response = requests.get(avatar_url)
                if response.status_code == 200:
                    with open(avatar_path, 'wb') as f:
                        f.write(response.content)
            except Exception as e:
                logger.error(f"下载头像失败: {str(e)}")
                avatar_path = None
                
        return nickname, avatar_path
    except Exception as e:
        logger.error(f"获取Gewechat用户信息失败: {str(e)}")
        return None, None

def start_channel(channel_name: str):
    channel = channel_factory.create_channel(channel_name)
    available_channels = [
        "wx",
        "terminal",
        "wechatmp",
        "wechatmp_service",
        "wechatcom_app",
        "wework",
        "wechatcom_service",
        "gewechat",
        const.FEISHU,
        const.DINGTALK
    ]
    if channel_name in available_channels:
        PluginManager().load_plugins()
    channel.startup()

def run():
    try:
        # load config
        load_config()
        # create channel
        channel_name = conf().get("channel_type", "wx")
        
        # 获取gewechat用户信息
        if channel_name == "gewechat":
            get_gewechat_profile()

        start_channel(channel_name)
    except Exception as e:
        logger.error("App startup failed!")
        logger.exception(e)

def start_run():
    global current_process_instance

    if current_process_instance is not None and current_process_instance.is_alive():
        os.kill(current_process_instance.pid, signal.SIGTERM)  # 杀掉当前进程
        current_process_instance.join()  # 等待当前进程结束
    
    current_process_instance = Process(target=run)
    current_process_instance.start()
    time.sleep(15)  # 等待进程启动
    load_config()
    # 重启后获取用户状态
    if not current_process_instance.is_alive():
        return (
            gr.update(value="重启失败❌ 请检查日志"),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False)
        )
        
    if conf().get("channel_type") == "gewechat":
        nickname, _ = get_gewechat_profile()
        if nickname:
            return (
                gr.update(value=f"重启成功😀 [{nickname}]🤖  已在线✅"),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=True, value=get_avatar_image())
            )
        else:
            return (
                gr.update(value="重启成功😀 但用户未登录❗"),
                gr.update(visible=True),
                gr.update(visible=True, value=get_qrcode_image()),
                gr.update(visible=False)
            )
    return (
        gr.update(value="重启成功😀"),
        gr.update(visible=True),
        gr.update(visible=True, value=get_qrcode_image()),
        gr.update(visible=False)
    )
    
def get_qrcode_image():
    image_path = 'tmp/login.png'
    if os.path.exists(image_path):
        return image_path
    else:
        return None

def get_avatar_image():
    image_path = 'tmp/avatar.png'
    if os.path.exists(image_path):
        return image_path
    else:
        return None

def verify_login(username, password):
    correct_username = conf().get("web_ui_username", "dow")
    correct_password = conf().get("web_ui_password", "dify-on-wechat")
    if username == correct_username and password == correct_password:
        return True
    return False

def login(username, password):
    if verify_login(username, password):
        # 获取用户信息
        nickname = None
        avatar_path = None
        is_gewechat = conf().get("channel_type") == "gewechat"
        
        if is_gewechat:
            nickname, avatar_path = get_gewechat_profile()
            
        # 根据不同情况决定显示二维码还是头像
        show_qrcode = not (is_gewechat and avatar_path)
        
        # 设置状态信息
        status_text = "启动成功😀 " + (f"[{nickname}]🤖  已在线✅" if nickname else "")
            
        return (
            gr.update(visible=True, value=status_text),  # 在顶部状态栏显示状态
            gr.update(visible=show_qrcode),  # 只在非gewechat或gewechat未登录时显示二维码
            gr.update(visible=True), 
            gr.update(visible=show_qrcode),  # 刷新二维码按钮也只在显示二维码时可见
            gr.update(visible=False),  # Hide username input
            gr.update(visible=False),  # Hide password input
            gr.update(visible=False),   # Hide login button
            gr.update(value=avatar_path, visible=bool(avatar_path)),  # 只在有头像时显示
            gr.update(visible=False),  # Hide login form group
            gr.update(visible=True)  # Show control group
        )
    else:
        return (
            gr.update(visible=True, value="用户名或密码错误"),
            gr.update(visible=False), 
            gr.update(visible=False), 
            gr.update(visible=False),
            gr.update(visible=True),   # Show username input
            gr.update(visible=True),   # Show password input
            gr.update(visible=True),   # Show login button
            gr.update(visible=False),   # Hide avatar
            gr.update(visible=True),  # Show login form group
            gr.update(visible=False)  # Hide control group
        )

with gr.Blocks(title="DoW Web UI", theme=gr.themes.Soft()) as demo:
    # 顶部状态栏
    with gr.Row(equal_height=True):
        with gr.Column(scale=1):
            login_status = gr.Textbox(
                label="状态",
                value="",
                interactive=False,
                visible=True,
                container=True
            )
    
    # 主要内容区
    with gr.Row(equal_height=True):
        # 左侧控制区
        with gr.Column(scale=3, min_width=300):
            # 登录表单
            with gr.Column(visible=True) as login_form:
                with gr.Column(variant="box"):
                    gr.Markdown("### 登录")
                    username_input = gr.Textbox(
                        label="用户名",
                        placeholder="请输入用户名",
                        container=True
                    )
                    password_input = gr.Textbox(
                        label="密码",
                        type="password",
                        placeholder="请输入密码",
                        container=True
                    )
                    with gr.Row():
                        login_button = gr.Button(
                            "登录",
                            variant="primary",
                            scale=2
                        )
            
            # 控制按钮组
            with gr.Column(visible=False) as control_group:
                with gr.Row(equal_height=True, variant="panel"):
                    with gr.Column(scale=1):
                        restart_button = gr.Button(
                            "重启服务",
                            visible=False,
                            variant="primary",
                            size="lg",
                            min_width=120
                        )
                    with gr.Column(scale=1):
                        refresh_button = gr.Button(
                            "刷新二维码",
                            visible=False,
                            variant="primary",
                            size="lg",
                            min_width=120
                        )
        
        # 右侧图片区
        with gr.Column(scale=4):
            with gr.Column(variant="box"):
                qrcode_image = gr.Image(
                    value=get_qrcode_image(),
                    label="微信登录二维码",
                    show_label=True,
                    container=True,
                    visible=False,
                    height=450
                )
                user_avatar = gr.Image(
                    value=get_avatar_image(),
                    label="当前登录用户",
                    show_label=True,
                    container=True,
                    visible=False,
                    height=450
                )

    # 事件处理
    login_button.click(
        login,
        inputs=[username_input, password_input],
        outputs=[
            login_status,
            qrcode_image,
            restart_button,
            refresh_button,
            username_input,
            password_input,
            login_button,
            user_avatar,
            login_form,
            control_group
        ]
    )

    restart_button.click(
        start_run,
        outputs=[
            login_status,
            refresh_button,
            qrcode_image,
            user_avatar
        ]
    )

    
    refresh_button.click(get_qrcode_image, outputs=qrcode_image)
    
    # TODO: 增加退出登录按钮
    
    # TODO: 退出与重启需要二次确认

if __name__ == "__main__":
    start_run()
    demo.launch(server_name="0.0.0.0", server_port=conf().get("web_ui_port", 7860))
