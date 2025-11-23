"""
Excel文档解析器
从Excel文件中提取表格数据
"""

from src.core.logger import logger


class ExcelParser:
    """
    Excel文档解析器
    使用openpyxl库提取表格数据
    """

    def __init__(self):
        """初始化Excel解析器"""
        pass

    def parse(self, file_path: str, sheet_name=None):
        """
        解析Excel文档

        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称，默认为第一个工作表

        Returns:
            解析出的表格数据列表和合并单元格信息
        """
        try:
            from openpyxl import load_workbook
            
            logger.info(f"开始解析Excel文件: {file_path}")
            
            # 加载工作簿（openpyxl不与正在运行的Excel实例交互）
            # 当文件被Excel打开时，openpyxl会读取上次保存的版本
            try:
                # 不使用read_only模式，以便能够访问merged_cells信息
                workbook = load_workbook(file_path, data_only=True)
                logger.info("Excel工作簿加载成功，openpyxl独立于正在运行的Excel实例")
            except PermissionError:
                logger.warning(f"文件可能已被Excel打开且正在被编辑，尝试以只读模式访问: {file_path}")
                # 在只读模式下无法访问merged_cells，但仍可以读取数据
                workbook = load_workbook(file_path, read_only=True, data_only=True)
                logger.info("Excel工作簿以只读模式加载成功")
            
            # 获取工作表
            if sheet_name:
                # 如果指定了工作表名称
                if sheet_name in workbook.sheetnames:
                    worksheet = workbook[sheet_name]
                    logger.info(f"使用指定的工作表: {sheet_name}")
                else:
                    logger.warning(f"工作表 '{sheet_name}' 不存在，使用默认工作表")
                    worksheet = workbook.active
            else:
                # 使用第一个工作表（默认）
                worksheet = workbook.active
                logger.info(f"使用默认工作表: {worksheet.title}")
            
            # 提取表格数据
            table_data = []
            
            # 遍历工作表的行
            if workbook.read_only:
                # 只读模式下的处理方式
                for row in worksheet.rows:
                    # 将行数据转换为列表，处理None值
                    row_data = ["" if cell.value is None else str(cell.value) for cell in row]
                    table_data.append(row_data)
            else:
                # 正常模式下的处理方式
                for row in worksheet.iter_rows(values_only=True):
                    # 将行数据转换为列表，处理None值
                    row_data = ["" if cell is None else str(cell) for cell in row]
                    table_data.append(row_data)
            
            # 获取合并单元格信息
            merged_cells_info = []
            # 只有在非只读模式下才能访问merged_cells
            if not workbook.read_only:
                try:
                    for merged_cell in worksheet.merged_cells.ranges:
                        merged_cells_info.append({
                            'min_row': merged_cell.min_row - 1,  # 转换为0基索引
                            'max_row': merged_cell.max_row - 1,
                            'min_col': merged_cell.min_col - 1,
                            'max_col': merged_cell.max_col - 1
                        })
                    logger.info(f"检测到 {len(merged_cells_info)} 个合并单元格")
                except Exception as e:
                    logger.warning(f"获取合并单元格信息时出错: {e}")
            else:
                logger.info("在只读模式下无法获取合并单元格信息")
            
            logger.info(f"成功解析Excel文件，共 {len(table_data)} 行数据")
            
            # 关闭工作簿
            workbook.close()
            logger.info("Excel工作簿已关闭")
            
            return {
                'data': table_data,
                'merged_cells': merged_cells_info
            }
            
        except FileNotFoundError:
            logger.error(f"Excel文件未找到: {file_path}")
            return {
                'data': [],
                'merged_cells': []
            }
        except PermissionError:
            logger.error(f"没有权限访问Excel文件，可能已被其他程序独占锁定: {file_path}")
            return {
                'data': [],
                'merged_cells': []
            }
        except Exception as e:
            logger.error(f"解析Excel文件时出错: {e}", exc_info=True)
            return {
                'data': [],
                'merged_cells': []
            }