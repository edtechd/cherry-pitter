#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_pit_chute.py
Поз. 11: Лоток отвода косточек (Pit Chute)
"""

import sys
import os
import math
from freecad_utils import (
    FreeCAD, Part, make_cylinder, make_cone,
    generate_standard_part_drawing
)

def create_pit_chute():
    """
    Constructs the Pit Collector Funnel & Exit Chute B-Rep solid at local origin (0,0,0).
    Upper funnel rim is centered at (0, 0, 0).
    """
    hopper_out = make_cone(14.0, 20.0, 18.0, (0, 0, 0))
    hopper_in = make_cone(11.5, 17.5, 20.0, (0, 0, -1.0))
    funnel = hopper_out.cut(hopper_in)
    
    pipe = make_cylinder(9.0, 25.0, (0, 0, 0), (0, -1, -0.6))
    pipe = pipe.cut(make_cylinder(7.0, 27.0, (0, 0, 1.0), (0, -1, -0.6)))
    return funnel.fuse(pipe)

create_part = create_pit_chute

if __name__ == "__main__":
    shape = create_pit_chute()
    notes = [
        "1. * Размеры для справок.",
        "2. Материал: PETG. Заполнение 30%.",
        "3. Наклон сливного патрубка обеспечивает гравитационный сброс косточек."
    ]
    generate_standard_part_drawing(
        part_name="part_pit_chute",
        part_shape=shape,
        doc_code="ВЧ.01.00.011",
        title_name="Лоток отвода косточек",
        material="PETG",
        scale=1.0,
        sheet="A3_Landscape",
        notes=notes
    )
