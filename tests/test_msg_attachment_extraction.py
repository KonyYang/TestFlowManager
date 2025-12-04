#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模块：用于提取指定.msg文件的所有附件到目标文件夹
"""

import os
import sys
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.features.email_extractor.service.email_extractor_service import EmailExtractorService
from src.features.email_extractor.model.email_extractor_data import EmailExtractorData


def test_extract_msg_attachments():
    """
    测试提取.msg文件的所有附件到指定目录
    """
    # 源文件路径
    msg_file_path = r"D:\e-mail\Cable Assy Signal Porton Partial Qualification Testing_OPS.msg"
    
    # 目标提取目录
    extract_folder = r"D:\extract"
    
    print(f"开始测试提取附件...")
    print(f"源文件: {msg_file_path}")
    print(f"目标目录: {extract_folder}")
    
    # 检查源文件是否存在
    if not os.path.exists(msg_file_path):
        print(f"错误: 源文件不存在: {msg_file_path}")
        return False
    
    # 创建目标目录（如果不存在）
    os.makedirs(extract_folder, exist_ok=True)
    print(f"已确保目标目录存在: {extract_folder}")
    
    # 初始化数据模型和服务
    data_model = EmailExtractorData()
    email_service = EmailExtractorService(data_model)
    
    try:
        # 处理MSG文件
        print("正在处理MSG文件...")
        result = email_service.process_msg_file(msg_file_path)
        
        if not result.get("success"):
            print(f"处理MSG文件失败: {result.get('error')}")
            return False
        
        # 获取邮件数据
        email_data = result.get("email_data", {})
        attachments = email_data.get("attachments", [])
        
        print(f"成功处理MSG文件，发现 {len(attachments)} 个附件")
        
        # 检查是否有附件
        if not attachments:
            print("警告: 未发现任何附件")
            return True
        
        # 获取临时文件夹路径（其中包含了所有附件）
        temp_folder = email_service.get_temp_folder()
        if not temp_folder or not os.path.exists(temp_folder):
            print("错误: 未能创建包含附件的临时文件夹")
            return False
        
        print(f"附件已保存至临时文件夹: {temp_folder}")
        
        # 将附件从临时文件夹复制到目标目录
        copied_count = 0
        for filename in os.listdir(temp_folder):
            source_path = os.path.join(temp_folder, filename)
            dest_path = os.path.join(extract_folder, filename)
            
            # 跳过目录，只处理文件
            if os.path.isfile(source_path):
                try:
                    shutil.copy2(source_path, dest_path)
                    print(f"已复制附件: {filename}")
                    copied_count += 1
                except Exception as e:
                    print(f"复制附件 {filename} 失败: {e}")
        
        print(f"成功复制 {copied_count} 个附件到目标目录")
        
        # 清理临时文件夹
        email_service.cleanup_temp_folder()
        print("已清理临时文件夹")
        
        return True
        
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        # 确保清理临时文件夹
        try:
            email_service.cleanup_temp_folder()
        except:
            pass
        return False


if __name__ == "__main__":
    success = test_extract_msg_attachments()
    if success:
        print("\n测试完成: 所有附件已成功提取")
        sys.exit(0)
    else:
        print("\n测试失败: 提取过程中发生错误")
        sys.exit(1)