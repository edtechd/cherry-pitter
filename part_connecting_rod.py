#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_connecting_rod.py
Поз. 6: Шатун со сферическими шарнирными головками SI3T/K (Connecting Rod Assembly)
Соединяет кривошипный палец колеса horizontal_crankshaft (R = 18.0 мм)
и палец каретки штока needle_slider (MGN9H).
Межосевое расстояние: L = 85.0 мм.
Диаметр отверстий под пальцы: Ø3.0H7 (под пальцы Ø3.0h7).
Ширина головки по кольцу корпуса: 4.5 мм, по внутреннему шару: 6.0 мм.
Оформление рабочего чертежа с видами, размерами и техническими требованиями по ГОСТ (ЕСКД).
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


def create_connecting_rod(length=85.0):
    """
    Создает твердотельную 3D B-Rep модель шатуна в сборе:
    - Межцентровое расстояние между осями шарниров: length (ном. 85.0 мм);
    - Нижняя шарнирная головка SI3T/K: центр в (0, 0, -length/2);
    - Верхняя шарнирная головка SI3T/K: центр в (0, 0, +length/2);
    - Оси отверстий под пальцы: направлены вдоль локальной оси X (1, 0, 0);
    - Диаметр отверстий шарниров: Ø3.0 мм (H7);
    - Наружный диаметр проушины корпуса: Ø11.0 мм, ширина кольца 4.5 мм;
    - Сферический шарнирный вкладыш: диаметр Ø7.0 мм, ширина торцов 6.0 мм;
    - Шестигранные контргайки DIN 439 / DIN 934 M3 (под ключ S = 5.5 мм, высота 2.4 мм);
    - Центральная соединительная шпилька: M3 (Ø3.0 мм) между контргайками.
    """
    half_l = length / 2.0
    p_bot = FreeCAD.Vector(0.0, 0.0, -half_l)
    p_top = FreeCAD.Vector(0.0, 0.0, half_l)

    # 1. Центральная соединительная резьбовая шпилька М3
    # Проходит между контргайками (от -half_l + 16.4 до +half_l - 16.4)
    l_stud = length - 30.0
    stud = Part.makeCylinder(1.5, l_stud, FreeCAD.Vector(0, 0, -l_stud / 2.0), FreeCAD.Vector(0, 0, 1))

    # Вспомогательная функция построения шарнирной головки SI3T/K
    def make_si3tk_head(p_center, z_dir):
        # Внешнее цилиндрическое кольцо корпуса: Ø11.0 мм (R = 5.5 мм), ширина 4.5 мм вдоль оси X
        casing = Part.makeCylinder(5.5, 4.5, p_center - FreeCAD.Vector(2.25, 0, 0), FreeCAD.Vector(1, 0, 0))

        # Сферический вкладыш: сфера Ø7.0 мм (R = 3.5 мм), усеченная плоскостями до ширины 6.0 мм
        ball_sphere = Part.makeSphere(3.5, p_center)
        ball_box = Part.makeBox(6.0, 12.0, 12.0, p_center - FreeCAD.Vector(3.0, 6.0, 6.0))
        ball = ball_sphere.common(ball_box)

        # Цилиндрическая резьбовая шейка хвостовика: Ø6.0 мм (R = 3.0 мм), длина 14.0 мм вдоль оси шатуна
        neck = Part.makeCylinder(3.0, 14.0, p_center, z_dir)

        # Шестигранная контргайка M3 (S = 5.5 мм, толщина 2.4 мм) на хвостовике
        p_nut = p_center + z_dir * 14.0
        r_hex = 5.5 / math.sqrt(3.0)
        nut_pts = []
        for i in range(6):
            ang = math.radians(i * 60.0)
            nut_pts.append(FreeCAD.Vector(r_hex * math.cos(ang), r_hex * math.sin(ang), 0))
        nut_pts.append(nut_pts[0])
        polygon = Part.makePolygon(nut_pts)
        face = Part.Face(polygon)
        nut = face.extrude(FreeCAD.Vector(0, 0, 2.4 if z_dir.z > 0 else -2.4))
        nut.translate(p_nut)

        return casing.fuse(ball).fuse(neck).fuse(nut)

    head_bot = make_si3tk_head(p_bot, FreeCAD.Vector(0, 0, 1))
    head_top = make_si3tk_head(p_top, FreeCAD.Vector(0, 0, -1))

    rod_body = stud.fuse(head_bot).fuse(head_top)

    # 2. Чистовые сквозные калиброванные отверстия под пальцы Ø3.0H7
    bore_bot = Part.makeCylinder(1.5, 12.0, p_bot - FreeCAD.Vector(6.0, 0, 0), FreeCAD.Vector(1, 0, 0))
    bore_top = Part.makeCylinder(1.5, 12.0, p_top - FreeCAD.Vector(6.0, 0, 0), FreeCAD.Vector(1, 0, 0))

    rod = rod_body.cut(bore_bot).cut(bore_top)

    if not rod.isValid():
        raise ValueError("Connecting rod shape is topologically invalid!")

    return rod


create_part = create_connecting_rod


def generate_connecting_rod_drawing(part_name="part_connecting_rod",
                                    doc_code="ВЧ.01.00.006",
                                    title_name="Шатун в сборе",
                                    scale=2.0,
                                    sheet="A3_Landscape"):
    """
    Генерирует рабочий чертеж шатуна ВЧ.01.00.006 по ЕСКД:
    - Главный вид (вид спереди): ориентация вдоль оси стержня, отображает межосевое расстояние 85.0 мм;
    - Вид сбоку (вид слева): показывает толщину корпуса 4.5 мм и ширину шара 6.0 мм;
    - Вид сверху: торец верхней проушины и отверстие Ø3H7;
    - Аксонометрия: изометрический вид узла;
    - Размеры и технические требования по ГОСТ 2.307 / 2.316.
    """
    shape = create_connecting_rod(85.0)

    doc = FreeCAD.newDocument(f"Doc_{part_name}")
    feat = doc.addObject("Part::Feature", part_name)
    feat.Shape = shape
    doc.recompute()

    page, template = create_drawing_page(doc, sheet, f"Page_{part_name}")

    # Размещение видов на листе А3 (420 x 297 мм) в масштабе 2:1
    # Габарит детали: по Z = 96.0 мм (в масштабе 2:1 -> 192.0 мм), по Y = 11.0 мм (22 мм), по X = 6.0 мм (12 мм)
    # Повернем модель для чертежа: длинная ось L=85 мм горизонтально, чтобы идеально заполнить лист А3!
    # Или разместим вертикально:
    # FrontView: проекция вдоль оси X (1, 0, 0).
    # На виде спереди видны кольца проушин Ø11, гайки S=5.5 и межосевое L=85 мм!
    # Направление проецирования для FrontView: (1.0, 0.0, 0.0)
    # Направление проецирования для SideView (слева): (0.0, -1.0, 0.0)

    # Вид спереди (FrontView, проецирование вдоль оси отверстий X):
    # Центр детали: (0, 0, 0)
    x_front = 145.0
    y_front = 150.0
    v_front = add_part_view(doc, page, feat, "FrontView", (1.0, 0.0, 0.0), scale, x_front, y_front)

    # Вид слева (SideView, проецирование перпендикулярно оси X и Z):
    x_side = 235.0
    y_side = 150.0
    v_side = add_part_view(doc, page, feat, "SideView", (0.0, -1.0, 0.0), scale, x_side, y_side)

    # Изометрический вид:
    x_iso = 330.0
    y_iso = 205.0
    v_iso = add_part_view(doc, page, feat, "IsoView", (1.2, -1.0, 0.8), scale * 0.8, x_iso, y_iso)
    v_iso.CoarseView = True

    doc.recompute()

    # Оверлей размеров по ГОСТ 2.307 (масштаб 2:1)
    # Размеры на FrontView (X_center = 145.0, Y_center = 150.0, в SVG Y_svg = 297 - 150 = 147):
    # Центр нижней головки: Z = -42.5 -> в масштабе 2:1 это -85.0 мм в 3D -> Y_svg = 147 + 85.0 = 232.0
    # Центр верхней головки: Z = +42.5 -> в масштабе 2:1 это +85.0 мм в 3D -> Y_svg = 147 - 85.0 = 62.0
    # X_center = 145.0:
    # Межосевой размер 85: слева от FrontView на X = 110.0
    
    dpi_scale = 1.0668
    svg_dims = f'''<svg xmlns="http://www.w3.org/2000/svg"
     width="{420.0 * dpi_scale}mm" height="{297.0 * dpi_scale}mm"
     viewBox="0 0 420 297" style="background: none;">
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M 0 2 L 10 5 L 0 8 z" fill="black"/>
  </marker>
  <marker id="dot" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4">
    <circle cx="5" cy="5" r="3" fill="black"/>
  </marker>
</defs>
<style>
  .dim-line {{ stroke: black; stroke-width: 0.35; fill: none; }}
  .dim-text {{ font-family: osifont, "ISOCPEUR", "DejaVu Sans", Arial; font-size: 3.5px; fill: black; text-anchor: middle; }}
  .dim-text-vert {{ font-family: osifont, "ISOCPEUR", "DejaVu Sans", Arial; font-size: 3.5px; fill: black; text-anchor: middle; transform: rotate(-90deg); }}
  .title-text {{ font-family: osifont, "ISOCPEUR", "DejaVu Sans", Arial; font-size: 5.0px; font-weight: bold; fill: black; text-anchor: middle; }}
  .center-mark {{ stroke: black; stroke-width: 0.25; stroke-dasharray: 4, 1.5, 1, 1.5; }}
</style>

<!-- Названия видов -->
<text x="145" y="40" class="title-text">Вид спереди</text>
<text x="235" y="40" class="title-text">Вид слева</text>
<text x="330" y="145" class="title-text">Изометрия</text>

<!-- Осевые линии FrontView -->
<!-- Верхняя головка (145, 62) -->
<line x1="130" y1="62" x2="160" y2="62" class="center-mark" />
<line x1="145" y1="47" x2="145" y2="77" class="center-mark" />
<!-- Нижняя головка (145, 232) -->
<line x1="130" y1="232" x2="160" y2="232" class="center-mark" />
<line x1="145" y1="217" x2="145" y2="247" class="center-mark" />
<!-- Центральная продольная ось -->
<line x1="145" y1="77" x2="145" y2="217" class="center-mark" />

<!-- Размер 85* (межосевое расстояние) -->
<line x1="145" y1="62" x2="105" y2="62" class="dim-line" />
<line x1="145" y1="232" x2="105" y2="232" class="dim-line" />
<line x1="110" y1="62" x2="110" y2="232" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow)" />
<text x="104" y="147" class="dim-text" transform="rotate(-90 104 147)">85*</text>

<!-- Выноска отверстий Ø3H7 -->
<path d="M 145 62 L 175 52 L 195 52" class="dim-line" marker-start="url(#dot)" />
<text x="185" y="49" class="dim-text">2 отв. Ø3H7</text>

<!-- Выноска наружного диаметра головки Ø11 -->
<path d="M 153 70 L 175 78 L 195 78" class="dim-line" marker-start="url(#dot)" />
<text x="185" y="75" class="dim-text">Ø11</text>

<!-- Выноска резьбы и контргайки М3 -->
<path d="M 145 100 L 175 105 L 200 105" class="dim-line" marker-start="url(#dot)" />
<text x="188" y="102" class="dim-text">Гайка M3 DIN 439 (S=5,5)</text>

<!-- Выноска шпильки М3 -->
<path d="M 145 147 L 175 147 L 195 147" class="dim-line" marker-start="url(#dot)" />
<text x="185" y="144" class="dim-text">Шпилька M3 DIN 975</text>

<!-- Размеры на SideView (X_center = 235, Y_center = 147 в SVG) -->
<!-- Ширина головки 4.5 и шара 6.0 на верхней головке: -->
<!-- Верхняя головка: Y_svg = 62. Торцы шара при X = 235 ± 6.0 = [229, 241] -->
<line x1="229" y1="58" x2="229" y2="48" class="dim-line" />
<line x1="241" y1="58" x2="241" y2="48" class="dim-line" />
<line x1="229" y1="51" x2="241" y2="51" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow)" />
<text x="235" y="48" class="dim-text">6,0</text>

<!-- Ширина корпуса 4.5: при X = 235 ± 4.5 = [230.5, 239.5] -->
<line x1="230.5" y1="66" x2="216" y2="66" class="dim-line" />
<line x1="239.5" y1="66" x2="254" y2="66" class="dim-line" />
<path d="M 230.5 72 L 210 80 L 190 80" class="dim-line" marker-start="url(#dot)" />
<text x="200" y="77" class="dim-text">4,5</text>
</svg>'''

    sym_dims = doc.addObject('TechDraw::DrawViewSymbol', 'DimensionsOverlay')
    sym_dims.Symbol = svg_dims
    page.addView(sym_dims)
    doc.recompute()
    sym_dims.X = 210.0
    sym_dims.Y = 148.5
    doc.recompute()

    # Технические требования
    notes = [
        "1. * Размеры для справок.",
        "2. Межцентровое расстояние шарнирных головок L = 85.0 ± 0.2 мм регулируется шпилькой M3.",
        "3. Шарнирные наконечники: шарнирные головки SI3T/K (внутренняя резьба M3, отверстие Ø3H7).",
        "4. Фиксация длины: контргайки M3 DIN 439 (низкие, S=5.5 мм). Момент затяжки 1.2 Н·м.",
        "5. Предельный угол наклона шарнирного шара: ±13° во всех направлениях.",
        "6. Смазка вкладышей: ЦИАТИМ-201 ГОСТ 6267-74."
    ]
    notes_h = 42.0
    svg_notes = f'''<svg xmlns="http://www.w3.org/2000/svg" width="185mm" height="{notes_h}mm" viewBox="0 0 185 {notes_h}">
<text x="5" y="8" font-family="osifont, Arial" font-size="3.5" font-weight="bold" fill="black">Технические требования:</text>'''
    for idx, line in enumerate(notes):
        svg_notes += f'<text x="5" y="{14 + idx * 4.8}" font-family="osifont, Arial" font-size="2.9" fill="black">{line}</text>'
    svg_notes += '</svg>'

    sym_notes = doc.addObject('TechDraw::DrawViewSymbol', 'TechNotes')
    sym_notes.Symbol = svg_notes
    page.addView(sym_notes)
    doc.recompute()
    sym_notes.X = 327.5
    sym_notes.Y = 82.0
    doc.recompute()

    # Основная надпись по ГОСТ 2.104
    title_fields = {
        'Номер': doc_code,
        'Название': title_name,
        'Информация': 'SI3T/K - DIN 975',
        'Масштаб': f"{int(scale)}:1",
        'Лист': '1',
        'Листов': '1',
        'Масса': '0.018',
        'Материал': 'Сталь / SI3T/K',
        'Разработал': 'Инженер',
        'Проверил': 'Контролер',
        'Утвердил': 'Иванов И. И.',
        'Организация1': 'Проект VISHNI',
        'Организация2': 'VISHNI CAD',
        'Дата_разработки': '01.01.01',
        'Дата_проверки': '01.01.01',
        'Дата_утверждения': '01.01.01'
    }
    fill_gost_title_block(template, title_fields)
    doc.recompute()

    out_pdf = os.path.abspath(f"{part_name}.pdf")
    out_fcstd = os.path.abspath(f"{part_name}.FCStd")
    out_png = os.path.abspath(f"{part_name}.png")

    export_drawing(doc, page, out_pdf, out_fcstd, out_png)
    print(f"Drawing {part_name} generated successfully!")


if __name__ == "__main__":
    generate_connecting_rod_drawing()
