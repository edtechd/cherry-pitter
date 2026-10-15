#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_motor_jgy370.py
Поз. 13: Мотор-редуктор червячный постоянного тока JGY-370 (DC Worm Gear Motor)
Обозначение: ВЧ.02.00.001

Назначение:
- Главный привод вишнечистки: передает вращение (30-40 об/мин, 12В) через вертикальный вал
  на жесткую муфту, мальтийский механизм (карусель ягод) и коническую передачу (кривошип иглы).
- Точные размеры редуктора по чертежу производителя: 32.0 х 46.0 х 25.2 мм.
- 4 крепежных резьбовых отверстия М3 с реальной сеткой 18.0 х 33.0 мм (Y = +9.0 и Y = -24.0 мм).
- Приливы вокруг крепежных отверстий 4-Ø7.4 мм.
- Выходной вал D-образный Ø6.0 мм со срезом (длина среза 12.0 мм, вылет 14.0 мм от буртика).
- Центрирующий буртик выходного вала Ø12.0 мм высотой 2.0 мм.
- Внутреннее глухое осевое резьбовое отверстие в валу М3 х 0.5 глубиной 12.0 мм.
- Цилиндрический корпус двигателя Ø24.4 мм длиной 30.8 мм, заподлицо по задней стенке (Z = -25.2 мм).
- Выводные контактные клеммы длиной 4.2 мм.
"""

import sys
import os
import math

# Добавление путей FreeCAD
sys.path.append('/usr/lib/freecad/lib')
sys.path.append('/usr/share/freecad/Mod/TechDraw')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from freecad_utils import (
    FreeCAD, Part, TechDraw, TechDrawGui,
    make_box, make_cylinder,
    create_drawing_page, add_part_view,
    fill_gost_title_block, export_drawing
)


def create_motor_jgy370():
    """
    Constructs the highly accurate JGY-370 Worm Gear Motor B-Rep solid model.
    Local coordinate datum:
    - Output shaft axis is along Z at (0, 0).
    - Gearbox front mounting reference face is at Z = 0.0.
    - Output shaft extends along +Z (Z in [2.0, 16.0], collar at Z in [0, 2.0]).
    - Gearbox body extends along -Z (Z in [-25.2, 0.0]).
    - Gearbox width 32.0 mm (X in [-16.0, 16.0]).
    - Gearbox height 46.0 mm (Y in [-31.0, 15.0]):
      Top edge is at Y = +15.0 mm (+9.0 mm from top holes, +15.0 mm from shaft).
      Bottom edge is at Y = -31.0 mm (-24.0 mm from bottom holes, -31.0 mm from shaft).
    - Motor can Ø24.4 mm extends along -Y from Y = -31.0 to Y = -61.8 mm.
      Rear face of motor is flush with gearbox rear face at Z = -25.2 mm (axis at Z = -13.0 mm).
    - Terminals extend from Y = -61.8 to Y = -66.0 mm (length 4.2 mm).
    - 4-M3 mounting holes at X = ±9.0 mm, Y = +9.0 mm and Y = -24.0 mm.
    """
    # ----------------------------------------------------------------
    # 1. Корпус червячного редуктора 32.0 х 46.0 х 25.2 мм со скругленными углами R=1.5 мм
    # ----------------------------------------------------------------
    w_gb = 32.0
    l_gb = 46.0
    h_gb = 25.2
    r_fillet = 1.5

    x1, x2 = -16.0, 16.0
    y1, y2 = -31.0, 15.0
    z_bot = -25.2

    p1 = FreeCAD.Vector(x1 + r_fillet, y1, z_bot)
    p2 = FreeCAD.Vector(x2 - r_fillet, y1, z_bot)
    p3 = FreeCAD.Vector(x2, y1 + r_fillet, z_bot)
    p4 = FreeCAD.Vector(x2, y2 - r_fillet, z_bot)
    p5 = FreeCAD.Vector(x2 - r_fillet, y2, z_bot)
    p6 = FreeCAD.Vector(x1 + r_fillet, y2, z_bot)
    p7 = FreeCAD.Vector(x1, y2 - r_fillet, z_bot)
    p8 = FreeCAD.Vector(x1, y1 + r_fillet, z_bot)

    edges = [
        Part.makeLine(p1, p2),
        Part.Edge(Part.Arc(p2, FreeCAD.Vector(x2 - r_fillet * (1 - math.cos(math.radians(45))),
                                              y1 + r_fillet * (1 - math.sin(math.radians(45))), z_bot), p3)),
        Part.makeLine(p3, p4),
        Part.Edge(Part.Arc(p4, FreeCAD.Vector(x2 - r_fillet * (1 - math.cos(math.radians(45))),
                                              y2 - r_fillet * (1 - math.sin(math.radians(45))), z_bot), p5)),
        Part.makeLine(p5, p6),
        Part.Edge(Part.Arc(p6, FreeCAD.Vector(x1 + r_fillet * (1 - math.cos(math.radians(45))),
                                              y2 - r_fillet * (1 - math.sin(math.radians(45))), z_bot), p7)),
        Part.makeLine(p7, p8),
        Part.Edge(Part.Arc(p8, FreeCAD.Vector(x1 + r_fillet * (1 - math.cos(math.radians(45))),
                                              y1 + r_fillet * (1 - math.sin(math.radians(45))), z_bot), p1))
    ]
    wire_gb = Part.Wire(edges)
    gearbox_body = Part.Face(wire_gb).extrude(FreeCAD.Vector(0, 0, h_gb))

    # ----------------------------------------------------------------
    # 2. Центрирующий буртик выходного вала: Ø12.0 мм, высота 2.0 мм (Z in [0, 2.0])
    # ----------------------------------------------------------------
    collar = Part.makeCylinder(6.0, 2.0, FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1))

    # ----------------------------------------------------------------
    # 3. Выходной D-вал: Ø6.0 мм, вылет 14.0 мм над буртиком (Z in [2.0, 16.0])
    # ----------------------------------------------------------------
    cyl_shaft = Part.makeCylinder(3.0, 14.0, FreeCAD.Vector(0, 0, 2.0), FreeCAD.Vector(0, 0, 1))
    # Лыска среза: длина 12.0 мм от торца вала (Z in [4.0, 16.0]), срез на X = -2.5 мм (толщина 5.5 мм)
    d_cutter = make_box(4.0, 8.0, 12.0, (-6.5, -4.0, 4.0))
    shaft = cyl_shaft.cut(d_cutter)
    # Торцевое осевое резьбовое отверстие М3 х 0.5 глубиной 12.0 мм (сверление Ø2.5 мм, Z in [4.0, 16.0])
    shaft_hole = Part.makeCylinder(1.25, 12.0, FreeCAD.Vector(0, 0, 4.0), FreeCAD.Vector(0, 0, 1))
    shaft = shaft.cut(shaft_hole)

    # ----------------------------------------------------------------
    # 4. Цилиндрический двигатель (can): Ø24.4 мм, длина 30.8 мм (Y in [-61.8, -31.0])
    #    Ось цилиндра: X = 0.0, Z = -13.0 мм (задняя образующая Z = -25.2 мм заподлицо с редуктором)
    # ----------------------------------------------------------------
    can = Part.makeCylinder(12.2, 30.8, FreeCAD.Vector(0, -31.0, -13.0), FreeCAD.Vector(0, -1, 0))
    # Задний подшипниковый выступ: Ø6.0 мм, высота 1.5 мм (Y in [-63.3, -61.8])
    rear_hub = Part.makeCylinder(3.0, 1.5, FreeCAD.Vector(0, -61.8, -13.0), FreeCAD.Vector(0, -1, 0))

    # Клеммы питания: 2 контактных лепестка вылетом 4.2 мм (Y in [-66.0, -61.8])
    t1 = make_box(2.0, 4.2, 0.6, (-6.0 - 1.0, -66.0, -13.0 - 0.3))
    t2 = make_box(2.0, 4.2, 0.6, ( 6.0 - 1.0, -66.0, -13.0 - 0.3))

    # ----------------------------------------------------------------
    # 5. Средний овальный прилив («стадион») на лицевой крышке редуктора (Z in [0, 0.5])
    # ----------------------------------------------------------------
    c_st1 = Part.makeCylinder(2.5, 0.5, FreeCAD.Vector(-4.0, -12.0, 0), FreeCAD.Vector(0, 0, 1))
    c_st2 = Part.makeCylinder(2.5, 0.5, FreeCAD.Vector( 4.0, -12.0, 0), FreeCAD.Vector(0, 0, 1))
    b_st = make_box(8.0, 5.0, 0.5, (-4.0, -14.5, 0))
    stadium_boss = c_st1.fuse(c_st2).fuse(b_st)

    # ----------------------------------------------------------------
    # 6. 4 опорных прилива Ø7.4 мм вокруг крепежных отверстий (Z in [0, 0.5])
    # ----------------------------------------------------------------
    hole_locs = [
        (-9.0,   9.0),
        ( 9.0,   9.0),
        (-9.0, -24.0),
        ( 9.0, -24.0)
    ]
    bosses = []
    for hx, hy in hole_locs:
        b = Part.makeCylinder(3.7, 0.5, FreeCAD.Vector(hx, hy, 0), FreeCAD.Vector(0, 0, 1))
        bosses.append(b)

    # ----------------------------------------------------------------
    # 7. 4 винта М2 стяжки крышки редуктора по углам
    # ----------------------------------------------------------------
    corner_screws = []
    for cx in [-13.5, 13.5]:
        for cy in [12.5, -28.5]:
            sc = Part.makeCylinder(1.5, 0.4, FreeCAD.Vector(cx, cy, 0), FreeCAD.Vector(0, 0, 1))
            corner_screws.append(sc)

    # ----------------------------------------------------------------
    # Сборка монолитного твердотельного тела (B-Rep fuse & cut)
    # ----------------------------------------------------------------
    motor_solid = gearbox_body.fuse(collar).fuse(shaft).fuse(can).fuse(rear_hub).fuse(t1).fuse(t2).fuse(stadium_boss)
    for b in bosses:
        motor_solid = motor_solid.fuse(b)
    for sc in corner_screws:
        motor_solid = motor_solid.fuse(sc)

    # 4 глухих резьбовых отверстия М3 под крепеж (глубина 5.0 мм)
    for hx, hy in hole_locs:
        h_cut = Part.makeCylinder(1.25, 6.0, FreeCAD.Vector(hx, hy, -5.0), FreeCAD.Vector(0, 0, 1))
        motor_solid = motor_solid.cut(h_cut)

    if not motor_solid.isValid():
        raise RuntimeError("JGY-370 Motor shape is invalid!")

    return motor_solid

create_part = create_motor_jgy370


def generate_motor_jgy370_drawing(part_name="part_motor_jgy370",
                                  doc_code="ВЧ.02.00.001",
                                  title_name="Мотор-редуктор JGY-370",
                                  material="Цинк / Сталь",
                                  scale=1.5,
                                  sheet="A3_Landscape",
                                  notes=None):
    """
    Генерирует официальный рабочий чертеж мотор-редуктора JGY-370 по ГОСТ (ЕСКД):
    - Вид спереди (Front View) с размерами редуктора 32х46, отверстиями 4-М3, сеткой 18х33;
    - Вид сбоку (Side View) с вылетом вала 14 мм, срезом 12 мм, толщиной 25.2 мм и двигателем Ø24.4х30.8;
    - Аксонометрический вид (изометрия);
    - Полный векторный размерный оверлей по ГОСТ 2.307;
    - Штамп по ГОСТ 2.104 и технические требования по ГОСТ 2.316.
    """
    shape = create_motor_jgy370()

    doc = FreeCAD.newDocument(f"Doc_{part_name}")
    feat = doc.addObject("Part::Feature", part_name)
    feat.Shape = shape
    doc.recompute()

    page, template = create_drawing_page(doc, sheet, f"Page_{part_name}")

    # Координаты проекционных видов на формате А3 (420 x 297 мм) при масштабе 1.5:1
    x_front = 115.0
    y_front = 175.0

    x_side = 215.0
    y_side = 175.0

    x_iso = 330.0
    y_iso = 190.0

    # 1. Вид спереди (Front View: глядя вдоль оси Z на переднюю грань с валом)
    v_front = add_part_view(doc, page, feat, "FrontView", (0.0, 0.0, 1.0), scale, x_front, y_front)
    v_front.XDirection = FreeCAD.Vector(1.0, 0.0, 0.0)

    # 2. Вид сбоку (Side View: глядя со стороны -X в сторону +X)
    v_side = add_part_view(doc, page, feat, "SideView", (-1.0, 0.0, 0.0), scale, x_side, y_side)
    v_side.XDirection = FreeCAD.Vector(0.0, 0.0, 1.0)
    doc.recompute()

    # 3. Изометрический вид
    v_iso = add_part_view(doc, page, feat, "IsoView", (1.2, -1.2, 0.9), scale * 0.9, x_iso, y_iso)
    doc.recompute()

    # 4. Основная надпись (штамп ГОСТ 2.104)
    title_fields = {
        'Номер': doc_code,
        'Название': title_name,
        'Масштаб': '1.5:1',
        'Лист': '1',
        'Листов': '1',
        'Материал1': material,
        'Материал2': '',
        'Материал3': '',
        'Организация1': 'Проект VISHNI',
        'Организация2': 'VISHNI CAD',
        'Разработал': 'Инженер',
        'Проверил': 'Контролер'
    }
    fill_gost_title_block(template, title_fields)
    doc.recompute()

    # 5. Технические требования (ГОСТ 2.316)
    if notes is None:
        notes = [
            "1. * Размеры для справок.",
            "2. Мотор-редуктор червячный постоянного тока JGY-370.",
            "3. Номинальное напряжение питания: 12 В постоянного тока.",
            "4. Скорость выходного вала: 30-40 об/мин, крутящий момент ном.: 2.5-3.0 кгс·см.",
            "5. Редуктор самотормозящийся червячный с металлическими шестернями.",
            "6. Выходной вал Ø6 мм с лыской D-cut 12 мм и торцевой резьбой М3х0.5 (глуб. 12 мм).",
            "7. Крепление: 4 резьбовых отверстия М3 на межосевом расстоянии 18 х 33 мм.",
            "8. Предельные отклонения размеров: по ГОСТ 30893.1-m (±t2/2)."
        ]

    notes_h = 16.0 + len(notes) * 5.6
    notes_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="185mm" height="{notes_h}mm" viewBox="0 0 185 {notes_h}">
<text x="5" y="10" font-family="osifont, Arial, sans-serif" font-size="3.5px" font-weight="bold" fill="#000">Технические требования:</text>'''
    for idx, line in enumerate(notes):
        notes_svg += f'<text x="5" y="{16.5 + idx * 5.4}" font-family="osifont, Arial, sans-serif" font-size="3.0px" fill="#000">{line}</text>'
    notes_svg += '</svg>'

    sym_notes = doc.addObject('TechDraw::DrawViewSymbol', 'TechNotes')
    sym_notes.Symbol = notes_svg
    page.addView(sym_notes)
    doc.recompute()
    sym_notes.X = 322.5
    sym_notes.Y = 55.0 + notes_h / 2.0 + 3.0
    doc.recompute()

    # 6. Векторный оверлей размеров по ГОСТ 2.307
    svg_dim = '''<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">
<rect x="0" y="0" width="420" height="297" fill="none" stroke="none" />
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
  .dim-line { stroke: #000; stroke-width: 0.35; fill: none; }
  .dim-ext { stroke: #000; stroke-width: 0.25; fill: none; }
  .center-line { stroke: #000; stroke-width: 0.25; stroke-dasharray: 6,1.5,1.5,1.5; fill: none; }
  .dim-text { font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: middle; font-weight: bold; }
  .dim-text-left { font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: start; }
  .view-title { font-family: osifont, Arial, sans-serif; font-size: 4.5px; fill: #000; text-anchor: middle; font-weight: bold; }
  .leader { stroke: #000; stroke-width: 0.35; fill: none; }
</style>

<!-- ==================== ВИД СПЕРЕДИ (FrontView) ==================== -->
<text x="115" y="32" class="view-title">Вид спереди</text>

<!-- Осевые линии FrontView (центр вала при X=115.0, Y=83.75) -->
<line x1="85" y1="83.75" x2="145" y2="83.75" class="center-line" />
<line x1="115" y1="50" x2="115" y2="187" class="center-line" />

<!-- Размер: Ширина редуктора 32.0 мм (X in [91.0, 139.0]) -->
<line x1="91.0" y1="46" x2="139.0" y2="46" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="91.0" y1="59" x2="91.0" y2="44" class="dim-ext" />
<line x1="139.0" y1="59" x2="139.0" y2="44" class="dim-ext" />
<text x="115.0" y="44.5" class="dim-text">32.0</text>

<!-- Размер: Межосевое расстояние отверстий 18 мм (X in [101.5, 128.5]) -->
<line x1="101.5" y1="53" x2="128.5" y2="53" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="101.5" y1="68" x2="101.5" y2="51" class="dim-ext" />
<line x1="128.5" y1="68" x2="128.5" y2="51" class="dim-ext" />
<text x="115.0" y="51.5" class="dim-text">18</text>

<!-- Размер: От верха до верхних отверстий 6.0 мм (Y in [61.25, 70.25]) -->
<line x1="81.0" y1="61.25" x2="81.0" y2="70.25" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="89.0" y1="61.25" x2="79.0" y2="61.25" class="dim-ext" />
<line x1="99.0" y1="70.25" x2="79.0" y2="70.25" class="dim-ext" />
<text x="78.0" y="66.5" transform="rotate(-90 78.0 66.5)" class="dim-text">6.0</text>

<!-- Размер: От верхних отверстий до вала 9.0 мм (Y in [70.25, 83.75]) -->
<line x1="81.0" y1="70.25" x2="81.0" y2="83.75" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="99.0" y1="70.25" x2="79.0" y2="70.25" class="dim-ext" />
<line x1="95.0" y1="83.75" x2="79.0" y2="83.75" class="dim-ext" />
<text x="78.0" y="77.5" transform="rotate(-90 78.0 77.5)" class="dim-text">9.0</text>

<!-- Размер: От нижних отверстий до низа редуктора 7.0 мм (Y in [119.75, 130.25]) -->
<line x1="81.0" y1="119.75" x2="81.0" y2="130.25" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="99.0" y1="119.75" x2="79.0" y2="119.75" class="dim-ext" />
<line x1="89.0" y1="130.25" x2="79.0" y2="130.25" class="dim-ext" />
<text x="78.0" y="125.5" transform="rotate(-90 78.0 125.5)" class="dim-text">7.0</text>

<!-- Размер: Межосевое отверстий 33.0 мм (Y in [70.25, 119.75]) -->
<line x1="71.0" y1="70.25" x2="71.0" y2="119.75" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="79.0" y1="70.25" x2="69.0" y2="70.25" class="dim-ext" />
<line x1="79.0" y1="119.75" x2="69.0" y2="119.75" class="dim-ext" />
<text x="68.0" y="95.5" transform="rotate(-90 68.0 95.5)" class="dim-text">33.0</text>

<!-- Размер: Длина корпуса двигателя 30.8 мм (Y in [130.25, 176.45]) -->
<line x1="71.0" y1="130.25" x2="71.0" y2="176.45" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="89.0" y1="130.25" x2="69.0" y2="130.25" class="dim-ext" />
<line x1="94.0" y1="176.45" x2="69.0" y2="176.45" class="dim-ext" />
<text x="68.0" y="154.0" transform="rotate(-90 68.0 154.0)" class="dim-text">30.8</text>

<!-- Размер: Высота редуктора 46.0 мм (Y in [61.25, 130.25]) -->
<line x1="61.0" y1="61.25" x2="61.0" y2="130.25" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="79.0" y1="61.25" x2="59.0" y2="61.25" class="dim-ext" />
<line x1="79.0" y1="130.25" x2="59.0" y2="130.25" class="dim-ext" />
<text x="58.0" y="96.0" transform="rotate(-90 58.0 96.0)" class="dim-text">46.0</text>

<!-- Выноски к крепежным отверстиям и валу -->
<path d="M 128.5 70.25 L 145 64 L 175 64" class="leader" marker-start="url(#dot)" />
<text x="147" y="62.5" class="dim-text-left">4-M3 (глуб. 5)</text>

<path d="M 132.2 70.25 L 148 72 L 175 72" class="leader" marker-start="url(#dot)" />
<text x="150" y="70.5" class="dim-text-left">4-Ø7.4</text>

<path d="M 115 83.75 L 135 96 L 175 96" class="leader" marker-start="url(#dot)" />
<text x="137" y="94.5" class="dim-text-left">M3*0.5 глуб. 12 (в валу)</text>


<!-- ==================== ВИД СБОКУ (SideView) ==================== -->
<text x="215" y="32" class="view-title">Вид сбоку</text>

<!-- Осевые линии SideView (Z=0 при X=221.9, Y=0 при Y=83.75) -->
<line x1="180" y1="83.75" x2="250" y2="83.75" class="center-line" />
<line x1="202.4" y1="120" x2="202.4" y2="187" class="center-line" />

<!-- Толщина редуктора 25.2 мм (Z in [-25.2, 0] -> X in [184.1, 221.9]) -->
<line x1="184.1" y1="46" x2="221.9" y2="46" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="184.1" y1="59" x2="184.1" y2="44" class="dim-ext" />
<line x1="221.9" y1="59" x2="221.9" y2="44" class="dim-ext" />
<text x="203.0" y="44.5" class="dim-text">25.2</text>

<!-- Высота центрирующего буртика 2.0 мм (Z in [0, 2] -> X in [221.9, 224.9]) -->
<line x1="221.9" y1="53" x2="224.9" y2="53" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="221.9" y1="80" x2="221.9" y2="51" class="dim-ext" />
<line x1="224.9" y1="80" x2="224.9" y2="51" class="dim-ext" />
<text x="223.4" y="51.5" class="dim-text">2.0</text>

<!-- Вылет вала 14.0 мм (Z in [2, 16] -> X in [224.9, 245.9]) -->
<line x1="224.9" y1="46" x2="245.9" y2="46" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="224.9" y1="78" x2="224.9" y2="44" class="dim-ext" />
<line x1="245.9" y1="78" x2="245.9" y2="44" class="dim-ext" />
<text x="235.4" y="44.5" class="dim-text">14.0</text>

<!-- Длина лыски среза 12.0 мм (Z in [4, 16] -> X in [227.9, 245.9]) -->
<line x1="227.9" y1="53" x2="245.9" y2="53" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="227.9" y1="80" x2="227.9" y2="51" class="dim-ext" />
<line x1="245.9" y1="80" x2="245.9" y2="51" class="dim-ext" />
<text x="236.9" y="51.5" class="dim-text">12.0</text>

<!-- Диаметр вала Ø6 мм (D-cut) -->
<path d="M 238 80.0 L 250 95 L 275 95" class="leader" marker-start="url(#dot)" />
<text x="252" y="93.5" class="dim-text-left">Вал Ø6 (D-cut 5.5)</text>

<!-- Диаметр двигателя Ø24.4 мм -->
<line x1="184.1" y1="192" x2="220.7" y2="192" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="184.1" y1="178" x2="184.1" y2="194" class="dim-ext" />
<line x1="220.7" y1="178" x2="220.7" y2="194" class="dim-ext" />
<text x="202.4" y="196" class="dim-text">Ø24.4</text>

<!-- Вылет клемм 4.2 мм -->
<line x1="176" y1="176.45" x2="176" y2="182.75" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="185" y1="176.45" x2="174" y2="176.45" class="dim-ext" />
<line x1="185" y1="182.75" x2="174" y2="182.75" class="dim-ext" />
<text x="173" y="180.5" transform="rotate(-90 173 180.5)" class="dim-text">4.2</text>

</svg>'''

    sym_dim = doc.addObject('TechDraw::DrawViewSymbol', 'OverlayDimensions')
    sym_dim.Symbol = svg_dim
    page.addView(sym_dim)
    doc.recompute()

    sym_dim.Scale = 420.0 / (1488.0 * 25.4 / 96.0)
    sym_dim.X = 210.0
    sym_dim.Y = 148.5
    doc.recompute()

    out_pdf = f"{part_name}.pdf"
    out_fcstd = f"{part_name}.FCStd"
    out_png = f"{part_name}.png"

    export_drawing(doc, page, out_pdf, out_fcstd, out_png)
    print(f"SUCCESS: Drawing and 3D CAD files for {part_name} generated successfully!")


if __name__ == "__main__":
    generate_motor_jgy370_drawing()
