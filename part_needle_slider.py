#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_needle_slider.py
Поз. 7: Каретка штока (Needle Slider Carriage for MGN9H Rail)
Спроектирована для установки на каретку линейной направляющей MGN9H.
Оснащена выносной консолью с сокетом для иглы штока точно над центром лунки 3 (угол 120°),
а также встроенным пальцем Ø3.0 мм (h7) для шарнирной головки шатуна SI3T/K.
Оформление рабочего чертежа с продольным разрезом А-А и размерами по ГОСТ (ЕСКД).
"""

import sys
import os
import math

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


def create_needle_slider():
    """
    Создает аналитический B-Rep солид каретки штока:
    Координаты:
    - Начало координат (0,0,0) привязано к центру верхней монтажной плоскости каретки MGN9H:
      - X in [-10.0, +10.0] - поперечная ось (ширина 20.0 мм);
      - Y in [0.0, 5.0] - нормаль к плоскости каретки (толщина фланца 5.0 мм);
      - Z in [-17.0, +17.0] - продольная ось движения по рельсу (длина 34.0 мм);
    - Крепеж к каретке MGN9H: 4 отверстия Ø3.4 мм с цековками Ø6.0 x 3.2 мм под винты M3 DIN 912
      (сетка B = 15.0 мм по X, C = 16.0 мм по Z: X = ±7.5 мм, Z = ±8.0 мм);
      Для 2 отверстий со стороны консоли (X = +7.5 мм) цековки продлены навынос (сквозь тело консоли
      до Y = 25 мм), обеспечивая сквозной монтаж 4 винтами DIN 912 M3x8 к каретке MGN9H;
    - Выносная консоль под иглу штока:
      - Центр оси сокета: строго X = +8.0 мм, Y = +14.0 мм (соответствует лунке 3 барабана);
      - Цилиндрическая бобышка сокета: Ø9.0 мм (R = 4.5 мм), высота 28.0 мм (Z in [-14.0, +14.0] мм);
      - Сквозное отверстие сокета под иглу: Ø3.0 мм (+0.05 мм);
      - Резьбовое отверстие М3 (сверление Ø2.5 мм) под установочный винт DIN 913 на передней грани;
    - Боковая колодка под шатун со сквозным резьбовым отверстием M3:
      - Колодка на правом фланце при X in [10.0, 20.0] мм, Z in [10.0, 21.0] мм, Y in [0.0, 5.0] мм
        (выполнена наподлицо с привалочной плоскостью слайдера Y = 0.0 для печати без поддержек);
      - Сквозное резьбовое отверстие М3 (сверление Ø2.5 мм) по оси X = 17.0 мм, Z = 16.0 мм;
      - Ось вкрученного винта M3 направлена вдоль оси Y (в зону Y < 0) и служит пальцем
        под шарнирную головку шатуна SI3T/K (середина шарнира при Y = -3.0 мм).
    """
    # 1. Базовый опорный фланец (20.0 x 5.0 x 34.0 мм, Y in [0.0, 5.0])
    flange = make_box(20.0, 5.0, 34.0, (-10.0, 0.0, -17.0))

    # 2. Выносная консоль к сокету иглы со скосом 45° для печати без поддержек:
    # Сечение консоли в плоскости XY со скосом 45° от (10.0, 5.0) до (12.0, 7.0),
    # устраняющим горизонтальное нависание над столом принтера
    arm_pts = [
        FreeCAD.Vector(2.0, 4.0, -12.0),
        FreeCAD.Vector(10.0, 4.0, -12.0),
        FreeCAD.Vector(10.0, 5.0, -12.0),
        FreeCAD.Vector(12.0, 7.0, -12.0),
        FreeCAD.Vector(12.0, 14.0, -12.0),
        FreeCAD.Vector(2.0, 14.0, -12.0),
        FreeCAD.Vector(2.0, 4.0, -12.0)
    ]
    arm_wire = Part.makePolygon(arm_pts)
    arm_face = Part.Face(arm_wire)
    arm = arm_face.extrude(FreeCAD.Vector(0, 0, 24.0))

    # 3. Цилиндрическая бобышка сокета иглы (Ø9.0 мм, высота 28.0 мм, центр X = 8.0, Y = 14.0)
    boss = Part.makeCylinder(4.5, 28.0, FreeCAD.Vector(8.0, 14.0, -14.0), FreeCAD.Vector(0, 0, 1))

    # 4. Колодка крепления с шатуном (X in [10.0, 20.0], Y in [0.0, 5.0], Z in [10.0, 21.0])
    # Выполнена строго наподлицо с привалочной плоскостью слайдера Y = 0.0
    bracket = make_box(10.0, 5.0, 11.0, (10.0, 0.0, 10.0))

    slider = flange.fuse(arm).fuse(boss).fuse(bracket)

    # 5. 4 крепежных отверстия под винты M3 DIN 912 (Ø3.4 мм сквозное, цековка Ø6.0 мм)
    # Для 2 отверстий при sx = 7.5 мм цековки продлены навынос (длина 25 мм сквозь всю высоту консоли)
    for sx in [-7.5, 7.5]:
        for sz in [-8.0, 8.0]:
            th = make_cylinder(1.7, 10.0, (sx, -1.0, sz), (0, 1, 0))
            cb_len = 25.0 if sx > 0 else 5.0
            cb = make_cylinder(3.0, cb_len, (sx, 1.8, sz), (0, 1, 0))
            slider = slider.cut(th).cut(cb)

    # 6. Сквозное отверстие сокета под иглу Ø3.0 мм
    needle_bore = Part.makeCylinder(1.5, 32.0, FreeCAD.Vector(8.0, 14.0, -16.0), FreeCAD.Vector(0, 0, 1))
    slider = slider.cut(needle_bore)

    # 7. Резьбовое отверстие М3 под установочный винт DIN 913 фиксации иглы
    clamp_hole = Part.makeCylinder(1.25, 8.0, FreeCAD.Vector(8.0, 19.5, 0.0), FreeCAD.Vector(0, -1, 0))
    slider = slider.cut(clamp_hole)

    # 8. Сквозное резьбовое отверстие M3 (Ø2.5 мм) под винт-палец шатуна (ось X = 17.0, Z = 16.0)
    pin_screw_hole = Part.makeCylinder(1.25, 10.0, FreeCAD.Vector(17.0, -2.0, 16.0), FreeCAD.Vector(0, 1, 0))
    slider = slider.cut(pin_screw_hole)

    if not slider.isValid():
        raise ValueError("Needle slider solid shape is topologically invalid!")

    return slider


create_part = create_needle_slider


def generate_needle_slider_drawing(part_name="part_needle_slider",
                                   doc_code="ВЧ.01.00.007",
                                   title_name="Каретка штока",
                                   material="PETG",
                                   scale=2.0,
                                   sheet="A3_Landscape",
                                   notes=None):
    """
    Генерирует рабочий чертеж каретки штока по ГОСТ (ЕСКД):
    - Формат А3, масштаб 2:1;
    - Главный вид (FrontView): крепление к MGN9H, 4 отв. M3, палец Ø3x8 мм, сокет;
    - Вид сверху (TopView): вынос консоли на 14 мм, смещение на 8 мм к лунке 3, ширина 20 мм;
    - Продольный разрез А-А (SectionView): сечение через ось сокета иглы и крепежные цековки;
    - Изометрический вид (IsoView);
    - Векторный оверлей размеров (ГОСТ 2.307) с DPI компенсацией;
    - Штамп ГОСТ 2.104 и техтребования ГОСТ 2.316.
    """
    shape = create_needle_slider()

    doc = FreeCAD.newDocument(f"Doc_{part_name}")
    feat = doc.addObject("Part::Feature", part_name)
    feat.Shape = shape
    doc.recompute()

    page, template = create_drawing_page(doc, sheet, f"Page_{part_name}")

    # Координаты проекций на формате А3 (420 x 297 мм), масштаб 2:1
    x_front = 95.0
    y_front_td = 195.0   # SVG Y = 102.0

    x_top = 95.0
    y_top_td = 65.0      # SVG Y = 232.0 (строгая проекционная связь по X с FrontView)

    x_sec = 215.0
    y_sec_td = 195.0     # SVG Y = 102.0 (строгая проекционная связь по Y с FrontView)

    x_iso = 330.0
    y_iso_td = 205.0     # SVG Y = 92.0

    # 1. Главный вид (FrontView)
    v_front = add_part_view(doc, page, feat, "FrontView", (0.0, -1.0, 0.0), scale, x_front, y_front_td)

    # 2. Вид сверху (TopView)
    v_top = add_part_view(doc, page, feat, "TopView", (0.0, 0.0, 1.0), scale, x_top, y_top_td)

    # 3. Продольный разрез А-А (SectionView)
    sec = doc.addObject("TechDraw::DrawViewSection", "SectionView")
    sec.BaseView = v_top
    sec.SectionNormal = FreeCAD.Vector(1.0, 0.0, 0.0)
    sec.SectionOrigin = FreeCAD.Vector(8.0, 14.0, 0.0)
    sec.SectionDirection = "Left"
    sec.SectionSymbol = "A"
    page.addView(sec)
    doc.recompute()

    sec.Direction = FreeCAD.Vector(-1.0, 0.0, 0.0)
    sec.XDirection = FreeCAD.Vector(0.0, 1.0, 0.0)
    sec.Rotation = 180.0
    sec.Scale = scale
    sec.X = x_sec
    sec.Y = y_sec_td
    sec.IsoCount = 0
    sec.ViewObject.HatchColor = (0.0, 0.0, 0.0, 1.0)
    doc.recompute()

    # 4. Аксонометрический вид (IsoView)
    v_iso = add_part_view(doc, page, feat, "IsoView", (1.2, -1.5, 1.0), 1.6, x_iso, y_iso_td)

    # 5. Основная надпись (штамп ГОСТ 2.104)
    title_fields = {
        'Номер': doc_code,
        'Название': title_name,
        'Информация': 'MGN9H',
        'Масштаб': f"{int(scale)}:1" if scale >= 1 else f"1:{int(1/scale)}",
        'Лист': '1',
        'Листов': '1',
        'Материал1': material,
        'Материал2': '3D-печать',
        'Материал3': '',
        'Организация1': 'Проект VISHNI',
        'Организация2': 'VISHNI CAD',
        'Разработал': 'Инженер',
        'Проверил': 'Контролер'
    }
    fill_gost_title_block(template, title_fields)
    doc.recompute()

    # 6. Технические требования (ГОСТ 2.316) над штампом (X in [235, 415], Y in [180, 238])
    if notes is None:
        notes = [
            "1. * Размеры для справок.",
            "2. Материал детали: PETG. Заполнение не менее 60%, 4 периметра.",
            "   Базовая плоскость 3D-печати — привалочная плоскость к каретке (XY стола).",
            "3. Крепление к каретке MGN9H: 4 винта DIN 912 M3x8 (ГОСТ 11738-84).",
            "   Для 2 отверстий со стороны консоли предусмотрен сквозной монтаж навынос.",
            "4. Сокет под иглу Ø3,0H7 глубина 28 мм. Фиксация иглы: винт DIN 913 M3x6.",
            "5. Отверстие М3 (сверло Ø2,5) под винт DIN 912 M3 (стержень служит пальцем шатуна).",
            "6. Вынос сокета (+14,0 мм) и смещение (+8,0 мм) обеспечивают строгое",
            "   совпадение оси иглы с центром лунки 3 барабана (угол 120°).",
            "7. Неуказанные предельные отклонения размеров: ±IT14/2."
        ]

    notes_lines = ['<text x="235" y="176" font-family="osifont, Arial, sans-serif" font-size="3.6px" font-weight="bold" fill="#000">Технические требования:</text>']
    for idx, line in enumerate(notes):
        notes_lines.append(f'<text x="235" y="{182 + idx * 5.0}" font-family="osifont, Arial, sans-serif" font-size="2.9px" fill="#000">{line}</text>')
    notes_svg = '\n'.join(notes_lines)

    # 7. Векторный оверлей размеров (ГОСТ 2.307)
    # Масштаб 2:1
    # Аналитическая привязка к центрам проекций TechDraw:
    # FrontView: center (95.0, 102.0) -> cx=5.0, cz=2.0
    # TopView: center (95.0, 232.0) -> cx=5.0, cy=5.75
    # SectionView: center (215.0, 102.0) -> cy=9.25, cz=0.0

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
  .dim-text-sm {{ font-family: osifont, Arial, sans-serif; font-size: 2.8px; fill: #000; text-anchor: middle; }}
  .view-title {{ font-family: osifont, Arial, sans-serif; font-size: 4.5px; fill: #000; text-anchor: middle; font-weight: bold; }}
  .leader {{ stroke: #000; stroke-width: 0.35; fill: none; }}
</style>

<!-- ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ -->
{notes_svg}

<!-- ==================== ГЛАВНЫЙ ВИД (FrontView) ==================== -->
<text x="95" y="48" class="view-title">Вид спереди</text>

<!-- Осевые линии 4 отверстий: x = 70.0, 100.0; y = 90.0, 122.0 -->
<line x1="70" y1="84" x2="70" y2="128" class="center-line" />
<line x1="100" y1="84" x2="100" y2="128" class="center-line" />
<line x1="63" y1="90" x2="107" y2="90" class="center-line" />
<line x1="63" y1="122" x2="107" y2="122" class="center-line" />

<!-- Осевые отверстия под винт-палец: x = 119.0, y = 74.0 -->
<line x1="119" y1="66" x2="119" y2="82" class="center-line" />
<line x1="111" y1="74" x2="127" y2="74" class="center-line" />

<!-- 1. Межосевое отверстий по X: B = 15 -->
<line x1="70" y1="90" x2="70" y2="58" class="dim-ext" />
<line x1="100" y1="90" x2="100" y2="58" class="dim-ext" />
<line x1="70" y1="60" x2="100" y2="60" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="85" y="58.5" class="dim-text">15</text>

<!-- 2. Межосевое отверстий по Z: C = 16 -->
<line x1="70" y1="90" x2="48" y2="90" class="dim-ext" />
<line x1="70" y1="122" x2="48" y2="122" class="dim-ext" />
<line x1="51" y1="90" x2="51" y2="122" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="49" y="106" transform="rotate(-90 49 106)" class="dim-text">16</text>

<!-- 3. Длина фланца L = 34 (снизу 140, сверху 72) -->
<line x1="65" y1="72" x2="38" y2="72" class="dim-ext" />
<line x1="65" y1="140" x2="38" y2="140" class="dim-ext" />
<line x1="41" y1="72" x2="41" y2="140" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="39" y="106" transform="rotate(-90 39 106)" class="dim-text">34</text>

<!-- 4. Ширина фланца W = 20 (x in [65, 105]) -->
<line x1="65" y1="140" x2="65" y2="152" class="dim-ext" />
<line x1="105" y1="140" x2="105" y2="152" class="dim-ext" />
<line x1="65" y1="149" x2="105" y2="149" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="85" y="147.5" class="dim-text">20</text>

<!-- Выноска 4 крепежных отверстий M3 -->
<path d="M 70 122 L 55 138 L 28 138" class="leader" marker-start="url(#dot)" />
<text x="41" y="136.5" class="dim-text">4 отв. Ø3,4</text>
<text x="41" y="142.5" class="dim-text-sm">цек. Ø6 (2 отв. навынос)</text>

<!-- Выноска резьбы под винт-палец шатуна -->
<path d="M 119 74 L 135 62 L 160 62" class="leader" marker-start="url(#dot)" />
<text x="147" y="60.5" class="dim-text">Резьба M3</text>
<text x="147" y="66.5" class="dim-text-sm">(под винт-палец шатуна)</text>

<!-- ==================== ВИД СВЕРХУ (TopView) ==================== -->
<text x="95" y="180" class="view-title">Вид сверху</text>

<!-- Осевые линии сокета и фланца -->
<!-- Boss center: x = 101.0, y = 215.5 -->
<line x1="101" y1="202" x2="101" y2="228" class="center-line" />
<line x1="88" y1="215.5" x2="114" y2="215.5" class="center-line" />

<!-- Threaded hole center: x = 119.0 -->
<line x1="119" y1="228" x2="119" y2="248" class="center-line" />

<!-- Ось симметрии фланца по X: x = 85.0 -->
<line x1="85" y1="228" x2="85" y2="250" class="center-line" />

<!-- 5. Толщина фланца и колодки: 5 (y in [233.5, 243.5]) -->
<line x1="65" y1="243.5" x2="52" y2="243.5" class="dim-ext" />
<line x1="65" y1="233.5" x2="52" y2="233.5" class="dim-ext" />
<line x1="55" y1="243.5" x2="55" y2="233.5" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="52" y="239" transform="rotate(-90 52 239)" class="dim-text">5</text>

<!-- 6. Вынос сокета от плоскости каретки: 14 (от y=243.5 до y=215.5) -->
<line x1="105" y1="243.5" x2="135" y2="243.5" class="dim-ext" />
<line x1="101" y1="215.5" x2="135" y2="215.5" class="dim-ext" />
<line x1="132" y1="243.5" x2="132" y2="215.5" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="130" y="230" transform="rotate(-90 130 230)" class="dim-text">14</text>

<!-- 7. Смещение сокета по X: 8 (от x=85.0 до x=101.0) -->
<line x1="85" y1="233.5" x2="85" y2="202" class="dim-ext" />
<line x1="101" y1="215.5" x2="101" y2="202" class="dim-ext" />
<line x1="85" y1="204" x2="101" y2="204" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="93" y="202.5" class="dim-text">8</text>

<!-- Выноска сокета Ø3H7 -->
<path d="M 101 215.5 L 82 200 L 55 200" class="leader" marker-start="url(#dot)" />
<text x="68" y="198.5" class="dim-text">Сокет Ø3,0H7</text>
<text x="68" y="204.5" class="dim-text-sm">(под иглу штока)</text>

<!-- ==================== РАЗРЕЗ А-А (SectionView) ==================== -->
<text x="215" y="48" class="view-title">А-А</text>

<!-- Осевая линия сокета в разрезе: x = 205.5, y in [65, 138] -->
<line x1="205.5" y1="65" x2="205.5" y2="138" class="center-line" />

<!-- 9. Диаметр бобышки сокета Ø9 (x in [196.5, 214.5]) -->
<line x1="196.5" y1="74" x2="196.5" y2="60" class="dim-ext" />
<line x1="214.5" y1="74" x2="214.5" y2="60" class="dim-ext" />
<line x1="196.5" y1="62" x2="214.5" y2="62" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="205.5" y="60.5" class="dim-text">Ø9</text>

<!-- 10. Высота бобышки сокета: 28 (y in [74, 130]) -->
<line x1="196.5" y1="74" x2="182" y2="74" class="dim-ext" />
<line x1="196.5" y1="130" x2="182" y2="130" class="dim-ext" />
<line x1="185" y1="74" x2="185" y2="130" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="183" y="103" transform="rotate(-90 183 103)" class="dim-text">28</text>

<!-- Выноска резьбового отверстия M3 фиксации иглы -->
<path d="M 205.5 102 L 188 115 L 160 115" class="leader" marker-start="url(#dot)" />
<text x="174" y="113.5" class="dim-text">Резьба M3</text>
<text x="174" y="119.5" class="dim-text-sm">(винт DIN 913)</text>

<!-- ==================== ИЗОМЕТРИЯ ==================== -->
<text x="330" y="48" class="view-title">Изометрия</text>

</svg>'''

    sym_dim = doc.addObject('TechDraw::DrawViewSymbol', 'OverlayDimensions')
    sym_dim.Symbol = svg_dim
    page.addView(sym_dim)
    doc.recompute()

    # Компенсация бага DPI (90 vs 96 DPI):
    scale_corr = 420.0 / (1488.0 * 25.4 / 96.0)
    sym_dim.Scale = scale_corr
    sym_dim.X = 210.0
    sym_dim.Y = 148.5
    doc.recompute()

    out_pdf = os.path.abspath(f"{part_name}.pdf")
    out_fcstd = os.path.abspath(f"{part_name}.FCStd")
    out_png = os.path.abspath(f"{part_name}.png")

    export_drawing(doc, page, out_pdf, out_fcstd, out_png)
    print(f"Drawing for {part_name} generated successfully!")


if __name__ == "__main__":
    generate_needle_slider_drawing()
