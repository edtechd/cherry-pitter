#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_flange_coupling.py
Поз. 18: Фланец переходный жесткий (Rigid Flange Coupling Connector ID: 8mm)
Стандартное изделие для передачи крутящего момента от вала привода к ведущему колесу мальтийского механизма.
"""

import sys
import os
import math
from freecad_utils import (
    FreeCAD, Part, TechDraw, TechDrawGui,
    make_cylinder, make_box,
    create_drawing_page, add_part_view,
    fill_gost_title_block, export_drawing
)

def create_flange_coupling():
    """
    Constructs the 8mm Rigid Flange Coupling connector at local origin (0,0,0).
    - Base flange: Ø32.0 mm, thickness 3.0 mm (Z in [0, 3.0])
    - Cylindrical hub: Ø16.0 mm, height 10.0 mm (Z in [3.0, 13.0], total height 13.0 mm)
    - Central bore: Ø8.0 mm through
    - 4 mounting holes: Ø4.2 mm on PCD Ø24.0 mm for M4 screws
    - 2 set screw holes: M4 radial threaded holes at 90 deg on the hub
    """
    # 1. Base flange (Ø32 mm, thickness 3 mm)
    flange = make_cylinder(16.0, 3.0, (0, 0, 0))
    
    # 2. Cylindrical hub (Ø16 mm, height 10 mm)
    hub = make_cylinder(8.0, 10.0, (0, 0, 3.0))
    coupling = flange.fuse(hub)
    
    # 3. Central shaft bore (Ø8 mm through)
    bore = make_cylinder(4.0, 15.0, (0, 0, -1.0))
    coupling = coupling.cut(bore)
    
    # 4. 4 Flange mounting holes (Ø4.2 mm on PCD 24 mm)
    for ang in [0, 90, 180, 270]:
        rad = math.radians(ang)
        hole = make_cylinder(2.1, 5.0, (12.0 * math.cos(rad), 12.0 * math.sin(rad), -1.0))
        coupling = coupling.cut(hole)
        
    # 5. 2 M4 radial set screw holes on the hub (at Z = 8.0 mm, 90 deg apart)
    for ang in [45, 135]:
        rad = math.radians(ang)
        set_screw = Part.makeCylinder(2.0, 10.0, FreeCAD.Vector(0, 0, 8.0), FreeCAD.Vector(math.cos(rad), math.sin(rad), 0))
        coupling = coupling.cut(set_screw)
        
    if not coupling.isValid():
        print("WARNING: Flange coupling shape is topologically invalid!")
        
    return coupling

create_part = create_flange_coupling

def generate_flange_coupling_drawing(part_name="part_flange_coupling",
                                     doc_code="ВЧ.00.00.011",
                                     title_name="Фланец переходный",
                                     material="Сталь 45 оцинк.",
                                     scale=2.0,
                                     sheet="A3_Landscape",
                                     notes=None):
    """
    Генерирует рабочий чертеж фланцевого коннектора по ГОСТ (ЕСКД):
    - Вид сверху с секущей плоскостью А-А;
    - Вертикальный разрез А-А вместо вида спереди;
    - Аксонометрический вид (изометрия);
    - Нанесение основных размеров и выносок (ГОСТ 2.307);
    - Штамп по ГОСТ 2.104 и технические требования по ГОСТ 2.316.
    """
    shape = create_flange_coupling()
    
    doc = FreeCAD.newDocument(f"Doc_{part_name}")
    feat = doc.addObject("Part::Feature", part_name)
    feat.Shape = shape
    doc.recompute()
    
    page, template = create_drawing_page(doc, sheet, f"Page_{part_name}")
    
    # Координаты для формата А3 (масштаб 2:1)
    x_c = 135.0
    y_top_td = 200.0   # SVG y = 97.0
    y_sec_td = 90.0    # SVG y = 207.0
    
    # 1. Вид сверху (Top View с секущей линией А-А)
    v_top = add_part_view(doc, page, feat, "TopView", (0, 0, 1), scale, x_c, y_top_td)
    
    # 2. Вертикальный диаметральный разрез А-А
    sec = doc.addObject("TechDraw::DrawViewSection", "SectionView")
    sec.BaseView = v_top
    sec.SectionNormal = FreeCAD.Vector(0.0, -1.0, 0.0)
    sec.SectionOrigin = FreeCAD.Vector(0.0, 0.0, 1.5)
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
    add_part_view(doc, page, feat, "IsoView", (1.0, -1.2, 0.9), 1.8, 315.0, 200.0)
    
    # 4. Основная надпись (штамп ГОСТ 2.104)
    title_fields = {
        'Номер': doc_code,
        'Название': title_name,
        'Масштаб': f"{int(scale)}:1" if scale >= 1 else f"1:{int(1/scale)}",
        'Лист': '1',
        'Листов': '1',
        'Материал1': 'Сталь 45',
        'Материал2': 'оцинк.',
        'Материал3': '',
        'Организация1': 'Проект VISHNI',
        'Организация2': '',
        'Разработал': 'Инженер',
        'Проверил': 'Контролер'
    }
    fill_gost_title_block(template, title_fields)
    doc.recompute()
    
    # 5. Технические требования (ГОСТ 2.316)
    notes_svg = ""
    if notes:
        notes_lines = ['<text x="230" y="145" font-family="osifont, Arial, sans-serif" font-size="3.6px" font-weight="bold" fill="#000">Технические требования:</text>']
        for idx, line in enumerate(notes):
            notes_lines.append(f'<text x="230" y="{152 + idx * 5.8}" font-family="osifont, Arial, sans-serif" font-size="3.2px" fill="#000">{line}</text>')
        notes_svg = '\n'.join(notes_lines)
        
    # 6. Векторный оверлей размеров и надписей (ГОСТ 2.307)
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
<text x="135" y="168" class="view-title">А-А</text>

<!-- Осевые линии разреза -->
<line x1="135" y1="172" x2="135" y2="226" class="center-line" />
<line x1="111" y1="210" x2="111" y2="224" class="center-line" />
<line x1="159" y1="210" x2="159" y2="224" class="center-line" />

<!-- 1. Ø16 (ступица) -->
<line x1="119" y1="194" x2="119" y2="174" class="dim-ext" />
<line x1="151" y1="194" x2="151" y2="174" class="dim-ext" />
<line x1="119" y1="176" x2="151" y2="176" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="135" y="174.5" class="dim-text">Ø16</text>

<!-- 2. Ø8 (отверстие) -->
<line x1="127" y1="194" x2="127" y2="183" class="dim-ext" />
<line x1="143" y1="194" x2="143" y2="183" class="dim-ext" />
<line x1="127" y1="185" x2="143" y2="185" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="135" y="183.5" class="dim-text">Ø8H8</text>

<!-- 3. Ø32 (фланец) -->
<line x1="103" y1="220" x2="103" y2="234" class="dim-ext" />
<line x1="167" y1="220" x2="167" y2="234" class="dim-ext" />
<line x1="103" y1="231" x2="167" y2="231" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="135" y="229.5" class="dim-text">Ø32</text>

<!-- 4. Высота общая 13 -->
<line x1="119" y1="194" x2="90" y2="194" class="dim-ext" />
<line x1="103" y1="220" x2="90" y2="220" class="dim-ext" />
<line x1="93" y1="194" x2="93" y2="220" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="90" y="207" transform="rotate(-90 90 207)" class="dim-text">13</text>

<!-- 5. Толщина фланца 3 -->
<line x1="167" y1="214" x2="177" y2="214" class="dim-ext" />
<line x1="167" y1="220" x2="177" y2="220" class="dim-ext" />
<line x1="175" y1="209" x2="175" y2="214" class="dim-line" marker-end="url(#arrow)" />
<line x1="175" y1="225" x2="175" y2="220" class="dim-line" marker-end="url(#arrow)" />
<line x1="175" y1="214" x2="175" y2="220" class="dim-line" />
<line x1="175" y1="220" x2="181" y2="220" class="dim-line" />
<text x="178" y="218.5" class="dim-text">3</text>

<!-- 6. Высота ступицы 10 -->
<line x1="151" y1="194" x2="188" y2="194" class="dim-ext" />
<line x1="167" y1="214" x2="188" y2="214" class="dim-ext" />
<line x1="185" y1="194" x2="185" y2="214" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="188" y="204" transform="rotate(-90 188 204)" class="dim-text">10</text>

<!-- ==================== ВИД СВЕРХУ ==================== -->
<line x1="135" y1="60" x2="135" y2="134" class="center-line" />
<line x1="98" y1="97" x2="172" y2="97" class="center-line" />
<circle cx="135" cy="97" r="24" class="center-line" />

<line x1="111" y1="93" x2="111" y2="101" class="center-line" />
<line x1="159" y1="93" x2="159" y2="101" class="center-line" />
<line x1="131" y1="73" x2="139" y2="73" class="center-line" />
<line x1="131" y1="121" x2="139" y2="121" class="center-line" />

<!-- Выноска отверстий фланца -->
<path d="M 111 73 L 85 55 L 25 55" class="leader" marker-start="url(#dot)" />
<text x="55" y="53" class="dim-text">4 отв. Ø4,2</text>
<text x="55" y="59" class="dim-text" font-size="2.8px">на Ø24* (под винты М4)</text>

<!-- Выноска отверстий ступицы -->
<path d="M 146.3 85.7 L 175 65 L 235 65" class="leader" marker-start="url(#dot)" />
<text x="205" y="63" class="dim-text">2 отв. М4 (установочные)</text>
<text x="205" y="69" class="dim-text" font-size="2.8px">угол между осями 90°</text>

<!-- ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ -->
{notes_svg}

</svg>'''

    sym_dim = doc.addObject('TechDraw::DrawViewSymbol', 'OverlayDimensions')
    sym_dim.Symbol = svg_dim
    page.addView(sym_dim)
    doc.recompute()
    
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
        "2. Материал: Сталь 45 ГОСТ 1050-88.",
        "3. Покрытие: Ц9.хр ГОСТ 9.301-86.",
        "4. Резьба метрическая: М4-7H ГОСТ 24705-2004.",
        "5. Неуказанные предельные отклонения: ±IT14/2.",
        "6. Острые кромки притупить R 0.3."
    ]
    generate_flange_coupling_drawing(notes=notes)
