#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_motor_jgy370.py
Поз. 13: Мотор-редуктор JGY-370 (DC Worm Gear Motor)
"""

import sys
import os
import math
from freecad_utils import (
    FreeCAD, Part, make_box, make_cylinder,
    generate_standard_part_drawing
)

def create_motor_jgy370():
    """
    Constructs the JGY-370 Worm Gear Motor solid model at local origin (0,0,0).
    Output shaft axis is along Z at (0, 0), mounting flange face is at Z = 0.
    Gearbox and motor can extend below Z = 0.
    """
    # Output D-shaft (6 mm diameter)
    shaft = Part.makeCylinder(3.0, 15.0, FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1))
    
    # Mounting boss collar
    collar = Part.makeCylinder(6.0, 4.0, FreeCAD.Vector(0, 0, -4.0), FreeCAD.Vector(0, 0, 1))
    
    # Zinc alloy gearbox case (32 x 46 x 25 mm)
    gearbox = make_box(32.0, 46.0, 21.0, (-16.0, -23.0, -25.0))
    
    # Cylindrical motor body can (24.4 mm dia, length 30.8 mm)
    can = Part.makeCylinder(12.2, 30.8, FreeCAD.Vector(0, -38.0, -12.5), FreeCAD.Vector(0, -1, 0))
    
    return gearbox.fuse(collar).fuse(shaft).fuse(can)

create_part = create_motor_jgy370

if __name__ == "__main__":
    shape = create_motor_jgy370()
    notes = [
        "1. * Размеры для справок.",
        "2. Мотор-редуктор червячный постоянного тока JGY-370.",
        "3. Напряжение питания: 12 В. Скорость: 30-40 об/мин.",
        "4. Выходной вал D-образный ф6 мм со срезом."
    ]
    generate_standard_part_drawing(
        part_name="part_motor_jgy370",
        part_shape=shape,
        doc_code="ВЧ.02.00.001",
        title_name="Мотор-редуктор JGY-370",
        material="Цинк / Сталь",
        scale=1.0,
        sheet="A3_Landscape",
        notes=notes
    )
