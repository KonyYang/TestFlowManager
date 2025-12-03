from abc import ABC, abstractmethod
from src.core.logger import logger


class BaseExportService(ABC):
    """导出服务抽象基类"""
    
    def __init__(self, data_model):
        self.data_model = data_model
    
    @abstractmethod
    def export_to_excel(self, file_path):
        """导出到Excel的抽象方法"""
        pass
    
    def _save_workbook_safely(self, workbook, file_path):
        """安全保存工作簿，处理权限错误"""
        try:
            workbook.save(file_path)
            logger.debug(f"文件已成功保存到: {file_path}")
            return True
        except PermissionError:
            logger.error(f"导出失败: 文件被占用，可能已在Excel中打开 {file_path}")
            return False
        except Exception as e:
            logger.error(f"导出失败: {e}", exc_info=True)
            return False