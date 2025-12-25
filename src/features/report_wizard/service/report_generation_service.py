"""
报告生成服务模块
提供报告生成相关的业务逻辑服务
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from src.core.logger import logger
from src.features.report_wizard.service.header_modifier import HeaderModifier
from src.features.report_wizard.model.header_data import HeaderData


class ReportGenerationService:
    """
    报告生成服务类
    提供报告生成相关的业务逻辑服务
    """

    def __init__(self):
        """初始化报告生成服务"""
        self.template_path = r"D:\TestFlowManager\Template\E-3707_H Laboratory Test Report_241216.docx"
        self.default_output_dir = r"D:\TestFlowManager\Output"

    def validate_template_exists(self) -> bool:
        """
        验证模板文件是否存在
        
        Returns:
            bool: 模板文件是否存在
        """
        if not os.path.exists(self.template_path):
            logger.error(f"模板文件不存在: {self.template_path}")
            return False
        return True

    def create_report_from_template(self, header_data: HeaderData, output_dir: Optional[str] = None) -> str:
        """
        基于模板创建报告文件
        
        Args:
            header_data: 页眉数据
            output_dir: 输出目录，如果为None则使用默认目录
            
        Returns:
            str: 生成的报告文件路径
        """
        try:
            # 验证模板文件
            if not self.validate_template_exists():
                raise FileNotFoundError(f"模板文件不存在: {self.template_path}")

            # 确定输出目录
            if output_dir is None:
                output_dir = self.default_output_dir
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)

            # 生成输出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if header_data.report_no:
                filename = f"{header_data.report_no}_Report_{timestamp}.docx"
            else:
                filename = f"Test_Report_{timestamp}.docx"
            
            output_path = os.path.join(output_dir, filename)

            # 复制模板到输出位置
            shutil.copy2(self.template_path, output_path)
            logger.info(f"模板已复制到: {output_path}")

            # 修改页眉信息
            header_modifier = HeaderModifier(output_path)
            try:
                header_modifier.open()
                
                # 准备页眉数据字典
                header_dict = {
                    "report_no": header_data.report_no,
                    "version": header_data.version,
                    "date": header_data.date,
                    "tester": header_data.tester,
                    "report_title": header_data.report_title,
                    "requested_by": header_data.requested_by,
                    "test_period": header_data.test_period,
                    "completion_date": header_data.completion_date
                }
                
                # 修改首页页眉
                success = header_modifier.modify_header(header_dict)
                if success:
                    logger.info("首页页眉信息已成功修改")
                else:
                    logger.error("首页页眉信息修改失败")
                            
                # 修改第二节页眉
                success2 = header_modifier.modify_second_header(header_dict)
                if success2:
                    logger.info("第二节页眉信息已成功修改")
                else:
                    logger.error("第二节页眉信息修改失败")
                            
                # 修改修订记录表格中的日期
                success3 = header_modifier.modify_revision_record_date(header_dict)
                if success3:
                    logger.info("修订记录表格日期已成功修改")
                else:
                    logger.error("修订记录表格日期修改失败")
                            
                # 最后使用win32com保存整个文档，因为Word应用可能已经打开了文档
                header_modifier.save_with_win32()
            finally:
                header_modifier.cleanup()

            return output_path

        except Exception as e:
            logger.error(f"创建报告失败: {e}")
            raise

    def load_project_data(self, project_path: str) -> Optional[HeaderData]:
        """
        从项目路径加载项目数据
        
        Args:
            project_path: 项目路径
            
        Returns:
            HeaderData: 从项目中加载的页眉数据，如果失败则返回None
        """
        try:
            # 查找项目中的JSON文件
            project_dir = Path(project_path)
            json_files = list(project_dir.glob("*.json"))
            
            if not json_files:
                logger.warning(f"在项目路径中未找到JSON文件: {project_path}")
                return None
            
            # 使用第一个找到的JSON文件
            json_file = json_files[0]
            with open(json_file, 'r', encoding='utf-8') as f:
                import json
                json_data = json.load(f)
                
                # 从JSON数据创建HeaderData对象
                header_data = HeaderData.from_json(json_data)
                logger.info(f"成功从 {json_file} 加载项目数据")
                return header_data
                
        except Exception as e:
            logger.error(f"加载项目数据失败: {e}")
            return None