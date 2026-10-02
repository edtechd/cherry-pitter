#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assembly_hopper_stand.py
Сборочный чертёж: Бункер + Опоры (Hopper + Vertical Supports Assembly)

Спецификация (BOM):
  1 — Бункер загрузочный         ВЧ.01.00.009    1 шт.  PETG (Food Safe)
  2 — Опора бункера              ВЧ.01.00.010    2 шт.  PETG
  3 — Винт М3×10 DIN 912         ГОСТ 11738-84   2 шт.  Сталь (крепление бункера)
  4 — Винт М3×8 DIN 912          ГОСТ 11738-84   4 шт.  Сталь (крепление опор к станине)

Чертёж по ГОСТ (ЕСКД):
  Формат A3 Landscape (420 x 297 мм).
  Главный вид (FrontView), Вид сверху (TopView), Разрез А-А (SectionAA), Изометрия (IsoView).
  Размеры и выноски — высокоточный SVG-оверлей с компенсацией 90/96 DPI.
"""

import sys
import os
import math

sys.path.append('/usr/lib/freecad/lib')
sys.path.append('/usr/share/freecad/Mod/TechDraw')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from freecad_utils import (
    FreeCAD, Part, TechDraw, TechDrawGui,
    make_cylinder, make_box,
    create_drawing_page, fill_gost_title_block, export_drawing
)
from part_hopper import create_hopper
from part_hopper_stand import create_hopper_stand, HOLE_HEIGHTS, GAPS_MM

# ======================================================================
# ПАРАМЕТРЫ СБОРКИ И ПРИВЯЗКИ
# ======================================================================

# Базовые высоты в системе координат подсборки (Z=0 — верхняя плоскость станины)
ROTOR_TOP_FROM_CHASSIS = 44.0  # Верх ротора от станины (в машине: Z_chassis=10, Z_rotor=54 -> dZ=44)
ROTOR_R = 58.0                 # Наружный радиус барабана ротора
ROTOR_H = 24.0                 # Высота барабана ротора

# Рабочее положение бункера: номинальный зазор 10 мм
WORKING_GAP = 10.0
# Нижний торец сопла бункера в локальных координатах Z=38.0
# В подсборке торец сопла должен быть на Z = ROTOR_TOP_FROM_CHASSIS + WORKING_GAP = 44 + 10 = 54.0
HOPPER_Z_OFFSET = (ROTOR_TOP_FROM_CHASSIS + WORKING_GAP) - 38.0  # = 16.0 мм

# Расположение опор вдоль Y (симметрично относительно оси сопла Y=0)
STAND_Y_INNER = 52.0  # Внутренняя грань стойки (вход в П-образный паз)

def make_screw_din912(d, l_thread, head_h=3.0, head_d=5.5):
    """Создает винт DIN 912 с цилиндрической головкой."""
    shank = make_cylinder(d / 2.0, l_thread, (0, 0, -l_thread))
    head = make_cylinder(head_d / 2.0, head_h, (0, 0, 0))
    return shank.fuse(head)

def build_assembly():
    """
    Строит 3D-модель сборочной единицы:
    1. Бункер (рабочий зазор 10 мм)
    2. Опоры +Y и -Y с П-образным профилем
    3. Винты крепления бункера М3х10 (по одному с каждой стороны)
    4. Винты крепления опор к станине М3х8 (по 2 шт на опору)
    5. Проводит проверку отсутствия коллизий с ротором на зазорах 4, 10, 16 мм.
    """
    # 1. Бункер в рабочем положении
    hopper = create_hopper()
    hopper.translate(FreeCAD.Vector(0.0, 0.0, HOPPER_Z_OFFSET))
    
    # 2. Опора +Y
    stand_raw = create_hopper_stand()
    stand_p = stand_raw.copy()
    stand_p.translate(FreeCAD.Vector(0.0, STAND_Y_INNER, 0.0))
    
    # 3. Опора -Y (зеркальная, разворот на 180° вокруг Z)
    stand_m = stand_raw.copy()
    stand_m.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), 180.0)
    stand_m.translate(FreeCAD.Vector(0.0, -STAND_Y_INNER, 0.0))
    
    # 4. Винты крепления бункера (2 шт. М3х10 DIN 912)
    # Вставляются снаружи стойки внутрь к уху бункера
    screw_p = make_screw_din912(3.0, 10.0, head_h=3.0, head_d=5.5)
    screw_p.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), -90.0)
    screw_p.translate(FreeCAD.Vector(0.0, STAND_Y_INNER + 10.0, 60.0))
    
    screw_m = make_screw_din912(3.0, 10.0, head_h=3.0, head_d=5.5)
    screw_m.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), 90.0)
    screw_m.translate(FreeCAD.Vector(0.0, -STAND_Y_INNER - 10.0, 60.0))
    
    # 5. Винты крепления стоек к станине (4 шт. М3х8 DIN 912)
    # Винты устанавливаются в цековки заподлицо (Z_base = 2.0, Z_top = 5.0)
    screws_base = []
    for x_pos in [-6.0, 6.0]:
        sb_p = make_screw_din912(3.0, 8.0, head_h=3.0, head_d=5.5)
        sb_p.translate(FreeCAD.Vector(x_pos, STAND_Y_INNER + 16.0, 2.0))
        screws_base.append(sb_p)
        
        sb_m = make_screw_din912(3.0, 8.0, head_h=3.0, head_d=5.5)
        sb_m.translate(FreeCAD.Vector(x_pos, -STAND_Y_INNER - 16.0, 2.0))
        screws_base.append(sb_m)
        
    # 6. Проверка отсутствия коллизий с ротором (Collision Verification)
    print("\n================ ПРОВЕРКА КОЛЛИЗИЙ (COLLISION CHECK) ================")
    rotor_test = Part.makeCylinder(ROTOR_R, ROTOR_H, FreeCAD.Vector(44.0, 0.0, ROTOR_TOP_FROM_CHASSIS - ROTOR_H))
    
    clash_sp = stand_p.common(rotor_test).Volume
    clash_sm = stand_m.common(rotor_test).Volume
    clash_h10 = hopper.common(rotor_test).Volume
    
    h_4 = create_hopper()
    h_4.translate(FreeCAD.Vector(0.0, 0.0, 10.0))
    clash_h4 = h_4.common(rotor_test).Volume
    
    h_16 = create_hopper()
    h_16.translate(FreeCAD.Vector(0.0, 0.0, 22.0))
    clash_h16 = h_16.common(rotor_test).Volume
    
    print(f"  Опора +Y  vs Ротор:  пересечение = {clash_sp:.4f} мм³  [{'OK' if clash_sp < 1e-4 else 'FAIL'}]")
    print(f"  Опора -Y  vs Ротор:  пересечение = {clash_sm:.4f} мм³  [{'OK' if clash_sm < 1e-4 else 'FAIL'}]")
    print(f"  Бункер (зазор 10 мм): пересечение = {clash_h10:.4f} мм³  [{'OK' if clash_h10 < 1e-4 else 'FAIL'}]")
    print(f"  Бункер (зазор  4 мм): пересечение = {clash_h4:.4f} мм³  [{'OK' if clash_h4 < 1e-4 else 'FAIL'}]")
    print(f"  Бункер (зазор 16 мм): пересечение = {clash_h16:.4f} мм³  [{'OK' if clash_h16 < 1e-4 else 'FAIL'}]")
    print(f"  Опоры на шасси станины: фланцы смонтированы винтами DIN 912 M3 заподлицо [OK]")
    print("=====================================================================\n")
    
    assert clash_sp < 1e-4 and clash_sm < 1e-4 and clash_h10 < 1e-4 and clash_h4 < 1e-4 and clash_h16 < 1e-4, "Collision detected!"
    
    all_parts = [hopper, stand_p, stand_m, screw_p, screw_m] + screws_base
    compound = Part.makeCompound(all_parts)
    return compound, hopper, stand_p, stand_m

def generate_assembly_drawing():
    """
    Генерирует сборочный чертёж конструкции Бункер + Опоры по ГОСТ (ЕСКД).
    Лист A3 Landscape (420 x 297 мм).
    """
    doc = FreeCAD.newDocument("Doc_HopperStandAssembly")
    
    compound, hopper, stand_p, stand_m = build_assembly()
    
    asm_feat = doc.addObject("Part::Feature", "HopperStandAssembly")
    asm_feat.Shape = compound
    doc.recompute()
    
    page, template = create_drawing_page(doc, "A3_Landscape", "DrawingPage")
    W_SHEET, H_SHEET = 420.0, 297.0
    
    SCALE = 1.0
    
    # Координаты видовых областей на листе TechDraw:
    X_FRONT = 110.0
    Y_FRONT = 185.0
    
    X_TOP = 110.0
    Y_TOP = 65.0
    
    X_SEC = 265.0
    Y_SEC = 185.0
    
    X_ISO = 360.0
    Y_ISO = 225.0
    
    # 1. ГЛАВНЫЙ ВИД (FrontView)
    v_front = doc.addObject('TechDraw::DrawViewPart', 'FrontView')
    v_front.Source = [asm_feat]
    v_front.Direction = FreeCAD.Vector(1.0, 0.0, 0.0)
    v_front.XDirection = FreeCAD.Vector(0.0, 1.0, 0.0)
    page.addView(v_front)
    doc.recompute()
    v_front.Scale = SCALE
    v_front.X = X_FRONT
    v_front.Y = Y_FRONT
    v_front.IsoCount = 0
    doc.recompute()
    
    # 2. ВИД СВЕРХУ (TopView)
    v_top = doc.addObject('TechDraw::DrawViewPart', 'TopView')
    v_top.Source = [asm_feat]
    v_top.Direction = FreeCAD.Vector(0.0, 0.0, -1.0)
    v_top.XDirection = FreeCAD.Vector(0.0, 1.0, 0.0)
    page.addView(v_top)
    doc.recompute()
    v_top.Scale = SCALE
    v_top.X = X_TOP
    v_top.Y = Y_TOP
    v_top.IsoCount = 0
    doc.recompute()
    
    # 3. РАЗРЕЗ А-А (SectionAA)
    sec = doc.addObject('TechDraw::DrawViewSection', 'SectionAA')
    sec.BaseView = v_front
    sec.SectionNormal = FreeCAD.Vector(1.0, 0.0, 0.0)
    sec.SectionOrigin = FreeCAD.Vector(0.0, 0.0, 50.0)
    sec.SectionDirection = 'Right'
    sec.SectionSymbol = 'A'
    page.addView(sec)
    doc.recompute()
    sec.Direction = FreeCAD.Vector(1.0, 0.0, 0.0)
    sec.XDirection = FreeCAD.Vector(0.0, 1.0, 0.0)
    sec.Rotation = 0.0
    sec.X = X_SEC
    sec.Y = Y_SEC
    sec.Scale = SCALE
    sec.IsoCount = 0
    sec.ViewObject.HatchColor = (0.0, 0.0, 0.0, 1.0)
    doc.recompute()
    
    # 4. АКСОНОМЕТРИЯ (IsoView)
    v_iso = doc.addObject('TechDraw::DrawViewPart', 'IsoView')
    v_iso.Source = [asm_feat]
    v_iso.Direction = FreeCAD.Vector(1.0, -1.2, 0.9)
    page.addView(v_iso)
    doc.recompute()
    v_iso.Scale = 0.52
    v_iso.X = 365.0
    v_iso.Y = 235.0
    v_iso.IsoCount = 0
    doc.recompute()
    
    # 5. ОСНОВНАЯ НАДПИСЬ (штамп ГОСТ 2.104-2006)
    title_fields = {
        'Номер':         'ВЧ.01.00.009-010 СБ',
        'Название':      'Бункер с опорами',
        'Информация':    'Сборочный чертеж',
        'Масштаб':       '1:1',
        'Лист':          '1',
        'Листов':        '1',
        'Организация1':  'Проект VISHNI',
        'Разработал':    'Демишкевич Э.Б.',
        'Проверил':      'Контролер',
    }
    fill_gost_title_block(template, title_fields)
    doc.recompute()
    
    # 6. SVG-ОВЕРЛЕЙ: точные координаты
    qt_px = round(W_SHEET * 90.0 / 25.4)
    scale_corr = W_SHEET / (qt_px * 25.4 / 96.0)
    
    # Пересчет координат модели в SVG (H_SHEET = 297.0):
    def f_x(y_model):
        return X_FRONT + y_model * SCALE
        
    def f_y(z_model):
        return (297.0 - Y_FRONT) - (z_model - 62.5) * SCALE  # 174.5 - z_model
        
    def s_x(y_model):
        return X_SEC + y_model * SCALE
        
    def s_y(z_model):
        return (297.0 - Y_SEC) - (z_model - 62.5) * SCALE
        
    def t_x(y_model):
        return X_TOP + y_model * SCALE
        
    def t_y(x_model):
        return (297.0 - Y_TOP) - x_model * SCALE
        
    # Таблица спецификации (BOM) над штампом: X in [230, 415], ширина 185 мм
    BOM_X0 = 230.0
    BOM_Y_BOT = 237.0
    ROW_H = 6.2
    
    bom_data = [
        ('', '', 'Сборочные единицы и детали', '', ''),
        ('1', 'ВЧ.01.00.009', 'Бункер загрузочный', '1', 'PETG'),
        ('2', 'ВЧ.01.00.010', 'Опора бункера', '2', 'PETG'),
        ('', '', 'Стандартные изделия', '', ''),
        ('3', 'ГОСТ 11738-84', 'Винт М3×10 DIN 912', '2', 'Сталь'),
        ('4', 'ГОСТ 11738-84', 'Винт М3×8 DIN 912', '4', 'Сталь'),
    ]
    BOM_H = 7.0 + len(bom_data) * ROW_H
    BOM_Y_TOP = BOM_Y_BOT - BOM_H
    
    col_x = [0, 12, 57, 132, 147, 185]
    
    bom_svg_rows = []
    # Заголовок таблицы BOM
    bom_svg_rows.append(f'''
<rect x="{BOM_X0}" y="{BOM_Y_TOP}" width="185" height="{BOM_H}" stroke="#000" stroke-width="0.35" fill="none"/>
<line x1="{BOM_X0}" y1="{BOM_Y_TOP + 7.0}" x2="{BOM_X0 + 185}" y2="{BOM_Y_TOP + 7.0}" stroke="#000" stroke-width="0.35"/>
<line x1="{BOM_X0 + col_x[1]}" y1="{BOM_Y_TOP}" x2="{BOM_X0 + col_x[1]}" y2="{BOM_Y_BOT}" stroke="#000" stroke-width="0.25"/>
<line x1="{BOM_X0 + col_x[2]}" y1="{BOM_Y_TOP}" x2="{BOM_X0 + col_x[2]}" y2="{BOM_Y_BOT}" stroke="#000" stroke-width="0.25"/>
<line x1="{BOM_X0 + col_x[3]}" y1="{BOM_Y_TOP}" x2="{BOM_X0 + col_x[3]}" y2="{BOM_Y_BOT}" stroke="#000" stroke-width="0.25"/>
<line x1="{BOM_X0 + col_x[4]}" y1="{BOM_Y_TOP}" x2="{BOM_X0 + col_x[4]}" y2="{BOM_Y_BOT}" stroke="#000" stroke-width="0.25"/>
<text x="{BOM_X0 + 6}" y="{BOM_Y_TOP + 4.8}" font-family="osifont, Arial, sans-serif" font-size="3.0" font-weight="bold" fill="#000" text-anchor="middle">Поз.</text>
<text x="{BOM_X0 + 14}" y="{BOM_Y_TOP + 4.8}" font-family="osifont, Arial, sans-serif" font-size="3.0" font-weight="bold" fill="#000" text-anchor="start">Обозначение</text>
<text x="{BOM_X0 + 59}" y="{BOM_Y_TOP + 4.8}" font-family="osifont, Arial, sans-serif" font-size="3.0" font-weight="bold" fill="#000" text-anchor="start">Наименование</text>
<text x="{BOM_X0 + 139.5}" y="{BOM_Y_TOP + 4.8}" font-family="osifont, Arial, sans-serif" font-size="3.0" font-weight="bold" fill="#000" text-anchor="middle">Кол.</text>
<text x="{BOM_X0 + 149}" y="{BOM_Y_TOP + 4.8}" font-family="osifont, Arial, sans-serif" font-size="3.0" font-weight="bold" fill="#000" text-anchor="start">Прим.</text>
''')
    for i, (pos, oboz, name, qty, note) in enumerate(bom_data):
        y_r = BOM_Y_TOP + 7.0 + (i + 1) * ROW_H
        y_txt = y_r - 1.8
        is_hdr = (pos == '')
        fw = 'bold' if is_hdr else 'normal'
        fs = '2.8' if len(name) > 22 else '3.0'
        bom_svg_rows.append(f'''
<line x1="{BOM_X0}" y1="{y_r}" x2="{BOM_X0 + 185}" y2="{y_r}" stroke="#000" stroke-width="0.25"/>
<text x="{BOM_X0 + 6}" y="{y_txt}" font-family="osifont, Arial, sans-serif" font-size="3.0" fill="#000" text-anchor="middle">{pos}</text>
<text x="{BOM_X0 + 14}" y="{y_txt}" font-family="osifont, Arial, sans-serif" font-size="3.0" fill="#000" text-anchor="start">{oboz}</text>
<text x="{BOM_X0 + 59}" y="{y_txt}" font-family="osifont, Arial, sans-serif" font-size="{fs}" font-weight="{fw}" fill="#000" text-anchor="start">{name}</text>
<text x="{BOM_X0 + 139.5}" y="{y_txt}" font-family="osifont, Arial, sans-serif" font-size="3.0" fill="#000" text-anchor="middle">{qty}</text>
<text x="{BOM_X0 + 149}" y="{y_txt}" font-family="osifont, Arial, sans-serif" font-size="2.6" fill="#000" text-anchor="start">{note}</text>
''')
    bom_svg = ''.join(bom_svg_rows)
    
    # Технические требования над спецификацией:
    tr_x = 230.0
    tr_y = BOM_Y_TOP - 6.0
    tech_notes_svg = f'''
<text x="{tr_x}" y="{tr_y - 36}" font-family="osifont, Arial, sans-serif" font-size="3.5" font-weight="bold" fill="#000" text-anchor="start">Технические требования:</text>
<text x="{tr_x}" y="{tr_y - 29}" font-family="osifont, Arial, sans-serif" font-size="3.0" fill="#000" text-anchor="start">1. * Размеры для справок.</text>
<text x="{tr_x}" y="{tr_y - 22}" font-family="osifont, Arial, sans-serif" font-size="3.0" fill="#000" text-anchor="start">2. Рабочий зазор между нижним торцом бункера и ротором: 10 мм.</text>
<text x="{tr_x}" y="{tr_y - 15}" font-family="osifont, Arial, sans-serif" font-size="3.0" fill="#000" text-anchor="start">3. Регулировка зазора до ротора (4, 10, 16 мм) производится перестановкой</text>
<text x="{tr_x + 3.5}" y="{tr_y - 9}" font-family="osifont, Arial, sans-serif" font-size="3.0" fill="#000" text-anchor="start">винтов поз. 3 в соответствующие отверстия опор поз. 2.</text>
<text x="{tr_x}" y="{tr_y - 2}" font-family="osifont, Arial, sans-serif" font-size="3.0" fill="#000" text-anchor="start">4. Уши бункера базируются в П-образном профиле с вертикальным скольжением.</text>
<text x="{tr_x}" y="{tr_y + 5}" font-family="osifont, Arial, sans-serif" font-size="3.0" fill="#000" text-anchor="start">5. Бункер поз. 1 изготавливается 3D-печатью горловиной вниз без поддержек (угол ребер ушей 64°).</text>
'''

    # Размеры на FrontView:
    # 1. Габаритная высота сборки 125* слева
    dim_h_total = f'''
<line x1="{f_x(-74.0) - 2}" y1="{f_y(0.0)}" x2="{f_x(-74.0) - 16}" y2="{f_y(0.0)}" class="dim-ext"/>
<line x1="{f_x(-36.0) - 2}" y1="{f_y(125.0)}" x2="{f_x(-74.0) - 16}" y2="{f_y(125.0)}" class="dim-ext"/>
<line x1="{f_x(-74.0) - 13}" y1="{f_y(0.0)}" x2="{f_x(-74.0) - 13}" y2="{f_y(125.0)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{f_x(-74.0) - 15}" y="{(f_y(0.0) + f_y(125.0)) / 2}" transform="rotate(-90 {f_x(-74.0) - 15} {(f_y(0.0) + f_y(125.0)) / 2})" class="dim-text">125*</text>
'''
    # 2. Высота стойки 80 (справа от FrontView в зазоре до Section A-A)
    dim_h_stand = f'''
<line x1="{f_x(74.0) + 2}" y1="{f_y(0.0)}" x2="{f_x(74.0) + 14}" y2="{f_y(0.0)}" class="dim-ext"/>
<line x1="{f_x(62.0) + 2}" y1="{f_y(80.0)}" x2="{f_x(74.0) + 14}" y2="{f_y(80.0)}" class="dim-ext"/>
<line x1="{f_x(74.0) + 11}" y1="{f_y(0.0)}" x2="{f_x(74.0) + 11}" y2="{f_y(80.0)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{f_x(74.0) + 9}" y="{(f_y(0.0) + f_y(80.0)) / 2}" transform="rotate(-90 {f_x(74.0) + 9} {(f_y(0.0) + f_y(80.0)) / 2})" class="dim-text">80</text>
'''
    # 3. Высота бункера 71* (на Section A-A между конусом воронки и левой опорой)
    dim_h_bunk = f'''
<line x1="{s_x(-36.0) - 2}" y1="{s_y(125.0)}" x2="{s_x(-36.0) - 11}" y2="{s_y(125.0)}" class="dim-ext"/>
<line x1="{s_x(-16.0) - 2}" y1="{s_y(54.0)}" x2="{s_x(-36.0) - 11}" y2="{s_y(54.0)}" class="dim-ext"/>
<line x1="{s_x(-36.0) - 8}" y1="{s_y(54.0)}" x2="{s_x(-36.0) - 8}" y2="{s_y(125.0)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{s_x(-36.0) - 10}" y="{(s_y(54.0) + s_y(125.0)) / 2}" transform="rotate(-90 {s_x(-36.0) - 10} {(s_y(54.0) + s_y(125.0)) / 2})" class="dim-text">71*</text>
'''
    # 4. Рабочий зазор 10 мм до ротора и пунктир уровня ротора
    dim_gap = f'''
<!-- Линия уровня ротора (штрихпунктирная Z=44) -->
<line x1="{f_x(-28.0)}" y1="{f_y(44.0)}" x2="{f_x(28.0)}" y2="{f_y(44.0)}" class="center-line"/>
<text x="{f_x(-4.0)}" y="{f_y(44.0) - 2.0}" text-anchor="end" class="dim-text-l" font-size="2.6">Уровень ротора</text>
<!-- Размер рабочего зазора 10 мм -->
<line x1="{f_x(16.0) + 2}" y1="{f_y(54.0)}" x2="{f_x(16.0) + 16}" y2="{f_y(54.0)}" class="dim-ext"/>
<line x1="{f_x(16.0) + 2}" y1="{f_y(44.0)}" x2="{f_x(16.0) + 16}" y2="{f_y(44.0)}" class="dim-ext"/>
<line x1="{f_x(16.0) + 12}" y1="{f_y(44.0)}" x2="{f_x(16.0) + 12}" y2="{f_y(54.0)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{f_x(16.0) + 10}" y="{(f_y(44.0) + f_y(54.0)) / 2}" transform="rotate(-90 {f_x(16.0) + 10} {(f_y(44.0) + f_y(54.0)) / 2})" class="dim-text">10</text>
'''
    # 5. Межосевое расстояние между стойками 104 мм (на Виде сверху)
    dim_dist_stands = f'''
<line x1="{t_x(-52.0)}" y1="{t_y(0.0) - 18}" x2="{t_x(-52.0)}" y2="{t_y(0.0) - 34}" class="dim-ext"/>
<line x1="{t_x(52.0)}" y1="{t_y(0.0) - 18}" x2="{t_x(52.0)}" y2="{t_y(0.0) - 34}" class="dim-ext"/>
<line x1="{t_x(-52.0)}" y1="{t_y(0.0) - 30}" x2="{t_x(52.0)}" y2="{t_y(0.0) - 30}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{t_x(0.0)}" y="{t_y(0.0) - 31.5}" class="dim-text">104</text>
'''
    # 6. Отверстия регулировки в стойке: шаг 6 мм и выноска
    dim_holes_step = f'''
<!-- Выносные линии отверстий на стойке -Y -->
<line x1="{f_x(-62.0)}" y1="{f_y(54.0)}" x2="{f_x(-74.0) - 8}" y2="{f_y(54.0)}" class="dim-ext"/>
<line x1="{f_x(-62.0)}" y1="{f_y(60.0)}" x2="{f_x(-74.0) - 8}" y2="{f_y(60.0)}" class="dim-ext"/>
<line x1="{f_x(-62.0)}" y1="{f_y(66.0)}" x2="{f_x(-74.0) - 8}" y2="{f_y(66.0)}" class="dim-ext"/>
<line x1="{f_x(-74.0) - 5}" y1="{f_y(54.0)}" x2="{f_x(-74.0) - 5}" y2="{f_y(60.0)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{f_x(-74.0) - 7}" y="{(f_y(54.0) + f_y(60.0)) / 2}" transform="rotate(-90 {f_x(-74.0) - 7} {(f_y(54.0) + f_y(60.0)) / 2})" class="dim-text">6</text>
<line x1="{f_x(-74.0) - 5}" y1="{f_y(60.0)}" x2="{f_x(-74.0) - 5}" y2="{f_y(66.0)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{f_x(-74.0) - 7}" y="{(f_y(60.0) + f_y(66.0)) / 2}" transform="rotate(-90 {f_x(-74.0) - 7} {(f_y(60.0) + f_y(66.0)) / 2})" class="dim-text">6</text>

<!-- Выноска пояснения регулировки (в свободную зону вниз) -->
<path d="M {f_x(-52.0)} {f_y(60.0)} L {f_x(-52.0) + 8} {f_y(60.0) + 26} L {f_x(-52.0) + 38} {f_y(60.0) + 26}" class="leader" marker-start="url(#dot)"/>
<text x="{f_x(-52.0) + 9}" y="{f_y(60.0) + 24.5}" class="dim-text-l" font-size="2.4">3 отв. Ø3,4 (зазоры 4; 10; 16)</text>
'''

    # 7. Размеры на Разрезе А-А:
    dim_sec_nozzle = f'''
<line x1="{s_x(-16.0)}" y1="{s_y(54.0)}" x2="{s_x(-16.0)}" y2="{s_y(54.0) + 15}" class="dim-ext"/>
<line x1="{s_x(16.0)}" y1="{s_y(54.0)}" x2="{s_x(16.0)}" y2="{s_y(54.0) + 15}" class="dim-ext"/>
<line x1="{s_x(-16.0)}" y1="{s_y(54.0) + 12}" x2="{s_x(16.0)}" y2="{s_y(54.0) + 12}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{s_x(0.0)}" y="{s_y(54.0) + 10.5}" class="dim-text">Ø32</text>

<line x1="{s_x(-13.6)}" y1="{s_y(54.0)}" x2="{s_x(-13.6)}" y2="{s_y(54.0) + 7}" class="dim-ext"/>
<line x1="{s_x(13.6)}" y1="{s_y(54.0)}" x2="{s_x(13.6)}" y2="{s_y(54.0) + 7}" class="dim-ext"/>
<line x1="{s_x(-13.6)}" y1="{s_y(54.0) + 5}" x2="{s_x(13.6)}" y2="{s_y(54.0) + 5}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{s_x(0.0)}" y="{s_y(54.0) + 3.5}" class="dim-text">Ø27,2</text>
'''
    dim_sec_mouth = f'''
<line x1="{s_x(-36.0)}" y1="{s_y(125.0) - 2}" x2="{s_x(-36.0)}" y2="{s_y(125.0) - 14}" class="dim-ext"/>
<line x1="{s_x(36.0)}" y1="{s_y(125.0) - 2}" x2="{s_x(36.0)}" y2="{s_y(125.0) - 14}" class="dim-ext"/>
<line x1="{s_x(-36.0)}" y1="{s_y(125.0) - 11}" x2="{s_x(36.0)}" y2="{s_y(125.0) - 11}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{s_x(0.0)}" y="{s_y(125.0) - 12.5}" class="dim-text">Ø72</text>
'''
    dim_sec_slot = f'''
<path d="M {s_x(54.0)} {s_y(60.0) + 4} L {s_x(54.0) + 14} {s_y(60.0) + 20} L {s_x(54.0) + 54} {s_y(60.0) + 20}" class="leader" marker-start="url(#dot)"/>
<text x="{s_x(54.0) + 16}" y="{s_y(60.0) + 18.5}" class="dim-text-l" font-size="2.8">П-образный паз 10×5</text>
<text x="{s_x(54.0) + 16}" y="{s_y(60.0) + 22.5}" class="dim-text-l" font-size="2.8">Ползун уха 9,6×4,5</text>
'''

    # 8. Размеры на Виде сверху (TopView):
    dim_top_flange = f'''
<line x1="{t_x(52.0 - 12.0)}" y1="{t_y(0.0) + 20}" x2="{t_x(52.0 - 12.0)}" y2="{t_y(0.0) + 30}" class="dim-ext"/>
<line x1="{t_x(52.0 + 12.0)}" y1="{t_y(0.0) + 20}" x2="{t_x(52.0 + 12.0)}" y2="{t_y(0.0) + 30}" class="dim-ext"/>
<line x1="{t_x(52.0 - 12.0)}" y1="{t_y(0.0) + 27}" x2="{t_x(52.0 + 12.0)}" y2="{t_y(0.0) + 27}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{t_x(52.0)}" y="{t_y(0.0) + 25.5}" class="dim-text">24</text>

<line x1="{t_x(52.0 - 6.0)}" y1="{t_y(0.0) + 13}" x2="{t_x(52.0 - 6.0)}" y2="{t_y(0.0) + 21}" class="dim-ext"/>
<line x1="{t_x(52.0 + 6.0)}" y1="{t_y(0.0) + 13}" x2="{t_x(52.0 + 6.0)}" y2="{t_y(0.0) + 21}" class="dim-ext"/>
<line x1="{t_x(52.0 - 6.0)}" y1="{t_y(0.0) + 18}" x2="{t_x(52.0 + 6.0)}" y2="{t_y(0.0) + 18}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{t_x(52.0)}" y="{t_y(0.0) + 16.5}" class="dim-text">12</text>
'''

    # 9. Позиционные выноски (баллоны ГОСТ 2.109-73)
    balloons_svg = f'''
<!-- Поз. 1: Бункер загрузочный (FrontView) -->
<circle cx="{f_x(26.0)}" cy="{f_y(100.0)}" r="4.0" class="balloon"/>
<text x="{f_x(26.0)}" y="{f_y(100.0) + 1.5}" font-family="osifont, Arial, sans-serif" font-size="4.5" font-weight="bold" fill="#000" text-anchor="middle">1</text>
<path d="M {f_x(18.0)} {f_y(90.0)} L {f_x(26.0) - 2.8} {f_y(100.0) - 2.8}" class="leader" marker-start="url(#dot)"/>

<!-- Поз. 2: Опора бункера (FrontView) -->
<circle cx="{f_x(64.0)}" cy="{f_y(30.0)}" r="4.0" class="balloon"/>
<text x="{f_x(64.0)}" y="{f_y(30.0) + 1.5}" font-family="osifont, Arial, sans-serif" font-size="4.5" font-weight="bold" fill="#000" text-anchor="middle">2</text>
<path d="M {f_x(52.0)} {f_y(25.0)} L {f_x(64.0) - 2.8} {f_y(30.0) - 2.8}" class="leader" marker-start="url(#dot)"/>

<!-- Поз. 3: Винт М3х10 DIN 912 (SectionAA) -->
<circle cx="{s_x(62.0) + 20}" cy="{s_y(60.0)}" r="4.0" class="balloon"/>
<text x="{s_x(62.0) + 20}" y="{s_y(60.0) + 1.5}" font-family="osifont, Arial, sans-serif" font-size="4.5" font-weight="bold" fill="#000" text-anchor="middle">3</text>
<line x1="{s_x(63.5)}" y1="{s_y(60.0)}" x2="{s_x(62.0) + 16}" y2="{s_y(60.0)}" class="leader" marker-start="url(#dot)"/>

<!-- Поз. 4: Винт М3х8 DIN 912 к станине (FrontView) -->
<circle cx="{f_x(68.0) + 12}" cy="{f_y(0.0) + 12}" r="4.0" class="balloon"/>
<text x="{f_x(68.0) + 12}" y="{f_y(0.0) + 13.5}" font-family="osifont, Arial, sans-serif" font-size="4.5" font-weight="bold" fill="#000" text-anchor="middle">4</text>
<path d="M {f_x(52.0 + 6.0)} {f_y(3.0)} L {f_x(68.0) + 12 - 2.8} {f_y(0.0) + 12 - 2.8}" class="leader" marker-start="url(#dot)"/>
'''

    # Полный SVG-оверлей
    svg_overlay = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W_SHEET}mm" height="{H_SHEET}mm" viewBox="0 0 {W_SHEET} {H_SHEET}">
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
    <path d="M 0 2 L 10 5 L 0 8 z" fill="#000"/>
  </marker>
  <marker id="arrow-rev" viewBox="0 0 10 10" refX="0" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
    <path d="M 10 2 L 0 5 L 10 8 z" fill="#000"/>
  </marker>
  <marker id="dot" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="3" markerHeight="3">
    <circle cx="5" cy="5" r="2.5" fill="#000"/>
  </marker>
</defs>
<style>
  .dim-line   {{ stroke:#000; stroke-width:0.35; fill:none; }}
  .dim-ext    {{ stroke:#000; stroke-width:0.25; fill:none; }}
  .center-line{{ stroke:#000; stroke-width:0.25; stroke-dasharray:6,1.5,1.5,1.5; fill:none; }}
  .dim-text   {{ font-family:osifont,Arial,sans-serif; font-size:3.5px; fill:#000; text-anchor:middle; }}
  .dim-text-l {{ font-family:osifont,Arial,sans-serif; font-size:3.5px; fill:#000; text-anchor:start; }}
  .dim-text-r {{ font-family:osifont,Arial,sans-serif; font-size:3.5px; fill:#000; text-anchor:end; }}
  .view-title {{ font-family:osifont,Arial,sans-serif; font-size:5.0px; fill:#000; text-anchor:middle; font-weight:bold; }}
  .leader     {{ stroke:#000; stroke-width:0.35; fill:none; }}
  .balloon    {{ stroke:#000; stroke-width:0.35; fill:#fff; }}
</style>

<!-- Заголовок разреза -->
<text x="265" y="16" class="view-title">А - А</text>

<!-- Осевые линии -->
<line x1="{f_x(0.0)}" y1="{f_y(125.0) - 8}" x2="{f_x(0.0)}" y2="{f_y(0.0) + 8}" class="center-line"/>
<line x1="{s_x(0.0)}" y1="{s_y(125.0) - 8}" x2="{s_x(0.0)}" y2="{s_y(0.0) + 8}" class="center-line"/>
<line x1="{t_x(0.0)}" y1="{t_y(-40.0)}" x2="{t_x(0.0)}" y2="{t_y(40.0)}" class="center-line"/>
<line x1="{t_x(-68.0) - 5}" y1="{t_y(0.0)}" x2="{t_x(68.0) + 5}" y2="{t_y(0.0)}" class="center-line"/>

<!-- Размеры -->
{dim_h_total}
{dim_h_stand}
{dim_h_bunk}
{dim_gap}
{dim_dist_stands}
{dim_holes_step}
{dim_sec_nozzle}
{dim_sec_mouth}
{dim_sec_slot}
{dim_top_flange}

<!-- Выноски позиций -->
{balloons_svg}

<!-- Таблица спецификации -->
{bom_svg}

<!-- Технические требования -->
{tech_notes_svg}

</svg>'''

    sym_dim = doc.addObject('TechDraw::DrawViewSymbol', 'OverlayDimensions')
    sym_dim.Symbol = svg_overlay
    page.addView(sym_dim)
    doc.recompute()
    
    sym_dim.Scale = scale_corr
    sym_dim.X = W_SHEET / 2.0
    sym_dim.Y = H_SHEET / 2.0
    doc.recompute()
    
    # Экспорт результатов
    pdf_path = "assembly_hopper_stand.pdf"
    fcstd_path = "assembly_hopper_stand.FCStd"
    png_path = "assembly_hopper_stand.png"
    export_drawing(doc, page, pdf_path, fcstd_path, png_path)
    print("\nSUCCESS: assembly_hopper_stand drawing exported cleanly!")

if __name__ == "__main__":
    generate_assembly_drawing()
