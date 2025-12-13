"""
模板数据工具模块
提供预定义的测试条件和要求模板数据
"""

from typing import Dict, Tuple, List


def get_condition_requirement_templates() -> Dict[str, Tuple[str, str]]:
    """
    获取条件和要求的模板数据
    
    Returns:
        Dict[str, Tuple[str, str]]: 测试方法映射到(条件, 要求)的字典
    """
    return {
        "Examination": ("10x min magnification", "No detrimental condition"),
        "LLCR": ("20mV max,100mA max", "Initial: ≤ mΩ;\nAfter test: ≤ mΩ"),
        "CR": ("A", "Initial:  mΩ;\nAfter test:  mΩ"),
        "Insulation Resistance": ("V/C, minutes, mated", " MΩ (GΩ)"),
        "Dielectric Withstanding Voltage": ("V/C ,minutes, mated", "No evidence of arc-over, insulation breakdown, or leakage current >1mA"),
        "Current Rating": ("Method 2,\nA", "T-Rise  "),
        "Mating": ("25.4mm/min", "Mating Force  N\nUn-mating Force  N"),
        "Retention": ("12.7mm/min", "Header  N;\nRec.  N"),
        "Salt": ("Test Condition B,\nDuration 48 hours", "No damage"),
        "Thermal Shock": ("-~,\n30minute/dwell time,  cycles", "No damage"),
        "Humidity": ("Method IV with step 7a cold cycling(-10),\n25~65, 90% ~98%RH,\n24H/cycle, total 10cycles", "No damage"),
        "High Temp": (", hours", "No damage"),
        "MFG": ("Class IIA, unmated _hours then mated _hours", "No damage"),
        "Thermal disturbance": ("+~ +,\n_minutes dwell,\nRamp rate /min,\ncycles", "No damage"),
        "Dust": ("Benign dust composition,\n1hour, unmated for both connectors", "No damage"),
        "Reseating": ("Manually unmated/mated\n3 cycles", "No damage"),
        "Solderability": ("Dry aging 155@4Hours;\nTest A1, Solder Dip:\nFlux type: Standard #2\nFlux immersion time: 10s\nSolder Temp.: 2455,\nSolder immersion time: 5s", "95% Coverage"),
        "Vibration": ("Condition- ，letter ,\n~Hz, Grms, hours/axis", "No damage,\nNo discontinuity >1us"),
        "Shock": ("50G, 11ms, half sine wave.\n3shocks/ axis. total 18shocks", "No damage,\nNo discontinuity >1us"),
        "Durability": ("cycles, 25.4mm/min", "No damage"),
        "Component heat resistance": ("Procedure 5, Test Level 6:\n260 for 3passes", "No damage"),
        "flex": ("Test Condition I\nCable flex angle 90,\nTest speed:12-14 cycles/min,\nTotal 100 cycles.\nLoad weight: 1.2kg for all signal wires.\nRoller diameter:10mm", "No evidence of physical\ndamage"),
    }


def get_template_aliases() -> Dict[str, List[str]]:
    """
    获取模板别名映射，用于处理同一测试项目的不同表达方式
    
    Returns:
        Dict[str, List[str]]: 主键映射到其别名列表的字典
    """
    return {
        "Examination": [
            "visual examination",
            "Examination of Product",
            "visual inspection",
            "visual check",
        ],
        "LLCR": [
            "low level contact resistance",
            "contact resistance(low level)",
            "contact resistance (low level)"
        ],
        "CR": [
            "contact resistance"
        ],
        "Insulation Resistance": [
            "insulation resistance"
        ]
    }