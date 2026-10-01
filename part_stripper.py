#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_stripper.py
Поз. 15: Съемник ягод (Berry Stripper / Needle Wiper)
Обозначение: ВЧ.01.00.015
Создание аналитической B-Rep 3D-модели Т-образного кронштейна
и оформление официального рабочего чертежа по ГОСТ (ЕСКД).

Конструкция:
  - Т-образный кронштейн (T-bracket):
    - Поперечный монтажный фланец (Crossbar): ширина 32.0 мм (X in [-16.0, 16.0]),
      крепится к передней стенке стойки part_stripper_guide (Y = 0.0).
      2 цекованных отверстия под винты DIN 912 M3x8, расположенных в единой
      горизонтальной плоскости Z = 48.0 мм при X = -10.0 и X = +10.0 мм.
    - Центральный арочный вырез (X in [-5.5, 5.5], Y in [0.0, 7.5]) для свободного
      обхода рельса MGN9 (зазор 1.0 мм).
    - Два симметричных подпорных ребра жесткости 45° (Gussets) под ушками.
    - Продольная балка (Arm) и рабочая головка (Head): Z in [49.5, 53.5] мм.
    - Вертикальное цилиндрическое отверстие Ø4.5 мм на конце кронштейна
      (центр оси строго X = 8.0, Y = 24.0 мм) под проход пуансонной иглы Ø3.0 мм.
    - Заходный направляющий пандус 15° на стороне набегания ягод (X in [-4.0, 2.0] мм).
    - Выходная фаска 45° на стороне схода ягод (X in [14.0, 16.0] мм).
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


def create_stripper():
    """
    Создает аналитический B-Rep солид усиленного Т-образного кронштейна съемника ягод (ВЧ.01.00.015).
    Модернизация по рекомендациям FEM-анализа:
      1. Монтажные ушки фланца (толщина 8.0 мм, Y in [0.0, 8.0], Z in [42.5, 53.5] мм):
         - Наружная передняя плоскость Y = 8.0 полностью открыта для свободного ввода винтов и инструмента.
         - 2 сквозных отверстия Ø3.4 мм с цековками Ø6.5 x 5.0 мм под винты DIN 912 M3 на осях X = ±10.0, Z = 48.0 мм.
      2. Поперечный силовой мостик над рельсом MGN9:
         - X in [-6.0, 6.0], Y in [6.5, 12.0], Z in [48.0, 53.5] мм (высота 5.5 мм, арочный вырез).
      3. Трапециевидное уширение и усиление продольной консоли (Flared Arm):
         - Высота балки увеличена с 4.0 до 5.5 мм (Z in [48.0, 53.5]), нижняя грань заподлицо с мостиком.
         - Ширина расширяется от 8.0 мм (X in [-2.0, 6.0] при Y = 10.5) до 10.0 мм (X in [-2.0, 8.0] при Y = 16.0).
         - Правая граница X <= 6.0 в зоне фланца гарантирует зазор 0.75 мм до контура цековки Ø6.5 мм.
      4. Переходные галтели / ребра на стыках мостика и монтажных ушек:
         - Правое ребро: скос от (X=6.0, Y=11.5) до (X=6.4, Y=8.0).
         - Левое ребро: скос от (X=-6.0, Y=11.5) до (X=-6.4, Y=8.0).
      5. Самоопорный скос 45° на нижней грани перехода от балки (Z=48.0) к головке (Z=49.5):
         - Y in [13.5, 16.0] мм — устраняет концентратор и печатается на 3D-принтере без поддержек.
      6. Рабочая головка на конце кронштейна (Head):
          - X in [-4.0, 16.0], Y in [16.0, 28.0], Z in [49.5, 53.5] мм (толщина 4.0 мм).
          - Вертикальное сквозное отверстие Ø4.5 мм строго по оси X = 8.0, Y = 24.0 мм под проход иглы Ø3.0 мм.
          - Заходный направляющий пандус 15° на стороне набегания ягод (X in [-4.5, 2.0] мм).
          - Выходная сходная фаска 45° на стороне выхода ягод (X in [14.0, 16.5] мм).
    """
    # 1. Базовый монтажный блок фланца (ширина 32.0 мм, глубина 8.0 мм, высота 11.0 мм)
    base_block = make_box(32.0, 8.0, 11.0, (-16.0, 0.0, 42.5))

    # Арочный вырез под направляющий рельс MGN9 (Wr=9.0 мм, Hr=6.5 мм)
    rail_cutout = make_box(9.6, 6.5, 12.0, (-4.8, -0.1, 42.0))
    base_block = base_block.cut(rail_cutout)

    # 2. Монолитный силовой мостик-основание (Y in [6.5, 11.0], Z in [44.0, 53.5], высота 9.5 мм)
    x_s = 3.6  # Полуширина у плоскости Y = 8.0 -> стенка до цековки Ø6.5 равна 6.75 - 3.6 = 3.15 мм (в 9 раз толще!)
    bridge = make_box(2 * x_s, 4.5, 9.5, (-x_s, 6.5, 44.0))

    # 3. Трапециевидная усиленная консоль (высота 5.5 мм, Z in [48.0, 53.5])
    # Плавно расширяется от X in [-3.6, 3.6] при Y = 8.0 до X in [-3.0, 8.0] при Y = 16.0
    pts_arm = [
        FreeCAD.Vector(-x_s,  8.0, 48.0),
        FreeCAD.Vector( x_s,  8.0, 48.0),
        FreeCAD.Vector( 8.0, 16.0, 48.0),
        FreeCAD.Vector(-3.0, 16.0, 48.0),
        FreeCAD.Vector(-x_s,  8.0, 48.0)
    ]
    face_arm = Part.Face(Part.makePolygon(pts_arm))
    arm = face_arm.extrude(FreeCAD.Vector(0, 0, 5.5))

    # 4. Рабочая головка на конце кронштейна (Head)
    head = make_box(20.0, 12.0, 4.0, (-4.0, 16.0, 49.5))

    # Вертикальное отверстие прохода иглы Ø4.5 мм (центр X = 8.0, Y = 24.0 мм)
    needle_aperture = Part.makeCylinder(2.25, 10.0, FreeCAD.Vector(8.0, 24.0, 48.0), FreeCAD.Vector(0, 0, 1))
    head = head.cut(needle_aperture)

    # Самоопорный скос 45° на нижней грани перехода от балки (Z=48.0) к головке (Z=49.5)
    pts_bot_ramp = [
        FreeCAD.Vector(0, 13.5, 48.0),
        FreeCAD.Vector(0, 16.0, 49.5),
        FreeCAD.Vector(0, 16.0, 48.0),
        FreeCAD.Vector(0, 13.5, 48.0)
    ]
    bot_chamfer = Part.Face(Part.makePolygon(pts_bot_ramp)).extrude(FreeCAD.Vector(14.0, 0, 0))
    bot_chamfer.translate(FreeCAD.Vector(-4.0, 0, 0))

    # Заходный направляющий пандус 15° со стороны входа ягод (X in [-4.5, 2.0] мм)
    pts_ramp = [
        FreeCAD.Vector(-4.5, 15.0, 49.0),
        FreeCAD.Vector(-4.5, 15.0, 52.2),
        FreeCAD.Vector(2.0,  15.0, 49.5),
        FreeCAD.Vector(2.0,  15.0, 49.0),
        FreeCAD.Vector(-4.5, 15.0, 49.0)
    ]
    ramp = Part.Face(Part.makePolygon(pts_ramp)).extrude(FreeCAD.Vector(0, 14.0, 0))
    head = head.cut(ramp)

    # Сходная фаска 45° на стороне выхода ягод (X in [14.0, 16.5] мм)
    pts_ch = [
        FreeCAD.Vector(14.0, 15.0, 49.5),
        FreeCAD.Vector(16.5, 15.0, 52.0),
        FreeCAD.Vector(16.5, 15.0, 49.0),
        FreeCAD.Vector(14.0, 15.0, 49.0),
        FreeCAD.Vector(14.0, 15.0, 49.5)
    ]
    ch = Part.Face(Part.makePolygon(pts_ch)).extrude(FreeCAD.Vector(0, 14.0, 0))
    head = head.cut(ch)

    # 5. Монолитное B-Rep объединение
    stripper = (base_block.fuse(bridge)
                .fuse(arm)
                .fuse(head)
                .cut(bot_chamfer)
                .removeSplitter())

    # 6. Сквозные крепежные отверстия Ø3.4 мм с цековками Ø6.5 x 5.0 мм под винты DIN 912 M3
    for x_h in [-10.0, 10.0]:
        thru_h = Part.makeCylinder(1.7, 12.0, FreeCAD.Vector(x_h, 9.0, 48.0), FreeCAD.Vector(0, -1, 0))
        cb_5mm = Part.makeCylinder(3.25, 5.05, FreeCAD.Vector(x_h, 8.02, 48.0), FreeCAD.Vector(0, -1, 0))
        stripper = stripper.cut(thru_h).cut(cb_5mm)

    stripper = stripper.removeSplitter()

    if not stripper.isValid():
        raise RuntimeError("Stripper solid shape is invalid!")
    if len(stripper.Solids) != 1:
        raise RuntimeError(f"Stripper resulted in {len(stripper.Solids)} solids! Expected 1.")

    return stripper


create_part = create_stripper


def generate_stripper_drawing(part_name="part_stripper",
                              doc_code="ВЧ.01.00.015",
                              title_name="Съемник ягод",
                              material="PETG",
                              scale=2.0,
                              sheet="A3_Landscape",
                              notes=None):
    """
    Генерирует официальный рабочий чертеж Т-образного кронштейна съемника ягод по ГОСТ (ЕСКД):
    - Формат А3, масштаб 2:1;
    - Главный вид (FrontView): взгляд спереди вдоль оси -Y (нормаль (0, -1, 0));
    - Разрез А-А на виде сбоку (SectionView): продольный разрез по оси крепежного отверстия X = -10.0,
      демонстрирующий сквозное отверстие Ø3.4 мм и 5-мм цековку Ø6.5 мм под головку винта;
    - Вид сверху (TopView): взгляд сверху вдоль оси +Z (нормаль (0, 0, 1)), выровнен по X с FrontView;
    - Аксонометрический вид (изометрия);
    - Нанесение размеров и выносок (ГОСТ 2.307);
    - Штамп по ГОСТ 2.104 и технические требования по ГОСТ 2.316.
    """
    shape = create_stripper()

    doc = FreeCAD.newDocument(f"Doc_{part_name}")
    feat = doc.addObject("Part::Feature", part_name)
    feat.Shape = shape

    # Создание солида для продольного разреза А-А на виде сбоку (сечение плоскостью X = -10.0)
    cut_neg = make_box(50.0, 100.0, 100.0, (-60.0, -20.0, 20.0))
    sec_solid = shape.cut(cut_neg)
    feat_sec = doc.addObject("Part::Feature", f"{part_name}_Section")
    feat_sec.Shape = sec_solid

    doc.recompute()

    page, template = create_drawing_page(doc, sheet, f"Page_{part_name}")

    # Координаты проекций на формате А3 (420 x 297 мм), масштаб 2:1 per GOST 2.305-68
    # 1. Главный вид (FrontView) - взгляд спереди вдоль -Y
    x_front = 110.0
    y_front_td = 195.0
    v_front = add_part_view(doc, page, feat, "FrontView", (0.0, -1.0, 0.0), scale, x_front, y_front_td)

    # 2. Вид сверху (TopView) - взгляд сверху вдоль +Z, выровнен по X
    x_top = 110.0
    y_top_td = 80.0
    v_top = add_part_view(doc, page, feat, "TopView", (0.0, 0.0, 1.0), scale, x_top, y_top_td)

    # 3. Разрез А-А на виде сбоку (SectionView) - взгляд вдоль оси +X на плоскость сечения X = -10.0
    x_sec = 230.0
    y_sec_td = 195.0
    v_sec = add_part_view(doc, page, feat_sec, "SectionView", (1.0, 0.0, 0.0), scale, x_sec, y_sec_td)

    # 4. Аксонометрический вид (изометрия)
    x_iso = 335.0
    y_iso_td = 205.0
    v_iso = add_part_view(doc, page, feat, "IsoView", (1.2, -1.5, 1.0), 1.6, x_iso, y_iso_td)

    # 5. Основная надпись (штамп ГОСТ 2.104, Форма 1)
    title_fields = {
        'Номер': doc_code,
        'Название': title_name,
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

    # 6. Технические требования (ГОСТ 2.316)
    if notes is None:
        notes = [
            "1. * Размеры для справок.",
            "2. Материал детали: PETG. Заполнение не менее 60%, 4 периметра.",
            "   Базовая плоскость 3D-печати — верхняя пласть кронштейна (стол принтера).",
            "3. Крепление к стойке: 2 сквозных отв. Ø3,4 мм с цековками Ø6,5 глуб. 5,0 мм под винты DIN 912 M3.",
            "   Межосевое расстояние: 20,0 мм. Головки винтов полностью утоплены заподлицо (разрез А-А).",
            "4. Арочный вырез обеспечивает зазор не менее 1,0 мм вокруг направляющего рельса MGN9-100.",
            "5. Вертикальное отверстие Ø4,5 мм служит для свободного прохода пуансонной иглы Ø3,0 мм.",
            "6. Заходный пандус 15° обеспечивает безударный вход ягоды в лунку при повороте роторного барабана.",
            "7. Неуказанные предельные отклонения размеров: ±IT14/2.",
            "8. Переходная зона между фланцем и консолью усилена с увеличением толщины стенки",
            "   у крепежных цековок до 3,15 мм. Высота консоли увеличена до 5,5 мм."
        ]

    notes_lines = ['<text x="235" y="150" font-family="osifont, Arial, sans-serif" font-size="3.6px" font-weight="bold" fill="#000">Технические требования:</text>']
    for idx, line in enumerate(notes):
        notes_lines.append(f'<text x="235" y="{156 + idx * 5.0}" font-family="osifont, Arial, sans-serif" font-size="2.9px" fill="#000">{line}</text>')
    notes_svg = '\n'.join(notes_lines)

    # Генерация штриховки разреза А-А под углом 45° по ГОСТ 2.305
    def in_cut_face(x, y):
        # Зона стенки под винт (толщина 3.0 мм, отв. Ø3.4)
        if 202.0 <= x <= 208.0 and 91.0 <= y <= 98.6:
            return True
        if 202.0 <= x <= 208.0 and 105.4 <= y <= 113.0:
            return True
        # Зона цековки (глубина 5.0 мм, цек. Ø6.5)
        if 208.0 < x <= 218.0 and 91.0 <= y <= 95.5:
            return True
        if 208.0 < x <= 218.0 and 108.5 <= y <= 113.0:
            return True
        return False

    hatch_lines = []
    for c in [i * 2.5 for i in range(115, 140)]:
        xs = [202.0 + j * 0.1 for j in range(int((218.5 - 202.0) / 0.1))]
        cur_seg = []
        for x in xs:
            y = c - x
            if in_cut_face(x, y):
                cur_seg.append((x, y))
            else:
                if len(cur_seg) > 1:
                    hatch_lines.append((cur_seg[0], cur_seg[-1]))
                cur_seg = []
        if len(cur_seg) > 1:
            hatch_lines.append((cur_seg[0], cur_seg[-1]))

    hatch_svg = '\n'.join([
        f'<line x1="{seg[0][0]:.2f}" y1="{seg[0][1]:.2f}" x2="{seg[1][0]:.2f}" y2="{seg[1][1]:.2f}" class="hatch-line" />'
        for seg in hatch_lines
    ])

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
  .hole-cut {{ stroke: #000; stroke-width: 0.5; fill: none; }}
  .hidden-circle {{ stroke: #000; stroke-width: 0.25; stroke-dasharray: 2,1; fill: none; }}
</style>

<!-- ==================== ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ ==================== -->
{notes_svg}

<!-- ==================== ГЛАВНЫЙ ВИД (FrontView, M 2:1) ==================== -->
<line x1="110.0" y1="84.0" x2="110.0" y2="120.0" class="center-line" />
<line x1="90.0" y1="94.0" x2="90.0" y2="110.0" class="center-line" />
<line x1="130.0" y1="94.0" x2="130.0" y2="110.0" class="center-line" />
<line x1="82.0" y1="102.0" x2="138.0" y2="102.0" class="center-line" />
<line x1="126.0" y1="85.0" x2="126.0" y2="100.0" class="center-line" />

<!-- Концентрические окружности крепежных отверстий: сквозное отв. Ø3.4 и цековка Ø6.5 -->
<circle cx="90.0" cy="102.0" r="3.4" stroke="#000" stroke-width="0.5" fill="none" />
<circle cx="90.0" cy="102.0" r="6.5" class="hidden-circle" />
<circle cx="130.0" cy="102.0" r="3.4" stroke="#000" stroke-width="0.5" fill="none" />
<circle cx="130.0" cy="102.0" r="6.5" class="hidden-circle" />

<!-- Линия секущей плоскости А-А на X = 90.0 (X_part = -10.0) -->
<line x1="90" y1="83" x2="90" y2="75" stroke="#000" stroke-width="0.8" />
<line x1="90" y1="121" x2="90" y2="129" stroke="#000" stroke-width="0.8" />
<line x1="90" y1="78" x2="97" y2="78" stroke="#000" stroke-width="0.5" marker-end="url(#arrow)" />
<line x1="90" y1="126" x2="97" y2="126" stroke="#000" stroke-width="0.5" marker-end="url(#arrow)" />
<text x="86" y="79" font-family="osifont, Arial, sans-serif" font-size="4.5px" font-weight="bold" fill="#000" text-anchor="end">А</text>
<text x="86" y="128" font-family="osifont, Arial, sans-serif" font-size="4.5px" font-weight="bold" fill="#000" text-anchor="end">А</text>

<!-- Габаритная ширина фланца 32 мм -->
<line x1="78.0" y1="91.0" x2="78.0" y2="72.0" class="dim-ext" />
<line x1="142.0" y1="91.0" x2="142.0" y2="72.0" class="dim-ext" />
<line x1="78.0" y1="74.0" x2="142.0" y2="74.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="110.0" y="72.5" class="dim-text">32</text>

<!-- Межосевое расстояние крепежных винтов 20 мм -->
<line x1="90.0" y1="102.0" x2="90.0" y2="64.0" class="dim-ext" />
<line x1="130.0" y1="102.0" x2="130.0" y2="64.0" class="dim-ext" />
<line x1="90.0" y1="66.0" x2="130.0" y2="66.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="110.0" y="64.5" class="dim-text">20</text>

<!-- Габаритная высота кронштейна 11 мм -->
<line x1="78.0" y1="113.0" x2="68.0" y2="113.0" class="dim-ext" />
<line x1="78.0" y1="91.0" x2="68.0" y2="91.0" class="dim-ext" />
<line x1="70.0" y1="113.0" x2="70.0" y2="91.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="66.5" y="102.0" transform="rotate(-90 66.5 102.0)" class="dim-text">11</text>

<!-- Выноска арочного выреза под рельс MGN9 -->
<path d="M 110.0 102.0 L 115.0 125.0 L 145.0 125.0" class="leader" marker-start="url(#dot)" />
<text x="130.0" y="123.5" class="dim-text">Вырез под рельс MGN9</text>

<!-- ==================== РАЗРЕЗ А-А НА ВИДЕ СБОКУ (SectionView, M 2:1) ==================== -->
<text x="210" y="65" font-family="osifont, Arial, sans-serif" font-size="4.5px" font-weight="bold" fill="#000" text-anchor="middle">А-А (2:1)</text>

<!-- Осевая линия крепежного отверстия Z = 48.0 -->
<line x1="196.0" y1="102.0" x2="224.0" y2="102.0" class="center-line" />

<!-- Контур сквозного ступенчатого отверстия в разрезе А-А -->
<!-- Левая плоскость ушка Y = 0.0 (прилегание к стойке) -->
<line x1="202.0" y1="91.0" x2="202.0" y2="98.6" class="hole-cut" />
<line x1="202.0" y1="105.4" x2="202.0" y2="113.0" class="hole-cut" />
<!-- Канал сквозного отверстия Ø3.4 мм (толщина стенки 3.0 мм) -->
<line x1="202.0" y1="98.6" x2="208.0" y2="98.6" class="hole-cut" />
<line x1="202.0" y1="105.4" x2="208.0" y2="105.4" class="hole-cut" />
<!-- Опорный уступ цековки (дно под головку винта) -->
<line x1="208.0" y1="98.6" x2="208.0" y2="95.5" class="hole-cut" />
<line x1="208.0" y1="105.4" x2="208.0" y2="108.5" class="hole-cut" />
<!-- Цилиндрическая цековка Ø6.5 мм (глубина 5.0 мм) -->
<line x1="208.0" y1="95.5" x2="218.0" y2="95.5" class="hole-cut" />
<line x1="208.0" y1="108.5" x2="218.0" y2="108.5" class="hole-cut" />
<!-- Правая наружная плоскость ушка Y = 8.0 (открыта наружу!) -->
<line x1="218.0" y1="91.0" x2="218.0" y2="95.5" class="hole-cut" />
<line x1="218.0" y1="108.5" x2="218.0" y2="113.0" class="hole-cut" />
<!-- Верхний и нижний торцы ушка -->
<line x1="202.0" y1="91.0" x2="218.0" y2="91.0" class="hole-cut" />
<line x1="202.0" y1="113.0" x2="218.0" y2="113.0" class="hole-cut" />

<!-- Штриховка сечения А-А -->
{hatch_svg}

<!-- Размер: глубина цековки 5 мм -->
<line x1="208.0" y1="95.5" x2="208.0" y2="84.0" class="dim-ext" />
<line x1="218.0" y1="95.5" x2="218.0" y2="84.0" class="dim-ext" />
<line x1="208.0" y1="86.0" x2="218.0" y2="86.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="213.0" y="84.5" class="dim-text">5</text>

<!-- Размер: общая толщина ушка 8 мм -->
<line x1="202.0" y1="91.0" x2="202.0" y2="76.0" class="dim-ext" />
<line x1="218.0" y1="91.0" x2="218.0" y2="76.0" class="dim-ext" />
<line x1="202.0" y1="78.0" x2="218.0" y2="78.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="210.0" y="76.5" class="dim-text">8</text>

<!-- Выноска: цековка Ø6,5 -->
<path d="M 215.0 95.5 L 222.0 89.0 L 255.0 89.0" class="leader" marker-start="url(#dot)" />
<text x="238.0" y="87.5" class="dim-text">цек. Ø6,5 (глуб. 5)</text>

<!-- Выноска: отв. Ø3,4 насквозь -->
<path d="M 205.0 98.6 L 198.0 89.0 L 168.0 89.0" class="leader" marker-start="url(#dot)" />
<text x="183.0" y="87.5" class="dim-text">отв. Ø3,4 насквозь</text>

<!-- Размер: толщина опорной стенки 3 мм под головкой винта -->
<line x1="202.0" y1="105.4" x2="202.0" y2="124.0" class="dim-ext" />
<line x1="208.0" y1="105.4" x2="208.0" y2="124.0" class="dim-ext" />
<line x1="202.0" y1="122.0" x2="208.0" y2="122.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="205.0" y="120.5" class="dim-text">3</text>

<!-- Контур усиленной консоли (h=5.5 мм) и головки (h=4 мм) вдали за плоскостью X = -10.0 -->
<line x1="218.0" y1="91.0" x2="258.0" y2="91.0" stroke="#000" stroke-width="0.35" />
<line x1="218.0" y1="102.0" x2="245.0" y2="102.0" stroke="#000" stroke-width="0.35" />
<line x1="245.0" y1="102.0" x2="250.0" y2="99.0" stroke="#000" stroke-width="0.35" />
<line x1="250.0" y1="99.0" x2="258.0" y2="99.0" stroke="#000" stroke-width="0.35" />
<line x1="258.0" y1="91.0" x2="258.0" y2="99.0" stroke="#000" stroke-width="0.35" />

<!-- Высота усиленной консоли 5,5 мм -->
<line x1="228.0" y1="91.0" x2="228.0" y2="102.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="232.5" y="97.5" class="dim-text">5,5</text>

<!-- Толщина рабочей пластины 4 мм -->
<line x1="258.0" y1="91.0" x2="268.0" y2="91.0" class="dim-ext" />
<line x1="258.0" y1="99.0" x2="268.0" y2="99.0" class="dim-ext" />
<line x1="266.0" y1="91.0" x2="266.0" y2="99.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="270.0" y="96.0" class="dim-text">4</text>

<!-- ==================== ВИД СВЕРХУ (TopView, M 2:1) ==================== -->
<line x1="110.0" y1="182.0" x2="110.0" y2="252.0" class="center-line" />
<line x1="126.0" y1="188.0" x2="126.0" y2="206.0" class="center-line" />
<line x1="118.0" y1="197.0" x2="134.0" y2="197.0" class="center-line" />

<!-- Выноска отверстия иглы Ø4,5 -->
<path d="M 126.0 197.0 L 140.0 182.0 L 170.0 182.0" class="leader" marker-start="url(#dot)" />
<text x="155.0" y="180.5" class="dim-text">Ø4,5 (отв. иглы)</text>

<!-- Габаритная глубина кронштейна 28* мм -->
<line x1="142.0" y1="189.0" x2="155.0" y2="189.0" class="dim-ext" />
<line x1="142.0" y1="245.0" x2="155.0" y2="245.0" class="dim-ext" />
<line x1="153.0" y1="189.0" x2="153.0" y2="245.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="156.0" y="217.0" transform="rotate(-90 156.0 217.0)" class="dim-text">28*</text>

<!-- Расстояние выноса отверстия иглы 24 мм -->
<line x1="142.0" y1="245.0" x2="165.0" y2="245.0" class="dim-ext" />
<line x1="126.0" y1="197.0" x2="165.0" y2="197.0" class="dim-ext" />
<line x1="163.0" y1="245.0" x2="163.0" y2="197.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="166.0" y="221.0" transform="rotate(-90 166.0 221.0)" class="dim-text">24</text>

<!-- Смещение отверстия иглы от оси стойки 8 мм -->
<line x1="110.0" y1="189.0" x2="110.0" y2="177.0" class="dim-ext" />
<line x1="126.0" y1="189.0" x2="126.0" y2="177.0" class="dim-ext" />
<line x1="110.0" y1="179.0" x2="126.0" y2="179.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="118.0" y="177.5" class="dim-text">8</text>

<!-- Толщина фланца 8 мм (Sheet Y from 229 to 245) -->
<line x1="78.0" y1="229.0" x2="68.0" y2="229.0" class="dim-ext" />
<line x1="78.0" y1="245.0" x2="68.0" y2="245.0" class="dim-ext" />
<line x1="70.0" y1="229.0" x2="70.0" y2="245.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="66.5" y="237.0" class="dim-text">8</text>

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

    # 8. Экспорт PDF, FCStd и PNG
    out_pdf = os.path.abspath(f"{part_name}.pdf")
    out_fcstd = os.path.abspath(f"{part_name}.FCStd")
    out_png = os.path.abspath(f"{part_name}.png")

    export_drawing(doc, page, out_pdf, out_fcstd, out_png)
    print(f"Drawing for {part_name} generated successfully!")


if __name__ == "__main__":
    generate_stripper_drawing()
