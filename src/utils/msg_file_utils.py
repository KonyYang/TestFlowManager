"""
.msg文件处理工具模块
提供处理Outlook .msg文件的功能
"""

import os
import tempfile
import shutil
import win32com.client
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

        # 创建临时文件夹用于存储附件
        temp_folder = tempfile.mkdtemp()
        
        success_count = 0
        error_messages = []
        attachments_info = []

        try:
            # 创建Outlook应用程序对象
            outlook = win32com.client.Dispatch("Outlook.Application")

            # 打开.msg文件
            msg = outlook.CreateItemFromTemplate(file_path)

            # 提取邮件基本信息
            email_info = {
                'subject': getattr(msg, 'Subject', '') or '',
                'sender': getattr(msg, 'SenderName', '') or '',
                'received_time': getattr(msg, 'ReceivedTime', '') or '',
                'body': getattr(msg, 'Body', '') or '',
                'attachments': []
            }

            # 获取附件集合
            attachments = msg.Attachments
            total_count = attachments.Count

            logger.info(f"找到 {total_count} 个附件")

            # 遍历所有附件
            for i in range(1, total_count + 1):
                try:
                    attachment = attachments.Item(i)
                    attachment_name = attachment.FileName

                    # 构建完整的保存路径
                    save_path = os.path.join(temp_folder, attachment_name)

                    # 处理文件名冲突
                    counter = 1
                    base_name, extension = os.path.splitext(attachment_name)
                    while os.path.exists(save_path):
                        new_name = f"{base_name}_{counter}{extension}"
                        save_path = os.path.join(temp_folder, new_name)
                        counter += 1

                    # 保存附件
                    attachment.SaveAsFile(save_path)
                    
                    # 读取附件内容
                    with open(save_path, 'rb') as f:
                        attachment_data = f.read()
                    
                    attachment_info = {
                        'filename': os.path.basename(save_path),
                        'size': os.path.getsize(save_path),
                        'content': attachment_data
                    }
                    
                    attachments_info.append(attachment_info)
                    email_info['attachments'].append(attachment_info)
                    logger.debug(f"成功提取: {os.path.basename(save_path)}")
                    success_count += 1

                except Exception as e:
                    error_msg = f"提取附件 {i} 时出错: {str(e)}"
                    error_messages.append(error_msg)
                    logger.warning(error_msg)

            # 清理COM对象
            msg = None
            outlook = None

        except Exception as e:
            error_messages.append(f"处理文件时出错: {str(e)}")
            logger.error(f"处理MSG文件时出错: {e}")
            # 清理临时文件夹
            shutil.rmtree(temp_folder, ignore_errors=True)
            return {"success": False, "error": f"处理文件时出错: {str(e)}"}

        # 清理临时文件夹
        shutil.rmtree(temp_folder, ignore_errors=True)

        logger.info(f"成功处理MSG文件，提取到 {success_count}/{total_count} 个附件")
        return {"success": True, "email_data": email_info}

    except FileNotFoundError:
        logger.error(f"MSG文件未找到: {file_path}")
        return {"success": False, "error": f"文件未找到: {file_path}"}
    except PermissionError:
        logger.error(f"没有权限访问MSG文件: {file_path}")
        return {"success": False, "error": f"没有权限访问文件: {file_path}"}
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