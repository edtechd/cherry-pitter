#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_hopper_stand.py
Поз. 10: Опора бункера (Hopper Vertical Support / Stand)

Назначение:
- Вертикальная опора с П-образным профилем для направляющего уха бункера.
- П-образный паз исключает поворот и горизонтальное смещение бункера (строго вертикальное движение).
- 3 калиброванных отверстия М3 обеспечивают регулировку рабочего зазора до ротора (4 мм, 10 мм, 16 мм).
- Опорный фланец в основании обеспечивает жесткое крепление к станине двумя винтами М3.
- Конструкция оптимизирована для 3D-печати (печать плашмя на задней грани или вертикально на фланце).
"""

import sys
import os
import math
from freecad_utils import (
    FreeCAD, Part, make_box, make_cylinder,
    create_drawing_page, fill_gost_title_block, export_drawing
)

# Геометрические параметры опоры (в локальной системе координат)
# Ось Z — вертикаль (высота стойки 0..80 мм)
# Ось X — ширина стойки (-8..+8 мм)
# Ось Y — глубина стойки (0..10 мм), П-образный паз открыт в сторону -Y (к бункеру)

STAND_H = 80.0              # Высота стойки
STAND_W = 16.0              # Ширина стойки вдоль X
STAND_D = 10.0              # Толщина стойки вдоль Y

SLOT_W = 10.0               # Ширина П-образного паза вдоль X (зазор 0.2 мм на сторону к уху 9.6 мм)
SLOT_D = 5.0                # Глубина П-образного паза вдоль Y
SLOT_Z_START = 5.0          # Нижняя граница паза (выше фланца)

# Высоты крепежных отверстий М3 от опорной плоскости стойки (Z=0)
# Соответствуют зазорам до ротора 4 мм, 10 мм, 16 мм:
GAPS_MM = [4.0, 10.0, 16.0]
HOLE_HEIGHTS = [54.0, 60.0, 66.0]   # Шаг 6.0 мм
HOLE_R = 1.7                        # Радиус отверстия М3 (Ø3.4 мм)

# Опорный фланец крепления к станине
FLANGE_W = 24.0             # Ширина фланца вдоль X (-12..+12)
FLANGE_D = 16.0             # Длина фланца вдоль Y (0..16)
FLANGE_H = 5.0              # Толщина фланца вдоль Z (0..5)
FLANGE_HOLE_X = 6.0         # Межосевое расстояние отверстий по X (±6.0 мм)
FLANGE_HOLE_Y = 11.0        # Положение крепежных отверстий по Y
FLANGE_HOLE_R = 1.7         # Отверстия под винты М3 (Ø3.4 мм)

def create_hopper_stand():
    """
    Создает твердотельную B-Rep модель опоры бункера с П-образным профилем.
    """
    # 1. Основное тело вертикальной колонны
    col = make_box(STAND_W, STAND_D, STAND_H, (-STAND_W / 2.0, 0.0, 0.0))
    
    # 2. П-образный направляющий паз (вырез с передней грани Y=0)
    slot_tool = make_box(SLOT_W, SLOT_D + 0.5, STAND_H - SLOT_Z_START + 2.0,
                         (-SLOT_W / 2.0, -0.2, SLOT_Z_START))
    col = col.cut(slot_tool)
    
    # 3. 3 отверстия М3 под фиксирующий винт бункера (через заднюю стенку Y=5..10 в паз)
    for zh in HOLE_HEIGHTS:
        h_tool = make_cylinder(HOLE_R, STAND_D + 4.0, (0.0, -2.0, zh), (0.0, 1.0, 0.0))
        col = col.cut(h_tool)
        
    # 4. Опорный монтажный фланец в основании
    flange = make_box(FLANGE_W, FLANGE_D, FLANGE_H, (-FLANGE_W / 2.0, 0.0, 0.0))
    # Крепежные отверстия к станине
    fh1 = make_cylinder(FLANGE_HOLE_R, FLANGE_H + 2.0, (-FLANGE_HOLE_X, FLANGE_HOLE_Y, -1.0))
    fh2 = make_cylinder(FLANGE_HOLE_R, FLANGE_H + 2.0, (FLANGE_HOLE_X, FLANGE_HOLE_Y, -1.0))
    flange = flange.cut(fh1).cut(fh2)
    
    # 5. Объединение фланца и стойки
    stand = flange.fuse(col)
    
    # Повторный чистый прорез паза для устранения возможных пересечений с телом фланца
    stand = stand.cut(slot_tool)
    
    assert stand.isValid(), "Hopper Stand shape is topologically invalid!"
    return stand

create_part = create_hopper_stand

def generate_stand_drawing():
    """
    Генерирует рабочий чертёж опоры бункера по ГОСТ (ЕСКД) с полным комплектом размеров.
    Масштаб 2:1, формат А3 Альбомная.
    """
    doc = FreeCAD.newDocument("Doc_part_hopper_stand")
    shape = create_hopper_stand()
    feat = doc.addObject("Part::Feature", "HopperStand")
    feat.Shape = shape
    doc.recompute()
    
    page, template = create_drawing_page(doc, "A3_Landscape", "Page_Stand")
    W_SHEET, H_SHEET = 420.0, 297.0
    SCALE = 2.0
    
    X_FRONT = 100.0
    Y_FRONT = 175.0
    
    X_SIDE = 200.0
    Y_SIDE = 175.0
    
    X_TOP = 100.0
    Y_TOP = 50.0
    
    X_ISO = 320.0
    Y_ISO = 200.0
    
    # 1. Главный вид (вид в П-образный паз)
    v_front = doc.addObject('TechDraw::DrawViewPart', 'FrontView')
    v_front.Source = [feat]
    v_front.Direction = FreeCAD.Vector(0.0, -1.0, 0.0)
    v_front.XDirection = FreeCAD.Vector(1.0, 0.0, 0.0)
    page.addView(v_front)
    doc.recompute()
    v_front.Scale = SCALE
    v_front.X = X_FRONT
    v_front.Y = Y_FRONT
    v_front.IsoCount = 0
    doc.recompute()
    
    # 2. Вид сбоку (профиль стойки)
    v_side = doc.addObject('TechDraw::DrawViewPart', 'SideView')
    v_side.Source = [feat]
    v_side.Direction = FreeCAD.Vector(1.0, 0.0, 0.0)
    v_side.XDirection = FreeCAD.Vector(0.0, 1.0, 0.0)
    page.addView(v_side)
    doc.recompute()
    v_side.Scale = SCALE
    v_side.X = X_SIDE
    v_side.Y = Y_SIDE
    v_side.IsoCount = 0
    doc.recompute()
    
    # 3. Вид сверху
    v_top = doc.addObject('TechDraw::DrawViewPart', 'TopView')
    v_top.Source = [feat]
    v_top.Direction = FreeCAD.Vector(0.0, 0.0, -1.0)
    v_top.XDirection = FreeCAD.Vector(1.0, 0.0, 0.0)
    page.addView(v_top)
    doc.recompute()
    v_top.Scale = SCALE
    v_top.X = X_TOP
    v_top.Y = Y_TOP
    v_top.IsoCount = 0
    doc.recompute()
    
    # 4. Изометрия
    v_iso = doc.addObject('TechDraw::DrawViewPart', 'IsoView')
    v_iso.Source = [feat]
    v_iso.Direction = FreeCAD.Vector(1.0, -1.2, 0.9)
    page.addView(v_iso)
    doc.recompute()
    v_iso.Scale = 1.0
    v_iso.X = X_ISO
    v_iso.Y = Y_ISO
    v_iso.IsoCount = 0
    doc.recompute()
    
    # Основная надпись по ГОСТ 2.104-2006
    title_fields = {
        'Номер':         'ВЧ.01.00.010',
        'Название':      'Опора бункера',
        'Масштаб':       '2:1',
        'Лист':          '1',
        'Листов':        '1',
        'Материал':      'PETG',
        'Организация1':  'Проект VISHNI',
        'Разработал':    'Демишкевич Э.Б.',
        'Проверил':      'Контролер',
    }
    fill_gost_title_block(template, title_fields)
    doc.recompute()
    
    def f_x(x): return X_FRONT + x * SCALE
    def f_y(z): return (297.0 - Y_FRONT) - (z - 40.0) * SCALE
    def s_x(y): return X_SIDE + (y - 8.0) * SCALE
    def s_y(z): return (297.0 - Y_SIDE) - (z - 40.0) * SCALE
    def t_x(x): return X_TOP + x * SCALE
    def t_y(y): return (297.0 - Y_TOP) - (y - 8.0) * SCALE
    
    qt_px = round(W_SHEET * 90.0 / 25.4)
    scale_corr = W_SHEET / (qt_px * 25.4 / 96.0)
    
    # Размеры на Главном виде
    dim_h80 = f'''
<line x1="{f_x(-12.0) - 4}" y1="{f_y(0.0)}" x2="{f_x(-12.0) - 22}" y2="{f_y(0.0)}" class="dim-ext"/>
<line x1="{f_x(-8.0) - 4}" y1="{f_y(80.0)}" x2="{f_x(-12.0) - 22}" y2="{f_y(80.0)}" class="dim-ext"/>
<line x1="{f_x(-12.0) - 18}" y1="{f_y(0.0)}" x2="{f_x(-12.0) - 18}" y2="{f_y(80.0)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{f_x(-12.0) - 20}" y="{(f_y(0.0) + f_y(80.0)) / 2}" transform="rotate(-90 {f_x(-12.0) - 20} {(f_y(0.0) + f_y(80.0)) / 2})" class="dim-text">80</text>
'''
    dim_holes_h = f'''
<line x1="{f_x(-8.0)}" y1="{f_y(54.0)}" x2="{f_x(-12.0) - 14}" y2="{f_y(54.0)}" class="dim-ext"/>
<line x1="{f_x(-8.0)}" y1="{f_y(60.0)}" x2="{f_x(-12.0) - 14}" y2="{f_y(60.0)}" class="dim-ext"/>
<line x1="{f_x(-8.0)}" y1="{f_y(66.0)}" x2="{f_x(-12.0) - 14}" y2="{f_y(66.0)}" class="dim-ext"/>
<line x1="{f_x(-12.0) - 10}" y1="{f_y(54.0)}" x2="{f_x(-12.0) - 10}" y2="{f_y(60.0)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{f_x(-12.0) - 12}" y="{(f_y(54.0) + f_y(60.0)) / 2}" transform="rotate(-90 {f_x(-12.0) - 12} {(f_y(54.0) + f_y(60.0)) / 2})" class="dim-text">6</text>
<line x1="{f_x(-12.0) - 10}" y1="{f_y(60.0)}" x2="{f_x(-12.0) - 10}" y2="{f_y(66.0)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{f_x(-12.0) - 12}" y="{(f_y(60.0) + f_y(66.0)) / 2}" transform="rotate(-90 {f_x(-12.0) - 12} {(f_y(60.0) + f_y(66.0)) / 2})" class="dim-text">6</text>

<line x1="{f_x(-12.0) - 10}" y1="{f_y(0.0)}" x2="{f_x(-12.0) - 10}" y2="{f_y(54.0)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{f_x(-12.0) - 12}" y="{(f_y(0.0) + f_y(54.0)) / 2}" transform="rotate(-90 {f_x(-12.0) - 12} {(f_y(0.0) + f_y(54.0)) / 2})" class="dim-text">54</text>

<!-- Выноска отверстий регулировки -->
<path d="M {f_x(0.0)} {f_y(60.0)} L {f_x(0.0) + 18} {f_y(60.0) - 15} L {f_x(0.0) + 68} {f_y(60.0) - 15}" class="leader" marker-start="url(#dot)"/>
<text x="{f_x(0.0) + 20}" y="{f_y(60.0) - 16.5}" class="dim-text-l" font-size="3.2">3 отв. Ø3,4 (зазоры 4; 10; 16)</text>
'''
    dim_widths = f'''
<line x1="{f_x(-5.0)}" y1="{f_y(80.0) - 2}" x2="{f_x(-5.0)}" y2="{f_y(80.0) - 14}" class="dim-ext"/>
<line x1="{f_x(5.0)}" y1="{f_y(80.0) - 2}" x2="{f_x(5.0)}" y2="{f_y(80.0) - 14}" class="dim-ext"/>
<line x1="{f_x(-5.0)}" y1="{f_y(80.0) - 10}" x2="{f_x(5.0)}" y2="{f_y(80.0) - 10}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{f_x(0.0)}" y="{f_y(80.0) - 11.5}" class="dim-text">10<tspan font-size="2.4" dy="-1.5">+0,1</tspan></text>

<line x1="{f_x(-8.0)}" y1="{f_y(80.0) - 2}" x2="{f_x(-8.0)}" y2="{f_y(80.0) - 24}" class="dim-ext"/>
<line x1="{f_x(8.0)}" y1="{f_y(80.0) - 2}" x2="{f_x(8.0)}" y2="{f_y(80.0) - 24}" class="dim-ext"/>
<line x1="{f_x(-8.0)}" y1="{f_y(80.0) - 20}" x2="{f_x(8.0)}" y2="{f_y(80.0) - 20}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{f_x(0.0)}" y="{f_y(80.0) - 21.5}" class="dim-text">16</text>
'''
    dim_flange_h = f'''
<line x1="{f_x(12.0) + 2}" y1="{f_y(0.0)}" x2="{f_x(12.0) + 12}" y2="{f_y(0.0)}" class="dim-ext"/>
<line x1="{f_x(12.0) + 2}" y1="{f_y(5.0)}" x2="{f_x(12.0) + 12}" y2="{f_y(5.0)}" class="dim-ext"/>
<line x1="{f_x(12.0) + 9}" y1="{f_y(0.0)}" x2="{f_x(12.0) + 9}" y2="{f_y(5.0)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{f_x(12.0) + 11}" y="{(f_y(0.0) + f_y(5.0)) / 2 + 1.2}" class="dim-text-l">5</text>
'''

    # Размеры на Виде сбоку
    dim_side_depths = f'''
<line x1="{s_x(0.0)}" y1="{s_y(80.0) - 2}" x2="{s_x(0.0)}" y2="{s_y(80.0) - 14}" class="dim-ext"/>
<line x1="{s_x(5.0)}" y1="{s_y(80.0) - 2}" x2="{s_x(5.0)}" y2="{s_y(80.0) - 14}" class="dim-ext"/>
<line x1="{s_x(0.0)}" y1="{s_y(80.0) - 10}" x2="{s_x(5.0)}" y2="{s_y(80.0) - 10}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{s_x(2.5)}" y="{s_y(80.0) - 11.5}" class="dim-text">5</text>

<line x1="{s_x(10.0)}" y1="{s_y(80.0) - 2}" x2="{s_x(10.0)}" y2="{s_y(80.0) - 14}" class="dim-ext"/>
<line x1="{s_x(5.0)}" y1="{s_y(80.0) - 10}" x2="{s_x(10.0)}" y2="{s_y(80.0) - 10}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{s_x(7.5)}" y="{s_y(80.0) - 11.5}" class="dim-text">5</text>

<line x1="{s_x(0.0)}" y1="{s_y(0.0) + 2}" x2="{s_x(0.0)}" y2="{s_y(0.0) + 14}" class="dim-ext"/>
<line x1="{s_x(16.0)}" y1="{s_y(0.0) + 2}" x2="{s_x(16.0)}" y2="{s_y(0.0) + 14}" class="dim-ext"/>
<line x1="{s_x(0.0)}" y1="{s_y(0.0) + 10}" x2="{s_x(16.0)}" y2="{s_y(0.0) + 10}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{s_x(8.0)}" y="{s_y(0.0) + 8.5}" class="dim-text">16</text>

<line x1="{s_x(11.0)}" y1="{s_y(0.0) + 2}" x2="{s_x(11.0)}" y2="{s_y(0.0) + 22}" class="dim-ext"/>
<line x1="{s_x(0.0)}" y1="{s_y(0.0) + 18}" x2="{s_x(11.0)}" y2="{s_y(0.0) + 18}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{s_x(5.5)}" y="{s_y(0.0) + 16.5}" class="dim-text">11</text>
'''

    # Размеры на Виде сверху
    dim_top = f'''
<line x1="{t_x(-12.0)}" y1="{t_y(16.0) + 2}" x2="{t_x(-12.0)}" y2="{t_y(16.0) + 18}" class="dim-ext"/>
<line x1="{t_x(12.0)}" y1="{t_y(16.0) + 2}" x2="{t_x(12.0)}" y2="{t_y(16.0) + 18}" class="dim-ext"/>
<line x1="{t_x(-12.0)}" y1="{t_y(16.0) + 14}" x2="{t_x(12.0)}" y2="{t_y(16.0) + 14}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{t_x(0.0)}" y="{t_y(16.0) + 12.5}" class="dim-text">24</text>

<line x1="{t_x(-6.0)}" y1="{t_y(11.0)}" x2="{t_x(-6.0)}" y2="{t_y(16.0) + 10}" class="dim-ext"/>
<line x1="{t_x(6.0)}" y1="{t_y(11.0)}" x2="{t_x(6.0)}" y2="{t_y(16.0) + 10}" class="dim-ext"/>
<line x1="{t_x(-6.0)}" y1="{t_y(16.0) + 7}" x2="{t_x(6.0)}" y2="{t_y(16.0) + 7}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{t_x(0.0)}" y="{t_y(16.0) + 5.5}" class="dim-text">12</text>

<path d="M {t_x(6.0)} {t_y(11.0)} L {t_x(6.0) + 18} {t_y(11.0) - 10} L {t_x(6.0) + 54} {t_y(11.0) - 10}" class="leader" marker-start="url(#dot)"/>
<text x="{t_x(6.0) + 20}" y="{t_y(11.0) - 11.5}" class="dim-text-l" font-size="3.2">2 отв. Ø3,4</text>
'''

    # Технические требования
    tech_notes = f'''
<text x="230" y="150" font-family="osifont, Arial, sans-serif" font-size="3.8" font-weight="bold" fill="#000">Технические требования:</text>
<text x="230" y="158" font-family="osifont, Arial, sans-serif" font-size="3.2" fill="#000">1. * Размеры для справок.</text>
<text x="230" y="165" font-family="osifont, Arial, sans-serif" font-size="3.2" fill="#000">2. Материал: PETG. Заполнение не менее 40%.</text>
<text x="230" y="172" font-family="osifont, Arial, sans-serif" font-size="3.2" fill="#000">3. П-образный паз шириной 10 мм обеспечивает вертикальное направление уха бункера.</text>
<text x="230" y="179" font-family="osifont, Arial, sans-serif" font-size="3.2" fill="#000">4. Отверстия М3 на высотах 54, 60, 66 мм соответствуют зазорам до ротора 4, 10, 16 мм.</text>
<text x="230" y="186" font-family="osifont, Arial, sans-serif" font-size="3.2" fill="#000">5. Крепление стойки к станине: 2 винта М3 через отверстия во фланце.</text>
'''

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
  .view-title {{ font-family:osifont,Arial,sans-serif; font-size:5.0px; fill:#000; text-anchor:middle; font-weight:bold; }}
  .leader     {{ stroke:#000; stroke-width:0.35; fill:none; }}
</style>

<!-- Осевые линии -->
<line x1="{f_x(0.0)}" y1="{f_y(80.0) - 8}" x2="{f_x(0.0)}" y2="{f_y(0.0) + 6}" class="center-line"/>
<line x1="{f_x(-4.0)}" y1="{f_y(54.0)}" x2="{f_x(4.0)}" y2="{f_y(54.0)}" class="center-line"/>
<line x1="{f_x(-4.0)}" y1="{f_y(60.0)}" x2="{f_x(4.0)}" y2="{f_y(60.0)}" class="center-line"/>
<line x1="{f_x(-4.0)}" y1="{f_y(66.0)}" x2="{f_x(4.0)}" y2="{f_y(66.0)}" class="center-line"/>

<line x1="{s_x(4.0)}" y1="{s_y(54.0)}" x2="{s_x(11.0)}" y2="{s_y(54.0)}" class="center-line"/>
<line x1="{s_x(4.0)}" y1="{s_y(60.0)}" x2="{s_x(11.0)}" y2="{s_y(60.0)}" class="center-line"/>
<line x1="{s_x(4.0)}" y1="{s_y(66.0)}" x2="{s_x(11.0)}" y2="{s_y(66.0)}" class="center-line"/>

<line x1="{t_x(0.0)}" y1="{t_y(0.0) - 6}" x2="{t_x(0.0)}" y2="{t_y(16.0) + 6}" class="center-line"/>
<line x1="{t_x(-12.0) - 6}" y1="{t_y(11.0)}" x2="{t_x(12.0) + 6}" y2="{t_y(11.0)}" class="center-line"/>
<line x1="{t_x(-6.0)}" y1="{t_y(11.0) - 6}" x2="{t_x(-6.0)}" y2="{t_y(11.0) + 6}" class="center-line"/>
<line x1="{t_x(6.0)}" y1="{t_y(11.0) - 6}" x2="{t_x(6.0)}" y2="{t_y(11.0) + 6}" class="center-line"/>

<!-- Размеры -->
{dim_h80}
{dim_holes_h}
{dim_widths}
{dim_flange_h}
{dim_side_depths}
{dim_top}
{tech_notes}
</svg>'''

    sym_dim = doc.addObject('TechDraw::DrawViewSymbol', 'OverlayDimensions')
    sym_dim.Symbol = svg_overlay
    page.addView(sym_dim)
    doc.recompute()
    sym_dim.Scale = scale_corr
    sym_dim.X = W_SHEET / 2.0
    sym_dim.Y = H_SHEET / 2.0
    doc.recompute()
    
    export_drawing(doc, page, "part_hopper_stand.pdf", "part_hopper_stand.FCStd", "part_hopper_stand.png")
    print("SUCCESS: part_hopper_stand drawing exported cleanly!")

if __name__ == "__main__":
    generate_stand_drawing()
