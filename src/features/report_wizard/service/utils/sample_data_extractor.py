"""
测试样品数据提取工具模块
提供从JSON数据中提取测试样品信息的功能
"""

from typing import Dict, Any, List
from src.core.logger import logger


class SampleDataExtractor:
    """
    测试样品数据提取器
    提供从JSON数据中提取测试样品信息的功能
    """

    @staticmethod
    def extract_sample_info_from_json(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从JSON数据中提取测试样品信息
        
        Args:
            json_data: 包含申请单数据的JSON字典
            
        Returns:
            包含测试样品信息的字典列表
        """
        logger.info("开始从JSON数据中提取测试样品信息")
        
        sample_info_list = []
        
        try:
            # 从JSON数据中获取测试样品相关信息
            product_name = json_data.get('product_name', '')
            part_number = json_data.get('part_number', '')
            lot_info = json_data.get('lot_info', '')
            base_material = json_data.get('base_material', '')
            contact_plating = json_data.get('contact_plating', '')
            contact_lubricant = json_data.get('contact_lubricant', '')
            housing_material = json_data.get('housing_material', '')

            
            logger.debug(f"提取到的样品信息: "
                        f"product_name='{product_name}', part_number='{part_number}', "
                        f"lot_info='{lot_info}', base_material='{base_material}', "
                        f"contact_plating='{contact_plating}', contact_lubricant='{contact_lubricant}', "
                        f"housing_material='{housing_material}'")
            
            # 根据所有字段中的分号数量确定行数
            # 将所有字段都按分号分割成数组
            product_entries = product_name.split(';') if product_name else []
            part_entries = part_number.split(';') if part_number else []
            lot_entries = lot_info.split(';') if lot_info else []
            base_material_entries = base_material.split(';') if base_material else []
            contact_plating_entries = contact_plating.split(';') if contact_plating else []
            contact_lubricant_entries = contact_lubricant.split(';') if contact_lubricant else []
            housing_material_entries = housing_material.split(';') if housing_material else []
            
            # 确定最大行数
            max_rows = max(len(product_entries), len(part_entries), len(lot_entries), 
                          len(base_material_entries), len(contact_plating_entries), 
                          len(contact_lubricant_entries), len(housing_material_entries))
            
            # 遍历每一行，填充对应的数据
            for i in range(max_rows):
                # 获取当前行的各个字段值
                current_product_name = product_entries[i].strip() if i < len(product_entries) else ""
                current_part_number = part_entries[i].strip() if i < len(part_entries) else ""
                current_lot_info = lot_entries[i].strip() if i < len(lot_entries) else ""
                current_base_material = base_material_entries[i].strip() if i < len(base_material_entries) else ""
                current_contact_plating = contact_plating_entries[i].strip() if i < len(contact_plating_entries) else ""
                current_contact_lubricant = contact_lubricant_entries[i].strip() if i < len(contact_lubricant_entries) else ""
                current_housing_material = housing_material_entries[i].strip() if i < len(housing_material_entries) else ""
                
                # 创建样品信息字典
                sample_info = {
                    'product_name': current_product_name,
                    'part_number': current_part_number,
                    'lot_info': current_lot_info,
                    'base_material': current_base_material,
                    'contact_plating': current_contact_plating,
                    'contact_lubricant': current_contact_lubricant,
                    'housing_material': current_housing_material
                }
                
                sample_info_list.append(sample_info)
            
            # 处理特殊情况：如果没有任何分号分割的数据但仍有单个值，创建一个条目
            if not sample_info_list and (product_name or part_number or lot_info or base_material or 
                contact_plating or contact_lubricant or housing_material):
                sample_info = {
                    'product_name': product_name,
                    'part_number': part_number,
                    'lot_info': lot_info,
                    'base_material': base_material,
                    'contact_plating': contact_plating,
                    'contact_lubricant': contact_lubricant,
                    'housing_material': housing_material
                }
                sample_info_list.append(sample_info)
            
            logger.info(f"成功提取到 {len(sample_info_list)} 条测试样品信息")
            
        except Exception as e:
            logger.error(f"提取测试样品信息时出错: {e}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
        
        return sample_info_list