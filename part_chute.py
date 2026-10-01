#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_chute.py
Деталь: Лоток приемный с Т-образным пазом (Receiving Chute with T-Slot)
Обозначение: ВЧ.01.00.010

Назначение:
  Приемный наклонный лоток для отвода чистых ягод в приемную тару.
  На задней стенке выполнен вертикальный Т-образный паз (T-slot)
  для установки шипа дефлектора ВЧ.01.00.013.
  Оснащен опорной стойкой и монтажным фланцем с 2 отверстиями Ø3.4 мм
  для крепления к станине.
"""

import sys
import os
import math

sys.path.append('/usr/lib/freecad/lib')
sys.path.append('/usr/share/freecad/Mod/TechDraw')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from freecad_utils import (
    FreeCAD, Part, make_box, make_cylinder, rot_z, rot_axis, trans,
    generate_standard_part_drawing
)

def create_chute():
    """
    Создает твердотельную 3D B-Rep модель приемного лотка с уклоном 34°
    и пазом «ласточкин хвост», оптимизированную для печати без поддержек.
    Базовая система координат:
      Позиция 5 (60°): Z = 0 плоскость станины, X - радиально наружу, Y - тангенциально CCW.
    Геометрия:
      - Уклон лотка: 34.0° вдоль +X (спуск от Z=44.5 до Z=21.9 мм).
      - Ширина канала в свету: 34.0 мм, толщина дна 3.5 мм, борта 14.0 мм.
      - Входная горловина открыта (передний бортик начинается на X_loc >= 22.0 мм).
      - Самонесущие скосы под 45° под боковыми полками желоба (угол нависания 35.9° <= 45°).
      - Плавное отхождение бобышки от центральной ножки под 45° (без высокого пилона на фланце).
      - Вертикальный паз типа «ласточкин хвост» с упором на Z=45.0 мм.
      - Монтажный фланец 34х48х4 мм с 2 отверстиями Ø3.4 под винты М3 (цековки Ø6.5 мм).
      - Цилиндрический зазор R=58.5 мм вокруг барабана.
    """
    c_x, c_y = -44.0, 0.0

    chute_w = 34.0
    floor_th = 3.5
    wall_h = 14.0
    wall_th = 3.0
    slope_deg = 34.0

    # 1. Желоб со стенками и самонесущими скосами под 45° под полками желоба
    # В локальной плоскости Y-Z контур дна имеет скосы от Y=±11 (Z=-12.5) до Y=±20 (Z=-3.5).
    # При наклоне на 34° эти грани имеют угол к горизонту 54.1° (нависание 35.9° <= 45°).
    p_outer = [
        FreeCAD.Vector(0, -20.0, wall_h),
        FreeCAD.Vector(0, -20.0, -floor_th),
        FreeCAD.Vector(0, -11.0, -floor_th - 9.0),
        FreeCAD.Vector(0, 11.0, -floor_th - 9.0),
        FreeCAD.Vector(0, 20.0, -floor_th),
        FreeCAD.Vector(0, 20.0, wall_h),
        FreeCAD.Vector(0, chute_w / 2.0, wall_h),
        FreeCAD.Vector(0, chute_w / 2.0, 0.0),
        FreeCAD.Vector(0, -chute_w / 2.0, 0.0),
        FreeCAD.Vector(0, -chute_w / 2.0, wall_h),
        FreeCAD.Vector(0, -20.0, wall_h)
    ]
    poly = Part.makePolygon(p_outer)
    face = Part.Face(poly)
    chute_solid = face.extrude(FreeCAD.Vector(60.0, 0.0, 0.0))

    # Снижение переднего бортика для беспрепятственного входа ягод из барабана
    front_cut = make_box(22.0, wall_th + 1.0, wall_h + 2.0, (-1.0, -chute_w / 2.0 - wall_th - 0.5, 0.0))
    chute_solid = chute_solid.cut(front_cut)

    # Наклон лотка на 34° и позиционирование
    chute_sloped = rot_axis(chute_solid, (0.0, 0.0, 0.0), (0.0, 1.0, 0.0), slope_deg)
    chute = trans(chute_sloped, 14.5, 0.0, 44.5)

    # 2. Бобышка под паз «ласточкин хвост» с плавным отхождением от ножки под 45°
    # Паз смещен вправо (центр X = 21.5 мм), чтобы обеспечить прочную стенку толщиной 2.8 мм слева от паза.
    # Бобышка строго расположена при Y >= 17.0 мм (снаружи желоба), что исключает лишние грани внутри лотка.
    # Нижний скос от (Y=17.0, Z=38.5) до (Y=22.5, Z=44.0) выполнен строго под 45.0°.
    x_c = 21.5
    boss_x_start = 14.5
    boss_x_len = 14.0  # X in [14.5, 28.5]

    p_boss = [
        FreeCAD.Vector(boss_x_start, 17.0, 38.5),
        FreeCAD.Vector(boss_x_start, 22.5, 44.0),
        FreeCAD.Vector(boss_x_start, 22.5, 62.5),
        FreeCAD.Vector(boss_x_start, 17.0, 62.5),
        FreeCAD.Vector(boss_x_start, 17.0, 38.5)
    ]
    poly_boss = Part.makePolygon(p_boss)
    face_boss = Part.Face(poly_boss)
    boss_solid = face_boss.extrude(FreeCAD.Vector(boss_x_len, 0.0, 0.0))
    chute = chute.fuse(boss_solid)

    # 3. Вырезка вертикального паза типа «ласточкин хвост» (Dovetail slot):
    # Центр паза X = 21.5 мм (гарантированная толщина стенки слева 2.8 мм, справа 2.8 мм).
    # Горловина на Y = 17.0: ширина 4.4 мм (X in [19.3, 23.7])
    # Основание на Y = 21.2: ширина 8.4 мм (X in [17.3, 25.7])
    # Высота: от Z = 44.0 (упор) до Z = 66.0 (открыт сверху)
    p1 = FreeCAD.Vector(x_c - 2.2, 17.0, 44.0)
    p2 = FreeCAD.Vector(x_c + 2.2, 17.0, 44.0)
    p3 = FreeCAD.Vector(x_c + 4.2, 21.2, 44.0)
    p4 = FreeCAD.Vector(x_c - 4.2, 21.2, 44.0)
    poly_slot = Part.makePolygon([p1, p2, p3, p4, p1])
    face_slot = Part.Face(poly_slot)
    slot_solid = face_slot.extrude(FreeCAD.Vector(0, 0, 22.0))
    chute = chute.cut(slot_solid)

    # Зачистка внутреннего объема лотка (гарантирует идеально плоское дно и гладкие борта)
    channel_cut = make_box(80.0, chute_w, 80.0, (-10.0, -chute_w / 2.0, 0.0))
    channel_cut = rot_axis(channel_cut, (0.0, 0.0, 0.0), (0.0, 1.0, 0.0), slope_deg)
    channel_cut = trans(channel_cut, 14.5, 0.0, 44.5)
    chute = chute.cut(channel_cut)

    # 4. Монолитная центральная ножка (spine) под желобом:
    # Ширина Y in [-11.0, 11.0] оставляет полный доступ к крепежным винтам на Y = ±17.5.
    spine = make_box(33.5, 22.0, 50.0, (14.5, -11.0, 4.0))
    spine = spine.cut(channel_cut)
    chute = chute.fuse(spine)

    # 5. Торцевая вертикальная обрезка входа (X = 14.5) и выхода (X = 48.0)
    # Исключает нависающие губки и выступы за пределы опорного фланца.
    cut_in = make_box(30.0, 60.0, 80.0, (-15.5, -30.0, -10.0))
    cut_out = make_box(30.0, 60.0, 80.0, (48.0, -30.0, -10.0))
    chute = chute.cut(cut_in).cut(cut_out)

    # 6. Монтажный фланец крепления к станине
    flange = make_box(34.0, 48.0, 4.0, (14.0, -24.0, 0.0))
    h1 = make_cylinder(1.7, 8.0, (30.0, -17.5, -1.0))
    h2 = make_cylinder(1.7, 8.0, (30.0, 17.5, -1.0))
    sf1 = make_cylinder(3.25, 3.0, (30.0, -17.5, 2.5))
    sf2 = make_cylinder(3.25, 3.0, (30.0, 17.5, 2.5))
    flange = flange.cut(h1).cut(h2).cut(sf1).cut(sf2)
    chute = chute.fuse(flange)

    # 7. Цилиндрический зазор вокруг барабана ротора (R = 58.5 мм)
    drum_clear = make_cylinder(58.5, 70.0, (c_x, c_y, 0.0))
    chute = chute.cut(drum_clear)
    chute = chute.removeSplitter()

    if not chute.isValid():
        raise RuntimeError("Chute shape is invalid!")

    return chute

create_part = create_chute

if __name__ == "__main__":
    shape = create_chute()
    print(f"Chute solids: {len(shape.Solids)}, valid: {shape.isValid()}, vol: {shape.Volume:.1f} mm³")

    notes = [
        "1. * Размеры для справок.",
        "2. Материал: Пищевой PETG (Food Safe). Заполнение не менее 40%.",
        "3. Уклон желоба 34° обеспечивает надежный гравитационный спуск ягод.",
        "4. Паз «ласточкин хвост» предназначен для скользящей посадки дефлектора ВЧ.01.00.013.",
        "5. Деталь полностью оптимизирована для печати на подошве фланца (Z-up) без поддержек."
    ]

    generate_standard_part_drawing(
        part_name="part_chute",
        part_shape=shape,
        doc_code="ВЧ.01.00.010",
        title_name="Лоток приемный",
        material="PETG",
        scale=1.0,
        sheet="A3_Landscape",
        notes=notes
    )
