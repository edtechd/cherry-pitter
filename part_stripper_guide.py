#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_stripper_guide.py
Поз. 8: Стойка направляющей MGN9-100 (Stripper Guide Tower for MGN9 Rail)
Создание аналитической B-Rep 3D-модели и оформление рабочего чертежа по ГОСТ (ЕСКД).
"""

import sys
import os
import math

# Пути FreeCAD и рабочей директории
sys.path.append('/usr/lib/freecad/lib')
sys.path.append('/usr/share/freecad/Mod/TechDraw')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide2 import QtWidgets
app = QtWidgets.QApplication.instance()
if not app:
    app = QtWidgets.QApplication(['FreeCAD', '-platform', 'offscreen'])

import FreeCAD
import FreeCADGui
if hasattr(FreeCADGui, "showMainWindow"):
    FreeCADGui.showMainWindow()

import Part
import TechDraw
import TechDrawGui

from freecad_utils import (
    make_box, make_cylinder,
    create_drawing_page, add_part_view,
    fill_gost_title_block, export_drawing
)


def create_stripper_guide():
    """
    Создает аналитический B-Rep солид стойки для направляющей рельсы MGN9-100:
    - Нижний фланец крепления к плите основания: 60.0 x 28.0 x 10.0 мм (Z in [0, 10.0]);
      Крепежные отверстия 2x Ø4.5 мм под винты M4 при X = ±23.0, Y = -8.0 (межцентровое 46.0 мм);
    - Нижнее тело стойки: 32.0 x 26.0 x 43.0 мм (Z in [0, 43.0], X in [-16, 16], Y in [-18, +8]);
    - Верхнее тело стойки: 32.0 x 18.0 x 100.0 мм (Z in [43.0, 143.0], X in [-16, 16], Y in [-18, 0]);
      На высоте Z = 43.0 мм образуется опорная горизонтальная ступенька («полочка»)
      шириной 32.0 мм и глубиной 8.0 мм под торец рельса MGN9-100;
    - 5 глухих крепежных отверстий M3 (Ø2.5 мм, глубина 10.0 мм) вдоль оси X = 0.0 на плоскости Y = 0.0
      на высотах Z in {50.5, 70.5, 90.5, 110.5, 130.5} мм (E = 7.5 мм от ступеньки, шаг P = 20.0 мм).
    """
    # 1. Опорный базовый фланец (ширина 60.0 мм)
    flange = make_box(60.0, 28.0, 10.0, (-30.0, -20.0, 0))

    # 2. Нижнее тело стойки под ступеньку (Z in [0, 43.0])
    col_lower = make_box(32.0, 26.0, 43.0, (-16.0, -18.0, 0))

    # 3. Верхнее тело стойки (Z in [43.0, 143.0])
    col_upper = make_box(32.0, 18.0, 100.0, (-16.0, -18.0, 43.0))

    tower = flange.fuse(col_lower).fuse(col_upper)

    # 4. Крепежные отверстия фланца к станине (2x Ø4.5 мм, межцентровое 46.0 мм)
    tower = tower.cut(make_cylinder(2.25, 20.0, (-23.0, -8.0, -5.0), (0, 0, 1)))
    tower = tower.cut(make_cylinder(2.25, 20.0, (23.0, -8.0, -5.0), (0, 0, 1)))

    # 5. 5 крепежных отверстий под рельс MGN9-100 (M3 глубина 10 мм, сверло Ø2.5 мм)
    # Отверстия сверлятся в лицевую плоскость Y = 0.0 по направлению -Y
    for dz in [7.5, 27.5, 47.5, 67.5, 87.5]:
        z = 43.0 + dz
        hole = Part.makeCylinder(1.25, 12.0, FreeCAD.Vector(0.0, 1.0, z), FreeCAD.Vector(0, -1, 0))
        tower = tower.cut(hole)

    # 6. 2 сквозных крепежных отверстия под съемник ягод ВЧ.01.00.015 (Z = 56.0 мм, X = ±10.0 мм)
    # Сквозные отверстия Ø3.4 мм через всю стенку 18 мм (от Y = 0.0 до Y = -18.0 мм)
    # с цековками Ø6.5 мм глубиной 4.0 мм со стороны задней стенки (Y = -18.0 мм)
    # под головки винтов DIN 912 M3 или гайки M3 (утоплены заподлицо)
    for x in [-10.0, 10.0]:
        thru_h = Part.makeCylinder(1.7, 22.0, FreeCAD.Vector(x, 1.0, 56.0), FreeCAD.Vector(0, -1, 0))
        cb_rear = Part.makeCylinder(3.25, 5.0, FreeCAD.Vector(x, -19.0, 56.0), FreeCAD.Vector(0, 1, 0))
        tower = tower.cut(thru_h).cut(cb_rear)

    if not tower.isValid():
        raise ValueError("Stripper guide solid shape is invalid!")

    return tower


create_part = create_stripper_guide


def generate_stripper_guide_drawing(part_name="part_stripper_guide",
                                    doc_code="ВЧ.01.00.008",
                                    title_name="Стойка направляющей MGN9",
                                    material="PETG",
                                    scale=1.0,
                                    sheet="A3_Landscape",
                                    notes=None):
    """
    Генерирует рабочий чертеж стойки направляющей MGN9 по ГОСТ (ЕСКД):
    - Вид спереди с показом ступеньки, 5 отверстий M3, фланца;
    - Вертикальный продольный разрез А-А в проекционной связи с показом ступенчатого профиля и отверстий;
    - Вид сверху с секущей плоскостью А-А;
    - Аксонометрический вид (изометрия);
    - Нанесение размеров и выносок (ГОСТ 2.307);
    - Штамп по ГОСТ 2.104 и технические требования по ГОСТ 2.316.
    """
    shape = create_stripper_guide()

    doc = FreeCAD.newDocument(f"Doc_{part_name}")
    feat = doc.addObject("Part::Feature", part_name)
    feat.Shape = shape
    doc.recompute()

    page, template = create_drawing_page(doc, sheet, f"Page_{part_name}")

    # Координаты проекций на формате А3 (420 x 297 мм)
    x_front = 95.0
    y_front_td = 179.0   # SVG Y = 118.0, базовая опорная линия Y = 189.5

    x_sec = 210.0
    y_sec_td = 179.0     # SVG Y = 118.0 (в проекционной связи по горизонтали)

    x_top = 95.0
    y_top_td = 55.0      # SVG Y = 242.0

    x_iso = 330.0
    y_iso_td = 205.0     # SVG Y = 92.0

    # 1. Вид спереди (FrontView) - взгляд на лицевую плоскость монтажа (0, 1, 0)
    v_front = add_part_view(doc, page, feat, "FrontView", (0, 1, 0), scale, x_front, y_front_td)

    # 2. Вид сверху (TopView) - проекция на плоскость XY
    v_top = add_part_view(doc, page, feat, "TopView", (0, 0, 1), scale, x_top, y_top_td)

    # 3. Вертикальный продольный разрез А-А (SectionView)
    sec = doc.addObject("TechDraw::DrawViewSection", "SectionView")
    sec.BaseView = v_top
    sec.SectionNormal = FreeCAD.Vector(1.0, 0.0, 0.0)
    sec.SectionOrigin = FreeCAD.Vector(0.0, 0.0, 0.0)
    sec.SectionDirection = "Left"
    sec.SectionSymbol = "A"
    page.addView(sec)
    doc.recompute()

    sec.Direction = FreeCAD.Vector(-1.0, 0.0, 0.0)
    sec.XDirection = FreeCAD.Vector(0.0, 1.0, 0.0)
    sec.Rotation = 180.0
    sec.CutSurfaceDisplay = "Hide"
    sec.X = x_sec
    sec.Y = y_sec_td
    sec.IsoCount = 0
    doc.recompute()

    # 4. Аксонометрический вид (IsoView)
    v_iso = add_part_view(doc, page, feat, "IsoView", (1.2, -1.5, 1.0), 0.85, x_iso, y_iso_td)

    # 5. Основная надпись (штамп ГОСТ 2.104)
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

    # 6. Технические требования (ГОСТ 2.316) над основной надписью (X in [245, 415])
    if notes is None:
        notes = [
            "1. * Размеры для справок.",
            "2. Стойка предназначена для установки рельса линейной направляющей MGN9-100.",
            "3. Ступенька на высоте 43,0 мм служит опорной базой для нижнего торца рельса.",
            "4. Резьба 5xM3 в отверстиях стойки нарезается метчиком (глубина 10 мм).",
            "5. Крепление съемника ягод ВЧ.01.00.015: 2 сквозных отв. Ø3,4 мм с цековками Ø6,5 глуб. 4,0 мм",
            "   на задней стенке (Z=56, межосевое 20 мм).",
            "6. Крепление к станине: 2 винта M4 (поз. 17), расстояние между осями 46 мм.",
            "7. Материал: PETG. Заполнение не менее 50%, количество периметров — не менее 4.",
            "8. Неуказанные предельные отклонения: ±IT14/2. Острые кромки притупить R 0.5."
        ]

    notes_lines = ['<text x="245" y="85" font-family="osifont, Arial, sans-serif" font-size="3.5px" font-weight="bold" fill="#000">Технические требования:</text>']
    for idx, line in enumerate(notes):
        notes_lines.append(f'<text x="245" y="{91.5 + idx * 5.2}" font-family="osifont, Arial, sans-serif" font-size="3.0px" fill="#000">{line}</text>')
    notes_svg = '\n'.join(notes_lines)

    # Генерация тонких линий штриховки под углом 45° по ГОСТ 2.305
    def generate_hatch_lines():
        def in_cut_face(x, y):
            if y < 46.5 or y > 189.5:
                return False
            if y >= 179.5:      # Фланец: X in [196.0, 224.0]
                if not (196.0 <= x <= 224.0):
                    return False
            elif y >= 146.5:    # Нижнее тело стойки: X in [196.0, 222.0]
                if not (196.0 <= x <= 222.0):
                    return False
            else:               # Верхнее тело стойки: X in [204.0, 222.0]
                if not (204.0 <= x <= 222.0):
                    return False
                # Обход 5 крепежных отверстий
                for yc in [59.0, 79.0, 99.0, 119.0, 139.0]:
                    if abs(y - yc) <= 1.25 and 204.0 <= x <= 214.0:
                        return False
                    if abs(y - yc) <= 1.25 and 214.0 < x <= 214.7:
                        if (x - 214.0) / 0.7 <= (1.0 - abs(y - yc) / 1.25):
                            return False
            return True

        lines = []
        for c in [i * 3.0 for i in range(75, 145)]:
            xs = [196.0 + j * 0.1 for j in range(int((225.0 - 196.0) / 0.1))]
            cur_seg = []
            for x in xs:
                y = c - x
                if in_cut_face(x, y):
                    cur_seg.append((x, y))
                else:
                    if len(cur_seg) > 1:
                        lines.append((cur_seg[0], cur_seg[-1]))
                    cur_seg = []
            if len(cur_seg) > 1:
                lines.append((cur_seg[0], cur_seg[-1]))
        return lines

    hatch_lines = generate_hatch_lines()
    hatch_svg = "\n".join([
        f'<line x1="{seg[0][0]:.2f}" y1="{seg[0][1]:.2f}" x2="{seg[1][0]:.2f}" y2="{seg[1][1]:.2f}" class="hatch-line" />'
        for seg in hatch_lines
    ])

    # Отрисовка геометрии 5 резьбовых отверстий в разрезе
    holes_svg_lines = []
    for yc in [59.0, 79.0, 99.0, 119.0, 139.0]:
        y_top = yc - 1.25
        y_bot = yc + 1.25
        holes_svg_lines.append(f'''
<line x1="204" y1="{y_top:.2f}" x2="214" y2="{y_top:.2f}" class="hole-line" />
<line x1="204" y1="{y_bot:.2f}" x2="214" y2="{y_bot:.2f}" class="hole-line" />
<line x1="214" y1="{y_top:.2f}" x2="214.7" y2="{yc:.2f}" class="hole-line" />
<line x1="214" y1="{y_bot:.2f}" x2="214.7" y2="{yc:.2f}" class="hole-line" />
<line x1="204" y1="{yc - 1.5:.2f}" x2="212" y2="{yc - 1.5:.2f}" class="thread-line" />
<line x1="204" y1="{yc + 1.5:.2f}" x2="212" y2="{yc + 1.5:.2f}" class="thread-line" />
<line x1="202" y1="{yc:.2f}" x2="217" y2="{yc:.2f}" class="center-line" />
''')
    holes_sec_svg = "\n".join(holes_svg_lines)

    # 7. Векторный оверлей размеров и выносок (ГОСТ 2.307)
    svg_dim = f'''<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="3.5" markerHeight="3.5" orient="auto-start-reverse">
    <path d="M 0 2 L 10 5 L 0 8 z" fill="#000" />
  </marker>
  <marker id="arrow-rev" viewBox="0 0 10 10" refX="0" refY="5" markerWidth="3.5" markerHeight="3.5" orient="auto-start-reverse">
    <path d="M 10 2 L 0 5 L 10 8 z" fill="#000" />
  </marker>
  <marker id="dot" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="2.5" markerHeight="2.5">
    <circle cx="5" cy="5" r="2.5" fill="#000" />
  </marker>
</defs>
<style>
  .dim-line {{ stroke: #000; stroke-width: 0.35; fill: none; }}
  .dim-ext {{ stroke: #000; stroke-width: 0.25; fill: none; }}
  .center-line {{ stroke: #000; stroke-width: 0.25; stroke-dasharray: 6,1.5,1.5,1.5; fill: none; }}
  .dim-text {{ font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: middle; }}
  .leader {{ stroke: #000; stroke-width: 0.35; fill: none; }}
  .hatch-line {{ stroke: #000; stroke-width: 0.25; fill: none; }}
  .hole-line {{ stroke: #000; stroke-width: 0.5; fill: none; }}
  .thread-line {{ stroke: #000; stroke-width: 0.25; stroke-dasharray: 2,1; fill: none; }}
</style>

<!-- ==================== ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ ==================== -->
{notes_svg}

<!-- ==================== ВИД СПЕРЕДИ (FrontView) ==================== -->
<!-- Осевая линия стойки X = 95.0 -->
<line x1="95" y1="40" x2="95" y2="195" class="center-line" />

<!-- 1. Габаритная высота 143* слева (X = 33) -->
<line x1="65" y1="189.5" x2="30" y2="189.5" class="dim-ext" />
<line x1="79" y1="46.5" x2="30" y2="46.5" class="dim-ext" />
<line x1="33" y1="189.5" x2="33" y2="46.5" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="31" y="80" transform="rotate(-90 31 80)" class="dim-text">143*</text>

<!-- 2. Высота ступеньки 43* слева (X = 48) -->
<line x1="79" y1="146.5" x2="45" y2="146.5" class="dim-ext" />
<line x1="48" y1="189.5" x2="48" y2="146.5" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="46" y="168" transform="rotate(-90 46 168)" class="dim-text">43*</text>

<!-- 3. Ширина стойки 32 сверху -->
<line x1="79" y1="46.5" x2="79" y2="36" class="dim-ext" />
<line x1="111" y1="46.5" x2="111" y2="36" class="dim-ext" />
<line x1="79" y1="38" x2="111" y2="38" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="95" y="36.5" class="dim-text">32</text>

<!-- 4. Ширина фланца 60 снизу -->
<line x1="65" y1="189.5" x2="65" y2="201" class="dim-ext" />
<line x1="125" y1="189.5" x2="125" y2="201" class="dim-ext" />
<line x1="65" y1="199" x2="125" y2="199" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="95" y="197.5" class="dim-text">60</text>

<!-- 5. Межцентровое отверстий фланца 46 -->
<line x1="72" y1="189.5" x2="72" y2="210" class="dim-ext" />
<line x1="118" y1="189.5" x2="118" y2="210" class="dim-ext" />
<line x1="72" y1="208" x2="118" y2="208" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="95" y="206.5" class="dim-text">46</text>

<!-- 6. Выноска отверстий фланца 2 отв. Ø4,5 справа от фланца -->
<path d="M 118 184.5 L 130 184.5 L 160 184.5" class="leader" marker-start="url(#dot)" />
<text x="145" y="183.0" class="dim-text">2 отв. Ø4,5</text>

<!-- 6b. Выноска отверстий крепления съемника 2 отв. Ø3,4 насквозь слева -->
<path d="M 85 133.5 L 75 126 L 45 126" class="leader" marker-start="url(#dot)" />
<text x="65" y="124.5" class="dim-text">2 отв. Ø3,4 насквозь; цек. Ø6,5</text>

<!-- 7. Размеры сетки крепежных отверстий рельса справа от FrontView -->
<!-- Отметка первого отверстия от ступеньки: 7,5 -->
<line x1="95" y1="146.5" x2="120" y2="146.5" class="dim-ext" />
<line x1="95" y1="139.0" x2="120" y2="139.0" class="dim-ext" />
<line x1="118" y1="146.5" x2="118" y2="139.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="115.5" y="143.8" transform="rotate(-90 115.5 143.8)" class="dim-text">7,5</text>

<!-- Суммарный шаг отверстий: 4 x 20 = 80 -->
<line x1="95" y1="59.0" x2="128" y2="59.0" class="dim-ext" />
<line x1="95" y1="139.0" x2="128" y2="139.0" class="dim-ext" />
<line x1="126" y1="139.0" x2="126" y2="59.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="124" y="99.0" transform="rotate(-90 124 99.0)" class="dim-text">4×20=80</text>

<!-- Выноска 5 отв. М3 глуб. 10 вверху -->
<path d="M 95 59.0 L 115 48.0 L 155 48.0" class="leader" marker-start="url(#dot)" />
<text x="135" y="46.5" class="dim-text">5 отв. M3 глуб. 10</text>


<!-- ==================== РАЗРЕЗ А-А (SectionView) ==================== -->
<!-- Штриховка сечения и геометрия отверстий -->
{hatch_svg}
{holes_sec_svg}

<!-- Надпись обозначения разреза А-А -->
<text x="210" y="30" font-family="osifont, Arial, sans-serif" font-size="4.5px" font-weight="bold" fill="#000" text-anchor="middle">А-А</text>

<!-- 8. Глубина стойки 18 сверху -->
<line x1="204" y1="46.5" x2="204" y2="36" class="dim-ext" />
<line x1="222" y1="46.5" x2="222" y2="36" class="dim-ext" />
<line x1="204" y1="38" x2="222" y2="38" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="213" y="36.5" class="dim-text">18</text>

<!-- 9. Глубина ступеньки 8 -->
<line x1="196" y1="146.5" x2="196" y2="136" class="dim-ext" />
<line x1="204" y1="146.5" x2="204" y2="136" class="dim-ext" />
<line x1="196" y1="138" x2="204" y2="138" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="200" y="136.5" class="dim-text">8</text>

<!-- 10. Глубина фланца 28 снизу -->
<line x1="196" y1="189.5" x2="196" y2="201" class="dim-ext" />
<line x1="224" y1="189.5" x2="224" y2="201" class="dim-ext" />
<line x1="196" y1="199" x2="224" y2="199" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="210" y="197.5" class="dim-text">28</text>

<!-- 11. Толщина фланца 10 справа -->
<line x1="224" y1="189.5" x2="240" y2="189.5" class="dim-ext" />
<line x1="222" y1="179.5" x2="240" y2="179.5" class="dim-ext" />
<line x1="237" y1="189.5" x2="237" y2="179.5" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="235" y="185.5" transform="rotate(-90 235 185.5)" class="dim-text">10</text>

<!-- Выноска опорной ступеньки -->
<path d="M 200 146.5 L 180 155 L 140 155" class="leader" marker-start="url(#dot)" />
<text x="160" y="153.5" class="dim-text">Опора рельса MGN9</text>

</svg>'''

    sym_dim = doc.addObject('TechDraw::DrawViewSymbol', 'OverlayDimensions')
    sym_dim.Symbol = svg_dim
    page.addView(sym_dim)
    doc.recompute()

    # Компенсация расхождения DPI QtSvg (90 DPI) и FreeCAD TechDraw (96 DPI)
    sym_dim.Scale = 420.0 / (1488.0 * 25.4 / 96.0)
    sym_dim.X = 210.0
    sym_dim.Y = 148.5
    doc.recompute()

    # 8. Экспорт векторного PDF, проекта FreeCAD и изображения PNG
    out_pdf = os.path.abspath(f"{part_name}.pdf")
    out_fcstd = os.path.abspath(f"{part_name}.FCStd")
    out_png = os.path.abspath(f"{part_name}.png")

    export_drawing(doc, page, out_pdf, out_fcstd, out_png)
    print(f"Drawing for {part_name} generated successfully!")


if __name__ == "__main__":
    generate_stripper_guide_drawing()
