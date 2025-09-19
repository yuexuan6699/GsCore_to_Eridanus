"""
配置服务
"""
import os
from pathlib import Path

from framework_common.framework_util.yamlLoader import YAMLManager


class ConfigService:
    """
    配置服务类
    """
    def __init__(self, config: YAMLManager):
        """
        初始化配置服务
        
        Args:
            config: YAML配置管理器
        """
        self.config = config
        
    def get_core_config(self) -> dict:
        """
        获取早柚核心配置
        
        Returns:
            核心配置字典
        """
        # 正确的配置访问路径：config.{插件文件夹名}.{yaml文件名}[配置节点]
        return {
            'BOT_ID': self.config.GsCore_to_Eridanus.gs_core['config'].get('BOT_ID', 'Eridanus'),
            'IP': self.config.GsCore_to_Eridanus.gs_core['config'].get('IP', '127.0.0.1'),
            'PORT': self.config.GsCore_to_Eridanus.gs_core['config'].get('PORT', 8765),
        }
    
    def update_core_config(self, bot_id: str = None, ip: str = None, port: int = None):
        """
        更新早柚核心配置
        
        Args:
            bot_id: Bot ID
            ip: IP地址
            port: 端口号
        """
        if bot_id is not None:
            self.config.GsCore_to_Eridanus.gs_core['config']['BOT_ID'] = bot_id
        if ip is not None:
            self.config.GsCore_to_Eridanus.gs_core['config']['IP'] = ip
        if port is not None:
            self.config.GsCore_to_Eridanus.gs_core['config']['PORT'] = port
        
        # 保存配置
        self.config.save_yaml("gs_core", plugin_name="GsCore_to_Eridanus")
    
    def get_plugin_config(self, plugin_name: str) -> dict:
        """
        获取指定插件的配置
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件配置字典
        """
        # 正确的配置访问路径：config.{插件文件夹名}.{yaml文件名}[配置节点]
        return getattr(self.config.GsCore_to_Eridanus, plugin_name, {}).get('config', {})

    def update_plugin_config(self, plugin_name: str, config: dict):
        """
        更新指定插件的配置
        
        Args:
            plugin_name: 插件名称
            config: 新的配置字典
        """
        # 确保插件配置命名空间存在
        if not hasattr(self.config.GsCore_to_Eridanus, plugin_name):
            setattr(self.config.GsCore_to_Eridanus, plugin_name, {})
        
        # 更新配置
        self.config.GsCore_to_Eridanus[plugin_name]['config'] = config
        
        # 保存配置，指定正确的插件名称和配置文件名
        self.config.save_yaml(plugin_name, plugin_name="GsCore_to_Eridanus")
