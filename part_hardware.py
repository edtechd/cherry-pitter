#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_hardware.py
Стандартные изделия: Центральная ось M8 и подшипники 608ZZ (Axle Bolt & Bearings)
"""

import sys
import os
import math
from freecad_utils import (
    FreeCAD, Part, make_cylinder,
    generate_standard_part_drawing
)

def create_hardware():
    """
    Constructs the central M8 axle bolt and 608ZZ rolling bearings along local Z axis.
    """
    # M8 bolt shank (length 65 mm)
    axle = make_cylinder(4.0, 65.0, (0, 0, 0))
    # Bolt head (13 mm across flats / circle 6.5 mm radius)
    head = make_cylinder(6.5, 6.0, (0, 0, 54.0))
    
    # 608ZZ Upper bearing (8x22x7 mm)
    b_top = make_cylinder(11.0, 7.0, (0, 0, 47.0)).cut(make_cylinder(4.0, 8.0, (0, 0, 46.5)))
    # 608ZZ Lower bearing (8x22x7 mm) located in Geneva wheel (Z = 23..30)
    b_bot = make_cylinder(11.0, 7.0, (0, 0, 23.0)).cut(make_cylinder(4.0, 8.0, (0, 0, 22.5)))
    
    return axle.fuse(head).fuse(b_top).fuse(b_bot)

create_part = create_hardware

if __name__ == "__main__":
    shape = create_hardware()
    notes = [
        "1. * Размеры для справок.",
        "2. Болт M8x65 DIN 912 (класс прочности 8.8).",
        "3. Подшипники 608ZZ ГОСТ 8338-75 (2 шт.)."
    ]
    generate_standard_part_drawing(
        part_name="part_hardware",
        part_shape=shape,
        doc_code="ВЧ.00.00.010",
        title_name="Ось M8 и подшипники 608ZZ",
        material="Сталь",
        scale=1.0,
        sheet="A3_Landscape",
        notes=notes
    )
