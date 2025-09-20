"""
.msg文件处理工具模块
提供处理Outlook .msg文件的功能
"""

import os
import extract_msg
from typing import List, Dict, Any, Optional
from src.core.logger import logger


def process_msg_file(file_path: str) -> Dict[str, Any]:
    """
    处理.msg文件，提取邮件信息和附件

    Args:
        file_path: .msg文件路径

    Returns:
        包含邮件信息和附件的字典
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"MSG文件不存在: {file_path}")
            return {"success": False, "error": f"文件不存在: {file_path}"}

        logger.info(f"正在处理MSG文件: {file_path}")

        # 打开.msg文件
        msg = extract_msg.Message(file_path)

        # 提取邮件基本信息
        email_info = {
            'subject': getattr(msg, 'subject', '') or '',
            'sender': getattr(msg, 'sender', '') or '',
            'received_time': getattr(msg, 'date', '') or '',
            'body': getattr(msg, 'body', '') or '',
            'attachments': []
        }

        # 提取附件
        if hasattr(msg, 'attachments'):
            for i, attachment in enumerate(msg.attachments):
                try:
                    # 处理嵌套的邮件对象作为附件
                    if isinstance(attachment, extract_msg.Message):
                        # 这是一个嵌套的邮件对象，将其作为.msg附件处理
                        filename = getattr(attachment, 'subject', f'attached_message_{i}') + '.msg'
                        # 为嵌套邮件创建简单的字节表示
                        attachment_data = f"Embedded message: {filename}".encode('utf-8')
                        attachment_size = len(attachment_data)

                        attachment_info = {
                            'filename': filename,
                            'size': attachment_size,
                            'content': attachment_data
                        }

                        email_info['attachments'].append(attachment_info)
                        logger.debug(f"提取嵌套邮件附件: {filename}, 大小: {attachment_size} 字节")
                        continue

                    # 处理普通附件
                    filename = getattr(attachment, 'longFilename', None) or \
                              getattr(attachment, 'filename', f'attachment_{i}')

                    # 安全地获取附件数据
                    attachment_data = None
                    attachment_size = 0

                    if hasattr(attachment, 'data'):
                        data = attachment.data
                        if data is not None:
                            try:
                                attachment_size = len(data)
                                attachment_data = data
                            except TypeError:
                                # 如果无法获取长度，则设置为0
                                attachment_size = 0
                                attachment_data = data

                    attachment_info = {
                        'filename': filename,
                        'size': attachment_size,
                        'content': attachment_data
                    }

                    email_info['attachments'].append(attachment_info)
                    logger.debug(f"提取附件: {filename}, 大小: {attachment_size} 字节")
                except Exception as e:
                    logger.warning(f"处理附件时出错: {e}")
                    continue

        msg.close()

        logger.info(f"成功处理MSG文件，提取到 {len(email_info['attachments'])} 个附件")
        return {"success": True, "email_data": email_info}

    except FileNotFoundError:
        logger.error(f"MSG文件未找到: {file_path}")
        return {"success": False, "error": f"文件未找到: {file_path}"}
    except PermissionError:
        logger.error(f"没有权限访问MSG文件: {file_path}")
        return {"success": False, "error": f"没有权限访问文件: {file_path}"}
    except extract_msg.exceptions.StandardViolationError as e:
        logger.error(f"MSG文件格式错误: {e}")
        return {"success": False, "error": f"文件格式错误: {str(e)}"}
    except Exception as e:
        logger.error(f"处理MSG文件时出错: {e}")
        return {"success": False, "error": f"处理文件时出错: {str(e)}"}


def validate_msg_file(file_path: str) -> Dict[str, Any]:
    """
    验证.msg文件

    Args:
        file_path: .msg文件路径

    Returns:
        验证结果
    """
    try:
        if not file_path:
            return {"success": False, "error": "文件路径不能为空"}

        if not os.path.exists(file_path):
            return {"success": False, "error": "文件不存在"}

        if not file_path.lower().endswith('.msg'):
            return {"success": False, "error": "文件格式不正确，请选择.msg文件"}

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return {"success": False, "error": "文件为空"}

        return {"success": True, "file_size": file_size}

    except Exception as e:
        logger.error(f"验证MSG文件时出错: {e}")
        return {"success": False, "error": str(e)}
