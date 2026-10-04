#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_assembly.py
Master Assembly & GOST A1 Drawing Generator for Automated Cherry Pitter.
Imports standalone part modules, places them via FreeCAD.Placement,
and generates the complete technical drawing assembly_drawing.pdf and assembly_drawing.FCStd.
"""

import sys
import os
import math

from freecad_utils import (
    FreeCAD, Part, TechDraw, TechDrawGui,
    make_cylinder,
    create_drawing_page, add_part_view, fill_gost_title_block, export_drawing
)

# Import individual part builders
from part_base_frame import create_base_frame
from part_rotor import create_rotor
from part_geneva_wheel import create_geneva_wheel
from part_geneva_driver import create_geneva_driver
from part_horizontal_crankshaft import create_horizontal_crankshaft
from part_connecting_rod import create_connecting_rod
from part_needle_slider import create_needle_slider
from part_stripper_guide import create_stripper_guide
from part_stripper import create_stripper
from part_mgn9_rail import create_mgn9_rail
from part_mgn9h_carriage import create_mgn9h_carriage
from part_punch_needle import create_punch_needle
from part_hopper import create_hopper
from part_hopper_stand import create_hopper_stand
from part_ejector import create_ejector
from part_deflector import create_deflector
from part_chute import create_chute
from part_pit_chute import create_pit_chute
from part_motor_jgy370 import create_motor_jgy370
from part_hardware import create_hardware
from part_flange_coupling import create_flange_coupling
from part_crankshaft_bracket import create_crankshaft_bracket

def build_assembly(doc):
    """
    Builds the complete 3D solid assembly compound in global coordinates.
    Returns:
        assembly_compound: FreeCAD Part compound of all placed parts
        part_features: Dictionary of individual Part::Feature objects
    """
    # 1. Base Frame Chassis
    base_frame = create_base_frame()
    # already at global datum (0, 0, 0)
    
    # 2. Rotor Turret Drum
    rotor = create_rotor()
    rotor.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 30.0), FreeCAD.Rotation())
    
    # 3. Geneva Wheel
    geneva_wheel = create_geneva_wheel()
    geneva_wheel.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 22.0), FreeCAD.Rotation())
    
    # 4. Geneva Driver with Integrated Bevel Gear
    geneva_driver = create_geneva_driver()
    geneva_driver.Placement = FreeCAD.Placement(FreeCAD.Vector(60.0, 0, 14.0), FreeCAD.Rotation())
    
    # 4a. Rigid Flange Coupling Connector ID: 6mm (Поз. 23)
    flange_coupling = create_flange_coupling()
    rot_coupling = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), 180.0)
    flange_coupling.Placement = FreeCAD.Placement(FreeCAD.Vector(60.0, 0, 14.0), rot_coupling)
    
    # 5. Horizontal Crankshaft
    # Involute bevel gear meshing with Geneva driver at apex [60.0, 0.0, 54.0]
    # Positioned at angle alpha = -60 deg around Geneva driver vertical axis
    # Disc line is oriented at 30 deg, strictly parallel to stripper guide base
    alpha_deg = -60.0
    alpha = math.radians(alpha_deg)
    p_apex = FreeCAD.Vector(60.0, 0.0, 54.0)
    mat_crank = FreeCAD.Matrix(
        0, -math.sin(alpha), -math.cos(alpha), 0,
        0,  math.cos(alpha), -math.sin(alpha), 0,
        1,  0,                0,               0,
        0,  0,                0,               1
    )
    rot_crank = FreeCAD.Rotation(mat_crank)
    # Apply tooth meshing phase offset of 1.5 deg for tooth-in-space engagement
    rot_crank = rot_crank.multiply(FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 1.5))
    pos_crank = p_apex - rot_crank.multVec(FreeCAD.Vector(0, 0, 40.0))
    
    crankshaft = create_horizontal_crankshaft()
    crankshaft.Placement = FreeCAD.Placement(pos_crank, rot_crank)
    
    # 5a. Horizontal Crankshaft Support Bracket (Поз. 16: Кронштейн кривошипа ВЧ.01.00.016)
    # Rigid stationary pillar supporting the cantilever M8 stationary axle of the crankshaft
    # Mounted on base_frame top surface (Z = 10.0), located behind the gear to prevent clash
    rot_bracket = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 210.0)
    crank_bracket = create_crankshaft_bracket()
    crank_bracket.Placement = FreeCAD.Placement(FreeCAD.Vector(pos_crank.x, pos_crank.y, 10.0), rot_bracket)
    
    # 8. Stripper Guide Tower
    # Positioned close to 120-degree cell (22.0, -38.1), rotated 30 deg around Z
    # Longitudinal axis (60 mm base width) is parallel to crankshaft disc line (30 deg)
    # Rotation axis of crankshaft is parallel to guide normal axis (-60 deg)
    beta_deg = 30.0
    rot_guide = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), beta_deg)
    u_norm = FreeCAD.Vector(-math.sin(math.radians(beta_deg)), math.cos(math.radians(beta_deg)), 0)
    u_len = FreeCAD.Vector(math.cos(math.radians(beta_deg)), math.sin(math.radians(beta_deg)), 0)
    s_dist = 24.0
    s_len = -8.0
    guide_x = 22.0 - s_dist * u_norm.x + s_len * u_len.x
    guide_y = -38.105 - s_dist * u_norm.y + s_len * u_len.y
    
    def make_screw_din912(d, l_thread, head_h=3.0, head_d=5.5):
        shank = make_cylinder(d / 2.0, l_thread, (0, 0, -l_thread))
        head = make_cylinder(head_d / 2.0, head_h, (0, 0, 0))
        return shank.fuse(head)

    stripper_guide = create_stripper_guide()
    stripper_guide.Placement = FreeCAD.Placement(FreeCAD.Vector(guide_x, guide_y, 10.0), rot_guide)
    
    # 8c. Berry Stripper (Поз. 15: Съемник ягод)
    stripper_body = create_stripper()
    stripper_body.translate(FreeCAD.Vector(0, 0, 8.0))
    stripper_screws = []
    for x_sc in [-10.0, 10.0]:
        sc = make_screw_din912(3.0, 16.0, head_h=3.0, head_d=5.5)
        sc.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), -90.0)
        sc.translate(FreeCAD.Vector(x_sc, 3.0, 56.0))
        stripper_screws.append(sc)
    stripper = Part.makeCompound([stripper_body] + stripper_screws)
    stripper.Placement = stripper_guide.Placement
    
    # 8a. Linear Guide Rail MGN9-100 (Поз. 14)
    # Mounted on stripper_guide step (Z = 43.0, face Y = 0.0)
    mat_r2g = FreeCAD.Matrix(
        0, 1, 0, 0,
        0, 0, 1, 0,
        1, 0, 0, 43.0,
        0, 0, 0, 1
    )
    pl_r2g = FreeCAD.Placement(mat_r2g)
    pl_rail_glob = stripper_guide.Placement.multiply(pl_r2g)
    mgn9_rail = create_mgn9_rail(length=100.0)
    mgn9_rail.Placement = pl_rail_glob
    
    # 8b. Linear Carriage MGN9H (Поз. 15)
    # Slides on rail along guide Z-axis; at BDC position Z_c = 86.39 mm
    z_c = 86.39
    mgn9h_carriage = create_mgn9h_carriage()
    mgn9h_carriage.translate(FreeCAD.Vector(z_c - 43.0, 0, 0))
    mgn9h_carriage.Placement = pl_rail_glob.multiply(mgn9h_carriage.Placement)
    
    # 7. Needle Slider Carriage (Поз. 7)
    # Mated to carriage top face (Y_guide = 10.0, Z_guide = z_c)
    slider = create_needle_slider()
    pl_slider_in_guide = FreeCAD.Placement(FreeCAD.Vector(0.0, 10.0, z_c), FreeCAD.Rotation())
    slider.Placement = stripper_guide.Placement.multiply(pl_slider_in_guide)
    
    # 13. Punch Needle Ø3x75 mm (Поз. 13)
    # Located inside slider socket, centered strictly at (8.0, 24.0) in guide coords
    # which maps to [X = 22.0, Y = -38.105] in global assembly coordinates
    needle_z_base = z_c + 14.0 - 75.0
    pl_needle_in_guide = FreeCAD.Placement(FreeCAD.Vector(8.0, 24.0, needle_z_base), FreeCAD.Rotation())
    punch_needle = create_punch_needle(length=75.0)
    punch_needle.Placement = stripper_guide.Placement.multiply(pl_needle_in_guide)
    
    # 6. Connecting Rod Kinematics & Placement (Поз. 6)
    p_crank_pin = crankshaft.Placement.multVec(FreeCAD.Vector(-18.0, 0.0, 12.0))
    p_slider_pin = slider.Placement.multVec(FreeCAD.Vector(17.0, -3.0, 16.0))
    v_pin_axis = rot_guide.multVec(FreeCAD.Vector(0, 1, 0))

    y_mid = (p_crank_pin.dot(v_pin_axis) + p_slider_pin.dot(v_pin_axis)) / 2.0
    p_crank_proj = p_crank_pin - v_pin_axis * p_crank_pin.dot(v_pin_axis) + v_pin_axis * y_mid
    p_slider_proj = p_slider_pin - v_pin_axis * p_slider_pin.dot(v_pin_axis) + v_pin_axis * y_mid

    vec_rod = p_slider_proj - p_crank_proj
    rod_length = vec_rod.Length
    rod_dir = vec_rod.normalize()
    p_rod_mid = (p_crank_proj + p_slider_proj) / 2.0

    con_rod = create_connecting_rod(length=rod_length)

    v_x_target = v_pin_axis
    v_z_target = rod_dir
    v_y_target = v_z_target.cross(v_x_target).normalize()

    mat_rod = FreeCAD.Matrix(
        v_x_target.x, v_y_target.x, v_z_target.x, 0,
        v_x_target.y, v_y_target.y, v_z_target.y, 0,
        v_x_target.z, v_y_target.z, v_z_target.z, 0,
        0, 0, 0, 1
    )
    con_rod.Placement = FreeCAD.Placement(p_rod_mid, FreeCAD.Rotation(mat_rod))
    
    # 9. Feeding Hopper
    hopper = create_hopper()
    hopper.Placement = FreeCAD.Placement(FreeCAD.Vector(-44.0, 0.0, 26.0), FreeCAD.Rotation())
    
    # 10. Hopper Vertical Stands & Mounting Fasteners (Поз. 10: Опоры бункера)
    # Stiff U-profile guides attached to base frame at Z = 10.0
    # Centerline aligned with hopper ears at X = -44.0, Y = ±52.0
    stand_raw = create_hopper_stand()
    
    # Stand +Y
    stand_p = stand_raw.copy()
    stand_p.Placement = FreeCAD.Placement(FreeCAD.Vector(-44.0, 52.0, 10.0), FreeCAD.Rotation())
    
    # Stand -Y (mirrored / rotated 180 deg around Z)
    stand_m = stand_raw.copy()
    rot180 = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 180.0)
    stand_m.Placement = FreeCAD.Placement(FreeCAD.Vector(-44.0, -52.0, 10.0), rot180)
    
    # Screws M3x10 fixing hopper ears in middle slot holes (Z = 70.0, nominal gap 10 mm)
    screw_p = make_screw_din912(3.0, 10.0, head_h=3.0, head_d=5.5)
    screw_p.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), -90.0)
    screw_p.translate(FreeCAD.Vector(-44.0, 62.0, 70.0))
    
    screw_m = make_screw_din912(3.0, 10.0, head_h=3.0, head_d=5.5)
    screw_m.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), 90.0)
    screw_m.translate(FreeCAD.Vector(-44.0, -62.0, 70.0))
    
    # Screws M3x8 fixing stand flanges to base frame (4 pcs, counterbored flush)
    screws_base = []
    for x_off in [-6.0, 6.0]:
        sb_p = make_screw_din912(3.0, 8.0, head_h=3.0, head_d=5.5)
        sb_p.translate(FreeCAD.Vector(-44.0 + x_off, 68.0, 12.0))
        screws_base.append(sb_p)
        
        sb_m = make_screw_din912(3.0, 8.0, head_h=3.0, head_d=5.5)
        sb_m.translate(FreeCAD.Vector(-44.0 + x_off, -68.0, 12.0))
        screws_base.append(sb_m)
        
    hopper_stands = Part.makeCompound([stand_p, stand_m, screw_p, screw_m] + screws_base)
    
    # 11. Ejector, Deflector & Chute Assembly (Поз. 12)
    # Positioned at Position 5 (60 deg), receiving pitted berries
    # Berry cycle: Load 0° (180°) -> Punch 120° (300°) -> Eject 240° (60°)
    r_pos5 = 44.0
    ang_pos5 = 60.0
    x_pos5 = r_pos5 * math.cos(math.radians(ang_pos5))
    y_pos5 = r_pos5 * math.sin(math.radians(ang_pos5))
    rot_pos5 = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), ang_pos5)
    pl_pos5 = FreeCAD.Placement(FreeCAD.Vector(x_pos5, y_pos5, 10.0), rot_pos5)

    ejector = create_ejector()
    ejector.Placement = pl_pos5
    deflector = create_deflector()
    deflector.Placement = pl_pos5
    chute = create_chute()
    chute.Placement = pl_pos5
    mono_chute = Part.makeCompound([ejector, deflector, chute])
    
    # 12. Pit Chute
    pit_chute = create_pit_chute()
    pit_chute.Placement = FreeCAD.Placement(FreeCAD.Vector(22.0, -38.1, 0.0), FreeCAD.Rotation())
    
    # 13. DC Motor JGY-370
    motor = create_motor_jgy370()
    motor.Placement = FreeCAD.Placement(FreeCAD.Vector(60.0, 0.0, 0.0), FreeCAD.Rotation())
    
    # Fasteners & Axle Hardware
    hardware = create_hardware()
    # already at origin
    
    parts_list = [
        ("BaseFrame", base_frame),
        ("Rotor", rotor),
        ("GenevaWheel", geneva_wheel),
        ("GenevaDriver", geneva_driver),
        ("FlangeCoupling", flange_coupling),
        ("HorizontalCrankshaft", crankshaft),
        ("CrankshaftBracket", crank_bracket),
        ("ConnectingRod", con_rod),
        ("StripperGuide", stripper_guide),
        ("Stripper", stripper),
        ("MGN9Rail", mgn9_rail),
        ("MGN9HCarriage", mgn9h_carriage),
        ("NeedleSlider", slider),
        ("PunchNeedle", punch_needle),
        ("Hopper", hopper),
        ("HopperStands", hopper_stands),
        ("MonolithicChute", mono_chute),
        ("PitChute", pit_chute),
        ("MotorJGY370", motor),
        ("Hardware", hardware),
    ]
    
    compound_shapes = []
    part_features = {}
    for name, shp in parts_list:
        feat = doc.addObject("Part::Feature", name)
        feat.Shape = shp
        part_features[name] = feat
        compound_shapes.append(shp)
        
    assembly_compound = Part.makeCompound(compound_shapes)
    asm_feat = doc.addObject("Part::Feature", "AssemblyCompound")
    asm_feat.Shape = assembly_compound
    doc.recompute()
    
    return asm_feat, part_features

def main():
    print("Initializing FreeCAD Document for Master Assembly...")
    doc = FreeCAD.newDocument("Cherry_Pitter_Master_Assembly")
    
    print("Constructing 3D B-Rep solid models and placing in kinematic coordinates...")
    asm_feat, part_features = build_assembly(doc)
    print("Assembly constructed successfully!")
    
    print("Setting up TechDraw GOST A1 Landscape drawing sheet...")
    page, template = create_drawing_page(doc, "A1_Landscape", "AssemblyDrawing")
    
    # Scale 1:1 on A1 sheet (841 x 594 mm)
    scale_ortho = 1.0
    scale_iso = 0.85
    
    # 1. Front View (Главный вид)
    add_part_view(doc, page, asm_feat, "FrontView", (0.0, -1.0, 0.0), scale_ortho, 185.0, 405.0)
    
    # 2. Top View (Вид сверху, выровнен по оси X с главным видом)
    add_part_view(doc, page, asm_feat, "TopView", (0.0, 0.0, 1.0), scale_ortho, 185.0, 165.0)
    
    # 3. Left View (Вид слева, выровнен по оси Y с главным видом)
    add_part_view(doc, page, asm_feat, "LeftView", (1.0, 0.0, 0.0), scale_ortho, 445.0, 405.0)
    doc.recompute()
    
    print("Adding Specification Table (BOM) per GOST 2.106...")
    rows = [
        ('', '', 'Сборочные единицы и детали', '', ''),
        ('1', 'ВЧ.01.00.001', 'Станина-шасси', '1', 'PETG'),
        ('2', 'ВЧ.01.00.002', 'Карусель ягод (Барабан)', '1', 'PETG'),
        ('3', 'ВЧ.01.00.003', 'Колесо мальтийского креста', '1', 'PETG'),
        ('4', 'ВЧ.01.00.004', 'Колесо ведущее коническое', '1', 'PETG, z=40, m=2'),
        ('5', 'ВЧ.01.00.005', 'Колесо коническое с кривошипом', '1', 'PETG, z=40, m=2'),
        ('6', 'ВЧ.01.00.006', 'Шатун с головками SI3T/K', '1', 'L=85 мм, M3'),
        ('7', 'ВЧ.01.00.007', 'Каретка штока', '1', 'PETG, сокет ф3'),
        ('8', 'ВЧ.01.00.008', 'Стойка направляющей MGN9', '1', 'PETG'),
        ('9', 'ВЧ.01.00.009', 'Бункер загрузочный', '1', 'PETG'),
        ('10', 'ВЧ.01.00.010', 'Опора бункера', '2', 'PETG'),
        ('11', 'ВЧ.01.00.011', 'Лоток отвода косточек', '1', 'PETG'),
        ('12', 'ВЧ.01.00.012', 'Выталкиватель ягод', '1', 'PETG'),
        ('13', 'ВЧ.01.00.013', 'Лоток отвода чистых ягод', '1', 'PETG'),
        ('14', 'ВЧ.01.00.014', 'Игла штока Ø3х75', '1', 'Сталь 12Х18Н10Т'),
        ('15', 'ВЧ.01.00.015', 'Съемник ягод', '1', 'PETG'),
        ('16', 'ВЧ.01.00.016', 'Кронштейн кривошипа', '1', 'PETG'),
        ('', '', 'Стандартные изделия', '', ''),
        ('17', 'ВЧ.02.00.002', 'Рельс направляющий MGN9-100', '1', 'Сталь 55 / ТВЧ'),
        ('18', 'ВЧ.02.00.001', 'Каретка шариковая MGN9H', '1', 'Сталь GCr15'),
        ('19', '', 'Мотор-редуктор JGY-370', '1', '12В 30об/м'),
        ('20', 'ГОСТ 8338-75', 'Подшипник 608ZZ (8x22x7)', '2', 'Сталь'),
        ('21', '', 'Вал стальной прециз. 5х75', '1', 'Сталь 45'),
        ('22', 'DIN 912', 'Винт M8x65 с гайкой', '1', 'Сталь'),
        ('23', 'ВЧ.00.00.011', 'Фланец переходный (коннектор) ф6', '1', 'Сталь оцинк.'),
        ('24', 'DIN 912', 'Винты M3x8 (фланец)', '4', 'Сталь 8.8'),
        ('25', 'ГОСТ 7798-70', 'Комплект крепежа M3, M4', '1', 'Компл.')
    ]
    
    w_total = 185.0
    row_h = 7.2
    h_total = 14.0 + len(rows) * row_h
    
    bom_lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_total}mm" height="{h_total}mm" viewBox="0 0 {w_total} {h_total}">']
    bom_lines.append(f'<rect x="0" y="0" width="{w_total}" height="{h_total}" fill="white" stroke="black" stroke-width="0.7" />')
    bom_lines.append(f'<rect x="0" y="0" width="{w_total}" height="14" fill="#f0f0f0" stroke="black" stroke-width="0.7" />')
    bom_lines.append('<text x="92.5" y="9.5" font-family="osifont, Arial" font-size="4.5" font-weight="bold" text-anchor="middle" fill="black">СПЕЦИФИКАЦИЯ СОСТАВНЫХ ЧАСТЕЙ</text>')
    
    col_x = [0, 12, 57, 132, 147, 185]
    for x in col_x[1:-1]:
        bom_lines.append(f'<line x1="{x}" y1="14" x2="{x}" y2="{h_total}" stroke="black" stroke-width="0.35" />')
        
    for i, r in enumerate(rows):
        y_top = 14.0 + i * row_h
        y_text = y_top + 5.0
        stroke_w = '0.7' if i == 0 else '0.35'
        if i == 0:
            bom_lines.append(f'<rect x="0" y="{y_top}" width="{w_total}" height="{row_h}" fill="#fafafa" stroke="none" />')
        bom_lines.append(f'<line x1="0" y1="{y_top+row_h}" x2="{w_total}" y2="{y_top+row_h}" stroke="black" stroke-width="{stroke_w}" />')
        
        pos, desig, name, qty, note = r
        is_section = (pos == '' and desig == '' and name != '' and qty == '')
        if is_section:
            bom_lines.append(f'<text x="92.5" y="{y_text}" font-family="osifont, Arial" font-size="3.8" font-weight="bold" text-anchor="middle" fill="black">{name}</text>')
        else:
            weight = 'bold' if i == 0 else 'normal'
            size = '3.5' if i == 0 else '3.1'
            bom_lines.append(f'<text x="6" y="{y_text}" font-family="osifont, Arial" font-size="{size}" font-weight="{weight}" text-anchor="middle" fill="black">{pos}</text>')
            bom_lines.append(f'<text x="14" y="{y_text}" font-family="osifont, Arial" font-size="{size}" font-weight="{weight}" fill="black">{desig}</text>')
            bom_lines.append(f'<text x="59" y="{y_text}" font-family="osifont, Arial" font-size="{size}" font-weight="{weight}" fill="black">{name}</text>')
            bom_lines.append(f'<text x="139.5" y="{y_text}" font-family="osifont, Arial" font-size="{size}" font-weight="{weight}" text-anchor="middle" fill="black">{qty}</text>')
            bom_lines.append(f'<text x="149" y="{y_text}" font-family="osifont, Arial" font-size="{size}" font-weight="{weight}" fill="black">{note}</text>')
            
    bom_lines.append('</svg>')
    svg_bom = '\n'.join(bom_lines)
    
    sym_bom = doc.addObject('TechDraw::DrawViewSymbol', 'BOMTable')
    sym_bom.Symbol = svg_bom
    page.addView(sym_bom)
    doc.recompute()
    sym_bom.X = 743.5
    sym_bom.Y = 585.0 - h_total / 2.0
    doc.recompute()
    
    print("Adding Technical Requirements per GOST 2.316...")
    notes_h = 135.0
    svg_notes = f'''<svg xmlns="http://www.w3.org/2000/svg" width="185mm" height="{notes_h}mm" viewBox="0 0 185 {notes_h}">
<rect x="0" y="0" width="185" height="{notes_h}" fill="white" stroke="black" stroke-width="0.7" />
<text x="10" y="14" font-family="osifont, Arial" font-size="4.2" font-weight="bold" fill="black">Технические требования:</text>
<text x="10" y="25" font-family="osifont, Arial" font-size="3.2" fill="black">1. * Размеры для справок.</text>
<text x="10" y="34" font-family="osifont, Arial" font-size="3.2" fill="black">2. Габаритные размеры изделия: 212 х 211 х 183* мм.</text>
<text x="10" y="43" font-family="osifont, Arial" font-size="3.2" fill="black">3. Межосевое расстояние мальтийского привода: 60* мм.</text>
<text x="10" y="52" font-family="osifont, Arial" font-size="3.2" fill="black">4. Передача коническая эвольвентная 1:1, z=40, m=2.0 мм (freecad.gears).</text>
<text x="10" y="61" font-family="osifont, Arial" font-size="3.2" fill="black">5. Величина рабочего хода штока пробивки: 36.0* мм.</text>
<text x="10" y="70" font-family="osifont, Arial" font-size="3.2" fill="black">6. Привод штока — шатун L=85 мм с шарнирами SI3T/K,</text>
<text x="14" y="77" font-family="osifont, Arial" font-size="3.2" fill="black">самоустанавливающийся без перекосов и заклиниваний.</text>
<text x="10" y="86" font-family="osifont, Arial" font-size="3.2" fill="black">7. Синхронизация: пробивка ягоды — в фазе выстоя (240°).</text>
<text x="14" y="93" font-family="osifont, Arial" font-size="3.2" fill="black">При повороте барабана (120°) игла выведена выше съемника.</text>
<text x="10" y="102" font-family="osifont, Arial" font-size="3.2" fill="black">8. Смазка шарниров и шестерен — ЦИАТИМ-201 ГОСТ 6267-74.</text>
<text x="10" y="111" font-family="osifont, Arial" font-size="3.2" fill="black">9. Детали поз. 1..13, 15, 16 изготавливать методом 3D-печати</text>
<text x="14" y="118" font-family="osifont, Arial" font-size="3.2" fill="black">из PETG с заполнением не менее 40%.</text>

<rect x="8" y="122" width="169" height="10" fill="#f5f5f5" stroke="#888" stroke-width="0.35" />
<text x="14" y="129" font-family="osifont, Arial" font-size="3.2" font-weight="bold" fill="black">• Производительность: до 30 ягод/мин   • Ход: 36.0 мм</text>
</svg>'''
    
    sym_notes = doc.addObject('TechDraw::DrawViewSymbol', 'TechNotes')
    sym_notes.Symbol = svg_notes
    page.addView(sym_notes)
    doc.recompute()
    sym_notes.X = 743.5
    sym_notes.Y = 62.0 + notes_h / 2.0
    doc.recompute()
    
    print("Adding Dimensions and Position Balloons Overlay...")
    svg_overlay = '''<svg xmlns="http://www.w3.org/2000/svg" width="600mm" height="580mm" viewBox="0 0 600 580">
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
    <path d="M 0 2 L 10 5 L 0 8 z" fill="#000" />
  </marker>
  <marker id="arrow-rev" viewBox="0 0 10 10" refX="0" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
    <path d="M 10 2 L 0 5 L 10 8 z" fill="#000" />
  </marker>
  <marker id="dot" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="3" markerHeight="3">
    <circle cx="5" cy="5" r="4" fill="#000" />
  </marker>
</defs>
<style>
  .dim-line { stroke: #000; stroke-width: 0.35; }
  .dim-text { font-family: osifont, Arial, sans-serif; font-size: 4.5px; fill: #000; text-anchor: middle; font-weight: bold; }
  .balloon-circle { fill: #fff; stroke: #000; stroke-width: 0.5; }
  .balloon-text { font-family: osifont, Arial, sans-serif; font-size: 4.5px; font-weight: bold; fill: #000; text-anchor: middle; }
  .leader { stroke: #000; stroke-width: 0.35; fill: none; }
</style>

<!-- DIMENSIONS ON FRONT VIEW -->
<line x1="50" y1="90" x2="50" y2="268" class="dim-line" marker-start="url(#arrow-rev)" marker-end="url(#arrow)" />
<line x1="45" y1="90" x2="160" y2="90" class="dim-line" />
<line x1="45" y1="268" x2="240" y2="268" class="dim-line" />
<text x="42" y="184" class="dim-text" transform="rotate(-90 42 184)">183*</text>

<line x1="80" y1="285" x2="290" y2="285" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="80" y1="275" x2="80" y2="290" class="dim-line" />
<line x1="290" y1="275" x2="290" y2="290" class="dim-line" />
<text x="185" y="282" class="dim-text">212*</text>

<!-- BALLOONS (Front View) -->
<path d="M 207 99 L 170 70 L 160 70" class="leader" marker-start="url(#dot)" />
<circle cx="153" cy="70" r="7" class="balloon-circle" />
<text x="153" y="71.7" class="balloon-text">8</text>

<path d="M 215 110 L 235 90 L 245 90" class="leader" marker-start="url(#dot)" />
<circle cx="252" cy="90" r="7" class="balloon-circle" />
<text x="252" y="91.7" class="balloon-text">17</text>

<path d="M 212 125 L 235 115 L 245 115" class="leader" marker-start="url(#dot)" />
<circle cx="252" cy="115" r="7" class="balloon-circle" />
<text x="252" y="116.7" class="balloon-text">18</text>

<path d="M 268 148 L 285 148 L 295 148" class="leader" marker-start="url(#dot)" />
<circle cx="302" cy="148" r="7" class="balloon-circle" />
<text x="302" y="149.7" class="balloon-text">16</text>

<path d="M 207 134 L 180 115 L 170 115" class="leader" marker-start="url(#dot)" />
<circle cx="163" cy="115" r="7" class="balloon-circle" />
<text x="163" y="116.7" class="balloon-text">7</text>

<path d="M 200 155 L 175 165 L 165 165" class="leader" marker-start="url(#dot)" />
<circle cx="158" cy="165" r="7" class="balloon-circle" />
<text x="158" y="166.7" class="balloon-text">14</text>

<path d="M 190 172 L 165 190 L 155 190" class="leader" marker-start="url(#dot)" />
<circle cx="148" cy="190" r="7" class="balloon-circle" />
<text x="148" y="191.7" class="balloon-text">15</text>

<path d="M 185 240 L 160 210 L 150 210" class="leader" marker-start="url(#dot)" />
<circle cx="143" cy="210" r="7" class="balloon-circle" />
<text x="143" y="211.7" class="balloon-text">2</text>

<path d="M 245 171 L 265 195 L 275 195" class="leader" marker-start="url(#dot)" />
<circle cx="282" cy="195" r="7" class="balloon-circle" />
<text x="282" y="196.7" class="balloon-text">4</text>

<path d="M 245 132 L 275 115 L 285 115" class="leader" marker-start="url(#dot)" />
<circle cx="292" cy="115" r="7" class="balloon-circle" />
<text x="292" y="116.7" class="balloon-text">5</text>

<path d="M 215 160 L 235 180 L 245 180" class="leader" marker-start="url(#dot)" />
<circle cx="252" cy="180" r="7" class="balloon-circle" />
<text x="252" y="181.7" class="balloon-text">6</text>

<!-- BALLOONS (Top View) -->
<path d="M 141 420 L 120 380 L 110 380" class="leader" marker-start="url(#dot)" />
<circle cx="103" cy="380" r="7" class="balloon-circle" />
<text x="103" y="381.7" class="balloon-text">9</text>

<path d="M 141 368 L 120 330 L 110 330" class="leader" marker-start="url(#dot)" />
<circle cx="103" cy="330" r="7" class="balloon-circle" />
<text x="103" y="331.7" class="balloon-text">10</text>

<path d="M 225 365 L 255 350 L 265 350" class="leader" marker-start="url(#dot)" />
<circle cx="272" cy="350" r="7" class="balloon-circle" />
<text x="272" y="351.7" class="balloon-text">12</text>

<path d="M 207 465 L 207 500 L 220 500" class="leader" marker-start="url(#dot)" />
<circle cx="227" cy="500" r="7" class="balloon-circle" />
<text x="227" y="501.7" class="balloon-text">11</text>
</svg>'''
    
    sym_dim = doc.addObject('TechDraw::DrawViewSymbol', 'OverlayAnnotations')
    sym_dim.Symbol = svg_overlay
    page.addView(sym_dim)
    doc.recompute()
    sym_dim.X = 300.0
    sym_dim.Y = 290.0
    doc.recompute()
    
    print("Filling GOST Title Block...")
    title_data = {
        'Номер': 'ВЧ.00.00.000 СБ',
        'Название': 'Вишнечистка автоматическая',
        'Информация': 'Сборочный чертеж',
        'Масштаб': '1:1',
        'Лист': '1',
        'Листов': '1',
        'Масса': '0.640',
        'Организация1': 'Проект VISHNI',
        'Организация2': 'VISHNI CAD',
        'Разработал': 'Инженер',
        'Проверил': 'Контролер',
        'Утвердил': 'Руководитель',
        'Дата_разработки': '18.09.26',
        'Дата_проверки': '18.09.26',
        'Дата_утверждения': '18.09.26'
    }
    fill_gost_title_block(template, title_data)
    doc.recompute()
    
    out_pdf = os.path.abspath("assembly_drawing.pdf")
    out_fcstd = os.path.abspath("assembly_drawing.FCStd")
    out_png = os.path.abspath("assembly_drawing.png")
    
    export_drawing(doc, page, out_pdf, out_fcstd, out_png)
    print("Master Assembly Drawing generated successfully!")

if __name__ == "__main__":
    main()
    os._exit(0)
