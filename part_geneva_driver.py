#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_geneva_driver.py
Поз. 4: Колесо ведущее мальтийского механизма с коническим зубчатым венцом (Geneva Driver with Bevel Gear)
Доработано:
- Толщина нижнего диска увеличена с 4 мм до 8 мм;
- Сквозное отверстие под вал удалено (монолитная ступица);
- Добавлено 4 глухих отверстия М4 глубиной 5 мм с нижней плоскости под крепление коннектора;
- Диаметр диска увеличен до d_a = 82.8 мм под нарезку конического зубчатого венца;
- Рассчитан и нарезан конический зубчатый венец (z = 40, m = 2.0 мм, δ = 45°, передача 1:1, Σ = 90°);
- Разрез А-А, размеры и оформление по ГОСТ (ЕСКД).
"""

import sys
import os
import math
from freecad_utils import (
    FreeCAD, Part, TechDraw, TechDrawGui,
    make_box, make_cylinder, make_cone, trans, rot_z,
    make_involute_bevel_gear,
    create_drawing_page, add_part_view,
    fill_gost_title_block, export_drawing
)

def create_geneva_driver():
    """
    Constructs the Geneva Driver with integrated Involute Bevel Gear at local origin (0,0,0).
    Generated via freecad.gears addon:
    - Base disc / Involute bevel gear rim: m = 2.0, z = 40, pitch diameter d = 80.0 mm,
      pitch cone angle delta = 45 deg, face height = 8.0 mm (Z in [0, 8.0]),
      backlash = 0.05 mm, clearance = 0.1, pressure angle = 20 deg.
    - 4 Blind M4 mounting holes at R = 12.0 mm (PCD 24 mm), depth 5.0 mm from Z = 0.
    - Locking cam: Z in [8.0, 14.0], R = 22.0 mm, height 6.0 mm, 240 deg dwell arc.
    - Driver pin: at R = 30.0 mm (X = -30.0, Y = 0), Ø5.0 mm, total height 16.0 mm (Z in [0, 16.0]).
    - Apex of pitch cone: Z_apex = 40.0 mm along rotation axis.
    """
    # 1. Involute bevel gear solid using freecad.gears addon
    gear = make_involute_bevel_gear(
        module=2.0,
        num_teeth=40,
        height=8.0,
        pitch_angle=45.0,
        pressure_angle=20.0,
        clearance=0.1,
        backlash=0.05,
        beta=0.0,
        reset_origin=True
    )

    # 2. Locking cam (Z in [8.0, 14.0], R = 22.0 mm, height 6.0 mm above disc)
    cam = make_cylinder(22.0, 6.0, (0, 0, 8.0))
    wedge_cut = make_box(30.0, 30.0, 10.0, (-25.0, -15.0, 7.0))
    cam = cam.cut(wedge_cut)
    gear = gear.fuse(cam)

    # 3. Drive pin at R = 30.0 mm (Z in [0, 16.0], R = 2.5 mm -> Ø5.0 mm)
    pin = make_cylinder(2.5, 16.0, (-30.0, 0, 0))
    gear = gear.fuse(pin)

    # 4. 4 Blind M4 mounting holes from bottom face (Z in [0, 5.0], radius 1.7 mm)
    for ang in [0, 90, 180, 270]:
        rad = math.radians(ang)
        hole = make_cylinder(1.7, 5.5, (12.0 * math.cos(rad), 12.0 * math.sin(rad), -0.5))
        gear = gear.cut(hole)

    if not gear.isValid():
        print("WARNING: Geneva driver shape is topologically invalid!")

    return gear

create_part = create_geneva_driver

def generate_geneva_driver_drawing(part_name="part_geneva_driver",
                                   doc_code="ВЧ.01.00.004",
                                   title_name="Колесо ведущее коническое",
                                   material="PETG",
                                   scale=1.0,
                                   sheet="A3_Landscape",
                                   notes=None):
    """
    Генерирует рабочий чертеж ведущего колеса с коническим венцом по ГОСТ (ЕСКД):
    - Вид сверху с секущей плоскостью А-А;
    - Вертикальный разрез А-А вместо вида спереди;
    - Аксонометрический вид (изометрия);
    - Нанесение основных линейных, диаметральных и радиальных размеров (ГОСТ 2.307);
    - Штамп по ГОСТ 2.104 и технические требования по ГОСТ 2.316.
    """
    shape = create_geneva_driver()
    
    doc = FreeCAD.newDocument(f"Doc_{part_name}")
    feat = doc.addObject("Part::Feature", part_name)
    feat.Shape = shape
    doc.recompute()
    
    page, template = create_drawing_page(doc, sheet, f"Page_{part_name}")
    
    # Координаты для формата А3 (420 x 297 мм)
    x_c = 135.0
    y_top_td = 200.0   # TopView вверху чертежа (SVG cy = 97.0)
    y_sec_td = 90.0    # Разрез А-А внизу в проекционной связи (SVG cy = 207.0)
    
    # 1. Вид сверху (Top View с секущей линией А-А)
    v_top = add_part_view(doc, page, feat, "TopView", (0, 0, 1), scale, x_c, y_top_td)
    
    # 2. Вертикальный разрез А-А (вместо вида спереди)
    sec = doc.addObject("TechDraw::DrawViewSection", "SectionView")
    sec.BaseView = v_top
    sec.SectionNormal = FreeCAD.Vector(0.0, -1.0, 0.0)
    sec.SectionOrigin = FreeCAD.Vector(0.0, 0.0, 4.0)
    sec.SectionDirection = "Down"
    sec.SectionSymbol = "A"
    page.addView(sec)
    doc.recompute()
    
    sec.Direction = FreeCAD.Vector(0.0, -1.0, 0.0)
    sec.XDirection = FreeCAD.Vector(1.0, 0.0, 0.0)
    sec.Rotation = 0.0
    sec.X = x_c
    sec.Y = y_sec_td
    sec.IsoCount = 0
    sec.ViewObject.HatchColor = (0.0, 0.0, 0.0, 1.0)
    doc.recompute()
    
    # 3. Аксонометрический вид (Iso View)
    add_part_view(doc, page, feat, "IsoView", (1.0, -1.2, 0.9), 0.85, 315.0, 200.0)
    
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
    
    # 5. Технические требования (ГОСТ 2.316) над основной надписью
    notes_svg = ""
    if notes:
        notes_lines = ['<text x="215" y="135" font-family="osifont, Arial, sans-serif" font-size="3.6px" font-weight="bold" fill="#000">Технические требования:</text>']
        for idx, line in enumerate(notes):
            notes_lines.append(f'<text x="215" y="{142 + idx * 5.6}" font-family="osifont, Arial, sans-serif" font-size="3.1px" fill="#000">{line}</text>')
        notes_svg = '\n'.join(notes_lines)
        
    # 6. Векторный оверлей размеров и выносок (ГОСТ 2.307)
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

<!-- ==================== РАЗРЕЗ А-А ==================== -->
<text x="135" y="180" class="view-title">А-А</text>

<!-- Осевые линии -->
<line x1="135" y1="184" x2="135" y2="228" class="center-line" />
<line x1="105" y1="193" x2="105" y2="228" class="center-line" />
<line x1="123" y1="208" x2="123" y2="217" class="center-line" />
<line x1="147" y1="208" x2="147" y2="217" class="center-line" />

<!-- 1. Межосевое расстояние цевки: 30* -->
<line x1="105" y1="224" x2="135" y2="224" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="120" y="222.5" class="dim-text">30*</text>

<!-- 2. Наружный диаметр диска по вершинам зубьев: Ø82,8* -->
<line x1="93.6" y1="215" x2="93.6" y2="238" class="dim-ext" />
<line x1="176.4" y1="215" x2="176.4" y2="238" class="dim-ext" />
<line x1="93.6" y1="235" x2="176.4" y2="235" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="135" y="233.5" class="dim-text">Ø82,8*</text>

<!-- 3. Диаметр цевки: Ø5 -->
<line x1="102.5" y1="199" x2="102.5" y2="188" class="dim-ext" />
<line x1="107.5" y1="199" x2="107.5" y2="188" class="dim-ext" />
<line x1="94" y1="191" x2="102.5" y2="191" class="dim-line" marker-end="url(#arrow)" />
<line x1="116" y1="191" x2="107.5" y2="191" class="dim-line" marker-end="url(#arrow)" />
<line x1="102.5" y1="191" x2="107.5" y2="191" class="dim-line" />
<text x="105" y="188.0" class="dim-text">Ø5</text>

<!-- 4. Высота цевки полная: 16 -->
<line x1="102.5" y1="199" x2="82" y2="199" class="dim-ext" />
<line x1="93.6" y1="215" x2="82" y2="215" class="dim-ext" />
<line x1="85" y1="199" x2="85" y2="215" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="83" y="208" transform="rotate(-90 83 208)\" class="dim-text">16</text>

<!-- 5. Толщина нижнего диска: 8 (выносная полка справа) -->
<line x1="176.4" y1="207" x2="184" y2="207" class="dim-ext" />
<line x1="176.4" y1="215" x2="184" y2="215" class="dim-ext" />
<line x1="182" y1="201" x2="182" y2="207" class="dim-line" marker-end="url(#arrow)" />
<line x1="182" y1="221" x2="182" y2="215" class="dim-line" marker-end="url(#arrow)" />
<line x1="182" y1="207" x2="182" y2="215" class="dim-line" />
<line x1="182" y1="215" x2="189" y2="215" class="dim-line" />
<text x="185.5" y="213.5" class="dim-text">8</text>

<!-- 6. Высота кулачка общая: 14 -->
<line x1="157" y1="201" x2="196" y2="201" class="dim-ext" />
<line x1="176.4" y1="215" x2="196" y2="215" class="dim-ext" />
<line x1="193" y1="201" x2="193" y2="215" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="191" y="209" transform="rotate(-90 191 209)" class="dim-text">14</text>

<!-- 7. Выноска глухих отверстий М4 (снизу справа) -->
<path d="M 147 212.5 L 165 224 L 210 224" class="leader" marker-start="url(#dot)" />
<text x="187.5" y="222.0" class="dim-text">4 отв. М4 глуб. 5</text>
<text x="187.5" y="227.5" class="dim-text" font-size="2.8px">на Ø24* (под коннектор)</text>

<!-- ==================== ВИД СВЕРХУ ==================== -->
<line x1="135" y1="50" x2="135" y2="144" class="center-line" />
<line x1="105" y1="82" x2="105" y2="112" class="center-line" />

<!-- Окружность траектории цевки R30 -->
<circle cx="135" cy="97" r="30" class="center-line" />

<!-- Окружность отверстий крепления Ø24 -->
<circle cx="135" cy="97" r="12" class="center-line" />

<!-- Делительная окружность конического венца d = 80 (r = 40) -->
<circle cx="135" cy="97" r="40" class="center-line" />

<!-- Выноска цевки (вверху слева) -->
<path d="M 103.2 95.2 L 80 65 L 20 65" class="leader" marker-start="url(#dot)" />
<text x="50" y="63" class="dim-text">Цевка Ø5 (h = 16)</text>
<text x="50" y="69" class="dim-text" font-size="2.8px">R30* (траектория)</text>

<!-- Выноска кулачка выстоя (вверху справа) -->
<path d="M 152 86 L 175 62 L 235 62" class="leader" marker-start="url(#dot)" />
<text x="205" y="60" class="dim-text">Кулачок выстоя R22*</text>
<text x="205" y="66" class="dim-text" font-size="2.8px">дуга выстоя 240° (h = 6)</text>

<!-- Выноска зубчатого венца (внизу справа) -->
<path d="M 172 110 L 195 125 L 255 125" class="leader" marker-start="url(#dot)" />
<text x="225" y="123" class="dim-text">Венец z = 40, m = 2,0</text>
<text x="225" y="129" class="dim-text" font-size="2.8px">δ = 45°, d = 80,0* (конич. 1:1)</text>

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
        "2. Зубчатый венец: конический эвольвентный (freecad.gears, ГОСТ 12289).",
        "   Параметры: z = 40, m = 2,0 мм, δ = 45°, d = 80,0* мм, h = 8,0 мм.",
        "3. Передаточное отношение конической передачи u = 1:1, угол осей Σ = 90°.",
        "4. Радиус расположения цевки: R = 30,0* мм.",
        "5. Диаметр кулачка выстоя: Ø44,0* мм (дуга выстоя 240°).",
        "6. 4 отв. М4 глуб. 5 мм — под винты крепления фланца ВЧ.00.00.011.",
        "7. Материал: PETG. Параметры 3D-печати: заполнение 50%, 4 периметра.",
        "8. Неуказанные предельные отклонения: ±IT14/2. Острые кромки притупить R 0.5."
    ]
    generate_geneva_driver_drawing(notes=notes)
