#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_base_frame.py
Поз. 1: Станина-шасси (Base Frame Chassis)
Обозначение: ВЧ.01.00.001

Назначение:
- Несущая силовая плита для базирования и закрепления всех узлов и механизмов:
  * Центральной неподвижной оси M8 карусели ягод и мальтийского механизма;
  * Мотор-редуктора постоянного тока JGY-370 с жесткой муфтой привода;
  * Стойки направляющей MGN9-100 узла пробивки косточек;
  * Опорного кронштейна горизонтального конического зубчатого колеса с кривошипом;
  * Двух регулируемых вертикальных стоек загрузочного бункера;
  * Приемного наклонного лотка отвода чистых ягод;
  * Воронки и патрубка гравитационного отвода косточек.
- Обеспечение минимальных габаритов прямоугольной формы с запасом +10 мм
  от внешних контуров опорных фланцев всех закрепляемых элементов:
  габариты 196.0 х 208.0 х 10.0 мм (X in [-66, 130], Y in [-106, 102]).
- 4 опорные ножки по углам высотой 30 мм с наклоном наружу 10° для обеспечения
  клиренса под размещение мотор-редуктора JGY-370 и повышенной устойчивости.
- Выемки в подошвах ножек под установку круглых резиновых шайб-виброопор Ø15 мм глубиной 5 мм.
- 100% адаптация для FDM 3D-печати в ориентации «кверх ногами» без поддержек (Zero Supports).
"""

import sys
import os
import math

# Добавление путей FreeCAD
sys.path.append('/usr/lib/freecad/lib')
sys.path.append('/usr/share/freecad/Mod/TechDraw')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from freecad_utils import (
    FreeCAD, Part, make_box, make_cylinder,
    create_drawing_page, add_part_view,
    fill_gost_title_block, export_drawing
)

# ====================================================================
# ГЕОМЕТРИЧЕСКИЕ ПАРАМЕТРЫ СТАНИНЫ-ШАССИ
# ====================================================================
# Габариты плиты в плане (рассчитаны по крайним точкам фланцев + 10 мм отступа):
# X in [-66.0, 130.0] -> ширина 196.0 мм
# Y in [-106.0, 102.0] -> длина 208.0 мм
X_MIN = -66.0
X_MAX = 130.0
Y_MIN = -106.0
Y_MAX = 102.0

# Высоты плиты и ножек
Z_PLATE_BOT = 0.0          # Нижняя плоскость плиты
Z_PLATE_TOP = 10.0         # Верхняя опорная плоскость (монтаж деталей)
PLATE_THICKNESS = 10.0     # Толщина плиты

LEG_HEIGHT = 30.0          # Высота ножек от нижней плоскости плиты (Z in [-30.0, 0.0])
LEG_ANGLE_DEG = 10.0       # Угол отклонения ножек в наружную сторону (град)
R_CORNER = 14.0            # Радиус скругления вертикальных наружных углов плиты

# Параметры резиновых шайб (виброопор)
WASHER_DIA = 15.0          # Диаметр резиновой шайбы
WASHER_R = WASHER_DIA / 2.0
WASHER_DEPTH = 5.0         # Глубина выемки под шайбу


def create_base_frame():
    """
    Создает чистую аналитическую B-Rep твердотельную модель станины-шасси:
    1. Прямоугольная плита основания 196 x 208 x 10 мм со скругленными углами R=14 мм.
    2. 4 угловые ножки высотой 30 мм, отклоненные наружу на 10 градусов.
    3. Выемки Ø15 мм глубиной 5 мм под круглые резиновые шайбы в торцах ножек.
    4. Монтажные и проходные отверстия под все элементы конструкции.
    """
    alpha = math.radians(LEG_ANGLE_DEG)
    
    # ----------------------------------------------------------------
    # 1. Плита основания со скругленными вертикальными углами
    # ----------------------------------------------------------------
    p1 = FreeCAD.Vector(X_MIN + R_CORNER, Y_MIN, 0)
    p2 = FreeCAD.Vector(X_MAX - R_CORNER, Y_MIN, 0)
    p3 = FreeCAD.Vector(X_MAX, Y_MIN + R_CORNER, 0)
    p4 = FreeCAD.Vector(X_MAX, Y_MAX - R_CORNER, 0)
    p5 = FreeCAD.Vector(X_MAX - R_CORNER, Y_MAX, 0)
    p6 = FreeCAD.Vector(X_MIN + R_CORNER, Y_MAX, 0)
    p7 = FreeCAD.Vector(X_MIN, Y_MAX - R_CORNER, 0)
    p8 = FreeCAD.Vector(X_MIN, Y_MIN + R_CORNER, 0)

    edges = [
        Part.makeLine(p1, p2),
        Part.Edge(Part.Arc(p2, FreeCAD.Vector(X_MAX - R_CORNER + R_CORNER * math.cos(math.radians(-45)),
                                              Y_MIN + R_CORNER + R_CORNER * math.sin(math.radians(-45)), 0), p3)),
        Part.makeLine(p3, p4),
        Part.Edge(Part.Arc(p4, FreeCAD.Vector(X_MAX - R_CORNER + R_CORNER * math.cos(math.radians(45)),
                                              Y_MAX - R_CORNER + R_CORNER * math.sin(math.radians(45)), 0), p5)),
        Part.makeLine(p5, p6),
        Part.Edge(Part.Arc(p6, FreeCAD.Vector(X_MIN + R_CORNER + R_CORNER * math.cos(math.radians(135)),
                                              Y_MAX - R_CORNER + R_CORNER * math.sin(math.radians(135)), 0), p7)),
        Part.makeLine(p7, p8),
        Part.Edge(Part.Arc(p8, FreeCAD.Vector(X_MIN + R_CORNER + R_CORNER * math.cos(math.radians(225)),
                                              Y_MIN + R_CORNER + R_CORNER * math.sin(math.radians(225)), 0), p1))
    ]
    wire_plate = Part.Wire(edges)
    plate = Part.Face(wire_plate).extrude(FreeCAD.Vector(0, 0, Z_PLATE_TOP))

    # ----------------------------------------------------------------
    # 2. Ножки по углам с отклонением наружу на 10 градусов
    # ----------------------------------------------------------------
    corners = [
        (X_MIN + R_CORNER, Y_MIN + R_CORNER, -1, -1),
        (X_MAX - R_CORNER, Y_MIN + R_CORNER, +1, -1),
        (X_MAX - R_CORNER, Y_MAX - R_CORNER, +1, +1),
        (X_MIN + R_CORNER, Y_MAX - R_CORNER, -1, +1),
    ]

    cone_len = (LEG_HEIGHT + 10.0) / math.cos(alpha)
    legs = []
    recesses = []

    # Твердотельный резец для горизонтальной подрезки ножек строго на плоскости Z = -LEG_HEIGHT
    trim_box = Part.makeBox(800.0, 800.0, 100.0, FreeCAD.Vector(-400.0, -400.0, -LEG_HEIGHT - 100.0))

    for cx, cy, sx, sy in corners:
        # Направляющий вектор оси ножки: наклон на 10 градусов вдоль диагонали угла наружу
        dir_x = sx * math.sin(alpha) * math.cos(math.radians(45.0))
        dir_y = sy * math.sin(alpha) * math.sin(math.radians(45.0))
        dir_z = -math.cos(alpha)
        axis = FreeCAD.Vector(dir_x, dir_y, dir_z).normalize()

        # Верх ножки заходит в тело плиты (Z = 2.0 мм) для монолитного слияния (fuse)
        p_top = FreeCAD.Vector(cx, cy, 2.0)
        
        # Коническая форма ножки: радиус вверху 14 мм (гладкое сопряжение с R14 угла),
        # радиус внизу ~11.5 мм (Ø23 мм), что оставляет толщину стенки 4 мм вокруг шайбы Ø15 мм
        cone = Part.makeCone(R_CORNER, 10.8, cone_len, p_top, axis)
        cone_trimmed = cone.cut(trim_box)
        legs.append(cone_trimmed)

        # Центр подошвы ножки на высоте Z = -LEG_HEIGHT (-30.0 мм)
        t_bot = (LEG_HEIGHT + 2.0) / math.cos(alpha)
        p_bot_center = p_top + axis * t_bot

        # Цилиндрическая выемка под круглую резиновую шайбу Ø15 мм, глубина 5 мм
        rec = Part.makeCylinder(WASHER_R, WASHER_DEPTH,
                                FreeCAD.Vector(p_bot_center.x, p_bot_center.y, -LEG_HEIGHT),
                                FreeCAD.Vector(0, 0, 1))
        recesses.append(rec)

    chassis = plate
    for l in legs:
        chassis = chassis.fuse(l)
    for r in recesses:
        chassis = chassis.cut(r)

    # ----------------------------------------------------------------
    # 3. Монтажные и технологические отверстия
    # ----------------------------------------------------------------
    # 3.1. Центральная ось M8 карусели ягод и мальтийского механизма:
    #      Сквозное отверстие Ø8.4 мм при (0, 0)
    chassis = chassis.cut(Part.makeCylinder(4.2, Z_PLATE_TOP + 4.0, FreeCAD.Vector(0, 0, -2.0), FreeCAD.Vector(0, 0, 1)))
    #      Цековка под головку винта или гайку M8 снизу Ø15.0 мм глубиной 5.0 мм
    chassis = chassis.cut(Part.makeCylinder(7.5, 5.0, FreeCAD.Vector(0, 0, -1.0), FreeCAD.Vector(0, 0, 1)))

    # 3.2. Мотор-редуктор JGY-370 и фланец муфты привода при (60.0, 0.0):
    #      Проходное центральное отверстие Ø17.0 мм (R=8.5 мм) под ступицу жесткой муфты
    chassis = chassis.cut(Part.makeCylinder(8.5, Z_PLATE_TOP + 4.0, FreeCAD.Vector(60.0, 0, -2.0), FreeCAD.Vector(0, 0, 1)))
    #      4 крепежных отверстия под винты M3 (Ø3.4 мм) при (60 ± 9.0, ± 9.0)
    for mx in [-9.0, 9.0]:
        for my in [-9.0, 9.0]:
            chassis = chassis.cut(Part.makeCylinder(1.7, Z_PLATE_TOP + 4.0, FreeCAD.Vector(60.0 + mx, my, -2.0), FreeCAD.Vector(0, 0, 1)))

    # 3.3. Стойка направляющей MGN9-100 (ВЧ.01.00.008):
    #      2 отверстия под винты M4 (Ø4.5 мм, R=2.25 мм)
    sg_holes = [
        FreeCAD.Vector(11.1532, -81.3178, -2.0),
        FreeCAD.Vector(50.9904, -58.3178, -2.0)
    ]
    for h in sg_holes:
        chassis = chassis.cut(Part.makeCylinder(2.25, Z_PLATE_TOP + 4.0, h, FreeCAD.Vector(0, 0, 1)))

    # 3.4. Кронштейн кривошипа горизонтального колеса (ВЧ.01.00.016):
    #      4 отверстия под винты M4 (Ø4.5 мм, R=2.25 мм)
    cb_holes = [
        FreeCAD.Vector(97.1244, -36.3013, -2.0),
        FreeCAD.Vector(108.1244, -55.3538, -2.0),
        FreeCAD.Vector(72.8756, -50.3013, -2.0),
        FreeCAD.Vector(83.8756, -69.3538, -2.0)
    ]
    for h in cb_holes:
        chassis = chassis.cut(Part.makeCylinder(2.25, Z_PLATE_TOP + 4.0, h, FreeCAD.Vector(0, 0, 1)))

    # 3.5. Вертикальные опоры загрузочного бункера (ВЧ.01.00.010):
    #      4 отверстия под винты M3 (Ø3.4 мм, R=1.7 мм)
    hs_holes = [
        FreeCAD.Vector(-50.0, 68.0, -2.0),
        FreeCAD.Vector(-38.0, 68.0, -2.0),
        FreeCAD.Vector(-50.0, -68.0, -2.0),
        FreeCAD.Vector(-38.0, -68.0, -2.0)
    ]
    for h in hs_holes:
        chassis = chassis.cut(Part.makeCylinder(1.7, Z_PLATE_TOP + 4.0, h, FreeCAD.Vector(0, 0, 1)))

    # 3.6. Приемный наклонный лоток ягод (ВЧ.01.00.010):
    #      2 отверстия под винты M3 (Ø3.4 мм, R=1.7 мм)
    chute_holes = [
        FreeCAD.Vector(52.1554, 55.3359, -2.0),
        FreeCAD.Vector(21.8446, 72.8359, -2.0)
    ]
    for h in chute_holes:
        chassis = chassis.cut(Part.makeCylinder(1.7, Z_PLATE_TOP + 4.0, h, FreeCAD.Vector(0, 0, 1)))

    # 3.7. Центральное окно сброса косточек в лоток (ВЧ.01.00.011):
    #      Коническое проходное отверстие под воронку (R1=14.5 снизу, R2=18.0 сверху)
    #      и вырез под наклонный патрубок отвода косточек (R=10.5 мм с уклоном)
    pit_cone = Part.makeCone(14.5, 18.0, Z_PLATE_TOP + 1.0, FreeCAD.Vector(22.0, -38.105, -0.5), FreeCAD.Vector(0, 0, 1))
    pit_pipe = Part.makeCylinder(10.5, 28.0, FreeCAD.Vector(22.0, -38.105, 1.0), FreeCAD.Vector(0, -1, -0.6))
    chassis = chassis.cut(pit_cone).cut(pit_pipe)

    if not chassis.isValid():
        raise RuntimeError("Base frame shape is invalid!")

    return chassis

create_part = create_base_frame


def generate_base_frame_drawing(part_name="part_base_frame",
                                doc_code="ВЧ.01.00.001",
                                title_name="Станина-шасси",
                                material="PETG",
                                scale=0.55,
                                sheet="A3_Landscape",
                                notes=None):
    """
    Генерирует официальный рабочий чертеж станины-шасси по ГОСТ (ЕСКД):
    - Вид сверху (Top View) с показом контура 196x208 мм, скруглений R14 и отверстий;
    - Главный вид (Front View) с показом ножек высотой 30 мм, толщины плиты 10 мм и уклона 10°;
    - Аксонометрический вид (изометрия);
    - Векторный оверлей размеров по ГОСТ 2.307;
    - Штамп по ГОСТ 2.104 и технические требования по ГОСТ 2.316.
    """
    shape = create_base_frame()

    doc = FreeCAD.newDocument(f"Doc_{part_name}")
    feat = doc.addObject("Part::Feature", part_name)
    feat.Shape = shape
    doc.recompute()

    page, template = create_drawing_page(doc, sheet, f"Page_{part_name}")

    # Координаты проекционных видов на формате А3 (420 x 297 мм)
    # Центр детали в плане: X_mid = 32.0, Y_mid = -2.0, Z_mid = -10.0
    x_front = 145.0
    y_front = 70.0

    x_top = 145.0
    y_top = 185.0

    x_iso = 325.0
    y_iso = 195.0

    # 1. Вид спереди (Front View)
    v_front = add_part_view(doc, page, feat, "FrontView", (0.0, -1.0, 0.0), scale, x_front, y_front)
    v_front.XDirection = FreeCAD.Vector(1.0, 0.0, 0.0)

    # 2. Вид сверху (Top View, выровнен по оси X)
    v_top = add_part_view(doc, page, feat, "TopView", (0.0, 0.0, 1.0), scale, x_top, y_top)
    v_top.XDirection = FreeCAD.Vector(1.0, 0.0, 0.0)

    # 3. Изометрический вид
    v_iso = add_part_view(doc, page, feat, "IsoView", (1.0, -1.2, 0.9), scale * 0.85, x_iso, y_iso)
    doc.recompute()

    # 4. Основная надпись (штамп ГОСТ 2.104)
    title_fields = {
        'Номер': doc_code,
        'Название': title_name,
        'Масштаб': '1:2',
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
            "2. Материал: пластик PETG (пищевой контакт / технический).",
            "   Заполнение не менее 40%, не менее 4 сплошных периметров.",
            "3. Базовая плоскость 3D-печати — верхняя монтажная плоскость (Z = 10.0 мм, стол принтера).",
            "   Печать детали выполнять в перевернутом положении («кверх ногами») БЕЗ поддержек (Zero Supports).",
            "4. В торцевые выемки ножек Ø15x5 установить резиновые шайбы-виброопоры Ø15 мм.",
            "5. Клиренс под станиной для электромотора JGY-370 составляет не менее 5.0 мм.",
            "6. Предельные отклонения размеров по ГОСТ 30893.1-m (±t2/2)."
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

    # 6. Векторный оверлей размеров и контуров (ГОСТ 2.307 / ГОСТ 2.303)
    svg_dim = '''<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">
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
  .contour-line { stroke: #000; stroke-width: 0.6; fill: none; }
  .contour-fill { fill: #fdfdfd; stroke: #000; stroke-width: 0.6; }
  .hidden-line { stroke: #000; stroke-width: 0.3; stroke-dasharray: 2.0,1.2; fill: none; }
  .dim-line { stroke: #000; stroke-width: 0.35; fill: none; }
  .dim-ext { stroke: #000; stroke-width: 0.25; fill: none; }
  .center-line { stroke: #000; stroke-width: 0.25; stroke-dasharray: 6,1.5,1.5,1.5; fill: none; }
  .dim-text { font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: middle; font-weight: bold; }
  .dim-text-left { font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: start; }
  .view-title { font-family: osifont, Arial, sans-serif; font-size: 4.5px; fill: #000; text-anchor: middle; font-weight: bold; }
  .leader { stroke: #000; stroke-width: 0.35; fill: none; }
</style>

<!-- ==================== ВИД СВЕРХУ (TopView) ==================== -->
<text x="145" y="32" class="view-title">Вид сверху</text>

<!-- Наружный контур плиты 196х208 со скруглениями R14 -->
<rect x="91.1" y="54.8" width="107.8" height="114.4" rx="7.7" ry="7.7" class="contour-line" />

<!-- 4 ножки в углах (вид сверху: скрытые контуры подошвы Ø23 и выемки Ø15) -->
<circle cx="96.7" cy="60.4" r="6.3" class="hidden-line" />
<circle cx="96.7" cy="60.4" r="4.1" class="hidden-line" />

<circle cx="193.3" cy="60.4" r="6.3" class="hidden-line" />
<circle cx="193.3" cy="60.4" r="4.1" class="hidden-line" />

<circle cx="193.3" cy="163.6" r="6.3" class="hidden-line" />
<circle cx="193.3" cy="163.6" r="4.1" class="hidden-line" />

<circle cx="96.7" cy="163.6" r="6.3" class="hidden-line" />
<circle cx="96.7" cy="163.6" r="4.1" class="hidden-line" />

<!-- Центральная ось M8: сквозное отверстие Ø8.4 и цековка Ø15 снизу -->
<circle cx="127.4" cy="110.9" r="2.3" class="contour-line" />
<circle cx="127.4" cy="110.9" r="4.1" class="hidden-line" />

<!-- Мотор JGY-370: проходное отверстие Ø17 и 4 отв. М3 на межцентровом 18 мм -->
<circle cx="160.4" cy="110.9" r="4.7" class="contour-line" />
<circle cx="155.4" cy="115.8" r="0.9" class="contour-line" />
<circle cx="155.4" cy="106.0" r="0.9" class="contour-line" />
<circle cx="165.3" cy="115.8" r="0.9" class="contour-line" />
<circle cx="165.3" cy="106.0" r="0.9" class="contour-line" />

<!-- Стойка направляющей MGN9: 2 отверстия Ø4.5 -->
<circle cx="133.5" cy="155.6" r="1.2" class="contour-line" />
<circle cx="155.4" cy="143.0" r="1.2" class="contour-line" />

<!-- Кронштейн кривошипа: 4 отверстия Ø4.5 -->
<circle cx="180.8" cy="130.9" r="1.2" class="contour-line" />
<circle cx="186.9" cy="141.3" r="1.2" class="contour-line" />
<circle cx="167.5" cy="138.6" r="1.2" class="contour-line" />
<circle cx="173.5" cy="149.0" r="1.2" class="contour-line" />

<!-- Опоры бункера: 4 отверстия Ø3.4 -->
<circle cx="99.9" cy="73.5" r="0.9" class="contour-line" />
<circle cx="106.5" cy="73.5" r="0.9" class="contour-line" />
<circle cx="99.9" cy="148.3" r="0.9" class="contour-line" />
<circle cx="106.5" cy="148.3" r="0.9" class="contour-line" />

<!-- Приемный лоток: 2 отверстия Ø3.4 -->
<circle cx="156.1" cy="80.5" r="0.9" class="contour-line" />
<circle cx="139.4" cy="70.8" r="0.9" class="contour-line" />

<!-- Окно сброса косточек: коническое проходное отверстие -->
<circle cx="139.5" cy="131.9" r="9.9" class="contour-line" />
<circle cx="139.5" cy="131.9" r="8.0" class="hidden-line" />

<!-- Осевые линии вида сверху -->
<line x1="85" y1="110.9" x2="205" y2="110.9" class="center-line" />
<line x1="127.4" y1="50" x2="127.4" y2="175" class="center-line" />
<line x1="160.4" y1="98" x2="160.4" y2="124" class="center-line" />

<!-- РАЗМЕРЫ НА ВИДЕ СВЕРХУ -->
<!-- Ширина 196* мм -->
<line x1="91.1" y1="44" x2="198.9" y2="44" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="91.1" y1="52" x2="91.1" y2="42" class="dim-ext" />
<line x1="198.9" y1="52" x2="198.9" y2="42" class="dim-ext" />
<text x="145" y="42.5" class="dim-text">196*</text>

<!-- Длина 208* мм -->
<line x1="77" y1="54.8" x2="77" y2="169.2" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="88" y1="54.8" x2="75" y2="54.8" class="dim-ext" />
<line x1="88" y1="169.2" x2="75" y2="169.2" class="dim-ext" />
<text x="74" y="112" transform="rotate(-90 74 112)" class="dim-text">208*</text>

<!-- Выноска 4 угла R14 -->
<path d="M 93 60 L 65 48 L 40 48" class="leader" marker-start="url(#dot)" />
<text x="38" y="46.5" class="dim-text-left">4 угла R14</text>

<!-- Выноска центральной оси М8 -->
<path d="M 127 113 L 105 130 L 70 130" class="leader" marker-start="url(#dot)" />
<text x="68" y="128.5" class="dim-text-left">Ø8,4 (ось М8); цек. Ø15 глуб. 5</text>

<!-- Выноска отверстий мотора JGY-370 -->
<path d="M 160 113 L 180 135 L 215 135" class="leader" marker-start="url(#dot)" />
<text x="182" y="133.5" class="dim-text-left">Ø17 (муфта); 4 отв. М3</text>


<!-- ==================== ГЛАВНЫЙ ВИД (FrontView) ==================== -->
<text x="145" y="202" class="view-title">Главный вид</text>

<!-- Контур плиты основания: Z in [0, 10] -> Y in [216.0, 221.5] -->
<rect x="91.1" y="216.0" width="107.8" height="5.5" class="contour-line" />

<!-- Левая наклонная ножка (наклон наружу влево 10°) -->
<path d="M 91.1 221.5
         L 89.0 238.0
         L 101.7 238.0
         L 104.5 221.5 Z" class="contour-line" />
<!-- Выемка под резиновую шайбу левой ножки -->
<line x1="91.2" y1="235.2" x2="99.5" y2="235.2" class="hidden-line" />
<line x1="91.2" y1="235.2" x2="91.2" y2="238.0" class="hidden-line" />
<line x1="99.5" y1="235.2" x2="99.5" y2="238.0" class="hidden-line" />

<!-- Правая наклонная ножка (наклон наружу вправо 10°) -->
<path d="M 198.9 221.5
         L 201.0 238.0
         L 188.3 238.0
         L 185.5 221.5 Z" class="contour-line" />
<!-- Выемка под резиновую шайбу правой ножки -->
<line x1="190.5" y1="235.2" x2="198.8" y2="235.2" class="hidden-line" />
<line x1="190.5" y1="235.2" x2="190.5" y2="238.0" class="hidden-line" />
<line x1="198.8" y1="235.2" x2="198.8" y2="238.0" class="hidden-line" />

<!-- Опорная линия стола -->
<line x1="80" y1="238.0" x2="210" y2="238.0" class="center-line" />

<!-- РАЗМЕРЫ НА ГЛАВНОМ ВИДЕ -->
<!-- Толщина плиты 10 мм -->
<line x1="77" y1="216.0" x2="77" y2="221.5" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="88" y1="216.0" x2="75" y2="216.0" class="dim-ext" />
<line x1="88" y1="221.5" x2="75" y2="221.5" class="dim-ext" />
<text x="74" y="219.2" transform="rotate(-90 74 219.2)" class="dim-text">10</text>

<!-- Габаритная высота 40* мм -->
<line x1="68" y1="216.0" x2="68" y2="238.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="72" y1="216.0" x2="66" y2="216.0" class="dim-ext" />
<line x1="72" y1="238.0" x2="66" y2="238.0" class="dim-ext" />
<text x="65" y="227.0" transform="rotate(-90 65 227.0)" class="dim-text">40*</text>

<!-- Высота ножек 30* мм -->
<line x1="210" y1="221.5" x2="210" y2="238.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<line x1="202" y1="221.5" x2="212" y2="221.5" class="dim-ext" />
<line x1="202" y1="238.0" x2="212" y2="238.0" class="dim-ext" />
<text x="214" y="230.0" transform="rotate(-90 214 230.0)" class="dim-text">30*</text>

<!-- Угол отклонения ножки 10° -->
<text x="83" y="232" class="dim-text">10°</text>

<!-- Выноска выемок под шайбы -->
<path d="M 95 238 L 80 252 L 35 252" class="leader" marker-start="url(#dot)" />
<text x="33" y="250.5" class="dim-text-left">4 выемки Ø15 глуб. 5</text>
<text x="33" y="255.5" class="dim-text-left" font-size="2.8px">(под резиновые шайбы-виброопоры)</text>

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
    generate_base_frame_drawing()
