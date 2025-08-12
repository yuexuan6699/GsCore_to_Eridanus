"""
数据结构定义
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class Message:
    """
    消息组件
    """
    type: str
    data: str

@dataclass
class MessageReceive:
    """
    接收消息
    """
    bot_id: str
    bot_self_id: str
    user_type: str
    group_id: Optional[str]
    user_id: str
    sender: Dict[str, Any]
    content: List[Message]
    msg_id: str
    user_pm: int

@dataclass
class MessageSend:
    """
    发送消息
    """
    bot_id: str
    target_type: str
    target_id: str
    content: List[Message]
    msg_id: Optional[str] = None