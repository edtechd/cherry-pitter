#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_hopper.py
Поз. 9: Бункер загрузочный (Feeding Hopper)

Конструкция адаптирована для 3D-печати:
- Печать осуществляется в перевернутом положении (базирование по верхней широкой горловине Z=109).
- Направляющие уши снабжены самонесущими наклонными ребрами (45°), что исключает необходимость поддержек.
- Направляющие уши имеют калиброванный размер 9.6 мм для скольжения в П-образном пазе стоек (10.0 мм).
- Фиксация к опорам осуществляется одним винтом М3 с каждой стороны на высоте Z=44.0.
"""

import sys
import os
import math
from freecad_utils import (
    FreeCAD, Part, make_box, make_cylinder, make_cone,
    create_drawing_page, fill_gost_title_block, export_drawing
)

# Основные геометрические параметры
NOZZLE_R_IN = 13.6          # Внутренний радиус сопла (проход для ягод Ø27.2)
NOZZLE_R_OUT = 16.0         # Наружный радиус сопла (Ø32.0, толщина стенки 2.4 мм)
NOZZLE_Z_BOT = 38.0         # Нижний торец сопла
NOZZLE_Z_TOP = 54.0         # Верхний торец сопла / переход в воронку

FUNNEL_R_TOP_OUT = 36.0     # Верхний наружный радиус горловины (Ø72.0)
FUNNEL_R_TOP_IN = 33.6      # Верхний внутренний радиус горловины (Ø67.2)
FUNNEL_Z_TOP = 109.0        # Верхний торец горловины (базовая плоскость при печати)

EAR_Y_INNER = 52.0          # Координата Y входа в П-образный паз стойки
EAR_TAB_THICK = 4.5         # Толщина ползуна уха вдоль Y (глубина паза стойки 5.0 мм)
EAR_TAB_W = 9.6             # Ширина ползуна уха вдоль X (ширина паза стойки 10.0 мм)
EAR_ARM_W = 8.0             # Ширина соединительного ребра вдоль X
EAR_Z_BOT = 38.0            # Нижняя кромка уха (совпадает с торцом сопла)
EAR_Z_TOP = 52.0            # Верхняя горизонтальная полка уха
EAR_HOLE_Z = 44.0           # Высота оси крепежного отверстия М3 в ухе
EAR_GUSSET_Z_TOP = 96.0     # Верхняя точка схода наклонного ребра жесткости (угол ~64°)

def create_hopper():
    """
    Создает твердотельную B-Rep модель загрузочного бункера с ушами.
    """
    # 1. Верхняя коническая воронка
    cone_out = make_cone(NOZZLE_R_OUT, FUNNEL_R_TOP_OUT, FUNNEL_Z_TOP - NOZZLE_Z_TOP, (0, 0, NOZZLE_Z_TOP))
    cone_in = make_cone(NOZZLE_R_IN, FUNNEL_R_TOP_IN, FUNNEL_Z_TOP - NOZZLE_Z_TOP + 1.0, (0, 0, NOZZLE_Z_TOP))
    funnel = cone_out.cut(cone_in)
    
    # 2. Дозирующее сопло
    nozzle_out = make_cylinder(NOZZLE_R_OUT, NOZZLE_Z_TOP - NOZZLE_Z_BOT + 1.0, (0, 0, NOZZLE_Z_BOT))
    nozzle_in = make_cylinder(NOZZLE_R_IN, NOZZLE_Z_TOP - NOZZLE_Z_BOT + 2.0, (0, 0, NOZZLE_Z_BOT - 0.5))
    hopper_body = funnel.fuse(nozzle_out).cut(nozzle_in)
    
    # 3. Направляющие уши с двух сторон (+Y и -Y)
    for sign in [1.0, -1.0]:
        y_tab_start = EAR_Y_INNER if sign > 0 else -EAR_Y_INNER - EAR_TAB_THICK
        y_arm_start = (NOZZLE_R_OUT - 1.5) if sign > 0 else -EAR_Y_INNER
        arm_len = (EAR_Y_INNER - (NOZZLE_R_OUT - 1.5))
        
        # Ползун уха (вставляется в П-образный паз)
        tab = make_box(EAR_TAB_W, EAR_TAB_THICK, EAR_Z_TOP - EAR_Z_BOT, (-EAR_TAB_W / 2.0, y_tab_start, EAR_Z_BOT))
        
        # Соединительная перемычка от сопла до ползуна
        arm = make_box(EAR_ARM_W, arm_len, EAR_Z_TOP - EAR_Z_BOT, (-EAR_ARM_W / 2.0, y_arm_start if sign > 0 else -EAR_Y_INNER, EAR_Z_BOT))
        
        # Наклонный косыночный упор повышенной крутизны (угол ~64° к горизонту, ~26° к вертикали печати)
        # Начинается высоко на конусе воронки (Z=96) и сходит к наружной кромке уха (Y=52),
        # что гарантирует полное отсутствие провисаний и ступеней при перевернутой 3D-печати.
        r_at_z = NOZZLE_R_OUT + (FUNNEL_R_TOP_OUT - NOZZLE_R_OUT) * (EAR_GUSSET_Z_TOP - NOZZLE_Z_TOP) / (FUNNEL_Z_TOP - NOZZLE_Z_TOP)
        x_g = -EAR_ARM_W / 2.0
        p1 = FreeCAD.Vector(x_g, (NOZZLE_R_OUT - 1.0) * sign, EAR_Z_TOP)
        p2 = FreeCAD.Vector(x_g, (r_at_z - 2.0) * sign, EAR_GUSSET_Z_TOP)
        p3 = FreeCAD.Vector(x_g, r_at_z * sign, EAR_GUSSET_Z_TOP)
        p4 = FreeCAD.Vector(x_g, EAR_Y_INNER * sign, EAR_Z_TOP)
        wire = Part.makePolygon([p1, p2, p3, p4, p1])
        face = Part.Face(wire)
        gusset = face.extrude(FreeCAD.Vector(EAR_ARM_W, 0, 0))
        
        # Самонесущий скос 45° на верхней внешней кромке ползуна уха (исключает горизонтальный нависающий потолок)
        x_t = -EAR_TAB_W / 2.0
        c1 = FreeCAD.Vector(x_t - 0.5, EAR_Y_INNER * sign, EAR_Z_TOP + 1.0)
        c2 = FreeCAD.Vector(x_t - 0.5, (EAR_Y_INNER + EAR_TAB_THICK + 1.0) * sign, EAR_Z_TOP + 1.0)
        c3 = FreeCAD.Vector(x_t - 0.5, (EAR_Y_INNER + EAR_TAB_THICK + 1.0) * sign, EAR_Z_TOP - EAR_TAB_THICK)
        wire_c = Part.makePolygon([c1, c2, c3, c1])
        face_c = Part.Face(wire_c)
        chamfer_tool = face_c.extrude(FreeCAD.Vector(EAR_TAB_W + 1.0, 0, 0))
        tab = tab.cut(chamfer_tool)
        
        ear_solid = tab.fuse(arm).fuse(gusset)
        
        # Одиночное отверстие М3 (Ø3.4 мм) под фиксирующий винт
        hole_y_center = (EAR_Y_INNER + EAR_TAB_THICK / 2.0) * sign
        h_m3 = make_cylinder(1.7, 12.0, (0, hole_y_center - 6.0 * sign, EAR_HOLE_Z), (0, sign, 0))
        ear_solid = ear_solid.cut(h_m3)
        
        hopper_body = hopper_body.fuse(ear_solid)
        
    # Чистовой вырез внутреннего канала для гарантированной гладкости
    inner_cleanup = make_cylinder(NOZZLE_R_IN, NOZZLE_Z_TOP - NOZZLE_Z_BOT + 2.0, (0, 0, NOZZLE_Z_BOT - 0.5)).fuse(
        make_cone(NOZZLE_R_IN, FUNNEL_R_TOP_IN, FUNNEL_Z_TOP - NOZZLE_Z_TOP + 1.0, (0, 0, NOZZLE_Z_TOP))
    )
    hopper_body = hopper_body.cut(inner_cleanup)
    
    assert hopper_body.isValid(), "Hopper shape is topologically invalid!"
    return hopper_body

create_part = create_hopper

def generate_hopper_drawing():
    """
    Генерирует рабочий чертёж бункера по ГОСТ (ЕСКД) с полным комплектом размеров.
    Масштаб 1:1, формат А3 Альбомная.
    """
    doc = FreeCAD.newDocument("Doc_part_hopper")
    shape = create_hopper()
    feat = doc.addObject("Part::Feature", "Hopper")
    feat.Shape = shape
    doc.recompute()
    
    page, template = create_drawing_page(doc, "A3_Landscape", "Page_Hopper")
    W_SHEET, H_SHEET = 420.0, 297.0
    SCALE = 1.0
    
    X_FRONT = 90.0
    Y_FRONT = 185.0
    
    X_SEC = 235.0
    Y_SEC = 185.0
    
    X_TOP = 90.0
    Y_TOP = 65.0
    
    X_ISO = 360.0
    Y_ISO = 230.0
    
    # 1. Главный вид (вид вдоль X)
    v_front = doc.addObject('TechDraw::DrawViewPart', 'FrontView')
    v_front.Source = [feat]
    v_front.Direction = FreeCAD.Vector(1.0, 0.0, 0.0)
    v_front.XDirection = FreeCAD.Vector(0.0, 1.0, 0.0)
    page.addView(v_front)
    doc.recompute()
    v_front.Scale = SCALE
    v_front.X = X_FRONT
    v_front.Y = Y_FRONT
    v_front.IsoCount = 0
    doc.recompute()
    
    # 2. Разрез А-А (фронтальный разрез по X=0)
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
    
    # 3. Вид сверху
    v_top = doc.addObject('TechDraw::DrawViewPart', 'TopView')
    v_top.Source = [feat]
    v_top.Direction = FreeCAD.Vector(0.0, 0.0, -1.0)
    v_top.XDirection = FreeCAD.Vector(0.0, 1.0, 0.0)
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
    v_iso.Scale = 0.55
    v_iso.X = X_ISO
    v_iso.Y = Y_ISO
    v_iso.IsoCount = 0
    doc.recompute()
    
    # Основная надпись по ГОСТ 2.104-2006
    title_fields = {
        'Номер':         'ВЧ.01.00.009',
        'Название':      'Бункер загрузочный',
        'Масштаб':       '1:1',
        'Лист':          '1',
        'Листов':        '1',
        'Материал':      'PETG',
        'Организация1':  'Проект VISHNI',
        'Разработал':    'Демишкевич Э.Б.',
        'Проверил':      'Контролер',
    }
    fill_gost_title_block(template, title_fields)
    doc.recompute()
    
    def f_x(y): return X_FRONT + y * SCALE
    def f_y(z): return (297.0 - Y_FRONT) - (z - 73.5) * SCALE
    def s_x(y): return X_SEC + y * SCALE
    def s_y(z): return (297.0 - Y_SEC) - (z - 73.5) * SCALE
    def t_x(y): return X_TOP + y * SCALE
    def t_y(x): return (297.0 - Y_TOP) - x * SCALE
    
    qt_px = round(W_SHEET * 90.0 / 25.4)
    scale_corr = W_SHEET / (qt_px * 25.4 / 96.0)
    
    # Размеры на Главном виде
    dim_front = f'''
<!-- Габаритная высота 71* -->
<line x1="{f_x(-56.5) - 4}" y1="{f_y(38.0)}" x2="{f_x(-56.5) - 16}" y2="{f_y(38.0)}" class="dim-ext"/>
<line x1="{f_x(-36.0) - 4}" y1="{f_y(109.0)}" x2="{f_x(-56.5) - 16}" y2="{f_y(109.0)}" class="dim-ext"/>
<line x1="{f_x(-56.5) - 12}" y1="{f_y(38.0)}" x2="{f_x(-56.5) - 12}" y2="{f_y(109.0)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{f_x(-56.5) - 14}" y="{(f_y(38.0) + f_y(109.0)) / 2}" transform="rotate(-90 {f_x(-56.5) - 14} {(f_y(38.0) + f_y(109.0)) / 2})" class="dim-text">71*</text>

<!-- Высота сопла 16 -->
<line x1="{f_x(-16.0) - 4}" y1="{f_y(54.0)}" x2="{f_x(-56.5) - 10}" y2="{f_y(54.0)}" class="dim-ext"/>
<line x1="{f_x(-56.5) - 7}" y1="{f_y(38.0)}" x2="{f_x(-56.5) - 7}" y2="{f_y(54.0)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{f_x(-56.5) - 9}" y="{(f_y(38.0) + f_y(54.0)) / 2}" transform="rotate(-90 {f_x(-56.5) - 9} {(f_y(38.0) + f_y(54.0)) / 2})" class="dim-text">16</text>

<!-- Высота оси отверстия 6 -->
<line x1="{f_x(56.5) + 2}" y1="{f_y(38.0)}" x2="{f_x(56.5) + 12}" y2="{f_y(38.0)}" class="dim-ext"/>
<line x1="{f_x(56.5) + 2}" y1="{f_y(44.0)}" x2="{f_x(56.5) + 12}" y2="{f_y(44.0)}" class="dim-ext"/>
<line x1="{f_x(56.5) + 9}" y1="{f_y(38.0)}" x2="{f_x(56.5) + 9}" y2="{f_y(44.0)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{f_x(56.5) + 11}" y="{(f_y(38.0) + f_y(44.0)) / 2 + 1.2}" class="dim-text-l">6</text>

<!-- Выноска на 2 отверстия Ø3,4 (вниз-влево в свободную зону) -->
<path d="M {f_x(54.25)} {f_y(44.0)} L {f_x(54.25) - 8} {f_y(44.0) + 16} L {f_x(54.25) - 36} {f_y(44.0) + 16}" class="leader" marker-start="url(#dot)"/>
<text x="{f_x(54.25) - 34}" y="{f_y(44.0) + 14.5}" class="dim-text-l" font-size="3.2">2 отв. Ø3,4</text>

<!-- Выноска ребра жесткости (в свободную зону между видами) -->
<path d="M {f_x(28.0)} {f_y(80.0)} L {f_x(28.0) + 10} {f_y(80.0) - 14} L {f_x(28.0) + 48} {f_y(80.0) - 14}" class="leader" marker-start="url(#dot)"/>
<text x="{f_x(28.0) + 12}" y="{f_y(80.0) - 17.0}" class="dim-text-l" font-size="3.0">Ребро жесткости 64°</text>
<text x="{f_x(28.0) + 12}" y="{f_y(80.0) - 12.5}" class="dim-text-l" font-size="2.6">(угол для 3D-печати)</text>
'''

    # Размеры на Виде сверху
    dim_top = f'''
<!-- Габаритная ширина 113 и расстояние 104 под Top View -->
<line x1="{t_x(-56.5)}" y1="{t_y(-36.0) + 4}" x2="{t_x(-56.5)}" y2="{t_y(-36.0) + 26}" class="dim-ext"/>
<line x1="{t_x(56.5)}" y1="{t_y(-36.0) + 4}" x2="{t_x(56.5)}" y2="{t_y(-36.0) + 26}" class="dim-ext"/>
<line x1="{t_x(-56.5)}" y1="{t_y(-36.0) + 22}" x2="{t_x(56.5)}" y2="{t_y(-36.0) + 22}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{t_x(0.0)}" y="{t_y(-36.0) + 20.5}" class="dim-text">113</text>

<line x1="{t_x(-52.0)}" y1="{t_y(-36.0) + 4}" x2="{t_x(-52.0)}" y2="{t_y(-36.0) + 15}" class="dim-ext"/>
<line x1="{t_x(52.0)}" y1="{t_y(-36.0) + 4}" x2="{t_x(52.0)}" y2="{t_y(-36.0) + 15}" class="dim-ext"/>
<line x1="{t_x(-52.0)}" y1="{t_y(-36.0) + 12}" x2="{t_x(52.0)}" y2="{t_y(-36.0) + 12}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{t_x(0.0)}" y="{t_y(-36.0) + 10.5}" class="dim-text">104</text>

<!-- Ширина ползуна уха 9.6-0.1 -->
<line x1="{t_x(56.5) + 2}" y1="{t_y(4.8)}" x2="{t_x(56.5) + 14}" y2="{t_y(4.8)}" class="dim-ext"/>
<line x1="{t_x(56.5) + 2}" y1="{t_y(-4.8)}" x2="{t_x(56.5) + 14}" y2="{t_y(-4.8)}" class="dim-ext"/>
<line x1="{t_x(56.5) + 10}" y1="{t_y(4.8)}" x2="{t_x(56.5) + 10}" y2="{t_y(-4.8)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{t_x(56.5) + 12}" y="{t_y(0.0)}" transform="rotate(-90 {t_x(56.5) + 12} {t_y(0.0)})" class="dim-text">9,6<tspan font-size="2.4" dy="-1.5">-0,1</tspan></text>

<!-- Толщина ползуна уха 4.5 (сверху уха) -->
<line x1="{t_x(52.0)}" y1="{t_y(4.8) - 2}" x2="{t_x(52.0)}" y2="{t_y(4.8) - 12}" class="dim-ext"/>
<line x1="{t_x(56.5)}" y1="{t_y(4.8) - 2}" x2="{t_x(56.5)}" y2="{t_y(4.8) - 12}" class="dim-ext"/>
<line x1="{t_x(52.0)}" y1="{t_y(4.8) - 8}" x2="{t_x(56.5)}" y2="{t_y(4.8) - 8}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{(t_x(52.0) + t_x(56.5)) / 2}" y="{t_y(4.8) - 9.5}" class="dim-text">4,5</text>

<!-- Ширина ребра 8 на левом ухе -->
<line x1="{t_x(-52.0) - 2}" y1="{t_y(4.0)}" x2="{t_x(-52.0) - 14}" y2="{t_y(4.0)}" class="dim-ext"/>
<line x1="{t_x(-52.0) - 2}" y1="{t_y(-4.0)}" x2="{t_x(-52.0) - 14}" y2="{t_y(-4.0)}" class="dim-ext"/>
<line x1="{t_x(-52.0) - 10}" y1="{t_y(4.0)}" x2="{t_x(-52.0) - 10}" y2="{t_y(-4.0)}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{t_x(-52.0) - 12}" y="{t_y(0.0)}" transform="rotate(-90 {t_x(-52.0) - 12} {t_y(0.0)})" class="dim-text">8</text>
'''

    # Размеры на Разрезе А-А:
    dim_sec = f'''
<!-- Ø72 и Ø67.2 вверху -->
<line x1="{s_x(-36.0)}" y1="{s_y(109.0) - 2}" x2="{s_x(-36.0)}" y2="{s_y(109.0) - 20}" class="dim-ext"/>
<line x1="{s_x(36.0)}" y1="{s_y(109.0) - 2}" x2="{s_x(36.0)}" y2="{s_y(109.0) - 20}" class="dim-ext"/>
<line x1="{s_x(-36.0)}" y1="{s_y(109.0) - 16}" x2="{s_x(36.0)}" y2="{s_y(109.0) - 16}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{s_x(0.0)}" y="{s_y(109.0) - 17.5}" class="dim-text">Ø72</text>

<line x1="{s_x(-33.6)}" y1="{s_y(109.0) - 2}" x2="{s_x(-33.6)}" y2="{s_y(109.0) - 11}" class="dim-ext"/>
<line x1="{s_x(33.6)}" y1="{s_y(109.0) - 2}" x2="{s_x(33.6)}" y2="{s_y(109.0) - 11}" class="dim-ext"/>
<line x1="{s_x(-33.6)}" y1="{s_y(109.0) - 8}" x2="{s_x(33.6)}" y2="{s_y(109.0) - 8}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{s_x(0.0)}" y="{s_y(109.0) - 9.5}" class="dim-text">Ø67,2</text>

<!-- Ø32 и Ø27.2 внизу сопла -->
<line x1="{s_x(-16.0)}" y1="{s_y(38.0) + 2}" x2="{s_x(-16.0)}" y2="{s_y(38.0) + 20}" class="dim-ext"/>
<line x1="{s_x(16.0)}" y1="{s_y(38.0) + 2}" x2="{s_x(16.0)}" y2="{s_y(38.0) + 20}" class="dim-ext"/>
<line x1="{s_x(-16.0)}" y1="{s_y(38.0) + 16}" x2="{s_x(16.0)}" y2="{s_y(38.0) + 16}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{s_x(0.0)}" y="{s_y(38.0) + 14.5}" class="dim-text">Ø32</text>

<line x1="{s_x(-13.6)}" y1="{s_y(38.0) + 2}" x2="{s_x(-13.6)}" y2="{s_y(38.0) + 11}" class="dim-ext"/>
<line x1="{s_x(13.6)}" y1="{s_y(38.0) + 2}" x2="{s_x(13.6)}" y2="{s_y(38.0) + 11}" class="dim-ext"/>
<line x1="{s_x(-13.6)}" y1="{s_y(38.0) + 8}" x2="{s_x(13.6)}" y2="{s_y(38.0) + 8}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)"/>
<text x="{s_x(0.0)}" y="{s_y(38.0) + 6.5}" class="dim-text">Ø27,2</text>
'''

    # Технические требования в свободной правой зоне (X=305..415, Y=135..195)
    tech_notes = f'''
<text x="305" y="142" font-family="osifont, Arial, sans-serif" font-size="3.8" font-weight="bold" fill="#000">Технические требования:</text>
<text x="305" y="150" font-family="osifont, Arial, sans-serif" font-size="3.2" fill="#000">1. * Размеры для справок.</text>
<text x="305" y="157" font-family="osifont, Arial, sans-serif" font-size="3.2" fill="#000">2. Материал: Пищевой PETG (Food Safe).</text>
<text x="305" y="164" font-family="osifont, Arial, sans-serif" font-size="3.2" fill="#000">3. Изготовление: 3D-печать в перевернутом</text>
<text x="308.5" y="171" font-family="osifont, Arial, sans-serif" font-size="3.2" fill="#000">положении (базирование по горловине Z=71*).</text>
<text x="305" y="178" font-family="osifont, Arial, sans-serif" font-size="3.2" fill="#000">4. Поддерживающие структуры не требуются</text>
<text x="308.5" y="185" font-family="osifont, Arial, sans-serif" font-size="3.2" fill="#000">(угол ребер жесткости 64° к горизонту).</text>
<text x="305" y="192" font-family="osifont, Arial, sans-serif" font-size="3.2" fill="#000">5. Крепление к стойкам: 2 винта М3 (по 1 шт. с боков).</text>
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

<!-- Заголовок разреза -->
<text x="{X_SEC}" y="16" class="view-title">А - А</text>

<!-- Осевые линии -->
<line x1="{f_x(0.0)}" y1="{f_y(109.0) - 8}" x2="{f_x(0.0)}" y2="{f_y(38.0) + 6}" class="center-line"/>
<line x1="{s_x(0.0)}" y1="{s_y(109.0) - 8}" x2="{s_x(0.0)}" y2="{s_y(38.0) + 6}" class="center-line"/>
<line x1="{t_x(0.0)}" y1="{t_y(36.0) - 6}" x2="{t_x(0.0)}" y2="{t_y(-36.0) + 6}" class="center-line"/>
<line x1="{t_x(-56.5) - 6}" y1="{t_y(0.0)}" x2="{t_x(56.5) + 6}" y2="{t_y(0.0)}" class="center-line"/>

<!-- Размеры -->
{dim_front}
{dim_top}
{dim_sec}
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
    
    export_drawing(doc, page, "part_hopper.pdf", "part_hopper.FCStd", "part_hopper.png")
    print("SUCCESS: part_hopper drawing exported cleanly!")

if __name__ == "__main__":
    generate_hopper_drawing()
