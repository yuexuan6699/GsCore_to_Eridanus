"""
早柚核心Docs适配器
"""
import asyncio
import base64
import os
import time
from base64 import b64encode
from pathlib import Path
from typing import List, Union

import aiofiles
import websockets.client
from msgspec import json as msgjson
from websockets.exceptions import ConnectionClosed, ConnectionClosedError

from framework_common.framework_util.websocket_fix import ExtendBot
from framework_common.framework_util.yamlLoader import YAMLManager
from developTools.event.events import GroupMessageEvent, PrivateMessageEvent
from developTools.message.message_components import (
    At,
    File,
    Image,
    Text,
    Record,
    Video,
    MessageComponent
)


class GsCoreAdapter:
    """
    早柚核心Docs适配器
    """
    def __init__(self, bot, config):
        """
        初始化适配器
        
        Args:
            bot: Eridanus的Bot对象
            config: 配置管理器
        """
        self.bot = bot
        self.config = config
        self.is_connect = False
        self.BOT_ID = config.gs_core.get("BOT_ID", "Eridanus")
        self.IP = config.gs_core.get("IP", "127.0.0.1")
        self.PORT = config.gs_core.get("PORT", 8765)
        self.ws_url = f'ws://{self.IP}:{self.PORT}/ws/{self.BOT_ID}'
        self.msg_list = asyncio.queues.Queue()
        self.pending = []
        
    async def connect(self):
        """
        连接到早柚核心
        """
        if not self.is_connect:
            try:
                self.bot.logger.info(f'正在连接到[gsuid-core]: {self.ws_url}...')
                self.ws = await websockets.client.connect(
                    self.ws_url, max_size=2**26, open_timeout=60, ping_timeout=60
                )
                self.is_connect = True
                # 启动消息处理任务
                recv_task = asyncio.create_task(self.recv_msg())
                send_task = asyncio.create_task(self.send_msg())
                self.pending = [recv_task, send_task]
                self.bot.logger.info('[gsuid-core]: 连接成功')
                return True
            except websockets.exceptions.InvalidURI as e:
                self.bot.logger.error(f'[链接错误] 无效的URI: {e}')
                self.is_connect = False
            except websockets.exceptions.NegotiationError as e:
                self.bot.logger.error(f'[链接错误] 协议协商失败: {e}')
                self.is_connect = False
            except websockets.exceptions.InvalidHandshake as e:
                self.bot.logger.error(f'[链接错误] 握手失败: {e}')
                self.is_connect = False
            except Exception as e:
                self.bot.logger.error(f'[链接错误] Core服务器连接失败: {e}')
                self.is_connect = False
            return False
    
    async def disconnect(self):
        """
        断开与早柚核心的连接
        """
        self.is_connect = False
        if hasattr(self, 'ws'):
            await self.ws.close()
        for task in self.pending:
            task.cancel()
    
    async def send_msg(self):
        """
        发送消息到早柚核心
        """
        while True:
            try:
                msg: dict = await self.msg_list.get()
                self.bot.logger.debug(f'从消息队列中取出消息: {msg}')
                
                # 编码消息
                try:
                    msg_send = msgjson.encode(msg)
                except Exception as e:
                    self.bot.logger.error(f'消息编码失败: {e}')
                    self.bot.logger.debug(f'无法编码的消息: {msg}')
                    continue
                
                # 发送消息
                self.bot.logger.debug(f'准备发送消息到早柚核心')
                await self.ws.send(msg_send)
                self.bot.logger.debug(f'消息发送到早柚核心完成')
            except asyncio.CancelledError:
                self.bot.logger.info('消息发送任务被取消')
                break
            except Exception as e:
                self.bot.logger.error(f'发送消息时出错: {e}')
                import traceback
                self.bot.logger.critical(traceback.format_exc())
                # 发生严重错误时断开连接并尝试重连
                self.is_connect = False
                await self.reconnect()
    
    async def recv_msg(self):
        """
        接收来自早柚核心的消息
        """
        try:
            async for message in self.ws:
                try:
                    # 解码消息
                    msg = msgjson.decode(message)
                    self.bot.logger.debug(f'收到原始消息: {message}')
                    
                    # 记录消息基本信息
                    bot_id = msg.get("bot_id", "")
                    target_type = msg.get("target_type", "")
                    target_id = msg.get("target_id", "")
                    self.bot.logger.info(
                        f'【接收】[gsuid-core]: '
                        f'{bot_id} - {target_type} - {target_id}'
                    )
                    
                    # 处理接收到的消息
                    await self.handle_gs_message(msg)
                except msgjson.DecodeError as e:
                    self.bot.logger.error(f'消息解码失败: {e}')
                    self.bot.logger.debug(f'无法解码的消息内容: {message}')
                except Exception as e:
                    self.bot.logger.error(f'处理消息时出错: {e}')
                    import traceback
                    self.bot.logger.critical(traceback.format_exc())
        except ConnectionClosedError as e:
            self.bot.logger.warning(f'与[gsuid-core]断开连接: {e}')
            self.is_connect = False
            # 尝试重连
            await self.reconnect()
        except Exception as e:
            self.bot.logger.error(f'接收消息时发生未预期的错误: {e}')
            import traceback
            self.bot.logger.critical(traceback.format_exc())
            # 发生严重错误时断开连接并尝试重连
            self.is_connect = False
            await self.reconnect()
    
    async def reconnect(self):
        """
        重新连接到早柚核心
        """
        max_retries = self.config.get('max_reconnect_attempts', 30)
        retry_interval = self.config.get('reconnect_interval', 5)
        
        for attempt in range(max_retries):
            await asyncio.sleep(retry_interval)
            try:
                self.bot.logger.info(f'[gsuid-core] 尝试重新连接 (尝试 {attempt + 1}/{max_retries})')
                success = await self.connect()
                if success:
                    self.bot.logger.info('[gsuid-core] 重新连接成功')
                    break
            except Exception as e:
                self.bot.logger.error(f'[gsuid-core] 重新连接失败 (尝试 {attempt + 1}/{max_retries}): {e}')
        else:
            self.bot.logger.error('[gsuid-core] 达到最大重连次数，放弃重新连接')
    
    async def handle_gs_message(self, msg: dict):
        """
        处理来自早柚核心的消息
        
        Args:
            msg: 来自早柚核心的消息
        """
        # 检查消息格式
        if not msg or not isinstance(msg, dict):
            self.bot.logger.warning('收到无效的消息格式')
            return
            
        # 检查消息内容
        content = msg.get('content')
        if not content or not isinstance(content, list) or len(content) == 0:
            self.bot.logger.debug('收到空消息内容')
            return
            
        # 解析日志消息
        if len(content) > 0:
            _data = content[0]
            if _data and isinstance(_data, dict) and _data.get('type') and str(_data.get('type', '')).startswith('log'):
                _type = str(_data['type']).split('_')[-1].lower()
                log_data = _data.get('data', '')
                if _type in ['debug', 'info', 'warning', 'error', 'critical']:
                    getattr(self.bot.logger, _type)(log_data)
                return
        
        # 发送消息到Eridanus
        target_id = msg.get('target_id')
        target_type = msg.get('target_type', '')
        
        if not target_id:
            self.bot.logger.warning('消息缺少目标ID')
            return
            
        try:
            # 转换消息格式
            eridanus_msg = await self._to_eridanus_msg(content)
            
            # 检查转换后的消息是否为空
            if not eridanus_msg:
                self.bot.logger.debug('转换后的消息为空')
                return
                
            # 根据目标类型发送消息
            if target_type == 'group':
                await self.bot.send_group_message(int(target_id), eridanus_msg)
                self.bot.logger.debug(f'群消息发送完成到 {target_id}')
            elif target_type == 'direct':
                await self.bot.send_friend_message(int(target_id), eridanus_msg)
                self.bot.logger.debug(f'私聊消息发送完成到 {target_id}')
            else:
                self.bot.logger.warning(f'未知的目标类型: {target_type}')
                
        except Exception as e:
            self.bot.logger.error(f'处理消息时出错: {e}')
            import traceback
            self.bot.logger.critical(traceback.format_exc())
    
    async def _to_eridanus_msg(self, msg: List[dict]) -> List[MessageComponent]:
        """
        将早柚核心消息转换为Eridanus消息
        
        Args:
            msg: 早柚核心消息列表
            
        Returns:
            转换后的Eridanus消息列表
        """
        if not msg or not isinstance(msg, list):
            return []
            
        message = []
        for _c in msg:
            if not _c or not isinstance(_c, dict):
                continue
                
            try:
                _data = _c.get('data')
                if _data is None:
                    continue
                    
                _type = str(_c.get('type', ''))
                _data_str = str(_data)
                
                if _type == 'text':
                    message.append(Text(text=_data_str))
                elif _type == 'image':
                    # 处理图片消息
                    if _data_str.startswith('link://'):
                        message.append(Image(file=_data_str[7:]))
                    elif _data_str.startswith('base64://'):
                        # 保存base64图片到临时文件
                        base64_data = _data_str[9:]
                        temp_path = self._save_base64_to_temp_file(base64_data, ".jpg")
                        message.append(Image(file=temp_path))
                    else:
                        message.append(Image(file=_data_str))
                elif _type == 'file':
                    # 处理文件消息
                    file_parts = _data_str.split('|')
                    if len(file_parts) == 2:
                        file_name, file_content = file_parts
                        temp_path = self._save_base64_to_temp_file(file_content, file_name)
                        message.append(File(file=temp_path, name=file_name))
                elif _type == 'at':
                    try:
                        qq_num = int(_data_str)
                        message.append(At(qq=qq_num))
                    except (ValueError, TypeError):
                        self.bot.logger.warning(f'无效的QQ号: {_data_str}')
                elif _type == 'record':
                    # 处理语音消息
                    if _data_str.startswith('base64://'):
                        base64_data = _data_str[9:]
                        temp_path = self._save_base64_to_temp_file(base64_data, ".mp3")
                        message.append(Record(file=temp_path))
                    else:
                        message.append(Record(file=_data_str))
                elif _type == 'video':
                    # 处理视频消息
                    if _data_str.startswith('base64://'):
                        base64_data = _data_str[9:]
                        temp_path = self._save_base64_to_temp_file(base64_data, ".mp4")
                        message.append(Video(file=temp_path))
                    else:
                        message.append(Video(file=_data_str))
            except Exception as e:
                self.bot.logger.error(f'转换消息组件时出错: {e}')
                continue
                
        return message
    
    def _save_base64_to_temp_file(self, base64_data: str, file_name: str) -> str:
        """
        将base64数据保存到指定目录
        
        Args:
            base64_data: base64编码的数据
            file_name: 文件名
            
        Returns:
            文件路径
        """
        # 创建目标目录 (使用相对路径)
        target_dir = Path(__file__).parent.parent.parent / "data" / "gs_core"
        self.bot.logger.debug(f'[调试] 目标目录路径: {target_dir}')
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            self.bot.logger.debug(f'[调试] 目录创建成功或已存在')
        except Exception as e:
            self.bot.logger.error(f'[错误] 目录创建失败: {e}')
            raise
        
        # 解码base64数据
        try:
            file_content = base64.b64decode(base64_data)
            self.bot.logger.debug(f'[调试] base64解码成功，数据长度: {len(file_content)}')
        except Exception as e:
            self.bot.logger.critical(f'[错误] base64解码失败: {e}')
            raise
        
        # 生成唯一文件名避免冲突
        timestamp = str(int(time.time() * 1000))  # 使用毫秒级时间戳
        # 确保文件名是安全的
        safe_file_name = "".join(c for c in file_name if c.isalnum() or c in (' ', '.', '_')).rstrip()
        unique_name = f"{timestamp}_{safe_file_name}"
        file_path = target_dir / unique_name
        
        # 调试日志
        self.bot.logger.debug(f'[调试] 原始文件名: {file_name}, 安全文件名: {safe_file_name}, 唯一文件名: {unique_name}')
        
        # 写入文件
        try:
            with open(file_path, 'wb') as f:
                f.write(file_content)
            # 调试日志
            self.bot.logger.debug(f'[调试] 文件已保存至: {file_path}')
            # 验证文件是否真的存在
            if not file_path.exists():
                self.bot.logger.critical(f'[错误] 文件保存后验证失败，文件不存在: {file_path}')
                raise FileNotFoundError(f'文件保存后验证失败，文件不存在: {file_path}')
        except Exception as e:
            self.bot.logger.critical(f'[错误] 文件保存失败: {e}')
            raise
        
        # 返回文件路径
        return str(file_path)
    
    async def handle_eridanus_message(self, event: Union[GroupMessageEvent, PrivateMessageEvent]):
        """
        处理来自Eridanus的消息
        
        Args:
            event: Eridanus消息事件
        """
        # 检查消息链是否为空
        if not event.message_chain:
            self.bot.logger.debug('收到空消息链')
            return
            
        # 检查消息前缀 - 只在第一条Text消息上检查
        prefix = self.config.gs_core.get('MESSAGE_PREFIX', '')
        if prefix:
            first_text_msg = None
            for msg in event.message_chain:
                if isinstance(msg, Text) and msg.text:
                    first_text_msg = msg
                    break
            
            if first_text_msg:
                text_content = str(first_text_msg.text)
                if not text_content.startswith(prefix):
                    self.bot.logger.debug(f'消息前缀不匹配，跳过处理: {text_content}')
                    return
                
                # 去除前缀
                new_text = text_content[len(prefix):].lstrip()
                first_text_msg.text = new_text
        
        # 确保已连接
        if not self.is_connect:
            await self.connect()
        
        # 检查连接状态
        if not hasattr(self, 'ws'):
            self.bot.logger.critical('[链接错误] Core服务器连接失败')
            return
        
        # 获取发送者信息
        user_name = event.sender.nickname if event.sender.nickname else "Unknown"
        sender = {
            'nickname': user_name,
        }
        
        # 获取平台信息
        pn = "qq"  # 默认为QQ平台
        self_id = str(event.self_id)
        user_id = str(event.user_id)
        
        # 构造消息链
        message: List[dict] = []
            
        for msg in event.message_chain:
            if not msg:
                continue
                
            try:
                if isinstance(msg, Text):
                    # 使用可能被前缀处理修改过的文本内容
                    text_content = str(msg.text) if msg.text else ''
                    message.append({
                        'type': 'text',
                        'data': text_content,
                    })
                elif isinstance(msg, Image):
                    # 处理图片消息
                    if hasattr(msg, 'file') and msg.file:
                        if str(msg.file).startswith('http'):
                            message.append({
                                'type': 'image',
                                'data': str(msg.file),
                            })
                        else:
                            # 读取本地文件并转换为base64
                            try:
                                base64_data = await self._file_to_base64(Path(str(msg.file)))
                                if base64_data:
                                    message.append({
                                        'type': 'image',
                                        'data': f'base64://{base64_data}',
                                    })
                            except Exception as e:
                                self.bot.logger.critical(f'处理图片文件时出错: {e}')
                    else:
                        self.bot.logger.warning('收到空图片消息')
                elif isinstance(msg, File):
                    # 处理文件消息
                    if hasattr(msg, 'file') and msg.file and hasattr(msg, 'name') and msg.name:
                        file_path = str(msg.file)
                        file_name = str(msg.name)
                        
                        if file_path.startswith('http'):
                            message.append({
                                'type': 'file',
                                'data': f'{file_name}|{file_path}',
                            })
                        else:
                            # 读取本地文件并转换为base64
                            try:
                                base64_data = await self._file_to_base64(Path(file_path))
                                if base64_data:
                                    message.append({
                                        'type': 'file',
                                        'data': f'{file_name}|{base64_data}',
                                    })
                            except Exception as e:
                                self.bot.logger.critical(f'处理文件时出错: {e}')
                    else:
                        self.bot.logger.warning('收到空文件消息')
                elif isinstance(msg, At):
                    if hasattr(msg, 'qq') and msg.qq:
                        try:
                            qq_num = int(msg.qq)
                            message.append({
                                'type': 'at',
                                'data': str(qq_num),
                            })
                        except (ValueError, TypeError):
                            self.bot.logger.warning(f'无效的@消息QQ号: {msg.qq}')
                # TODO: 处理其他类型的消息组件
            except Exception as e:
                self.bot.logger.critical(f'处理消息组件时出错: {e}')
                import traceback
                self.bot.logger.critical(traceback.format_exc())
                continue
        
        # 确定用户类型
        user_type = 'group' if isinstance(event, GroupMessageEvent) else 'direct'
        
        # 确定用户权限
        pm = 6  # 默认普通用户权限
        try:
            if hasattr(event, 'sender') and event.sender and hasattr(event.sender, 'role'):
                role = str(event.sender.role).lower()
                if role == 'owner':
                    pm = 2
                elif role == 'admin':
                    pm = 3
        except Exception as e:
            self.bot.logger.debug(f'确定用户权限时出错: {e}')
        
        # 检查消息是否为空
        if not message:
            self.bot.logger.debug('构造的消息为空，跳过发送')
            return
            
        # 构造消息对象
        try:
            group_id = None
            if isinstance(event, GroupMessageEvent) and hasattr(event, 'group_id'):
                group_id = str(event.group_id)
                
            msg = {
                'bot_id': pn,
                'bot_self_id': self_id,
                'user_type': user_type,
                'group_id': group_id,
                'user_id': user_id,
                'sender': sender,
                'content': message,
                'msg_id': str(event.message_id),
                'user_pm': pm,
            }
            
            # 发送到消息队列
            self.bot.logger.debug(f'准备将消息放入队列: {msg}')
            await self.msg_list.put(msg)
            self.bot.logger.debug(f'消息已放入队列')
            
        except Exception as e:
            self.bot.logger.critical(f'构造或发送消息对象时出错: {e}')
            import traceback
            self.bot.logger.error(traceback.format_exc())
    
    async def _file_to_base64(self, file_path: Path) -> str:
        """
        将文件转换为base64编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            base64编码的字符串
        """
        try:
            # 检查输入参数
            if not file_path:
                self.bot.logger.critical('[文件错误] 文件路径为空')
                return ""
                
            file_path_str = str(file_path)
            if not file_path_str:
                self.bot.logger.critical('[文件错误] 文件路径字符串为空')
                return ""
                
            # 处理file://和file:前缀
            if file_path_str.startswith('file://'):
                file_path = Path(file_path_str[7:])  # 移除'file://'前缀
            elif file_path_str.startswith('file:'):
                file_path = Path(file_path_str[6:])  # 移除'file:'前缀
            
            # 检查文件是否存在
            if not file_path.exists():
                # 尝试在data/gs_core目录中查找文件
                data_dir = Path(__file__).parent.parent.parent / "data" / "gs_core"
                alternative_path = data_dir / file_path.name
                self.bot.logger.debug(f'[调试] 尝试在 {data_dir} 中查找文件: {file_path.name}')
                
                if alternative_path.exists():
                    self.bot.logger.debug(f'[调试] 在替代路径找到文件: {alternative_path}')
                    file_path = alternative_path
                else:
                    self.bot.logger.debug(f'[文件错误] 文件不存在: {file_path} 且在 {data_dir} 中也未找到')
                    return ""  # 或者返回一个默认的base64字符串
                
            # 检查文件是否为空
            file_size = file_path.stat().st_size
            if file_size == 0:
                self.bot.logger.warning(f'[文件警告] 文件为空: {file_path}')
                return ""
                
            # 对于大文件，分块读取以避免内存问题
            if file_size > 10 * 1024 * 1024:  # 大于10MB的文件
                self.bot.logger.debug(f'[调试] 大文件分块读取: {file_path}')
                encoded_chunks = []
                async with aiofiles.open(str(file_path), 'rb') as file:
                    while True:
                        chunk = await file.read(8192)  # 8KB块
                        if not chunk:
                            break
                        encoded_chunks.append(b64encode(chunk).decode('utf-8'))
                return ''.join(encoded_chunks)
            else:
                # 读取文件并转换为base64
                async with aiofiles.open(str(file_path), 'rb') as file:
                    file_content = await file.read()
                    
                # 检查读取的内容是否为空
                if not file_content:
                    self.bot.logger.warning(f'[文件警告] 文件内容为空: {file_path}')
                    return ""
                    
                base64_encoded = b64encode(file_content)
                return base64_encoded.decode('utf-8')
            
        except FileNotFoundError:
            self.bot.logger.error(f'[文件错误] 文件未找到: {file_path}')
            return ""
        except PermissionError:
            self.bot.logger.critical(f'[文件错误] 没有权限访问文件: {file_path}')
            return ""
        except Exception as e:
            self.bot.logger.critical(f'[文件错误] 处理文件时出错: {e}')
            import traceback
            self.bot.logger.error(traceback.format_exc())
            return ""

def main(bot, config):
    """
    插件入口函数
    
    Args:
        bot: Eridanus的Bot对象
        config: 配置管理器
    """
    # 创建适配器实例
    adapter = GsCoreAdapter(bot, config.gs_core)
    
    # 注册事件监听器
    @bot.on(GroupMessageEvent)
    async def handle_group_message(event: GroupMessageEvent):
        await adapter.handle_eridanus_message(event)
    
    @bot.on(PrivateMessageEvent)
    async def handle_private_message(event: PrivateMessageEvent):
        await adapter.handle_eridanus_message(event)


__all__ = ['main']