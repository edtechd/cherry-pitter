#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_horizontal_crankshaft.py
Поз. 5: Колесо зубчатое коническое с кривошипом (Horizontal Bevel Gear with Crank Pin)
Спроектировано под привод от колеса geneva_driver (z = 40, m = 2.0 мм, u = 1:1, Σ = 90°).
Оснащено встроенным кривошипным пальцем R = 18.0 мм для обеспечения рабочего хода штока 36.0 мм.
Оформление рабочего чертежа с диаметральным разрезом А-А и размерами по ГОСТ (ЕСКД) и FREECAD.txt.
"""

import sys
import os
import math
from freecad_utils import (
    FreeCAD, Part, TechDraw, TechDrawGui,
    make_box, make_cylinder, rot_z,
    create_drawing_page, add_part_view,
    fill_gost_title_block, export_drawing
)

def create_horizontal_crankshaft():
    """
    Constructs the Horizontal Crankshaft Bevel Gear B-Rep solid along local Z-axis.
    - Bevel gear rim: z = 40, m = 2.0 mm, pitch diameter d = 80.0 mm, delta = 45 deg,
      face width b = 7.0 mm, outer diameter da = 82.83 mm (Ra = 41.414 mm),
      inner diameter d_inner = 70.10 mm (R_inner = 35.050 mm).
    - Disc body: thickness 8.0 mm (Z in [0, 8.0]).
    - Central hole: Ø22.1 mm (+0.1 mm tolerance) through for 608ZZ bearing (8x22x7 mm).
    - No protruding hub (monolithic gear disc).
    - Crank pin: on front face (Z in [8.0, 16.0]), at R = 18.0 mm (X = -18.0, Y = 0.0),
      Ø3.0 mm, height 8.0 mm, for SI3T/K rod end bearing connection. Provides stroke = 36.0 mm.
    """
    m = 2.0
    z = 40
    r_pitch = (m * z) / 2.0  # 40.0 mm
    delta = math.radians(45.0)
    face_width = 7.0
    r_outer = r_pitch + m * math.cos(delta)  # 41.414 mm
    r_inner = r_pitch - face_width * math.sin(delta)  # 35.050 mm
    z_apex = 8.0 + r_inner  # 43.05 mm

    # 1. Base disc blank (Z in [0, 8.0]) with conical bevel on outer rim
    disc_center = make_cylinder(r_inner, 8.0, (0, 0, 0))
    cone_outer = Part.makeCone(
        r_outer + 2.0, 0.0, r_outer + 2.0,
        FreeCAD.Vector(0, 0, z_apex - (r_outer + 2.0)),
        FreeCAD.Vector(0, 0, 1)
    )
    disc_blank = make_cylinder(r_outer, 8.0, (0, 0, 0)).common(cone_outer)
    gear_body = disc_center.fuse(disc_blank)

    # 2. 40 straight bevel tooth space cutters
    cutters = []
    for i in range(z):
        ang = i * (360.0 / z)
        c_box = make_box(12.0, 2.5, 6.0, (33.0, -1.25, 0.0))
        c_box = c_box.rotate(FreeCAD.Vector(38.0, 0, 5.0), FreeCAD.Vector(0, 1, 0), -45.0)
        c_box = rot_z(c_box, ang, (0, 0, 0))
        cutters.append(c_box)

    all_cutters = Part.makeCompound(cutters)
    gear = gear_body.cut(all_cutters)

    # 3. Crank pin on front face at R = 18.0 mm (X = -18.0, Y = 0.0, Z in [8.0, 16.0]), Ø3.0 mm, height 8.0 mm
    pin = make_cylinder(1.5, 8.0, (-18.0, 0, 8.0))
    gear = gear.fuse(pin)

    # 4. Central hole for 608ZZ bearing (Ø22.1 mm through, Z in [-2.0, 10.0])
    bearing_seat_r = (22.0 + 0.1) / 2.0  # 11.05 mm
    bore = make_cylinder(bearing_seat_r, 12.0, (0, 0, -2.0))
    gear = gear.cut(bore)

    if not gear.isValid():
        print("WARNING: Horizontal crankshaft gear shape is topologically invalid!")

    return gear

create_part = create_horizontal_crankshaft

def generate_horizontal_crankshaft_drawing(part_name="part_horizontal_crankshaft",
                                           doc_code="ВЧ.01.00.005",
                                           title_name="Колесо зубчатое с кривошипом",
                                           material="PETG",
                                           scale=1.0,
                                           sheet="A3_Landscape",
                                           notes=None):
    """
    Генерирует рабочий чертеж зубчатого колеса с кривошипом по ГОСТ (ЕСКД):
    - Вид сверху с горизонтальной секущей плоскостью А-А;
    - Вертикальный диаметральный разрез А-А в проекционной связи;
    - Аксонометрический вид (изометрия);
    - Нанесение основных линейных, диаметральных и радиальных размеров (ГОСТ 2.307);
    - Штамп по ГОСТ 2.104 и технические требования по ГОСТ 2.316.
    """
    shape = create_horizontal_crankshaft()

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

    # 2. Вертикальный диаметральный разрез А-А
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

<!-- Осевые линии разреза -->
<line x1="135" y1="186" x2="135" y2="230" class="center-line" />
<line x1="117" y1="193" x2="117" y2="212" class="center-line" />

<!-- 1. Радиус кривошипа: 18* (межосевое от центра до пальца) -->
<line x1="117" y1="191" x2="135" y2="191" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="126" y="189.5" class="dim-text">18*</text>

<!-- 2. Выноска диаметра пальца: Ø3 -->
<path d="M 117 201 L 102 192 L 85 192" class="leader" marker-start="url(#dot)" />
<text x="93.5" y="190.5" class="dim-text">Ø3</text>

<!-- 3. Наружный диаметр по вершинам зубьев: Ø82,8* -->
<line x1="93.6" y1="215" x2="93.6" y2="238" class="dim-ext" />
<line x1="176.4" y1="215" x2="176.4" y2="238" class="dim-ext" />
<line x1="93.6" y1="235" x2="176.4" y2="235" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="135" y="233.5" class="dim-text">Ø82,8*</text>

<!-- 4. Посадочное отверстие подшипника 608ZZ: Ø22,1+0,1 -->
<line x1="123.95" y1="215" x2="123.95" y2="228" class="dim-ext" />
<line x1="146.05" y1="215" x2="146.05" y2="228" class="dim-ext" />
<line x1="123.95" y1="225" x2="146.05" y2="225" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="135" y="223.5" class="dim-text">Ø22,1<tspan font-size="2.4px" dy="-1.5px">+0,1</tspan></text>

<!-- 5. Высота пальца кривошипа: 8 -->
<line x1="115.5" y1="199" x2="100" y2="199" class="dim-ext" />
<line x1="115.5" y1="207" x2="100" y2="207" class="dim-ext" />
<line x1="103" y1="199" x2="103" y2="207" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="101" y="204" transform="rotate(-90 101 204)" class="dim-text">8</text>

<!-- 6. Толщина диска венца: 8 (вынос справа) -->
<line x1="176.4" y1="207" x2="186" y2="207" class="dim-ext" />
<line x1="176.4" y1="215" x2="186" y2="215" class="dim-ext" />
<line x1="183" y1="201" x2="183" y2="207" class="dim-line" marker-end="url(#arrow)" />
<line x1="183" y1="221" x2="183" y2="215" class="dim-line" marker-end="url(#arrow)" />
<line x1="183" y1="207" x2="183" y2="215" class="dim-line" />
<line x1="183" y1="215" x2="190" y2="215" class="dim-line" />
<text x="186.5" y="213.5" class="dim-text">8</text>

<!-- 7. Выноска отверстия подшипника 608ZZ на разрезе -->
<path d="M 146 211 L 162 201 L 195 201" class="leader" marker-start="url(#dot)" />
<text x="178.5" y="199.5" class="dim-text">Подшипник 608ZZ</text>

<!-- ==================== ВИД СВЕРХУ ==================== -->
<!-- Осевые линии вида сверху -->
<line x1="135" y1="47" x2="135" y2="147" class="center-line" />
<line x1="85" y1="97" x2="185" y2="97" class="center-line" />
<line x1="117" y1="88" x2="117" y2="106" class="center-line" />

<!-- Окружность траектории пальца R18 (PCD 36) -->
<circle cx="135" cy="97" r="18" class="center-line" />

<!-- Делительная окружность конического венца d = 80 (r = 40) -->
<circle cx="135" cy="97" r="40" class="center-line" />

<!-- Окружность отверстия подшипника Ø22.1 (r = 11.05) -->
<circle cx="135" cy="97" r="11.05" class="center-line" />

<!-- Выноска пальца кривошипа (вверху слева) -->
<path d="M 115.5 95.5 L 90 62 L 20 62" class="leader" marker-start="url(#dot)" />
<text x="55" y="60" class="dim-text">Палец кривошипа Ø3 (h = 8)</text>
<text x="55" y="66" class="dim-text" font-size="2.8px">R18* (ход штока 36* мм)</text>

<!-- Выноска зубчатого венца (внизу справа) -->
<path d="M 172 110 L 195 125 L 255 125" class="leader" marker-start="url(#dot)" />
<text x="225" y="123" class="dim-text">Венец z = 40, m = 2,0</text>
<text x="225" y="129" class="dim-text" font-size="2.8px">δ = 45°, d = 80,0* (конич. 1:1)</text>

<!-- Выноска отверстия подшипника 608ZZ (вверху справа) -->
<path d="M 143 89 L 165 68 L 245 68" class="leader" marker-start="url(#dot)" />
<text x="205" y="66" class="dim-text">Отв. под подшипник 608ZZ</text>
<text x="205" y="72" class="dim-text" font-size="2.8px">Ø22,1+0,1 (посадка 8х22х7)</text>

<!-- ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ -->
{notes_svg}

</svg>'''

    sym_dim = doc.addObject('TechDraw::DrawViewSymbol', 'OverlayDimensions')
    sym_dim.Symbol = svg_dim
    page.addView(sym_dim)
    doc.recompute()

    # Масштабный коэффициент устранения расхождения DPI QtSvg (90 DPI vs 96 DPI FreeCAD) per FREECAD.txt
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
        "2. Параметры зубчатого венца: z = 40, m = 2,0 мм, δ = 45°, d = 80,0* мм.",
        "3. Передаточное отношение конической передачи u = 1:1, угол осей Σ = 90°.",
        "4. Радиус кривошипа R = 18,0* мм (обеспечивает ход штока 36,0* мм).",
        "5. Палец кривошипа Ø3 мм — под сферический шарнир SI3T/K (ГОСТ ISO 12240-4).",
        "6. Центральное отверстие Ø22,1+0,1 — посадочное место подшипника 608ZZ (ГОСТ 8338-75).",
        "7. Материал: PETG. Параметры 3D-печати: заполнение не менее 50%, 4 периметра.",
        "8. Неуказанные предельные отклонения: ±IT14/2. Острые кромки притупить R 0.5."
    ]
    generate_horizontal_crankshaft_drawing(notes=notes)


