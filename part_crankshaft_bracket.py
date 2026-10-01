#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_crankshaft_bracket.py
Поз. 16: Кронштейн кривошипа (Horizontal Crankshaft Support Bracket)
Обозначение: ВЧ.01.00.016

Назначение:
- Жесткая опорная стойка для базирования горизонтального конического зубчатого колеса
  с кривошипом horizontal_crankshaft (ВЧ.01.00.005) на высоте Z_asm = 57.05 мм.
- Восприятие радиальных и осевых сил от конического зацепления с geneva_driver (z=40, m=2)
  и динамических усилий пробивки косточек от шатуна connecting_rod.
- Монтаж к верхней плоскости станины base_frame (Z_asm = 10.0 мм) 4 винтами DIN 912 M4.
- Оптимизировано для 3D-печати методом FDM из пищевого пластика PETG:
  все наклонные ребра выполнены под углом 45°, обеспечивая 100% печать БЕЗ поддержек (Zero Supports).
- Оформление официального рабочего чертежа по ГОСТ (ЕСКД) и инструкциям FREECAD.txt.
"""

import sys
import os
import math

# Пути FreeCAD и библиотек
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

# ====================================================================
# ГЕОМЕТРИЧЕСКИЕ ПАРАМЕТРЫ КРОНШТЕЙНА (в локальной системе координат)
# ====================================================================
# Базовая опорная плоскость: Z = 0 (устанавливается на станину Z_asm = 10.0 мм)
# Горизонтальная ось кривошипа: X = 0.0, Z = 47.05 мм, направлена вдоль оси Y.
# Плоскость Y = 0.0: соответствует заднему торцу колеса кривошипа (Z_crank = 0.0).
# Направление -Y: в сторону шестерни и подшипника 608ZZ.
# Направление +Y: назад (от шестерни, в сторону свободного пространства).

H_AXIS = 47.05            # Высота оси вала от опорного фланца (57.05 - 10.0 мм)

# Опорный монтажный фланец
FLANGE_W = 44.0           # Ширина фланца вдоль X (-22.0 .. +22.0 мм)
FLANGE_D = 38.0           # Длина фланца вдоль Y (+2.0 .. +40.0 мм)
FLANGE_H = 8.0            # Толщина фланца вдоль Z (0.0 .. 8.0 мм)
HOLE_SPAN_X = 28.0        # Расстояние между отверстиями по X (±14.0 мм)
HOLE_Y1 = 10.0            # Координата Y первого ряда отверстий
HOLE_Y2 = 32.0            # Координата Y второго ряда отверстий
HOLE_R = 2.25             # Радиус сквозных отверстий под винты M4 (Ø4.5 мм)
CB_R = 4.0                # Радиус цековки под головку винта DIN 912 M4 (Ø8.0 мм)
CB_DEPTH = 4.0            # Глубина цековки под головку винта заподлицо

# Вертикальная монолитная стойка (пилон)
COL_W = 16.0              # Ширина стойки вдоль X (-8.0 .. +8.0 мм, зазор 6.0 мм до оси M4)
COL_D = 16.0              # Толщина стойки вдоль Y (+2.0 .. +18.0 мм)
COL_H = 47.05             # Высота стойки до оси вала

# Верхняя ступица (бобышка под ось M8)
BOSS_R = 12.0             # Наружный радиус бобышки (Ø24.0 мм)
BOSS_D = 16.0             # Длина бобышки вдоль Y (+2.0 .. +18.0 мм)
AXLE_R = 4.2              # Радиус отверстия под ось M8 (Ø8.4 мм)
AXLE_CB_R = 7.25          # Радиус цековки под головку/гайку M8 (Ø14.5 мм)
AXLE_CB_DEPTH = 6.0       # Глубина задней цековки под M8 (Y in [12.0 .. 18.0])

# Заднее ребро жесткости (наклон ровно 45°, ширина 8.0 мм)
# Начинается от Z = 28.0 мм (на 11.8 мм ниже цековки M8, не создавая ступеней возле болта)
# и спускается до Z = 8.0 мм при Y = 38.0 мм (dZ = 20.0 мм, dY = 20.0 мм -> 45.0°)
RIB_REAR_W = 8.0          # Ширина заднего ребра вдоль X (-4.0 .. +4.0 мм)
RIB_RUN = 20.0            # Длина ребра по Y (18.0 .. 38.0 мм)
RIB_RISE = 20.0           # Высота ребра по Z (8.0 .. 28.0 мм)


def create_crankshaft_bracket():
    """
    Создает чистую аналитическую B-Rep твердотельную модель кронштейна
    горизонтального колеса с кривошипом horizontal_crankshaft (ВЧ.01.00.016).
    Геометрия полностью оптимизирована для FDM 3D-печати без поддержек.
    """
    # 1. Опорный монтажный фланец (Z in [0, 8.0], X in [-22, 22], Y in [2, 40])
    flange = make_box(FLANGE_W, FLANGE_D, FLANGE_H, (-FLANGE_W / 2.0, 2.0, 0.0))

    # Крепежные отверстия фланца 4x Ø4.5 мм с цековками Ø8.0 мм глубиной 4.0 мм
    for hx in [-HOLE_SPAN_X / 2.0, HOLE_SPAN_X / 2.0]:
        for hy in [HOLE_Y1, HOLE_Y2]:
            h_thru = make_cylinder(HOLE_R, FLANGE_H + 4.0, (hx, hy, -2.0), (0, 0, 1))
            h_cb = make_cylinder(CB_R, FLANGE_H, (hx, hy, FLANGE_H - CB_DEPTH), (0, 0, 1))
            flange = flange.cut(h_thru).cut(h_cb)

    # 2. Основная вертикальная стойка (пилон)
    pillar = make_box(COL_W, COL_D, COL_H, (-COL_W / 2.0, 2.0, 0.0))

    # 3. Верхняя цилиндрическая бобышка (ступица)
    boss = make_cylinder(BOSS_R, BOSS_D, (0.0, 2.0, H_AXIS), (0, 1, 0))

    # 4. Заднее наклонное ребро жесткости (угол строго 45°, ширина 8.0 мм)
    # Габариты: X: [-4, 4], Y: [18, 38], Z: [8, 28]
    rib_box = make_box(RIB_REAR_W, RIB_RUN, RIB_RISE, (-RIB_REAR_W / 2.0, 18.0, FLANGE_H))
    cutter_rear = make_box(RIB_REAR_W + 4.0, RIB_RUN * 2.0, RIB_RISE * 2.0,
                           (-RIB_REAR_W / 2.0 - 2.0, 18.0, FLANGE_H + RIB_RISE))
    cutter_rear.rotate(FreeCAD.Vector(-RIB_REAR_W / 2.0 - 2.0, 18.0, FLANGE_H + RIB_RISE),
                       FreeCAD.Vector(1, 0, 0), 45.0)
    rib_rear = rib_box.cut(cutter_rear)

    # 5. Объединение монолитных твердотельных элементов (B-Rep fuse)
    bracket = flange.fuse(pillar).fuse(boss).fuse(rib_rear)

    # 6. Сквозное осевое отверстие Ø8.4 мм под винт DIN 912 M8
    h_axle = make_cylinder(AXLE_R, BOSS_D + 6.0, (0.0, 0.0, H_AXIS), (0, 1, 0))

    # 7. Задняя цековка Ø14.5 мм глубиной 6.0 мм под головку винта или гайку M8
    h_cb_axle = make_cylinder(AXLE_CB_R, AXLE_CB_DEPTH + 4.0,
                              (0.0, 2.0 + BOSS_D - AXLE_CB_DEPTH, H_AXIS), (0, 1, 0))

    bracket = bracket.cut(h_axle).cut(h_cb_axle)

    if bracket.isNull():
        raise ValueError("Bracket solid shape is NULL!")
    if not bracket.isValid():
        raise ValueError("Bracket solid shape is topologically invalid!")

    return bracket


create_part = create_crankshaft_bracket


def generate_crankshaft_bracket_drawing(part_name="part_crankshaft_bracket",
                                        doc_code="ВЧ.01.00.016",
                                        title_name="Кронштейн кривошипа",
                                        material="PETG",
                                        scale=1.0,
                                        sheet="A3_Landscape",
                                        notes=None):
    """
    Генерирует официальный рабочий чертеж кронштейна кривошипа по ГОСТ (ЕСКД):
    - Главный вид (вид спереди со стороны упорного буртика подшипника);
    - Вид сверху в строгой проекционной связи (выровнен по оси X);
    - Вид слева в проекционной связи (выровнен по оси Y с главным видом);
    - Аксонометрический вид (изометрия);
    - Векторный оверлей размеров по ГОСТ 2.307-2011 с компенсацией DPI (FREECAD.txt);
    - Штамп по ГОСТ 2.104 и технические требования по ГОСТ 2.316;
    - Экспорт в PDF, native FCStd и preview PNG.
    """
    shape = create_crankshaft_bracket()

    doc = FreeCAD.newDocument(f"Doc_{part_name}")
    feat = doc.addObject("Part::Feature", part_name)
    feat.Shape = shape
    doc.recompute()

    page, template = create_drawing_page(doc, sheet, f"Page_{part_name}")

    # Лист А3 Альбомная: 420.0 x 297.0 мм
    # Координаты проекционных видов:
    # Главный вид: FrontView (X=115.0, Y=190.0)
    # Вид сверху: TopView (X=115.0, Y=80.0) - строго X_top == X_front
    # Вид слева: LeftView (X=230.0, Y=190.0) - строго Y_side == Y_front
    # Изометрия: IsoView (X=325.0, Y=205.0)

    X_FRONT = 115.0
    Y_FRONT = 190.0
    Y_TOP = 80.0
    X_SIDE = 230.0

    # 1. Главный вид (Front View: нормаль (0, -1, 0) со стороны шестерни и упорного буртика)
    v_front = add_part_view(doc, page, feat, 'FrontView', (0.0, -1.0, 0.0), scale, X_FRONT, Y_FRONT)
    v_front.XDirection = FreeCAD.Vector(1.0, 0.0, 0.0)

    # 2. Вид сверху (Top View: нормаль (0, 0, 1) сверху вниз)
    v_top = add_part_view(doc, page, feat, 'TopView', (0.0, 0.0, 1.0), scale, X_FRONT, Y_TOP)
    v_top.XDirection = FreeCAD.Vector(1.0, 0.0, 0.0)

    # 3. Вид слева (Left View / Вид сбоку: нормаль (1, 0, 0), ось +Y направлена вправо)
    v_side = add_part_view(doc, page, feat, 'LeftView', (1.0, 0.0, 0.0), scale, X_SIDE, Y_FRONT)
    v_side.XDirection = FreeCAD.Vector(0.0, 1.0, 0.0)

    # 4. Аксонометрический вид (Изометрия)
    v_iso = add_part_view(doc, page, feat, 'IsoView', (-1.0, -1.2, 0.9), scale * 0.9, 325.0, 205.0)

    # 5. Основная надпись (Штамп ГОСТ 2.104, Форма 1)
    title_fields = {
        'Номер': doc_code,
        'Название': title_name,
        'Масштаб': f"{int(scale)}:1" if scale >= 1 else f"1:{int(1/scale)}",
        'Лист': '1',
        'Листов': '1',
        'Материал1': material,
        'Материал2': ' ',
        'Материал3': ' ',
        'Организация1': 'Проект VISHNI',
        'Организация2': 'ВЧ.01.00.000',
        'Разработал': 'Инженер',
        'Проверил': 'Контролер'
    }
    fill_gost_title_block(template, title_fields)
    doc.recompute()

    # 6. Технические требования (ГОСТ 2.316)
    if notes is None:
        notes = [
            "1. * Размеры для справок.",
            "2. Материал: пластик PETG. Заполнение не менее 45%, не менее 4 периметров.",
            "3. Базовая плоскость 3D-печати — опорный фланец (Z = 0, стол принтера).",
            "   Печать без поддерживающих структур (Zero Supports).",
            "4. Дистанционирование подшипника 608ZZ выполнять стандартными стальными шайбами",
            "   DIN 988 8x14x1 (2 шт.) или DIN 125 M8 между торцем бобышки и внутренним кольцом.",
            "5. Неуказанные радиусы скруглений 1,0...1,5 мм.",
            "6. Предельные отклонения размеров по ГОСТ 30893.1-m (±t2/2).",
            "7. Резьбовые сопряжения: винты DIN 912 M4 (станина), DIN 912 M8 (ось вала)."
        ]

    # Высота блока технических требований
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

    # 7. Векторный оверлей контуров и размеров по ГОСТ 2.307-2011 / ГОСТ 2.303-68
    cf_x = X_FRONT             # 115.0
    cf_y = 297.0 - Y_FRONT      # 107.0
    z_mid = 29.525

    def f_pt(x, z):
        return (cf_x + x * scale, cf_y - (z - z_mid) * scale)

    ct_x = X_FRONT             # 115.0
    ct_y = 297.0 - Y_TOP        # 217.0
    y_mid_top = 21.0

    def t_pt(x, y):
        return (ct_x + x * scale, ct_y - (y - y_mid_top) * scale)

    cs_x = X_SIDE              # 230.0
    cs_y = 297.0 - Y_FRONT      # 107.0

    def s_pt(y, z):
        return (cs_x + (y - y_mid_top) * scale, cs_y - (z - z_mid) * scale)

    # Опорные точки:
    f_axis = f_pt(0, 47.05)
    f_flange_l = f_pt(-22, 0)
    f_flange_r = f_pt(22, 0)
    f_flange_top = f_pt(0, 8)

    t_flange_front = t_pt(0, 2)
    t_flange_back = t_pt(0, 40)
    t_h1 = t_pt(14, 10)
    t_h2 = t_pt(14, 32)

    s_axis = s_pt(18, 47.05)
    s_boss_front = s_pt(2, 47.05)
    s_boss_back = s_pt(18, 47.05)

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
  .contour-line {{ stroke: #000; stroke-width: 0.5; fill: none; }}
  .hidden-line {{ stroke: #000; stroke-width: 0.25; stroke-dasharray: 2.5,1.2; fill: none; }}
  .dim-line {{ stroke: #000; stroke-width: 0.35; fill: none; }}
  .dim-ext {{ stroke: #000; stroke-width: 0.25; fill: none; }}
  .center-line {{ stroke: #000; stroke-width: 0.25; stroke-dasharray: 6,1.5,1.5,1.5; fill: none; }}
  .dim-text {{ font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: middle; }}
  .dim-text-left {{ font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: start; }}
  .leader {{ stroke: #000; stroke-width: 0.35; fill: none; }}
</style>

<!-- ==================== КОНТУРЫ ДЕТАЛИ ==================== -->
<!-- FrontView контур: монолитная стойка без боковых блоков -->
<path d="M {f_pt(-22, 0)[0]} {f_pt(-22, 0)[1]}
         L {f_pt(22, 0)[0]} {f_pt(22, 0)[1]}
         L {f_pt(22, 8)[0]} {f_pt(22, 8)[1]}
         L {f_pt(8, 8)[0]} {f_pt(8, 8)[1]}
         L {f_pt(8, 47.05)[0]} {f_pt(8, 47.05)[1]}
         L {f_pt(12, 47.05)[0]} {f_pt(12, 47.05)[1]}
         A 12 12 0 0 0 {f_pt(-12, 47.05)[0]} {f_pt(-12, 47.05)[1]}
         L {f_pt(-8, 47.05)[0]} {f_pt(-8, 47.05)[1]}
         L {f_pt(-8, 8)[0]} {f_pt(-8, 8)[1]}
         L {f_pt(-22, 8)[0]} {f_pt(-22, 8)[1]} Z" class="contour-line" />
<line x1="{f_pt(-22, 8)[0]}" y1="{f_pt(-22, 8)[1]}" x2="{f_pt(-8, 8)[0]}" y2="{f_pt(-8, 8)[1]}" class="contour-line" />
<line x1="{f_pt(8, 8)[0]}" y1="{f_pt(8, 8)[1]}" x2="{f_pt(22, 8)[0]}" y2="{f_pt(22, 8)[1]}" class="contour-line" />
<circle cx="{f_axis[0]}" cy="{f_axis[1]}" r="{4.2 * scale}" class="contour-line" />
<circle cx="{f_axis[0]}" cy="{f_axis[1]}" r="{7.25 * scale}" class="hidden-line" />

<!-- TopView контур: свободный доступ к 4 отверстиям -->
<rect x="{t_pt(-22, 40)[0]}" y="{t_pt(-22, 40)[1]}" width="{44 * scale}" height="{38 * scale}" class="contour-line" />
<rect x="{t_pt(-12, 18)[0]}" y="{t_pt(-12, 18)[1]}" width="{24 * scale}" height="{16 * scale}" class="contour-line" />
<rect x="{t_pt(-4, 38)[0]}" y="{t_pt(-4, 38)[1]}" width="{8 * scale}" height="{20 * scale}" class="contour-line" />
<circle cx="{t_pt(-14, 10)[0]}" cy="{t_pt(-14, 10)[1]}" r="{2.25 * scale}" class="contour-line" />
<circle cx="{t_pt(-14, 10)[0]}" cy="{t_pt(-14, 10)[1]}" r="{4.0 * scale}" class="contour-line" />
<circle cx="{t_pt(14, 10)[0]}" cy="{t_pt(14, 10)[1]}" r="{2.25 * scale}" class="contour-line" />
<circle cx="{t_pt(14, 10)[0]}" cy="{t_pt(14, 10)[1]}" r="{4.0 * scale}" class="contour-line" />
<circle cx="{t_pt(-14, 32)[0]}" cy="{t_pt(-14, 32)[1]}" r="{2.25 * scale}" class="contour-line" />
<circle cx="{t_pt(-14, 32)[0]}" cy="{t_pt(-14, 32)[1]}" r="{4.0 * scale}" class="contour-line" />
<circle cx="{t_pt(14, 32)[0]}" cy="{t_pt(14, 32)[1]}" r="{2.25 * scale}" class="contour-line" />
<circle cx="{t_pt(14, 32)[0]}" cy="{t_pt(14, 32)[1]}" r="{4.0 * scale}" class="contour-line" />

<!-- LeftView контур: единственный наклон 45° заднего ребра, без пересечений -->
<path d="M {s_pt(2, 0)[0]} {s_pt(2, 0)[1]}
         L {s_pt(40, 0)[0]} {s_pt(40, 0)[1]}
         L {s_pt(40, 8)[0]} {s_pt(40, 8)[1]}
         L {s_pt(38, 8)[0]} {s_pt(38, 8)[1]}
         L {s_pt(18, 28)[0]} {s_pt(18, 28)[1]}
         L {s_pt(18, 59.05)[0]} {s_pt(18, 59.05)[1]}
         L {s_pt(2, 59.05)[0]} {s_pt(2, 59.05)[1]}
         L {s_pt(2, 0)[0]} {s_pt(2, 0)[1]} Z" class="contour-line" />
<line x1="{s_pt(2, 8)[0]}" y1="{s_pt(2, 8)[1]}" x2="{s_pt(40, 8)[0]}" y2="{s_pt(40, 8)[1]}" class="contour-line" />

<!-- ==================== ОСЕВЫЕ ЛИНИИ ==================== -->
<line x1="{cf_x}" y1="{f_pt(0, 63)[1]}" x2="{cf_x}" y2="{f_pt(0, -3)[1]}" class="center-line" />
<line x1="{f_pt(-16, 47.05)[0]}" y1="{f_axis[1]}" x2="{f_pt(16, 47.05)[0]}" y2="{f_axis[1]}" class="center-line" />
<line x1="{cf_x}" y1="{t_pt(0, 44)[1]}" x2="{cf_x}" y2="{t_pt(0, -3)[1]}" class="center-line" />
<line x1="{s_pt(-2, 47.05)[0]}" y1="{s_axis[1]}" x2="{s_pt(24, 47.05)[0]}" y2="{s_axis[1]}" class="center-line" />

<!-- ==================== РАЗМЕРЫ ==================== -->
<!-- FrontView размеры -->
<!-- Габаритная ширина фланца: 44 мм -->
<line x1="{f_flange_l[0]}" y1="{f_flange_l[1]}" x2="{f_flange_l[0]}" y2="{f_flange_l[1] + 16}" class="dim-ext" />
<line x1="{f_flange_r[0]}" y1="{f_flange_r[1]}" x2="{f_flange_r[0]}" y2="{f_flange_r[1] + 16}" class="dim-ext" />
<line x1="{f_flange_l[0]}" y1="{f_flange_l[1] + 13}" x2="{f_flange_r[0]}" y2="{f_flange_r[1] + 13}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="{cf_x}" y="{f_flange_l[1] + 11.5}" class="dim-text">44</text>

<!-- Межосевое расстояние отверстий по ширине: 28 мм -->
<line x1="{f_pt(-14, 0)[0]}" y1="{f_pt(-14, 0)[1]}" x2="{f_pt(-14, 0)[0]}" y2="{f_pt(-14, 0)[1] + 8}" class="dim-ext" />
<line x1="{f_pt(14, 0)[0]}" y1="{f_pt(14, 0)[1]}" x2="{f_pt(14, 0)[0]}" y2="{f_pt(14, 0)[1] + 8}" class="dim-ext" />
<line x1="{f_pt(-14, 0)[0]}" y1="{f_pt(-14, 0)[1] + 6}" x2="{f_pt(14, 0)[0]}" y2="{f_pt(14, 0)[1] + 6}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="{cf_x}" y="{f_pt(-14, 0)[1] + 4.5}" class="dim-text">28</text>

<!-- Толщина фланца: 8 мм -->
<line x1="{f_flange_l[0]}" y1="{f_flange_l[1]}" x2="{f_flange_l[0] - 12}" y2="{f_flange_l[1]}" class="dim-ext" />
<line x1="{f_flange_l[0]}" y1="{f_flange_top[1]}" x2="{f_flange_l[0] - 12}" y2="{f_flange_top[1]}" class="dim-ext" />
<line x1="{f_flange_l[0] - 8}" y1="{f_flange_l[1]}" x2="{f_flange_l[0] - 8}" y2="{f_flange_top[1]}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="{f_flange_l[0] - 10}" y="{(f_flange_l[1] + f_flange_top[1]) / 2}" transform="rotate(-90 {f_flange_l[0] - 10} {(f_flange_l[1] + f_flange_top[1]) / 2})" class="dim-text">8</text>

<!-- Высота оси вала: 47,05* мм -->
<line x1="{f_flange_l[0] - 12}" y1="{f_flange_l[1]}" x2="{f_flange_l[0] - 24}" y2="{f_flange_l[1]}" class="dim-ext" />
<line x1="{f_pt(-12, 47.05)[0]}" y1="{f_axis[1]}" x2="{f_flange_l[0] - 24}" y2="{f_axis[1]}" class="dim-ext" />
<line x1="{f_flange_l[0] - 20}" y1="{f_flange_l[1]}" x2="{f_flange_l[0] - 20}" y2="{f_axis[1]}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="{f_flange_l[0] - 22}" y="{(f_flange_l[1] + f_axis[1]) / 2}" transform="rotate(-90 {f_flange_l[0] - 22} {(f_flange_l[1] + f_axis[1]) / 2})" class="dim-text">47,05*</text>

<!-- Габаритная высота: 59* мм -->
<line x1="{f_flange_r[0]}" y1="{f_flange_r[1]}" x2="{f_flange_r[0] + 16}" y2="{f_flange_r[1]}" class="dim-ext" />
<line x1="{f_pt(12, 59.05)[0]}" y1="{f_pt(0, 59.05)[1]}" x2="{f_flange_r[0] + 16}" y2="{f_pt(0, 59.05)[1]}" class="dim-ext" />
<line x1="{f_flange_r[0] + 12}" y1="{f_flange_r[1]}" x2="{f_flange_r[0] + 12}" y2="{f_pt(0, 59.05)[1]}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="{f_flange_r[0] + 14}" y="{(f_flange_r[1] + f_pt(0, 59.05)[1]) / 2}" transform="rotate(-90 {f_flange_r[0] + 14} {(f_flange_r[1] + f_pt(0, 59.05)[1]) / 2})" class="dim-text">59*</text>

<!-- Выноска диаметра отверстия оси: Ø8,4 -->
<path d="M {cf_x + 2} {f_axis[1] - 2} L {cf_x + 22} {f_axis[1] - 16} L {cf_x + 42} {f_axis[1] - 16}" class="leader" marker-start="url(#dot)" />
<text x="{cf_x + 24}" y="{f_axis[1] - 17.5}" class="dim-text-left">Ø8,4</text>

<!-- Наружный диаметр бобышки: Ø24 -->
<line x1="{f_pt(-12, 47.05)[0]}" y1="{f_pt(0, 59.05)[1]}" x2="{f_pt(-12, 47.05)[0]}" y2="{f_pt(0, 59.05)[1] - 10}" class="dim-ext" />
<line x1="{f_pt(12, 47.05)[0]}" y1="{f_pt(0, 59.05)[1]}" x2="{f_pt(12, 47.05)[0]}" y2="{f_pt(0, 59.05)[1] - 10}" class="dim-ext" />
<line x1="{f_pt(-12, 47.05)[0]}" y1="{f_pt(0, 59.05)[1] - 7}" x2="{f_pt(12, 47.05)[0]}" y2="{f_pt(0, 59.05)[1] - 7}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="{cf_x}" y="{f_pt(0, 59.05)[1] - 8.5}" class="dim-text">Ø24</text>

<!-- TopView размеры -->
<!-- Межосевое расстояние отверстий по Y: 22 мм -->
<line x1="{t_h1[0]}" y1="{t_h1[1]}" x2="{t_pt(22, 0)[0] + 10}" y2="{t_h1[1]}" class="dim-ext" />
<line x1="{t_h2[0]}" y1="{t_h2[1]}" x2="{t_pt(22, 0)[0] + 10}" y2="{t_h2[1]}" class="dim-ext" />
<line x1="{t_pt(22, 0)[0] + 7}" y1="{t_h1[1]}" x2="{t_pt(22, 0)[0] + 7}" y2="{t_h2[1]}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="{t_pt(22, 0)[0] + 9}" y="{(t_h1[1] + t_h2[1]) / 2}" transform="rotate(-90 {t_pt(22, 0)[0] + 9} {(t_h1[1] + t_h2[1]) / 2})" class="dim-text">22</text>

<!-- Габаритная глубина фланца: 38 мм -->
<line x1="{t_pt(22, 2)[0]}" y1="{t_flange_front[1]}" x2="{t_pt(22, 2)[0] + 20}" y2="{t_flange_front[1]}" class="dim-ext" />
<line x1="{t_pt(22, 40)[0]}" y1="{t_flange_back[1]}" x2="{t_pt(22, 40)[0] + 20}" y2="{t_flange_back[1]}" class="dim-ext" />
<line x1="{t_pt(22, 2)[0] + 16}" y1="{t_flange_front[1]}" x2="{t_pt(22, 40)[0] + 16}" y2="{t_flange_back[1]}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="{t_pt(22, 2)[0] + 18}" y="{(t_flange_front[1] + t_flange_back[1]) / 2}" transform="rotate(-90 {t_pt(22, 2)[0] + 18} {(t_flange_front[1] + t_flange_back[1]) / 2})" class="dim-text">38</text>

<!-- Выноска 4 отверстий: 4 отв. Ø4,5; цек. Ø8 х 4 -->
<path d="M {t_pt(-14, 10)[0]} {t_pt(-14, 10)[1]} L {t_pt(-14, 10)[0] - 16} {t_pt(-14, 10)[1] - 14} L {t_pt(-14, 10)[0] - 52} {t_pt(-14, 10)[1] - 14}" class="leader" marker-start="url(#dot)" />
<text x="{t_pt(-14, 10)[0] - 50}" y="{t_pt(-14, 10)[1] - 15.5}" class="dim-text-left">4 отв. Ø4,5</text>
<text x="{t_pt(-14, 10)[0] - 50}" y="{t_pt(-14, 10)[1] - 10.5}" class="dim-text-left">цек. Ø8 глуб. 4</text>

<!-- LeftView размеры и скрытые линии -->
<!-- Скрытые линии отверстия оси и цековки на виде слева -->
<line x1="{s_pt(2, 47.05 - 4.2)[0]}" y1="{s_pt(2, 47.05 - 4.2)[1]}" x2="{s_pt(12, 47.05 - 4.2)[0]}" y2="{s_pt(12, 47.05 - 4.2)[1]}" class="hidden-line" />
<line x1="{s_pt(2, 47.05 + 4.2)[0]}" y1="{s_pt(2, 47.05 + 4.2)[1]}" x2="{s_pt(12, 47.05 + 4.2)[0]}" y2="{s_pt(12, 47.05 + 4.2)[1]}" class="hidden-line" />
<line x1="{s_pt(12, 47.05 - 7.25)[0]}" y1="{s_pt(12, 47.05 - 7.25)[1]}" x2="{s_pt(18, 47.05 - 7.25)[0]}" y2="{s_pt(18, 47.05 - 7.25)[1]}" class="hidden-line" />
<line x1="{s_pt(12, 47.05 + 7.25)[0]}" y1="{s_pt(12, 47.05 + 7.25)[1]}" x2="{s_pt(18, 47.05 + 7.25)[0]}" y2="{s_pt(18, 47.05 + 7.25)[1]}" class="hidden-line" />
<line x1="{s_pt(12, 47.05 - 7.25)[0]}" y1="{s_pt(12, 47.05 - 7.25)[1]}" x2="{s_pt(12, 47.05 - 4.2)[0]}" y2="{s_pt(12, 47.05 - 4.2)[1]}" class="hidden-line" />
<line x1="{s_pt(12, 47.05 + 4.2)[0]}" y1="{s_pt(12, 47.05 + 4.2)[1]}" x2="{s_pt(12, 47.05 + 7.25)[0]}" y2="{s_pt(12, 47.05 + 7.25)[1]}" class="hidden-line" />

<!-- Длина бобышки: 16 мм -->
<line x1="{s_boss_front[0]}" y1="{s_pt(2, 59.05)[1]}" x2="{s_boss_front[0]}" y2="{s_pt(2, 59.05)[1] - 8}" class="dim-ext" />
<line x1="{s_boss_back[0]}" y1="{s_pt(18, 59.05)[1]}" x2="{s_boss_back[0]}" y2="{s_pt(18, 59.05)[1] - 8}" class="dim-ext" />
<line x1="{s_boss_front[0]}" y1="{s_pt(2, 59.05)[1] - 5}" x2="{s_boss_back[0]}" y2="{s_pt(18, 59.05)[1] - 5}" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="{(s_boss_front[0] + s_boss_back[0]) / 2}" y="{s_pt(2, 59.05)[1] - 6.5}" class="dim-text">16</text>

<!-- Задняя цековка под болт M8: цек. Ø14,5 глуб. 6 -->
<path d="M {s_pt(15, 47.05 - 7.25)[0]} {s_pt(15, 47.05 - 7.25)[1]} L {s_pt(15, 47.05 - 7.25)[0] + 16} {s_pt(15, 47.05 - 7.25)[1] + 14} L {s_pt(15, 47.05 - 7.25)[0] + 45} {s_pt(15, 47.05 - 7.25)[1] + 14}" class="leader" marker-start="url(#dot)" />
<text x="{s_pt(15, 47.05 - 7.25)[0] + 18}" y="{s_pt(15, 47.05 - 7.25)[1] + 12.5}" class="dim-text-left">цек. Ø14,5 глуб. 6</text>

<!-- Угол наклонного ребра жесткости: 45° -->
<text x="{s_pt(26, 20)[0]}" y="{s_pt(26, 20)[1]}" class="dim-text">45°</text>

</svg>'''


    # Добавление оверлея размеров с масштабированием DPI per FREECAD.txt
    sym_dim = doc.addObject('TechDraw::DrawViewSymbol', 'OverlayDimensions')
    sym_dim.Symbol = svg_dim
    page.addView(sym_dim)
    doc.recompute()

    # Точный расчет компенсации масштаба 90/96 DPI
    qt_pixels = round(420.0 * 90.0 / 25.4)
    freecad_mm = qt_pixels * 25.4 / 96.0
    scale_correction = 420.0 / freecad_mm

    sym_dim.Scale = scale_correction
    sym_dim.X = 210.0
    sym_dim.Y = 148.5
    doc.recompute()

    # 8. Экспорт рабочего чертежа в PDF, FCStd и PNG
    out_pdf = f"{part_name}.pdf"
    out_fcstd = f"{part_name}.FCStd"
    out_png = f"{part_name}.png"

    export_drawing(doc, page, out_pdf, out_fcstd, out_png)
    print(f"SUCCESS: Drawing and 3D CAD files for {part_name} generated successfully!")



if __name__ == "__main__":
    generate_crankshaft_bracket_drawing()
