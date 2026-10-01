#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_deflector.py
Деталь: Дефлектор ягод (Berry Deflector Guide Wall)
Обозначение: ВЧ.01.00.013

Назначение:
  Отражающая направляющая стенка, перекрывающая круговое движение
  ягоды против часовой стрелки (CCW) на позиции 4 и перенаправляющая ее
  радиально наружу в приемный лоток.
  В нижней части оснащена продольным шипом под углом 45° для регулируемого
  крепления ножа-подъемника (ВЧ.01.00.012).
  На наружном конце имеет Т-образный шип (ласточкин хвост) для монтажа
  в паз на задней стенке приемного лотка (ВЧ.01.00.010).
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
    Вычисляет точный масштабный коэффициент для устранения ошибки масштабирования DPI
    (90 DPI в QtSvg против 96 DPI в FreeCAD TechDraw).
    """
    qt_pixels = round(sheet_width_mm * 90.0 / 25.4)
    freecad_mm = qt_pixels * 25.4 / 96.0
    return sheet_width_mm / freecad_mm

def create_deflector():
    """
    Создает твердотельную 3D B-Rep модель дефлектора с шипом «ласточкин хвост» лотка
    и продольным регулировочным шипом под 45° для крепления ножа-подъемника.
    Базовая система координат совпадает с Позицией 5 (Z=0 плоскость станины).
    Высота стенки: от Z = 44.5 до Z = 62.5 (h = 18.0 мм).
    Ориентация: угол ~36.9° к радиальной оси, направляет ягоды из +Y в +X.
    """
    x_c = 21.5
    def_len = 44.0
    def_th = 3.5
    def_h = 18.0

    # 1. Основное тело дефлекторной стенки (толщина 3.5 мм)
    def_box = make_box(def_len, def_th, def_h, (0.0, -def_th / 2.0, 0.0))

    # 2. Продольное утолщение (симметричный двусторонний шип) под углом 45° в нижней части:
    # Идет вдоль обеих сторон стенки от входа (X'=0) до X'=27.0 мм (где оканчивается нож).
    # Основание шипа: Y' in [-4.25, +4.25] (общая ширина основания 8.5 мм при толщине стенки 3.5 мм).
    # Вертикальная заходная полка высотой 1.0 мм (Z in [0, 1.0]).
    # Скосы 45.0° с обеих сторон от |Y'|=4.25 до |Y'|=1.75 на высоте Z in [1.0, 3.5].
    # Общая высота шипа: 3.5 мм (Z in [44.5, 48.0] в абсолютных координатах).
    pts = [
        FreeCAD.Vector(0, -1.75, 3.5),
        FreeCAD.Vector(0, -4.25, 1.0),
        FreeCAD.Vector(0, -4.25, 0.0),
        FreeCAD.Vector(0, 4.25, 0.0),
        FreeCAD.Vector(0, 4.25, 1.0),
        FreeCAD.Vector(0, 1.75, 3.5),
        FreeCAD.Vector(0, -1.75, 3.5)
    ]
    face_t = Part.Face(Part.makePolygon(pts))
    tenon_full = face_t.extrude(FreeCAD.Vector(35.0, 0, 0))

    # 3. Правый переход с шипа в стандартную толщину стенки (3.5 мм):
    # Выполняется под углом 45° на участке X' in [27.0, 29.5] мм (dX = 2.5 мм, dY = 2.5 мм) с обеих сторон.
    p_cut_front = [
        FreeCAD.Vector(27.0, -5.0, -2.0),
        FreeCAD.Vector(50.0, -5.0, -2.0),
        FreeCAD.Vector(50.0, -1.75, -2.0),
        FreeCAD.Vector(29.5, -1.75, -2.0),
        FreeCAD.Vector(27.0, -4.25, -2.0),
        FreeCAD.Vector(27.0, -5.0, -2.0)
    ]
    cut_front = Part.Face(Part.makePolygon(p_cut_front)).extrude(FreeCAD.Vector(0, 0, 10.0))

    p_cut_back = [
        FreeCAD.Vector(27.0, 5.0, -2.0),
        FreeCAD.Vector(50.0, 5.0, -2.0),
        FreeCAD.Vector(50.0, 1.75, -2.0),
        FreeCAD.Vector(29.5, 1.75, -2.0),
        FreeCAD.Vector(27.0, 4.25, -2.0),
        FreeCAD.Vector(27.0, 5.0, -2.0)
    ]
    cut_back = Part.Face(Part.makePolygon(p_cut_back)).extrude(FreeCAD.Vector(0, 0, 10.0))

    tenon_body = tenon_full.cut(cut_front).cut(cut_back)

    # Объединение стенки и продольного шипа
    wall_with_tenon = def_box.fuse(tenon_body).removeSplitter()

    # Поворот и позиционирование в глобальной системе координат
    # Базовая отметка поднята до Z = 48.5 мм (просвет 4.5 мм над ротором для перехода DfAM ножа-подъемника)
    ang_def = math.degrees(math.atan2(15.0, 20.0)) # ~36.87°
    def_rot = rot_z(wall_with_tenon, ang_def)
    deflector_wall = trans(def_rot, -14.0, -5.0, 48.5)

    # 4. Обрезка наружной части стенки по линии Y = 17.0 мм
    # За пределы Y = 17.0 выходит только шип «ласточкин хвост»!
    cut_wall_beyond = make_box(60.0, 20.0, 30.0, (0.0, 17.0, 40.0))
    deflector_wall = deflector_wall.cut(cut_wall_beyond)

    # 5. Соединительный прилив вдоль стенки желоба (Y in [15.5, 17.0], X in [16.0, x_c + 2.0])
    tab = make_box(x_c + 2.0 - 16.0, 1.5, def_h, (16.0, 15.5, 48.5))

    # 6. Шип «ласточкин хвост» (Dovetail Tenon) для крепления к лотку:
    # Высота 17.0 мм, опущен до Z = 48.5 заподлицо с нижним торцом стенки дефлектора.
    # Образует сплошную плоскую грань опоры на печатный стол без единой поддержки!
    q1 = FreeCAD.Vector(x_c - 1.95, 16.8, 48.5)
    q2 = FreeCAD.Vector(x_c + 1.95, 16.8, 48.5)
    q3 = FreeCAD.Vector(x_c + 3.95, 20.9, 48.5)
    q4 = FreeCAD.Vector(x_c - 3.95, 20.9, 48.5)
    poly_t = Part.makePolygon([q1, q2, q3, q4, q1])
    face_t = Part.Face(poly_t)
    dovetail = face_t.extrude(FreeCAD.Vector(0, 0, 17.0))

    # 7. Финальное объединение в монолитное твердое тело
    deflector = deflector_wall.fuse(tab).fuse(dovetail)
    deflector = deflector.removeSplitter()

    if not deflector.isValid():
        raise RuntimeError("Deflector shape is invalid!")

    return deflector

def generate_deflector_drawing(shape, pdf_path="part_deflector.pdf",
                               fcstd_path="part_deflector.FCStd",
                               png_path="part_deflector.png"):
    """
    Генерирует официальный рабочий чертеж детали по ГОСТ (ЕСКД) формата А3:
      1. Главный вид (перпендикулярно перу дефлектора, масштаб 2:1)
      2. Третья проекция: вид слева / с торца (масштаб 2:1)
      3. Вид сверху (масштаб 2:1)
      4. Аксонометрический вид (масштаб 1.5:1)
      5. Вертикальный разрез А-А в плоскости, перпендикулярной дефлектору (масштаб 2:1)
      6. Полный размерный слой по ГОСТ 2.307-2011 с DPI-компенсацией
      7. Основная надпись (ГОСТ 2.104) и Технические требования (ГОСТ 2.316)
    """
    doc = FreeCAD.newDocument("Doc_part_deflector")
    feat = doc.addObject("Part::Feature", "part_deflector")
    feat.Shape = shape
    doc.recompute()

    page, template = create_drawing_page(doc, "A3_Landscape", "Page_part_deflector")
    page.ViewObject.ShowFrames = False

    # 1. Главный вид: нормаль (0.6, -0.8, 0.0), масштаб 2:1
    v_front = add_part_view(doc, page, feat, "FrontView", (0.6, -0.8, 0.0), 2.0, 100.0, 200.0)

    # 2. Третья проекция: вид слева / с торца (0.8, 0.6, 0.0), масштаб 2:1, соосность по Y
    v_left = add_part_view(doc, page, feat, "LeftView", (0.8, 0.6, 0.0), 2.0, 185.0, 200.0)

    # 3. Вид сверху: нормаль (0.0, 0.0, 1.0), масштаб 2:1, соосность по X с главным видом
    v_top = add_part_view(doc, page, feat, "TopView", (0.0, 0.0, 1.0), 2.0, 100.0, 95.0)

    # 4. Аксонометрия: масштаб 1.5:1
    v_iso = add_part_view(doc, page, feat, "IsoView", (1.0, -1.2, 0.9), 1.5, 335.0, 205.0)

    # 5. Вертикальный разрез А-А в плоскости, перпендикулярной перу дефлектора
    # Секущая плоскость на виде спереди (FrontView) на X' = 13.5 мм, направление взгляда вправо
    sec = doc.addObject("TechDraw::DrawViewSection", "SectionA")
    sec.BaseView = v_front
    sec.SectionNormal = FreeCAD.Vector(0.8, 0.6, 0.0)
    sec.SectionOrigin = FreeCAD.Vector(-3.2, 3.1, 50.0)
    sec.SectionDirection = "Right"
    sec.SectionSymbol = "A"
    page.addView(sec)
    doc.recompute()
    sec.Scale = 2.0
    sec.X = 185.0
    sec.Y = 95.0
    sec.IsoCount = 0
    sec.ViewObject.HatchColor = (0.0, 0.0, 0.0, 1.0)
    doc.recompute()

    # 6. Размерный слой и обозначения по ГОСТ (SVG Overlay)
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
  .dim-text { font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: middle; }
  .sec-title { font-family: osifont, Arial, sans-serif; font-size: 4.5px; font-weight: bold; fill: #000; text-anchor: middle; }
  .leader { stroke: #000; stroke-width: 0.35; fill: none; }
</style>

<!-- ==================== ГЛАВНЫЙ ВИД (РАЗМЕРЫ) ==================== -->
<!-- Длина рабочей части стенки дефлектора: 44* -->
<line x1="52.9" y1="76.0" x2="52.9" y2="62.0" class="dim-ext" />
<line x1="140.9" y1="76.0" x2="140.9" y2="62.0" class="dim-ext" />
<line x1="52.9" y1="64.0" x2="140.9" y2="64.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="96.9" y="62.5" class="dim-text">44*</text>

<!-- Высота стенки дефлектора: 18 -->
<line x1="49.0" y1="79.0" x2="37.0" y2="79.0" class="dim-ext" />
<line x1="49.0" y1="115.0" x2="37.0" y2="115.0" class="dim-ext" />
<line x1="40.0" y1="79.0" x2="40.0" y2="115.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="38.5" y="97.0" transform="rotate(-90 38.5 97.0)" class="dim-text">18</text>

<!-- Длина продольного шипа: 27 -->
<line x1="52.9" y1="118.0" x2="52.9" y2="129.0" class="dim-ext" />
<line x1="106.9" y1="118.0" x2="106.9" y2="129.0" class="dim-ext" />
<line x1="52.9" y1="126.0" x2="106.9" y2="126.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="73.0" y="124.5" class="dim-text">27</text>

<!-- Переход со скосом 45° -->
<path d="M 109.0 113.0 L 117.0 125.0 L 133.0 125.0" class="leader" marker-start="url(#dot)" />
<text x="125.0" y="123.5" class="dim-text">2,5×45°</text>

<!-- Высота шипа крепления к лотку: 17 -->
<line x1="143.0" y1="81.0" x2="153.0" y2="81.0" class="dim-ext" />
<line x1="143.0" y1="115.0" x2="153.0" y2="115.0" class="dim-ext" />
<line x1="150.0" y1="81.0" x2="150.0" y2="115.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="148.5" y="98.0" transform="rotate(-90 148.5 98.0)" class="dim-text">17</text>

<!-- ==================== РАЗРЕЗ А-А (РАЗМЕРЫ) ==================== -->
<!-- Обозначение сечения -->
<text x="185.0" y="173.0" class="sec-title">А-А (2:1)</text>

<!-- Полная высота сечения: 18 -->
<line x1="174.0" y1="184.0" x2="166.0" y2="184.0" class="dim-ext" />
<line x1="174.0" y1="220.0" x2="166.0" y2="220.0" class="dim-ext" />
<line x1="169.0" y1="184.0" x2="169.0" y2="220.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="167.5" y="202.0" transform="rotate(-90 167.5 202.0)" class="dim-text">18</text>

<!-- Толщина стенки: 3,5 -->
<line x1="181.5" y1="182.0" x2="181.5" y2="177.0" class="dim-ext" />
<line x1="188.5" y1="182.0" x2="188.5" y2="177.0" class="dim-ext" />
<line x1="181.5" y1="179.0" x2="188.5" y2="179.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="185.0" y="177.5" class="dim-text">3,5</text>

<!-- Ширина симметричного основания с шипом: 8,5 -->
<line x1="176.5" y1="222.0" x2="176.5" y2="229.0" class="dim-ext" />
<line x1="193.5" y1="222.0" x2="193.5" y2="229.0" class="dim-ext" />
<line x1="176.5" y1="226.0" x2="193.5" y2="226.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="185.0" y="224.5" class="dim-text">8,5</text>

<!-- Высота шипа: 3,5 -->
<line x1="196.0" y1="213.0" x2="204.0" y2="213.0" class="dim-ext" />
<line x1="196.0" y1="220.0" x2="204.0" y2="220.0" class="dim-ext" />
<line x1="201.0" y1="213.0" x2="201.0" y2="220.0" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="199.5" y="216.5" transform="rotate(-90 199.5 216.5)" class="dim-text">3,5</text>

<!-- Выноска угла скоса 45° с обеих сторон -->
<path d="M 191.0 215.5 L 202.0 205.0 L 226.0 205.0" class="leader" marker-start="url(#dot)" />
<text x="214.0" y="203.5" class="dim-text">2,5×45° (2 фаски)</text>

</svg>'''

    sym_dim = doc.addObject('TechDraw::DrawViewSymbol', 'DimensionsOverlay')
    sym_dim.Symbol = svg_dim
    page.addView(sym_dim)
    doc.recompute()
    sym_dim.Scale = get_symbol_scale_correction(420.0)
    sym_dim.X = 210.0
    sym_dim.Y = 148.5
    doc.recompute()

    # 7. Заполнение основной надписи (ГОСТ 2.104, Форма 1)
    title_fields = {
        'Номер': 'ВЧ.01.00.013',
        'Название': 'Дефлектор',
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

    # 8. Технические требования (ГОСТ 2.316)
    notes = [
        '1. * Размеры для справок.',
        '2. Материал: Пищевой PETG (Food Safe). Заполнение 100%.',
        '3. Симметричный двусторонний шип 45° предназначен для регулируемого крепления ножа-подъемника ВЧ.01.00.012.',
        '4. Шип «ласточкин хвост» сопрягается с пазом лотка ВЧ.01.00.010 с гарантированным зазором 0.25 мм.',
        '5. Деталь полностью оптимизирована для 3D-печати на нижнем торце (Z=44.5) без поддержек.'
    ]
    notes_h = 16.0 + len(notes) * 6.5
    svg_notes = f'''<svg xmlns="http://www.w3.org/2000/svg" width="185mm" height="{notes_h}mm" viewBox="0 0 185 {notes_h}">
<text x="5" y="10" font-family="osifont, Arial" font-size="3.5" font-weight="bold" fill="black">Технические требования:</text>'''
    for idx, line in enumerate(notes):
        svg_notes += f'<text x="5" y="{17 + idx*6.5}" font-family="osifont, Arial" font-size="3.0" fill="black">{line}</text>'
    svg_notes += '</svg>'

    sym_notes = doc.addObject('TechDraw::DrawViewSymbol', 'TechNotes')
    sym_notes.Symbol = svg_notes
    page.addView(sym_notes)
    doc.recompute()
    sym_notes.X = 327.5
    sym_notes.Y = 55.0 + notes_h / 2.0 + 2.0
    doc.recompute()

    # 9. Экспорт чертежа в PDF, native FCStd и растровый PNG
    export_drawing(doc, page, pdf_path, fcstd_path, png_path)
    print("Deflector drawing generated successfully!")

create_part = create_deflector

if __name__ == "__main__":
    shape = create_deflector()
    print(f"Deflector solids: {len(shape.Solids)}, valid: {shape.isValid()}, vol: {shape.Volume:.1f} mm³")
    generate_deflector_drawing(shape)
