#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_rotor.py
Поз. 2: Карусель ягод (Cherry Rotor Drum) - UPDATED with Circular Groove
"""

import sys
import os
import math

# Импорт утилит FreeCAD (согласно вашему стандарту)
from freecad_utils import (
    FreeCAD, Part, TechDraw, TechDrawGui,
    make_box, make_cylinder, make_cone, make_sphere,
    trans, rot_z, create_drawing_page, add_part_view,
    fill_gost_title_block, export_drawing
)

def create_rotor():
    """
    Создает B-Rep солид барабана ротора.
    Параметры из params.scad:
    rotor_outer_r = 58.0, rotor_h = 24.0, rotor_pocket_r = 44.0
    kicker_slot_w = 4.5, kicker_slot_depth = 19.0
    """
    # 1. Основное тело ротора
    drum = make_cylinder(58.0, 24.0, (0, 0, 0))
    
    # 2. Центральные отверстия (Ось М8 и подшипники 608ZZ)
    # Посадочные места под подшипники (верх и низ) - зазор 0.1 мм для press-fit
    bearing_seat_r = (22.0 + 0.1) / 2.0
    top_bearing = make_cylinder(bearing_seat_r, 7.0, (0, 0, 24.0 - 7.0 + 0.5)) # Oversize 0.5 для чистого выреза
    # bot_bearing = make_cylinder(bearing_seat_r, 7.0, (0, 0, -0.5))
    
    # Сквозное отверстие под вал
    shaft_hole = make_cylinder(4.1, 30.0, (0, 0, -3.0)) # Радиус 4.1 = Ø8.2
    
    drum = drum.cut(top_bearing).cut(shaft_hole)
    
    # 3. 6 Сферических лунок для ягод (Ø26, глубина 13 мм) и отверстия для косточек (Ø9.5)
    # Центр сферы R=13.0 находится на верхней плоскости Z=24.0 (полусфера глубиной 13 мм).
    # Для устранения сингулярности касания экватора с плоскостью Z=24.0 в OpenCASCADE
    # объединяем сферу с небольшим цилиндром вверх (Z=24..29).
    for i in range(6):
        ang = i * 60.0
        rad = math.radians(ang)
        px = 44.0 * math.cos(rad)
        py = 44.0 * math.sin(rad)
        
        sph = make_sphere(13.0, (px, py, 24.0))
        cyl_up = make_cylinder(13.0, 5.0, (px, py, 24.0))
        pocket_tool = sph.fuse(cyl_up)
        
        # Отверстие для выброса косточки Ø9.5 (r=4.75), высота с запасом от Z=-2 до Z=14
        pit_hole = make_cylinder(4.75, 16.0, (px, py, -2.0))
        
        drum = drum.cut(pocket_tool).cut(pit_hole)
        
    # 4. Кольцевой паз для ножа-экстрактора
    # Ширина 4.5 мм, глубина 19 мм. Центр паза на R = 44.0
    groove_outer_r = 44.0 + (4.5 / 2.0)
    groove_inner_r = 44.0 - (4.5 / 2.0)
    groove_height = 16.0 + 1.0 # +1 для гарантированного выхода через верх
    
    # Создаем инструмент для выреза паза (кольцо)
    outer_cyl = make_cylinder(groove_outer_r, groove_height, (0, 0, 24.0 - 16.0))
    inner_cyl = make_cylinder(groove_inner_r, groove_height + 2.0, (0, 0, 24.0 - 16.0 - 1.0))
    groove_tool = outer_cyl.cut(inner_cyl)
    
    drum = drum.cut(groove_tool)
        
    # 5. Крепежные отверстия для Мальтийского креста (6xM3 на R=20)
    for i in range(6):
        ang = i * 60.0
        rad = math.radians(ang)
        bx = 20.0 * math.cos(rad)
        by = 20.0 * math.sin(rad)
        bolt_hole = make_cylinder(1.5, 10.0, (bx, by, -1.0)) # r=1.5 для нарезки М3
        drum = drum.cut(bolt_hole)

    # Проверка валидности
    if not drum.isValid():
        print("WARNING: Rotor shape is invalid!")
        
    return drum

# Назначение функции для генератора
create_part = create_rotor

def generate_rotor_drawing(part_name="part_rotor_updated",
                           doc_code="ВЧ.01.00.002",
                           title_name="Барабан роторный (мод.)",
                           material="PETG",
                           scale=1.0,
                           sheet="A3_Landscape",
                           notes=None):
    """
    Генерирует рабочий чертеж ротора по ГОСТ (ЕСКД):
    - Вид сверху с секущей плоскостью А-А;
    - Вертикальный диаметральный разрез А-А вместо вида спереди;
    - Аксонометрический вид (изометрия);
    - Нанесение основных линейных, диаметральных и радиальных размеров;
    - Штамп по ГОСТ 2.104 и технические требования по ГОСТ 2.316.
    """
    shape = create_rotor()
    
    doc = FreeCAD.newDocument(f"Doc_{part_name}")
    feat = doc.addObject("Part::Feature", part_name)
    feat.Shape = shape
    doc.recompute()
    
    page, template = create_drawing_page(doc, sheet, f"Page_{part_name}")
    
    # Координаты для формата А3 (420 x 297 мм)
    x_c = 135.0
    y_top_td = 85.0    # SVG cy = 212.0
    y_sec_td = 210.0   # SVG cy = 87.0
    
    # 1. Вид сверху (Top View с секущей линией А-А)
    v_top = add_part_view(doc, page, feat, "TopView", (0, 0, 1), scale, x_c, y_top_td)
    
    # 2. Вертикальный диаметральный разрез А-А (вместо вида спереди)
    sec = doc.addObject("TechDraw::DrawViewSection", "SectionView")
    sec.BaseView = v_top
    sec.SectionNormal = FreeCAD.Vector(0.0, 1.0, 0.0)
    sec.SectionOrigin = FreeCAD.Vector(0.0, 0.0, 12.0)
    sec.SectionDirection = "Up"
    sec.SectionSymbol = "A"
    page.addView(sec)
    doc.recompute()
    
    # Направление взгляда +Y, поворот 180° для правильной ориентации (конические лунки сверху)
    sec.Direction = FreeCAD.Vector(0.0, 1.0, 0.0)
    sec.XDirection = FreeCAD.Vector(1.0, 0.0, 0.0)
    sec.Rotation = 180.0
    sec.X = x_c
    sec.Y = y_sec_td
    sec.IsoCount = 0
    sec.ViewObject.HatchColor = (0.0, 0.0, 0.0, 1.0)
    doc.recompute()
    
    # 3. Аксонометрический вид (Iso View)
    add_part_view(doc, page, feat, "IsoView", (1.0, -1.2, 0.9), 0.85, 315.0, 195.0)
    
    # 4. Основная надпись (штамп ГОСТ 2.104)
    title_fields = {
        'Номер': doc_code,
        'Название': title_name,
        'Масштаб': f"{int(scale)}:1" if scale >= 1 else f"1:{int(1/scale)}",
        'Лист': '1',
        'Листов': '1',
        'Материал1': material,
        'Материал2': '',
        'Материал3': '',
        'Организация1': 'Проект VISHNI',
        'Организация2': '',
        'Разработал': 'Инженер',
        'Проверил': 'Контролер'
    }
    fill_gost_title_block(template, title_fields)
    doc.recompute()
    
    # 5. Осевые кресты на лунках вида сверху
    cross_lines = []
    for ang_deg in [60, 120, 240, 300]:
        rad = math.radians(ang_deg)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        cx_p = 135.0 + 44.0 * cos_a
        cy_p = 212.0 - 44.0 * sin_a
        
        # Радиальная черта
        rx1 = cx_p - 8.0 * cos_a
        ry1 = cy_p + 8.0 * sin_a
        rx2 = cx_p + 8.0 * cos_a
        ry2 = cy_p - 8.0 * sin_a
        cross_lines.append(f'<line x1="{rx1:.2f}" y1="{ry1:.2f}" x2="{rx2:.2f}" y2="{ry2:.2f}" class="center-line" />')
        
        # Тангенциальная черта
        tx1 = cx_p + 7.0 * sin_a
        ty1 = cy_p + 7.0 * cos_a
        tx2 = cx_p - 7.0 * sin_a
        ty2 = cy_p - 7.0 * cos_a
        cross_lines.append(f'<line x1="{tx1:.2f}" y1="{ty1:.2f}" x2="{tx2:.2f}" y2="{ty2:.2f}" class="center-line" />')

    crosses_svg = '\n'.join(cross_lines)
    
    # 6. Технические требования (ГОСТ 2.316) над основной надписью
    notes_svg = ""
    if notes:
        notes_lines = ['<text x="230" y="198" font-family="osifont, Arial, sans-serif" font-size="3.6px" font-weight="bold" fill="#000">Технические требования:</text>']
        for idx, line in enumerate(notes):
            notes_lines.append(f'<text x="230" y="{205 + idx * 6.0}" font-family="osifont, Arial, sans-serif" font-size="3.2px" fill="#000">{line}</text>')
        notes_svg = '\n'.join(notes_lines)

    # 7. Векторный оверлей основных размеров и надписей (ГОСТ 2.307)
    svg_dim = f'''<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
    <path d="M 0 2 L 10 5 L 0 8 z" fill="#000" />
  </marker>
  <marker id="arrow-rev" viewBox="0 0 10 10" refX="0" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
    <path d="M 10 2 L 0 5 L 10 8 z" fill="#000" />
  </marker>
  <marker id="dot" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="3" markerHeight="3">
    <circle cx="5" cy="5" r="2.5" fill="#000" />
  </marker>
</defs>
<style>
  .dim-line {{ stroke: #000; stroke-width: 0.35; fill: none; }}
  .dim-ext {{ stroke: #000; stroke-width: 0.25; fill: none; }}
  .center-line {{ stroke: #000; stroke-width: 0.25; stroke-dasharray: 6,1.5,1.5,1.5; fill: none; }}
  .dim-text {{ font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: middle; }}
  .dim-text-left {{ font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: start; }}
  .dim-text-right {{ font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: end; }}
  .view-title {{ font-family: osifont, Arial, sans-serif; font-size: 5.0px; fill: #000; text-anchor: middle; font-weight: bold; }}
  .leader {{ stroke: #000; stroke-width: 0.35; fill: none; }}
</style>

<!-- НАДПИСЬ РАЗРЕЗА А-А -->
<text x="135" y="27" class="view-title">А-А</text>

<!-- ==================== РАЗРЕЗ А-А ==================== -->
<!-- Осевые линии разреза -->
<line x1="135" y1="31" x2="135" y2="103" class="center-line" />
<line x1="91" y1="67" x2="91" y2="104" class="center-line" />
<line x1="179" y1="67" x2="179" y2="104" class="center-line" />

<!-- 1. Наружный диаметр Ø116 -->
<line x1="77" y1="74" x2="77" y2="34" class="dim-ext" />
<line x1="193" y1="74" x2="193" y2="34" class="dim-ext" />
<line x1="77" y1="37" x2="193" y2="37" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="135" y="35.5" class="dim-text">Ø116</text>

<!-- 2. Посадочные места подшипников Ø22.1+0.1 -->
<line x1="123.95" y1="74" x2="123.95" y2="46" class="dim-ext" />
<line x1="146.05" y1="74" x2="146.05" y2="46" class="dim-ext" />
<line x1="123.95" y1="49" x2="146.05" y2="49" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="135" y="47.5" class="dim-text">Ø22,1<tspan font-size="2.4" dy="-1.5">+0,1</tspan></text>

<!-- 3. Верхний диаметр лунки Ø26 -->
<line x1="78" y1="74" x2="78" y2="57" class="dim-ext" />
<line x1="104" y1="74" x2="104" y2="57" class="dim-ext" />
<line x1="78" y1="60" x2="104" y2="60" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="91" y="58.5" class="dim-text">Ø26</text>

<!-- 4. Сквозное отверстие под вал Ø8.2 (Выноска) -->
<path d="M 130.9 87 L 118 72 L 102 72" class="leader" marker-start="url(#dot)" />
<text x="110" y="70.5" class="dim-text">Ø8,2</text>

<!-- 5. Общая высота детали 24 -->
<line x1="194" y1="75" x2="208" y2="75" class="dim-ext" />
<line x1="194" y1="99" x2="208" y2="99" class="dim-ext" />
<line x1="205" y1="75" x2="205" y2="99" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="203" y="87" transform="rotate(-90 203 87)" class="dim-text">24</text>

<!-- 6. Глубина гнезда подшипника 7 -->
<line x1="146.5" y1="82" x2="218" y2="82" class="dim-ext" />
<line x1="194" y1="75" x2="218" y2="75" class="dim-ext" />
<line x1="215" y1="69" x2="215" y2="75" class="dim-line" marker-end="url(#arrow)" />
<line x1="215" y1="88" x2="215" y2="82" class="dim-line" marker-end="url(#arrow)" />
<line x1="215" y1="75" x2="215" y2="82" class="dim-line" />
<text x="218" y="79.5" class="dim-text-left">7</text>

<!-- 7. Глубина сферической лунки 13 -->
<line x1="77" y1="75" x2="65" y2="75" class="dim-ext" />
<line x1="86.25" y1="88" x2="65" y2="88" class="dim-ext" />
<line x1="68" y1="75" x2="68" y2="88" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="66" y="81.5" transform="rotate(-90 66 81.5)" class="dim-text">13</text>

<!-- 8. Отверстие выброса косточки Ø9.5 -->
<line x1="86.25" y1="99" x2="86.25" y2="110" class="dim-ext" />
<line x1="95.75" y1="99" x2="95.75" y2="110" class="dim-ext" />
<line x1="76" y1="107" x2="86.25" y2="107" class="dim-line" marker-end="url(#arrow)" />
<line x1="106" y1="107" x2="95.75" y2="107" class="dim-line" marker-end="url(#arrow)" />
<line x1="86.25" y1="107" x2="95.75" y2="107" class="dim-line" />
<text x="91" y="105.5" class="dim-text">Ø9,5</text>

<!-- 9. Радиус сферы лунки Сфера R13 (ГОСТ 2.307-2011 п. 5.37) -->
<path d="M 83 84 L 66 96 L 40 96" class="leader" marker-start="url(#dot)" />
<text x="53" y="94.5" class="dim-text">Сфера R13</text>

<!-- 10. Межосевое расстояние противоположных лунок 88* -->
<line x1="91" y1="104" x2="91" y2="118" class="dim-ext" />
<line x1="179" y1="104" x2="179" y2="118" class="dim-ext" />
<line x1="91" y1="115" x2="179" y2="115" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="135" y="113.5" class="dim-text">88*</text>


<!-- ==================== ВИД СВЕРХУ ==================== -->
<!-- Вертикальная осевая линия вида сверху -->
<line x1="135" y1="145" x2="135" y2="279" class="center-line" />

<!-- Окружность центров лунок Ø88 -->
<circle cx="135" cy="212" r="44" class="center-line" />

<!-- Окружность центров крепежных отверстий мальтийского креста Ø40 -->
<circle cx="135" cy="212" r="20" class="center-line" />

<!-- Осевые кресты на лунках -->
{crosses_svg}

<!-- Выноска лунок для ягод -->
<path d="M 113 160.9 L 90 148 L 50 148" class="leader" marker-start="url(#dot)" />
<text x="70" y="146.5" class="dim-text">6 лунок (сфера Ø26)</text>

<!-- Выноска кольцевого паза экстрактора -->
<path d="M 111.9 249.1 L 88 268 L 45 268" class="leader" marker-start="url(#dot)" />
<text x="66.5" y="266.5" class="dim-text">Паз шир. 4,5; глуб. 16</text>

<!-- Выноска резьбовых отверстий крепления мальтийского колеса -->
<path d="M 145 194.7 L 175 165 L 220 165" class="leader" marker-start="url(#dot)" />
<text x="197.5" y="163.5" class="dim-text">6 отв. М3 - 7Н ↧ 10</text>
<text x="197.5" y="169.5" class="dim-text" font-size="2.8px">на Ø40*</text>

<!-- ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ -->
{notes_svg}

</svg>'''

    sym_dim = doc.addObject('TechDraw::DrawViewSymbol', 'OverlayDimensions')
    sym_dim.Symbol = svg_dim
    page.addView(sym_dim)
    doc.recompute()
    
    # Масштабный коэффициент устранения расхождения DPI QtSvg (90 DPI vs 96 DPI FreeCAD)
    sym_dim.Scale = 420.0 / (1488.0 * 25.4 / 96.0)
    sym_dim.X = 210.0
    sym_dim.Y = 148.5
    doc.recompute()
    
    pdf_name = f"{part_name}.pdf"
    fcstd_name = f"{part_name}.FCStd"
    png_name = f"{part_name}.png"
    export_drawing(doc, page, pdf_name, fcstd_name, png_name)
    print(f"Drawing for {part_name} generated successfully!")

if __name__ == "__main__":
    # Технические требования согласно ГОСТ 2.316
    notes = [
        "1. * Размеры для справок.",
        "2. Материал: PETG (допускается контакт с пищевыми продуктами).",
        "3. Параметры печати: заполнение 50%, 4 периметра.",
        "4. Кольцевой паз очистить от поддержек и отполировать.",
        "5. Острые кромки притупить R 0.5."
    ]
    
    # Генерация чертежа детали ротора с вертикальным разрезом и размерами
    generate_rotor_drawing(notes=notes)