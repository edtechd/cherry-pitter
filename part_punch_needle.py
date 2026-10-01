#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_punch_needle.py
Поз. 21: Игла штока (Punch Needle)
Прецизионный рабочий орган для выталкивания вишневых косточек.
Изготавливается из нержавеющей стали 12Х18Н10Т / AISI 304 (Ø3.0 мм, длина 75.0 мм).
"""

import sys
import os
import math

sys.path.append('/usr/lib/freecad/lib')
sys.path.append('/usr/share/freecad/Mod/TechDraw')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from freecad_utils import FreeCAD, Part, make_cylinder, make_box

def create_punch_needle(length=75.0, dia=3.0, bevel_angle=45.0):
    """
    Создает аналитический B-Rep солид прецизионной иглы штока:
    - Круглый калиброванный пруток диаметром dia = 3.0 мм (радиус r = 1.5 мм);
    - Длина length = 75.0 мм (от острия Z = 0.0 до верхнего торца Z = length);
    - Заточка рабочего наконечника под углом bevel_angle = 45° на нижнем конце (Z in [0, 2.5] мм);
    - Верхний цилиндрический хвостовик для фиксации в сокете каретки needle_slider установочным винтом M3.
    """
    r = dia / 2.0
    
    # 1. Цилиндрический стержень иглы вдоль оси Z от Z = 0 до Z = length
    shank = Part.makeCylinder(r, length, FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1))
    
    # 2. Клиновидная заточка рабочего острия (45°)
    # Для симметричного и чистого среза используем наклонную секущую призму
    cut_box = Part.makeBox(12.0, 12.0, 12.0, FreeCAD.Vector(-6.0, -6.0, -12.0))
    cut_box = cut_box.rotate(FreeCAD.Vector(0, 0, r), FreeCAD.Vector(0, 1, 0), bevel_angle)
    
    needle = shank.cut(cut_box)
    
    if not needle.isValid():
        raise ValueError("Punch needle solid shape is topologically invalid!")
        
    return needle

create_part = create_punch_needle

if __name__ == "__main__":
    shape = create_punch_needle()
    print(f"Punch needle created successfully! Valid: {shape.isValid()}, Volume: {shape.Volume:.2f} mm^3")
