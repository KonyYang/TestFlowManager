"""智能测试点位解析器模块

该模块提供了解析测试点位描述字符串的功能，
能够处理范围、前缀、多类别分组等功能。
"""

import re
from typing import Dict, List, Any, Tuple, Generator, Optional
from collections import defaultdict
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SmartPointParser:
    """智能测试点位解析器
    
    能够解析测试点位描述字符串并生成结构化数据。
    支持范围解析、前缀处理、多类别分组等功能。
    """

    def __init__(self, max_points: int = 1000, max_point_length: int = 50):
        """初始化解析器
        
        Args:
            max_points: 最大点位数量限制
            max_point_length: 单个点位最大长度限制
        """
        self.max_points = max_points
        self.max_point_length = max_point_length
        self.prefix_whitelist = set()  # 前缀白名单
        
        # 编译常用正则表达式以提高性能
        self._range_pattern = re.compile(r'^([^-]+)-(.+?)(?::(\d+))?$')
        self._exclude_pattern = re.compile(r'^(.+?)!(.+)$')
        self._prefix_extract_pattern = re.compile(r'^([a-zA-Z_\u4e00-\u9fff]*)(\d+)$')
        self._wildcard_pattern = re.compile(r'^(.+)\*$')

    def parse(self, input_str: str) -> Dict[str, Any]:
        """解析测试点位描述字符串
        
        Args:
            input_str: 测试点位描述字符串
            
        Returns:
            包含解析结果的字典
        """
        logger.debug(f"开始解析输入字符串: {input_str}")
        
        # 标准化输入
        normalized_input = self._normalize_input(input_str)
        logger.debug(f"标准化后的输入: {normalized_input}")
        
        # 按分号分割不同类别
        category_strings = [s.strip() for s in re.split(r'[;；]', normalized_input) if s.strip()]
        logger.debug(f"分割后的类别字符串: {category_strings}")
        
        categories = {}
        all_points = []
        parsing_errors = []
        warnings = []
        total_points_count = 0
        
        # 处理每个类别
        for category_str in category_strings:
            logger.debug(f"处理类别字符串: {category_str}")
            try:
                category_name, points = self._parse_category(category_str)
                logger.debug(f"类别 {category_name} 解析得到点位: {points}")
                
                # 如果类别已存在，合并点位
                if category_name in categories:
                    categories[category_name].extend(points)
                else:
                    categories[category_name] = points
                    
                all_points.extend(points)
                total_points_count += len(points)
                
                # 检查点位数量限制
                if total_points_count > self.max_points:
                    error_msg = f"点位总数超过限制 ({self.max_points})"
                    logger.warning(error_msg)
                    parsing_errors.append(error_msg)
                    break
                    
            except Exception as e:
                error_msg = f"解析类别 '{category_str}' 时出错: {str(e)}"
                logger.error(error_msg, exc_info=True)
                parsing_errors.append(error_msg)
        
        # 检查重复点位
        point_counts = defaultdict(int)
        for point in all_points:
            point_counts[point] += 1
            
        duplicates = [point for point, count in point_counts.items() if count > 1]
        if duplicates:
            warning_msg = f"发现重复点位: {', '.join(duplicates)}"
            logger.warning(warning_msg)
            warnings.append(warning_msg)
        
        result = {
            'categories': categories,
            'statistics': {
                'total_points': total_points_count,
                'category_count': len(categories),
                'parsing_errors': parsing_errors,
                'warnings': warnings
            },
            'raw_input': input_str,
            'normalized_input': normalized_input
        }
        
        logger.debug(f"解析完成，结果: {result}")
        return result

    def _normalize_input(self, input_str: str) -> str:
        """标准化输入字符串
        
        Args:
            input_str: 原始输入字符串
            
        Returns:
            标准化后的字符串
        """
        logger.debug(f"标准化输入: {input_str}")
        # 替换中文标点为英文标点
        normalized = input_str.replace('；', ';').replace('，', ',')
        # 移除制表符
        normalized = normalized.replace('\t', '')
        # 移除多余空格
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        logger.debug(f"标准化后: {normalized}")
        return normalized

    def _parse_category(self, category_str: str) -> Tuple[str, List[str]]:
        """解析单个类别字符串
        
        Args:
            category_str: 类别字符串
            
        Returns:
            (类别名称, 点位列表) 元组
        """
        logger.debug(f"解析类别字符串: {category_str}")
        
        # 按逗号分割点位
        point_parts = [p.strip() for p in re.split(r'[,，]', category_str) if p.strip()]
        logger.debug(f"分割后的点位部分: {point_parts}")
        
        points = []
        for part in point_parts:
            logger.debug(f"解析点位部分: {part}")
            points.extend(self._parse_point_part(part))
            
        # 确定类别名称
        first_point = point_parts[0] if point_parts else ""
        logger.debug(f"第一个点位: {first_point}")
        category_name = self._determine_category_name(first_point)
        logger.debug(f"确定的类别名称: {category_name}")
        
        # 验证前缀白名单
        if self.prefix_whitelist:
            logger.debug(f"检查前缀白名单: {self.prefix_whitelist}")
            for point in points:
                prefix = self._extract_prefix(point)
                logger.debug(f"点位 {point} 的前缀: {prefix}")
                if prefix and prefix not in self.prefix_whitelist:
                    raise ValueError(f"前缀 '{prefix}' 不在白名单中")
        
        logger.debug(f"类别 {category_name} 解析完成，点位: {points}")
        return category_name, points

    def _parse_point_part(self, point_part: str) -> List[str]:
        """解析单个点位部分
        
        Args:
            point_part: 点位部分字符串
            
        Returns:
            点位列表
        """
        logger.debug(f"解析点位部分: {point_part}")
        
        # 处理排除语法 (!)
        exclude_match = self._exclude_pattern.match(point_part)
        if exclude_match:
            logger.debug("检测到排除语法")
            base_part = exclude_match.group(1)
            exclude_part = exclude_match.group(2)
            exclude_points = set(p.strip() for p in re.split(r'[,，]', exclude_part) if p.strip())
            base_points = self._parse_point_expression(base_part)
            result = [p for p in base_points if p not in exclude_points]
            logger.debug(f"排除语法处理结果: {result}")
            return result
        
        result = self._parse_point_expression(point_part)
        logger.debug(f"点位表达式解析结果: {result}")
        return result

    def _parse_point_expression(self, expression: str) -> List[str]:
        """解析点位表达式
        
        Args:
            expression: 点位表达式
            
        Returns:
            点位列表
        """
        logger.debug(f"解析点位表达式: {expression}")
        
        # 处理通配符 (*)
        wildcard_match = self._wildcard_pattern.match(expression)
        if wildcard_match:
            logger.debug("检测到通配符语法")
            # 简单处理通配符，实际应用中可能需要更复杂的逻辑
            base_name = wildcard_match.group(1)
            # 这里简单返回一个示例列表，实际应用中可能需要根据配置展开
            result = [f"{base_name}{i}" for i in range(1, 6)]  # 默认展开为1-5
            logger.debug(f"通配符处理结果: {result}")
            return result
        
        # 处理范围 (-)
        range_match = self._range_pattern.match(expression)
        if range_match:
            logger.debug("检测到范围语法")
            start = range_match.group(1)
            end = range_match.group(2)
            step = int(range_match.group(3)) if range_match.group(3) else 1
            result = self._expand_range(start, end, step)
            logger.debug(f"范围处理结果: {result}")
            return result
        
        # 单个点位
        if len(expression) > self.max_point_length:
            raise ValueError(f"点位 '{expression}' 超过长度限制 ({self.max_point_length})")
        logger.debug(f"单个点位: {[expression]}")
        return [expression]

    def _expand_range(self, start: str, end: str, step: int = 1) -> List[str]:
        """展开范围表达式
        
        Args:
            start: 起始点位
            end: 结束点位
            step: 步长
            
        Returns:
            点位列表
        """
        logger.debug(f"展开范围: {start}-{end} 步长:{step}")
        
        # 提取前缀和数字部分
        start_prefix, start_num = self._split_prefix_number(start)
        end_prefix, end_num = self._split_prefix_number(end)
        logger.debug(f"起始点位前缀:{start_prefix} 数字:{start_num}")
        logger.debug(f"结束点位前缀:{end_prefix} 数字:{end_num}")
        
        # 检查前缀是否一致
        if start_prefix != end_prefix:
            raise ValueError(f"范围 '{start}-{end}' 前缀不匹配")
        
        # 检查数字顺序
        if start_num >= end_num:
            raise ValueError(f"范围 '{start}-{end}' 起始数字必须小于结束数字")
        
        # 生成点位
        points = []
        prefix = start_prefix
        for i in range(start_num, end_num + 1, step):
            point = f"{prefix}{i}" if prefix else str(i)
            if len(point) > self.max_point_length:
                raise ValueError(f"点位 '{point}' 超过长度限制 ({self.max_point_length})")
            points.append(point)
            
        logger.debug(f"范围展开结果: {points}")
        return points

    def _split_prefix_number(self, point: str) -> Tuple[str, int]:
        """分离前缀和数字部分
        
        Args:
            point: 点位字符串
            
        Returns:
            (前缀, 数字) 元组
        """
        logger.debug(f"分离前缀和数字: {point}")
        match = self._prefix_extract_pattern.match(point)
        if match:
            prefix = match.group(1)
            number = int(match.group(2))
            logger.debug(f"匹配成功，前缀:{prefix} 数字:{number}")
            return prefix, number
        else:
            # 纯数字
            try:
                result = "", int(point)
                logger.debug(f"纯数字结果: {result}")
                return result
            except ValueError:
                raise ValueError(f"无法解析点位 '{point}'")

    def _extract_prefix(self, point: str) -> str:
        """提取点位前缀
        
        Args:
            point: 点位字符串
            
        Returns:
            前缀字符串
        """
        logger.debug(f"提取点位前缀: {point}")
        match = self._prefix_extract_pattern.match(point)
        result = match.group(1) if match else ""
        logger.debug(f"提取结果: {result}")
        return result

    def _determine_category_name(self, first_point: str) -> str:
        """确定类别名称
        
        Args:
            first_point: 第一个点位
            
        Returns:
            类别名称
        """
        logger.debug(f"确定类别名称，第一个点位: {first_point}")
        if not first_point:
            logger.debug("无点位，返回 unknown")
            return "unknown"
            
        # 先检查是否是范围表达式
        range_match = self._range_pattern.match(first_point)
        if range_match:
            # 如果是范围表达式，使用范围的起始点来确定类别名称
            start = range_match.group(1)
            prefix = self._extract_prefix(start)
            if prefix:
                logger.debug(f"范围表达式的起始点前缀 {prefix} 作为类别名称")
                return prefix
            # 检查起始点是否为纯数字
            try:
                int(start)
                logger.debug("范围表达式的起始点为纯数字，类别名称为 numeric")
                return "numeric"
            except ValueError:
                pass
        
        # 提取前缀作为类别名称
        prefix = self._extract_prefix(first_point)
        if prefix:
            logger.debug(f"有前缀 {prefix}，作为类别名称")
            return prefix
            
        # 检查是否为纯数字
        try:
            int(first_point)
            logger.debug("纯数字，类别名称为 numeric")
            return "numeric"
        except ValueError:
            pass
            
        # 默认类别名称
        logger.debug("默认类别名称: custom")
        return "custom"

    def set_prefix_whitelist(self, whitelist: List[str]) -> None:
        """设置前缀白名单
        
        Args:
            whitelist: 允许的前缀列表
        """
        logger.debug(f"设置前缀白名单: {whitelist}")
        self.prefix_whitelist = set(whitelist)

    def set_max_points(self, max_points: int) -> None:
        """设置最大点位数量限制
        
        Args:
            max_points: 最大点位数量
        """
        logger.debug(f"设置最大点位数量: {max_points}")
        self.max_points = max_points

    def set_max_point_length(self, max_length: int) -> None:
        """设置单个点位最大长度限制
        
        Args:
            max_length: 最大长度
        """
        logger.debug(f"设置最大点位长度: {max_length}")
        self.max_point_length = max_length