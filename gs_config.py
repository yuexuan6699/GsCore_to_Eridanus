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
        return {
            'BOT_ID': self.config.config.get('BOT_ID', 'Eridanus'),
            'IP': self.config.config.get('IP', '127.0.0.1'),
            'PORT': self.config.config.get('PORT', 8765),
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
            self.config.config['BOT_ID'] = bot_id
        if ip is not None:
            self.config.config['IP'] = ip
        if port is not None:
            self.config.config['PORT'] = port
        
        # 保存配置
        self.config.save_yaml()
    
    def get_plugin_config(self, plugin_name: str) -> dict:
        """
        获取指定插件的配置
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件配置字典
        """
        return getattr(self.config, plugin_name, {}).get('config', {})
    
    def update_plugin_config(self, plugin_name: str, config: dict):
        """
        更新指定插件的配置
        
        Args:
            plugin_name: 插件名称
            config: 新的配置字典
        """
        if not hasattr(self.config, plugin_name):
            setattr(self.config, plugin_name, {})
        
        self.config[plugin_name]['config'] = config
        self.config.save_yaml()