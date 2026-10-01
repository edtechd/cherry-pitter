#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_base_frame.py
Поз. 1: Станина-шасси (Base Frame Chassis)
"""

import sys
import os
import math
from freecad_utils import (
    FreeCAD, Part, make_box, make_cylinder, trans, rot_z,
    generate_standard_part_drawing
)

def create_base_frame():
    """Constructs the Base Frame Chassis B-Rep solid at local datum (0,0,0)."""
    # Rotor axis is at datum (0, 0, 0)
    chassis = make_box(210.0, 145.0, 10.0, (-65.0, -75.0, 0))
    # deck = make_box(210.0, 145.0, 8.0, (-65.0, -75.0, 10.0))
    # deck_pocket = make_box(190.0, 125.0, 9.0, (-55.0, -65.0, 10.0))
    # deck = deck.cut(deck_pocket)
    # chassis = plate #.fuse(deck)
    
    # Rotor central bearing hub at (0, 0, 0)
    hub_rotor = make_cylinder(16.0, 18.0, (0, 0, 0))
    chassis = chassis.fuse(hub_rotor)
    
    # Motor mounting hub at (60, 0, 0)
    hub_motor = make_cylinder(22.0, 18.0, (60.0, 0, 0))
    chassis = chassis.fuse(hub_motor)
    
    # Tower mounting hub at (22, -38.1, 0)
    hub_tower = make_cylinder(14.0, 18.0, (22.0, -38.1, 0))
    chassis = chassis.fuse(hub_tower)
    
    # Rotor bore and bearing recesses (608ZZ)
    chassis = chassis.cut(make_cylinder(6.0, 25.0, (0, 0, -1.0)))
    chassis = chassis.cut(make_cylinder(11.1, 7.0, (0, 0, 11.0)))
    chassis = chassis.cut(make_cylinder(11.1, 7.0, (0, 0, 0)))
    
    # Motor bore and M3 mounting screw holes
    chassis = chassis.cut(make_cylinder(16.0, 25.0, (60.0, 0, -1.0)))
    chassis = chassis.cut(make_cylinder(1.7, 25.0, (60.0 - 9.0, -9.0, -1.0)))
    chassis = chassis.cut(make_cylinder(1.7, 25.0, (60.0 + 9.0, -9.0, -1.0)))
    chassis = chassis.cut(make_cylinder(1.7, 25.0, (60.0 - 9.0, 9.0, -1.0)))
    chassis = chassis.cut(make_cylinder(1.7, 25.0, (60.0 + 9.0, 9.0, -1.0)))
    
    # Tower central pit opening and mounting holes
    chassis = chassis.cut(make_cylinder(6.0, 25.0, (22.0, -38.1, -1.0)))
    chassis = chassis.cut(make_cylinder(2.2, 25.0, (22.0 - 18.0, -38.1 - 8.0, -1.0)))
    chassis = chassis.cut(make_cylinder(2.2, 25.0, (22.0 + 18.0, -38.1 - 8.0, -1.0)))
    
    
    # Clearance pocket for enlarged Geneva driver gear disc (R=42.5 mm, Z >= 13.5 mm)
    chassis = chassis.cut(make_cylinder(42.5, 15.0, (60.0, 0, 13.5)))
    return chassis

create_part = create_base_frame

if __name__ == "__main__":
    shape = create_base_frame()
    notes = [
        "1. * Размеры для справок.",
        "2. Материал: PETG. Заполнение не менее 35%.",
        "3. Неуказанные радиусы скруглений 1.5 мм."
    ]
    generate_standard_part_drawing(
        part_name="part_base_frame",
        part_shape=shape,
        doc_code="ВЧ.01.00.001",
        title_name="Станина-шасси",
        material="PETG",
        scale=0.8,
        sheet="A3_Landscape",
        notes=notes
    )
