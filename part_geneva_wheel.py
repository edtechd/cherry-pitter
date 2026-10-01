#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_geneva_wheel.py
Поз. 3: Колесо мальтийского креста (Geneva Driven Wheel) - UPDATED
Доработано:
- Центральное отверстие расширено до размеров подшипника 608ZZ (Ø22.1+0.1 мм)
- На чертеже вид спереди заменен на вертикальный диаметральный разрез А-А
- Нанесены полные размеры, осевые линии и выноски по ЕСКД (ГОСТ 2.305, 2.307)
"""

import sys
import os
import math
from freecad_utils import (
    FreeCAD, Part, TechDraw, TechDrawGui,
    make_box, make_cylinder, trans, rot_z,
    create_drawing_page, add_part_view,
    fill_gost_title_block, export_drawing
)

def create_geneva_wheel():
    """
    Constructs the 6-stop Geneva Driven Wheel at local origin (0,0,0).
    Base is at Z = 0, thickness = 8.0 mm, driven radius = 52.0 mm.
    Central hole is expanded to Ø22.1 mm (+0.1 mm tolerance) to house the 608ZZ bearing.
    """
    wheel = make_cylinder(52.0, 8.0, (0, 0, 0))
    
    # 1. Расширенное центральное отверстие под подшипник 608ZZ (8x22x7 мм)
    # Посадочный диаметр Ø22.1 мм (+0.1 мм допуск на усадку PETG)
    bearing_seat_r = (22.0 + 0.1) / 2.0  # 11.05 мм
    center_hole = make_cylinder(bearing_seat_r, 12.0, (0, 0, -2.0))
    wheel = wheel.cut(center_hole)
    
    # 2. 6 Радиальных пазов шириной 5.5 мм (под цевку Ø5.0 мм)
    for i in range(6):
        ang = i * 60.0
        rad = math.radians(ang)
        slot = make_box(28.0, 5.5, 12.0, (0, -2.75, -2.0))
        slot = trans(slot, 26.0, 0, 0)
        slot = rot_z(slot, ang)
        wheel = wheel.cut(slot)
        
    # 3. 6 Блокировочных вогнутых дуг выстоя (R = 22.5 мм под замок кривошипа)
    for i in range(6):
        ang = i * 60.0
        rad = math.radians(ang)
        cutout = make_cylinder(22.5, 12.0, (60.0 * math.cos(rad), 60.0 * math.sin(rad), -2.0))
        wheel = wheel.cut(cutout)
        
    # 4. 6 Крепежных отверстий Ø3.2 мм под винты М3 (крепление к ротору на R=20 мм)
    for i in range(6):
        ang = i * 60.0
        rad = math.radians(ang)
        wheel = wheel.cut(make_cylinder(1.6, 12.0, (20.0 * math.cos(rad), 20.0 * math.sin(rad), -2.0)))
        
    if not wheel.isValid():
        print("WARNING: Geneva wheel shape is topologically invalid!")
        
    return wheel

create_part = create_geneva_wheel

def generate_geneva_wheel_drawing(part_name="part_geneva_wheel",
                                  doc_code="ВЧ.01.00.003",
                                  title_name="Колесо мальтийского креста",
                                  material="PETG",
                                  scale=1.0,
                                  sheet="A3_Landscape",
                                  notes=None):
    """
    Генерирует рабочий чертеж мальтийского колеса по ГОСТ (ЕСКД):
    - Вид сверху с секущей плоскостью А-А;
    - Вертикальный диаметральный разрез А-А вместо вида спереди;
    - Аксонометрический вид (изометрия);
    - Нанесение основных линейных, диаметральных и радиальных размеров;
    - Штамп по ГОСТ 2.104 и технические требования по ГОСТ 2.316.
    """
    shape = create_geneva_wheel()
    
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
    sec.SectionOrigin = FreeCAD.Vector(0.0, 0.0, 4.0)
    sec.SectionDirection = "Up"
    sec.SectionSymbol = "A"
    page.addView(sec)
    doc.recompute()
    
    # Направление взгляда +Y, поворот 180° для правильной ориентации
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
    
    # 5. Осевые линии и кресты для пазов и крепежных отверстий вида сверху
    radial_centerlines = []
    for ang_deg in [60, 120, 240, 300]:
        rad = math.radians(ang_deg)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        
        # Осевая линия вдоль паза (от R=14 до R=54)
        x1_p = 135.0 + 14.0 * cos_a
        y1_p = 212.0 - 14.0 * sin_a
        x2_p = 135.0 + 54.0 * cos_a
        y2_p = 212.0 - 54.0 * sin_a
        radial_centerlines.append(f'<line x1="{x1_p:.2f}" y1="{y1_p:.2f}" x2="{x2_p:.2f}" y2="{y2_p:.2f}" class="center-line" />')
        
        # Поперечная черта на крепежном отверстии R=20
        hx = 135.0 + 20.0 * cos_a
        hy = 212.0 - 20.0 * sin_a
        tx1 = hx + 4.0 * sin_a
        ty1 = hy + 4.0 * cos_a
        tx2 = hx - 4.0 * sin_a
        ty2 = hy - 4.0 * cos_a
        radial_centerlines.append(f'<line x1="{tx1:.2f}" y1="{ty1:.2f}" x2="{tx2:.2f}" y2="{ty2:.2f}" class="center-line" />')

    radial_cl_svg = '\n'.join(radial_centerlines)

    # 6. Технические требования (ГОСТ 2.316) над основной надписью
    notes_svg = ""
    if notes:
        notes_lines = ['<text x="230" y="188" font-family="osifont, Arial, sans-serif" font-size="3.6px" font-weight="bold" fill="#000">Технические требования:</text>']
        for idx, line in enumerate(notes):
            notes_lines.append(f'<text x="230" y="{195 + idx * 5.8}" font-family="osifont, Arial, sans-serif" font-size="3.2px" fill="#000">{line}</text>')
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
<text x="135" y="44" class="view-title">А-А</text>

<!-- ==================== РАЗРЕЗ А-А ==================== -->
<!-- Осевые линии разреза -->
<line x1="135" y1="48" x2="135" y2="114" class="center-line" />
<line x1="115" y1="78" x2="115" y2="105" class="center-line" />
<line x1="155" y1="78" x2="155" y2="105" class="center-line" />

<!-- 1. Наружный диаметр Ø104* -->
<line x1="83" y1="83" x2="83" y2="50" class="dim-ext" />
<line x1="187" y1="83" x2="187" y2="50" class="dim-ext" />
<line x1="83" y1="53" x2="187" y2="53" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="135" y="51.5" class="dim-text">Ø104*</text>

<!-- 2. Посадочное отверстие подшипника 608ZZ: Ø22,1+0,1 -->
<line x1="123.95" y1="83" x2="123.95" y2="62" class="dim-ext" />
<line x1="146.05" y1="83" x2="146.05" y2="62" class="dim-ext" />
<line x1="123.95" y1="65" x2="146.05" y2="65" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="135" y="63.5" class="dim-text">Ø22,1<tspan font-size="2.4" dy="-1.5">+0,1</tspan></text>

<!-- 3. Межосевое расстояние отверстий крепления 40* -->
<line x1="115" y1="91" x2="115" y2="102" class="dim-ext" />
<line x1="155" y1="91" x2="155" y2="102" class="dim-ext" />
<line x1="115" y1="99" x2="155" y2="99" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="135" y="97.5" class="dim-text">40*</text>

<!-- 4. Межосевой диаметр оснований пазов 52* -->
<line x1="109" y1="91" x2="109" y2="111" class="dim-ext" />
<line x1="161" y1="91" x2="161" y2="111" class="dim-ext" />
<line x1="109" y1="108" x2="161" y2="108" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="135" y="106.5" class="dim-text">52*</text>

<!-- 5. Толщина детали 8 -->
<line x1="187" y1="83" x2="200" y2="83" class="dim-ext" />
<line x1="187" y1="91" x2="200" y2="91" class="dim-ext" />
<line x1="197" y1="77" x2="197" y2="83" class="dim-line" marker-end="url(#arrow)" />
<line x1="197" y1="97" x2="197" y2="91" class="dim-line" marker-end="url(#arrow)" />
<line x1="197" y1="83" x2="197" y2="91" class="dim-line" />
<text x="195" y="87" transform="rotate(-90 195 87)" class="dim-text">8</text>

<!-- ==================== ВИД СВЕРХУ ==================== -->
<!-- Осевые линии вида сверху -->
<line x1="72" y1="212" x2="198" y2="212" class="center-line" />
<line x1="135" y1="149" x2="135" y2="275" class="center-line" />
{radial_cl_svg}

<!-- Окружность центров крепежных отверстий Ø40 -->
<circle cx="135" cy="212" r="20" class="center-line" />

<!-- Окружность оснований пазов Ø52 -->
<circle cx="135" cy="212" r="26" class="center-line" />

<!-- Выноска блокировочных дуг выстоя (вверху справа) -->
<path d="M 153.8 179.5 L 175 155 L 225 155" class="leader" marker-start="url(#dot)" />
<text x="200" y="153.5" class="dim-text">6 выемок R22,5</text>
<text x="200" y="159.5" class="dim-text" font-size="2.8px">дуга блокировки</text>

<!-- Выноска центрального отверстия под подшипник (вверху слева) -->
<path d="M 127.2 204.2 L 95 168 L 40 168" class="leader" marker-start="url(#dot)" />
<text x="67.5" y="166.0" class="dim-text">Отв. под подшипник 608ZZ</text>
<text x="67.5" y="172.0" class="dim-text" font-size="2.8px">Ø22,1+0,1 (посадка с натягом)</text>

<!-- Выноска радиальных пазов (слева, ниже стрелки сечения А) -->
<path d="M 98 214.75 L 80 227 L 30 227" class="leader" marker-start="url(#dot)" />
<text x="55.0" y="225.0" class="dim-text">6 пазов шир. 5,5</text>
<text x="55.0" y="231.0" class="dim-text" font-size="2.8px">глубина 26*</text>

<!-- Выноска крепежных отверстий к ротору (внизу слева) -->
<path d="M 125 229.3 L 105 262 L 40 262" class="leader" marker-start="url(#dot)" />
<text x="72.5" y="260.0" class="dim-text">6 отв. Ø3,2 на Ø40*</text>
<text x="72.5" y="266.0" class="dim-text" font-size="2.8px">крепление к ротору (винт М3)</text>

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
    notes = [
        "1. * Размеры для справок.",
        "2. Число пазов: z = 6.",
        "3. Материал: PETG (допускается контакт с пищевыми продуктами).",
        "4. Параметры печати: заполнение 50%, 4 периметра.",
        "5. Центральное отверстие Ø22,1+0,1 — посадочное место подшипника 608ZZ (ГОСТ 8338-75).",
        "6. Отверстия Ø3,2 предназначены для соединения винтами М3 с ротором ВЧ.01.00.002.",
        "7. Острые кромки притупить R 0.5."
    ]
    generate_geneva_wheel_drawing(notes=notes)

