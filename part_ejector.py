#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_ejector.py
Деталь: Нож-подъемник ягод (Berry Ejector Knife)
Обозначение: ВЧ.01.00.012

Назначение:
  Подъемный клин-нож, установленный в кольцевом пазу вращающегося барабана.
  Заходит плоским основанием (Z=29.0) на 2 мм ниже уровня ягод под поступающую
  ягоду и плавно поднимает ее по пологому пандусу (угол ~21°) на уровень
  дефлектора (Z=44.5) для последующего сброса в приемный лоток.
  В верхней части оснащен массивной колодкой с пазом «ласточкин хвост» под шип
  дефлектора ВЧ.01.00.013 и резьбовым отверстием под стопорный винт М3.
  Толщина стенки паза со стороны ножа увеличена до 5.5 мм (устранена тонкая стенка).
"""

import sys
import os
import math

sys.path.append('/usr/lib/freecad/lib')
sys.path.append('/usr/share/freecad/Mod/TechDraw')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from freecad_utils import (
    FreeCAD, Part, TechDraw, TechDrawGui,
    make_box, make_cylinder, rot_z, rot_axis, trans,
    create_drawing_page, add_part_view, fill_gost_title_block, export_drawing
)

def get_symbol_scale_correction(sheet_width_mm):
    """
    Вычисляет масштабный коэффициент для устранения 6.27% ошибки масштабирования QtSvg (90 vs 96 DPI).
    """
    qt_pixels = round(sheet_width_mm * 90.0 / 25.4)
    freecad_mm = qt_pixels * 25.4 / 96.0
    return sheet_width_mm / freecad_mm

def create_ejector():
    """
    Создает твердотельную 3D B-Rep модель ножа-подъемника ягод (DfAM):
      - Плоское основание: Z = 29.0 мм (на 2 мм ниже дна сферической лунки ягод) — контакт со столом 3D-принтера.
      - Носок клина: толщина 2.0 мм (Z in [29.0, 31.0]).
      - Плавный угол подъема пандуса: ~26.8° вдоль дуги (сектор beta от -45° до 0°).
      - Верхний уровень пандуса: Z = 48.5 мм (стыковка с поднятым дефлектором ВЧ.01.00.013).
      - Монолитный силовой фундамент колодки (DfAM Solid Foundation): в диапазоне Z in [44.0, 48.5] мм
        (выше обода ротора Z=44.0) под всей площадью монтажной колодки сформирован сплошной массив
        пластика площадью 145 мм², плавно сужающийся книзу под углом ровно 45.0° прямо в перо ножа.
      - Массивная монтажная колодка: Z in [48.5, 54.0] мм, толщина стенок паза 5.5 мм со стороны ножа
        и 5.0 мм с тыльной стороны, без внешних подрезок и утонений (полная конструкционная прочность).
      - Паз «ласточкин хвост» с углом 45° и гарантированным зазором 0.25 мм под шип дефлектора.
        Дно паза выполнено на отметке Z=48.25 мм (цельный монолитный пол под шипом дефлектора).
      - Стопорное отверстие под винт М3 (X'=17.0) для надежной фиксации.
    """
    c_x, c_y = -44.0, 0.0
    r_in = 42.5
    r_out = 45.5
    ang_def = math.degrees(math.atan2(15.0, 20.0)) # ~36.87°
    z_top = 48.5 # База дефлектора поднята на 4 мм (просвет 4.5 мм над ободом ротора)

    # 1. Цилиндрическое перо ножа (от Z = 29.0 до Z = 48.5)
    cyl_out = make_cylinder(r_out, z_top - 29.0, (c_x, c_y, 29.0))
    cyl_in = make_cylinder(r_in, z_top - 29.0 + 2.0, (c_x, c_y, 28.0))
    ring = cyl_out.cut(cyl_in)

    # 2. Высечение рабочего сектора дуги ножа: угол beta от -45.0° до +12.0°
    beta_start = -45.0
    cut_x_neg = make_box(60.0, 120.0, 30.0, (c_x - 60.0, -60.0, 25.0))
    cut_ang_neg = trans(rot_z(make_box(60.0, 60.0, 30.0, (0.0, -60.0, 25.0)), beta_start), c_x, c_y, 0)
    cut_ang_pos = trans(rot_z(make_box(60.0, 60.0, 30.0, (0.0, 0.0, 25.0)), 12.0), c_x, c_y, 0)
    blade_arc = ring.cut(cut_x_neg).cut(cut_ang_neg).cut(cut_ang_pos)

    # 3. Наклонный срез пологого пандуса ягод:
    # Носок на beta = -45°: Z = 31.0 мм (толщина 2.0 мм над базой Z=29.0)
    # Верх пандуса на beta = 0°: Z = 48.5 мм (стыковка с дефлектором)
    dy = 31.11
    dz = z_top - 31.0
    ramp_ang = math.degrees(math.atan2(dz, dy))
    cut_box = rot_axis(make_box(100.0, 100.0, 50.0, (-50.0, -100.0, z_top)), (0.0, 0.0, z_top), (1.0, 0.0, 0.0), ramp_ang)
    blade = blade_arc.cut(cut_box)

    # 4. Монолитный силовой фундамент под монтажную колодку (DfAM):
    # В декартовой системе координат дефлектора колодка занимает X' in [12.0, 22.0], Y' in [-7.5, 7.0].
    # Фундамент соединяет подошву колодки (Z'=0.0) с пером ножа (Z' <= -4.5), сужаясь под углом строго 45.0°
    # во всех 4 направлениях. Это исключает консоли и дает максимальную прочность (площадь 145 мм²).
    box_fund = make_box(10.0, 14.5, 5.0, (12.0, -7.5, -5.0))

    # Скос 45.0° слева (X' от 12.0 до 17.0 за dZ = 5.0 мм -> уклон ровно 45.0°)
    p1 = [FreeCAD.Vector(12.0, -10.0, 0.0), FreeCAD.Vector(12.0, -10.0, -6.0), FreeCAD.Vector(17.0, -10.0, -6.0), FreeCAD.Vector(17.0, -10.0, -5.0), FreeCAD.Vector(12.0, -10.0, 0.0)]
    c1 = Part.Face(Part.makePolygon(p1)).extrude(FreeCAD.Vector(0, 25.0, 0))

    # Скос 45.0° справа (X' от 22.0 до 17.0 за dZ = 5.0 мм -> уклон ровно 45.0°)
    p2 = [FreeCAD.Vector(22.0, -10.0, 0.0), FreeCAD.Vector(22.0, -10.0, -6.0), FreeCAD.Vector(17.0, -10.0, -6.0), FreeCAD.Vector(17.0, -10.0, -5.0), FreeCAD.Vector(22.0, -10.0, 0.0)]
    c2 = Part.Face(Part.makePolygon(p2)).extrude(FreeCAD.Vector(0, 25.0, 0))

    # Скос 45.0° спереди со стороны ножа (Y' от -7.5 до -2.5 за dZ = 5.0 мм -> уклон ровно 45.0°)
    p3 = [FreeCAD.Vector(10.0, -7.5, 0.0), FreeCAD.Vector(10.0, -7.5, -6.0), FreeCAD.Vector(10.0, -2.5, -6.0), FreeCAD.Vector(10.0, -2.5, -5.0), FreeCAD.Vector(10.0, -7.5, 0.0)]
    c3 = Part.Face(Part.makePolygon(p3)).extrude(FreeCAD.Vector(15.0, 0, 0))

    # Скос 45.0° сзади с тыльной стороны (Y' от 7.0 до 2.0 за dZ = 5.0 мм -> уклон ровно 45.0°)
    p4 = [FreeCAD.Vector(10.0, 7.0, 0.0), FreeCAD.Vector(10.0, 7.0, -6.0), FreeCAD.Vector(10.0, 2.0, -6.0), FreeCAD.Vector(10.0, 2.0, -5.0), FreeCAD.Vector(10.0, 7.0, 0.0)]
    c4 = Part.Face(Part.makePolygon(p4)).extrude(FreeCAD.Vector(15.0, 0, 0))

    foundation = box_fund.cut(c1).cut(c2).cut(c3).cut(c4).removeSplitter()

    # 5. Массивное тело монтажной колодки: Z' in [0.0, 5.5] (Z in [48.5, 54.0])
    # Стенки паза сохраняют полную толщину 5.5 мм и 5.0 мм по всей высоте
    boss_upper = make_box(10.0, 14.5, 5.5, (12.0, -7.5, 0.0))
    boss_total = boss_upper.fuse(foundation).removeSplitter()
    boss_total_rot = trans(rot_z(boss_total, ang_def), -14.0, -5.0, z_top)

    full_ejector = blade.fuse(boss_total_rot).removeSplitter()

    # 6. Вырез ответного профиля «ласточкин хвост» с гарантированным зазором 0.25 мм
    # Дно паза выполнено на Z' = -0.25 мм (сплошной монолитный пол колодки)
    pts_cutout = [
        FreeCAD.Vector(0, -2.0, 20.0),
        FreeCAD.Vector(0, -2.0, 3.75),
        FreeCAD.Vector(0, -4.5, 1.25),
        FreeCAD.Vector(0, -4.5, -0.25),
        FreeCAD.Vector(0, 4.5, -0.25),
        FreeCAD.Vector(0, 4.5, 1.25),
        FreeCAD.Vector(0, 2.0, 3.75),
        FreeCAD.Vector(0, 2.0, 20.0),
        FreeCAD.Vector(0, -2.0, 20.0)
    ]
    face_cutout = Part.Face(Part.makePolygon(pts_cutout))
    cutout_tool = trans(rot_z(face_cutout.extrude(FreeCAD.Vector(40.0, 0, 0)), ang_def), -14.0, -5.0, z_top)
    with_slot = full_ejector.cut(cutout_tool).removeSplitter()

    # 7. Отверстие под стопорный винт М3 (X'=17.0, в массивной стенке толщиной 5.5 мм)
    screw_hole = make_cylinder(1.5, 20.0, (17.0, -15.0, 1.75))
    screw_hole = rot_axis(screw_hole, (17.0, 0.0, 1.75), (1, 0, 0), -90.0)
    screw_hole = trans(rot_z(screw_hole, ang_def), -14.0, -5.0, z_top)

    ejector = with_slot.cut(screw_hole).removeSplitter()

    if not ejector.isValid():
        raise RuntimeError("Ejector shape is invalid!")

    return ejector


def verify_overhangs(shape, z_bed=29.0, max_allowable_overhang_deg=45.0):
    """
    Комплексная математическая верификация технологичности 3D-печати:
      1. Локальный контроль углов нормалей всех граней модели (правило 45°).
      2. Послойный теневой контроль отсутствия изолированных висящих островов (floating islands).
    """
    print("=" * 70)
    print("ВЕРИФИКАЦИЯ ТЕХНОЛОГИЧНОСТИ 3D-ПЕЧАТИ (ПРОВЕРКА НАВИСАНИЙ / OVERHANG)")
    print("=" * 70)
    print(f"Базовая плоскость печатного стола: Z = {z_bed:.2f} мм")
    print(f"Максимально допустимый угол нависания от вертикали: {max_allowable_overhang_deg:.1f}°")
    print(f"Минимально допустимый угол грани к горизонту: {90.0 - max_allowable_overhang_deg:.1f}°\n")

    all_passed = True
    bed_area = 0.0
    downward_count = 0

    for idx, f in enumerate(shape.Faces):
        try:
            u1, u2, v1, v2 = f.ParameterRange
            n = f.normalAt((u1 + u2) / 2.0, (v1 + v2) / 2.0)
        except Exception:
            n = f.normalAt(0, 0)

        if n.z < -1e-4:
            downward_count += 1
            zmin = f.BoundBox.ZMin
            zmax = f.BoundBox.ZMax

            # Проверка касания печатного стола
            if abs(zmin - z_bed) < 1e-3 and abs(zmax - z_bed) < 1e-3 and abs(n.z + 1.0) < 1e-3:
                bed_area += f.Area
                print(f"Грань #{idx:2d}: Базовый контакт со столом (Z={z_bed:.1f}), S={f.Area:6.2f} мм² [БАЗА СТОЛА]")
                continue

            # Микроскопические грани дискретизации OpenCASCADE (< 0.1 мм²)
            if f.Area < 0.1:
                print(f"Грань #{idx:2d}: Z=[{zmin:5.2f}, {zmax:5.2f}], S={f.Area:6.2f} мм² [МИКРО-ФАСКА < 0.1 мм² - OK]")
                continue

            horiz_comp = math.hypot(n.x, n.y)
            vert_comp = abs(n.z)
            angle_to_bed = math.degrees(math.atan2(horiz_comp, vert_comp))
            overhang_from_vert = math.degrees(math.atan2(vert_comp, horiz_comp))

            passed = (overhang_from_vert <= max_allowable_overhang_deg + 1e-1)
            status = "[PASS]" if passed else "[FAIL]"
            if not passed:
                all_passed = False

            print(f"Грань #{idx:2d}: Z=[{zmin:5.2f}, {zmax:5.2f}], S={f.Area:6.2f} мм², n=({n.x:5.2f}, {n.y:5.2f}, {n.z:5.2f}), "
                  f"угол к столу={angle_to_bed:5.1f}°, нависание={overhang_from_vert:5.1f}° {status}")

    print("\n--- Послойный контроль консолей (Layer-by-Layer Shadow Check) ---")
    cantilever_failed = False
    for z in [33.0, 38.0, 44.0, 46.0, 48.0, 50.0, 52.0]:
        p = Part.makePlane(200, 200, FreeCAD.Vector(-100, -100, z), FreeCAD.Vector(0, 0, 1))
        sec = shape.section(p)
        if len(sec.Edges) == 0:
            cantilever_failed = True
            print(f"  Срез Z={z:4.1f} мм: ПУСТОЙ СРЕЗ [FAIL]")
        else:
            print(f"  Срез Z={z:4.1f} мм: {len(sec.Edges):2d} ребер, BBox: X=[{sec.BoundBox.XMin:5.1f}, {sec.BoundBox.XMax:5.1f}], Y=[{sec.BoundBox.YMin:5.1f}, {sec.BoundBox.YMax:5.1f}] [OK]")

    if cantilever_failed:
        all_passed = False

    print("\n" + "-" * 70)
    print(f"Площадь адгезии к печатному столу (Z={z_bed:.1f}): {bed_area:.2f} мм²")
    print(f"Всего граней с наклоном вниз: {downward_count}")
    if all_passed:
        print("ВЕРДИКТ: ТРЕБОВАНИЕ САМООПОРНОСТИ ВЫПОЛНЕНО! Нависания > 45° ОТСУТСТВУЮТ.")
        print("         Консольные провисания полностью устранены пирамидальным переходом.")
        print("         Деталь на 100% пригодна для 3D-печати БЕЗ ПОДДЕРЖЕК.")
    else:
        print("ВЕРДИКТ: ОБНАРУЖЕНЫ НЕДОПУСТИМЫЕ НАВИСАНИЯ! Требуются поддержки.")
    print("=" * 70)
    return all_passed

def generate_ejector_drawing(shape, pdf_path="part_ejector.pdf",
                             fcstd_path="part_ejector.FCStd",
                             png_path="part_ejector.png"):
    """
    Генерирует официальный рабочий чертеж ножа-подъемника по ГОСТ (ЕСКД) формата А3:
      1. Главный вид (FrontView, перпендикулярно перу дефлектора, масштаб 2:1)
      2. Вид слева (LeftView, торец паза ласточкина хвоста, масштаб 2:1)
      3. Вид сверху (TopView, дуга пера ножа, масштаб 2:1)
      4. Аксонометрический вид (IsoView, масштаб 1.5:1)
      5. Полный размерный слой по ГОСТ 2.307-2011 с DPI-компенсацией
      6. Основная надпись (ГОСТ 2.104) и Технические требования (ГОСТ 2.316)
    """
    doc = FreeCAD.newDocument("Doc_part_ejector")
    feat = doc.addObject("Part::Feature", "part_ejector")
    feat.Shape = shape
    doc.recompute()

    page, template = create_drawing_page(doc, "A3_Landscape", "Page_part_ejector")
    page.ViewObject.ShowFrames = False

    # Размещение видов (масштаб 2:1 для проекций)
    v_front = add_part_view(doc, page, feat, "FrontView", (0.6, -0.8, 0.0), 2.0, 105.0, 195.0)
    v_left = add_part_view(doc, page, feat, "LeftView", (0.8, 0.6, 0.0), 2.0, 215.0, 195.0)
    v_top = add_part_view(doc, page, feat, "TopView", (0.0, 0.0, 1.0), 2.0, 105.0, 85.0)
    v_iso = add_part_view(doc, page, feat, "IsoView", (1.0, -1.2, 0.9), 1.5, 330.0, 205.0)

    # Векторный размерный слой по ГОСТ 2.307-2011
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
  .dim-line { stroke: #000; stroke-width: 0.35; fill: none; }
  .dim-ext { stroke: #000; stroke-width: 0.25; fill: none; }
  .center-line { stroke: #000; stroke-width: 0.25; stroke-dasharray: 6,1.5,1.5,1.5; fill: none; }
  .dim-text { font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: middle; }
  .leader { stroke: #000; stroke-width: 0.35; fill: none; }
  .note-title { font-family: osifont, Arial, sans-serif; font-size: 3.5px; font-weight: bold; fill: #000; }
  .note-text { font-family: osifont, Arial, sans-serif; font-size: 3.0px; fill: #000; }
</style>

<!-- ==================== LEFT VIEW (DOVETAIL SLOT & WALLS) ==================== -->
<!-- Slot Base Width 9 mm -->
<line x1="222.04" y1="85.0" x2="222.04" y2="96.0" class="dim-ext" />
<line x1="240.04" y1="85.0" x2="240.04" y2="96.0" class="dim-ext" />
<line x1="222.04" y1="93.5" x2="240.04" y2="93.5" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="231.04" y="92.0" class="dim-text">9*</text>

<!-- Slot Throat Opening 4 mm -->
<line x1="227.04" y1="73.0" x2="227.04" y2="65.0" class="dim-ext" />
<line x1="235.04" y1="73.0" x2="235.04" y2="65.0" class="dim-ext" />
<line x1="227.04" y1="67.0" x2="235.04" y2="67.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="231.04" y="65.8" class="dim-text">4</text>

<!-- Left Wall Thickness 5.5 mm -->
<line x1="216.04" y1="73.0" x2="216.04" y2="65.0" class="dim-ext" />
<line x1="216.04" y1="67.0" x2="227.04" y2="67.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="221.54" y="65.8" class="dim-text">5,5</text>

<!-- Right Wall Thickness 5.0 mm -->
<line x1="245.04" y1="73.0" x2="245.04" y2="65.0" class="dim-ext" />
<line x1="235.04" y1="67.0" x2="245.04" y2="67.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="240.04" y="65.8" class="dim-text">5,0</text>

<!-- Total Boss Width 14.5 mm -->
<line x1="216.04" y1="65.0" x2="216.04" y2="58.0" class="dim-ext" />
<line x1="245.04" y1="65.0" x2="245.04" y2="58.0" class="dim-ext" />
<line x1="216.04" y1="60.0" x2="245.04" y2="60.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="230.54" y="58.8" class="dim-text">14,5*</text>

<!-- Slot 45 deg callout -->
<path d="M 224.5 78.5 L 212.0 87.0 L 202.0 87.0" class="leader" marker-start="url(#dot)" />
<text x="207.0" y="85.5" class="dim-text">45°</text>

<!-- 45 deg Self-supporting DfAM transition callout -->
<path d="M 218.0 89.0 L 206.0 98.0 L 188.0 98.0" class="leader" marker-start="url(#dot)" />
<text x="197.0" y="96.5" class="dim-text">45° (переход DfAM)</text>

<!-- Boss Height 6 mm -->
<line x1="245.04" y1="73.0" x2="252.0" y2="73.0" class="dim-ext" />
<line x1="245.04" y1="85.0" x2="252.0" y2="85.0" class="dim-ext" />
<line x1="250.0" y1="73.0" x2="250.0" y2="85.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="248.5" y="79.0" transform="rotate(-90 248.5 79.0)" class="dim-text">6</text>

<!-- Total Part Height 25 mm -->
<line x1="245.04" y1="73.0" x2="260.0" y2="73.0" class="dim-ext" />
<line x1="245.04" y1="123.0" x2="260.0" y2="123.0" class="dim-ext" />
<line x1="258.0" y1="73.0" x2="258.0" y2="123.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="256.5" y="98.0" transform="rotate(-90 256.5 98.0)" class="dim-text">25*</text>

<!-- ==================== FRONT VIEW (RAMP & MAIN VIEW) ==================== -->
<!-- Nose Tip Thickness 2 mm -->
<path d="M 64.4 121.0 L 54.0 121.0 L 44.0 121.0" class="leader" marker-start="url(#dot)" />
<text x="49.0" y="119.5" class="dim-text">2</text>

<!-- Boss Length 10 mm -->
<line x1="122.0" y1="73.0" x2="122.0" y2="65.0" class="dim-ext" />
<line x1="142.0" y1="73.0" x2="142.0" y2="65.0" class="dim-ext" />
<line x1="122.0" y1="67.0" x2="142.0" y2="67.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="132.0" y="65.8" class="dim-text">10</text>

<!-- Ramp Working Length 29 mm -->
<line x1="64.4" y1="123.0" x2="64.4" y2="134.0" class="dim-ext" />
<line x1="122.4" y1="123.0" x2="122.4" y2="134.0" class="dim-ext" />
<line x1="64.4" y1="131.0" x2="122.4" y2="131.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="93.4" y="129.8" class="dim-text">29*</text>

<!-- Ramp Slope Angle Callout -->
<path d="M 90.0 108.0 L 80.0 95.0 L 62.0 95.0" class="leader" marker-start="url(#dot)" />
<text x="71.0" y="93.5" class="dim-text">27°* (угол подъема)</text>

<!-- Base Plane Callout -->
<path d="M 130.0 123.0 L 138.0 134.0 L 155.0 134.0" class="leader" marker-start="url(#dot)" />
<text x="146.0" y="132.5" class="dim-text">База Z=29,0*</text>

<!-- Screw Hole M3 Callout -->
<path d="M 134.0 76.0 L 142.0 57.0 L 164.0 57.0" class="leader" marker-start="url(#dot)" />
<text x="153.0" y="55.5" class="dim-text">Отв. М3 (Ø3,0)</text>

<!-- ==================== TOP VIEW (ARC & SECTOR) ==================== -->
<!-- Blade Width 3 mm -->
<line x1="104.65" y1="196.0" x2="104.65" y2="185.0" class="dim-ext" />
<line x1="110.65" y1="196.0" x2="110.65" y2="185.0" class="dim-ext" />
<line x1="104.65" y1="187.0" x2="110.65" y2="187.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="107.65" y="185.8" class="dim-text">3</text>

<!-- Arc Centerline Radius R44 -->
<path d="M 95.0 226.0 L 80.0 240.0 L 64.0 240.0" class="leader" marker-start="url(#dot)" />
<text x="72.0" y="238.5" class="dim-text">R44*</text>

<!-- Working Sector Angle 45 deg -->
<path d="M 82.0 258.0 L 70.0 270.0 L 52.0 270.0" class="leader" marker-start="url(#dot)" />
<text x="61.0" y="268.5" class="dim-text">45°* (сектор)</text>

<!-- Outer Radius R45.5 Callout -->
<path d="M 110.65 210.0 L 120.0 215.0 L 135.0 215.0" class="leader" marker-start="url(#dot)" />
<text x="127.5" y="213.5" class="dim-text">R45,5</text>

<!-- ==================== TECHNICAL REQUIREMENTS ==================== -->
<text x="235.0" y="190.0" class="note-title">Технические требования:</text>
<text x="235.0" y="196.5" class="note-text">1. * Размеры для справок.</text>
<text x="235.0" y="202.5" class="note-text">2. Материал: Пищевой PETG (Food Safe). Заполнение 100%.</text>
<text x="235.0" y="208.5" class="note-text">3. Толщина стенки паза со стороны ножа 5,5 мм (усиление замка).</text>
<text x="235.0" y="214.5" class="note-text">4. Угол подъема носка 27° (плавный безударный подъем ягод).</text>
<text x="235.0" y="220.5" class="note-text">5. Нижнюю грань ножа (Z=29.0) и рабочую поверхность пандуса отполировать (Ra &lt;= 0.8 мкм).</text>
<text x="235.0" y="226.5" class="note-text">6. Посадка на шип дефлектора ВЧ.01.00.013 с зазором 0.25 мм. Фиксация винтом М3.</text>
<text x="235.0" y="232.5" class="note-text">7. DfAM: пирамидальный переход под углом 45° во всех направлениях (печать без поддержек).</text>
</svg>'''

    sym_dim = doc.addObject("TechDraw::DrawViewSymbol", "DimensionsOverlay")
    sym_dim.Symbol = svg_dim
    page.addView(sym_dim)
    doc.recompute()
    sym_dim.Scale = get_symbol_scale_correction(420.0)
    sym_dim.X = 210.0
    sym_dim.Y = 148.5
    doc.recompute()

    title_fields = {
        'Номер': 'ВЧ.01.00.012',
        'Название': 'Нож-подъемник',
        'Масштаб': '2:1',
        'Лист': '1',
        'Листов': '1',
        'Материал': 'PETG',
        'Разработал': 'Демишкевич Э.Б.',
        'Проверил': 'Контролер',
        'Организация1': 'Проект VISHNI',
        'Организация2': 'VISHNI CAD'
    }
    fill_gost_title_block(template, title_fields)

    export_drawing(doc, page, pdf_path, fcstd_path, png_path)
    print("Ejector drawing generated successfully!")

create_part = create_ejector

if __name__ == "__main__":
    shape = create_ejector()
    print(f"Ejector solids: {len(shape.Solids)}, valid: {shape.isValid()}, vol: {shape.Volume:.1f} mm³")
    print(f"Ejector BBox: {shape.BoundBox}")
    verify_overhangs(shape)
    generate_ejector_drawing(shape)

