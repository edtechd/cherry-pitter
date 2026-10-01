#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_mgn9_rail.py
Поз. 19: Рельс направляющий линейный MGN9-100 (Miniature Linear Guide Rail 100mm)
Создание B-Rep 3D-модели и оформление рабочего чертежа по ГОСТ (ЕСКД).
"""

import sys
import os
import math

# Пути FreeCAD и рабочей директории
sys.path.append('/usr/lib/freecad/lib')
sys.path.append('/usr/share/freecad/Mod/TechDraw')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from freecad_utils import (
    FreeCAD, Part, TechDraw, TechDrawGui,
    make_box, make_cylinder,
    create_drawing_page, add_part_view,
    fill_gost_title_block, export_drawing
)

def create_mgn9_rail(length=100.0, E=7.5, P=20.0, Wr=9.0, Hr=6.5, D=6.0, h=3.5, d=3.5):
    """
    Создает аналитический B-Rep солид направляющего рельса MGN9 длиной 100 мм.
    Координаты:
    - Начало координат (0,0,0) привязано к базовому торцу рельса:
      - X в [0, length] = [0, 100.0] - продольная ось;
      - Y в [-Wr/2, Wr/2] = [-4.5, +4.5] - поперечная ось;
      - Z в [0, Hr] = [0, 6.5] - вертикальная ось;
    - Продольные беговые канавки под шарики с обеих сторон (Z = Hr/2 = 3.25 мм, R = 1.1 мм, глубина 0.5 мм);
    - 5 крепежных ступенчатых отверстий с цековкой:
      - Базовый торец: E = 7.5 мм;
      - Шаг между отверстиями: P = 20.0 мм (x = 7.5, 27.5, 47.5, 67.5, 87.5 мм);
      - Расстояние до противоположного торца: 100 - 87.5 = 12.5 мм;
      - Цековка: диаметр D = 6.0 мм, глубина h = 3.5 мм (от Z=6.5 до Z=3.0 мм);
      - Сквозное отверстие: диаметр d = 3.5 мм под винт M3 (от Z=3.0 до Z=0).
    """
    # 1. Основное тело бруса
    rail = make_box(length, Wr, Hr, (0, -Wr / 2.0, 0))
    
    # 2. Продольные канавки под шарики на боковых гранях
    # Для устранения касательных сингулярностей делаем инструмент с запасом по X [-1.0, length+1.0]
    groove_r = 1.1
    y_cut_offset = Wr / 2.0 + groove_r - 0.5  # глубина врезания 0.5 мм
    z_groove = Hr / 2.0  # 3.25 мм
    
    groove_right = Part.makeCylinder(groove_r, length + 2.0, FreeCAD.Vector(-1.0, y_cut_offset, z_groove), FreeCAD.Vector(1, 0, 0))
    groove_left = Part.makeCylinder(groove_r, length + 2.0, FreeCAD.Vector(-1.0, -y_cut_offset, z_groove), FreeCAD.Vector(1, 0, 0))
    rail = rail.cut(groove_right).cut(groove_left)
    
    # 3. 5 крепежных ступенчатых отверстий вдоль X
    x_pos = E
    while x_pos < length:
        # Цековка (D=6.0 -> r=3.0, h=3.5 от верхней плоскости Z=6.5 вниз до 3.0)
        # Выпуск вверх до Z=8.0 для чистого пересечения
        cb = make_cylinder(D / 2.0, h + 1.5, (x_pos, 0, Hr - h), (0, 0, 1))
        # Сквозное отверстие (d=3.5 -> r=1.75, от Z=-1.0 до Z=Hr - h + 0.5)
        th = make_cylinder(d / 2.0, Hr - h + 1.5, (x_pos, 0, -1.0), (0, 0, 1))
        
        rail = rail.cut(cb).cut(th)
        x_pos += P
        
    if not rail.isValid():
        raise ValueError("Rail solid shape is invalid!")
        
    return rail

create_part = create_mgn9_rail

def generate_mgn9_rail_drawing(part_name="part_mgn9_rail",
                               doc_code="ВЧ.02.00.002",
                               title_name="Рельс направляющий MGN9-100",
                               material="Сталь 55 / ТВЧ",
                               scale=1.5,
                               sheet="A3_Landscape",
                               pdf_name=None,
                               fcstd_name=None,
                               png_name=None,
                               notes=None):
    """
    Генерирует рабочий чертеж направляющего рельса MGN9-100 по ГОСТ (ЕСКД):
    - Формат А3, масштаб 1.5:1 (длина 100 мм на листе составляет 150 мм);
    - Главный вид: продольный разрез А-А по оси отверстий Y=0, показывающий цековку Ø6х3.5 и отв. Ø3.5;
    - Вид сверху: связь по X, показывает шаг P=20, базовый размер E=7.5, ширину Wr=9;
    - Вид слева (с торца): сечение рельса Wr=9, Hr=6.5 и беговые дорожки под шарики;
    - Изометрический вид;
    - Векторный оверлей размеров по ГОСТ 2.307 с компенсацией DPI;
    - Основная надпись по ГОСТ 2.104 и техтребования по ГОСТ 2.316.
    """
    shape = create_mgn9_rail()
    
    doc = FreeCAD.newDocument(f"Doc_{part_name}")
    feat = doc.addObject("Part::Feature", part_name)
    feat.Shape = shape
    doc.recompute()
    
    page, template = create_drawing_page(doc, sheet, f"Page_{part_name}")
    
    # Координаты видов на листе А3 (420 x 297 мм), масштаб 1.5:1
    x_c = 130.0
    y_front_td = 195.0
    y_top_td = 110.0
    x_left = 250.0
    y_left_td = 195.0
    
    # 1. Вид сверху (BaseView для продольного разреза А-А)
    v_top = add_part_view(doc, page, feat, "TopView", (0.0, 0.0, 1.0), scale, x_c, y_top_td)
    
    # 2. Продольный диаметральный разрез А-А по оси отверстий Y=0
    sec = doc.addObject("TechDraw::DrawViewSection", "SectionView")
    sec.BaseView = v_top
    sec.SectionNormal = FreeCAD.Vector(0.0, -1.0, 0.0)
    sec.SectionOrigin = FreeCAD.Vector(50.0, 0.0, 3.25)
    sec.SectionDirection = "Down"
    sec.SectionSymbol = "A"
    page.addView(sec)
    doc.recompute()
    
    sec.Direction = FreeCAD.Vector(0.0, -1.0, 0.0)
    sec.XDirection = FreeCAD.Vector(1.0, 0.0, 0.0)
    sec.Rotation = 0.0
    sec.Scale = scale
    sec.X = x_c
    sec.Y = y_front_td
    sec.IsoCount = 0
    sec.ViewObject.HatchColor = (0.0, 0.0, 0.0, 1.0)
    doc.recompute()
    
    # 3. Вид с торца (слева, вдоль оси X)
    v_left = add_part_view(doc, page, feat, "LeftView", (1.0, 0.0, 0.0), 3.0, x_left, y_left_td)
    
    # 4. Изометрический вид
    add_part_view(doc, page, feat, "IsoView", (1.0, -1.2, 0.9), 1.1, 350.0, 205.0)
    
    # 5. Основная надпись (штамп ГОСТ 2.104)
    title_fields = {
        'Номер': doc_code,
        'Название': 'Рельс направляющий',
        'Информация': 'MGN9-100',
        'Масштаб': '1,5:1',
        'Лист': '1',
        'Листов': '1',
        'Материал1': 'Сталь 55',
        'Материал2': 'ГОСТ 1050-88',
        'Материал3': 'закалка ТВЧ',
        'Организация1': 'ПРОЕКТ VISHNI',
        'Разработал': 'Инженер',
        'Проверил': 'Контролер'
    }
    fill_gost_title_block(template, title_fields)
    doc.recompute()
    
    # 6. Технические требования (ГОСТ 2.316)
    if notes is None:
        notes = [
            "1. * Размеры для справок.",
            "2. Материал: высокоуглеродистая конструкционная сталь 55 ГОСТ 1050-88.",
            "3. Поверхностная закалка ТВЧ дорожек качения: 58...62 HRC на глубину не менее 0,8 мм.",
            "4. Базовый торец: E = 7,5 мм; противоположный торец: 12,5 мм (при симметричной резке E = 10,0 мм).",
            "5. Допуск прямолинейности и скручивания: 0,02 мм на 100 мм длины.",
            "6. Отверстия под крепежные винты М3 с цилиндрической головкой DIN 912 (ГОСТ 11738-84)."
        ]
        
    notes_svg_lines = ['<text x="220" y="165" font-family="osifont, Arial, sans-serif" font-size="3.6px" font-weight="bold" fill="#000">Технические требования:</text>']
    for idx, line in enumerate(notes):
        notes_svg_lines.append(f'<text x="220" y="{173 + idx * 5.5}" font-family="osifont, Arial, sans-serif" font-size="3.0px" fill="#000">{line}</text>')
    notes_svg = '\n'.join(notes_svg_lines)
    
    # 7. Векторный оверлей размеров (ГОСТ 2.307-2011)
    # Преобразование координат в SVG:
    # SectionView: center x = 130.0, y_td = 195.0 -> y_svg = 297 - 195 = 102.0
    # Длина 100 * 1.5 = 150 мм (x от 130 - 75 = 55.0 до 130 + 75 = 205.0)
    # Высота 6.5 * 1.5 = 9.75 мм (y_svg от 102 - 4.875 = 97.125 до 102 + 4.875 = 106.875)
    # Отверстия вдоль X при масштабе 1.5:
    # x0 (торец): 55.0
    # Отв. 1: 55.0 + 7.5 * 1.5 = 66.25
    # Отв. 2: 66.25 + 20 * 1.5 = 96.25
    # Отв. 3: 96.25 + 30 = 126.25
    # Отв. 4: 126.25 + 30 = 156.25
    # Отв. 5: 156.25 + 30 = 186.25
    # Правый торец: 205.0 (расстояние 205.0 - 186.25 = 18.75 = 12.5 * 1.5)
    #
    # TopView: center x = 130.0, y_td = 110.0 -> y_svg = 297 - 110 = 187.0
    # Ширина Wr = 9.0 * 1.5 = 13.5 мм (y_svg от 187 - 6.75 = 180.25 до 187 + 6.75 = 193.75)
    #
    # LeftView: масштаб 3:1, center x = 270.0, y_td = 195.0 -> y_svg = 102.0
    # Ширина 9.0 * 3 = 27.0 мм (x от 270 - 13.5 = 256.5 до 270 + 13.5 = 283.5)
    # Высота 6.5 * 3 = 19.5 мм (y_svg от 102 - 9.75 = 92.25 до 102 + 9.75 = 111.75)
    
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
  .dim-line {{ stroke: #000; stroke-width: 0.35; fill: none; }}
  .dim-ext {{ stroke: #000; stroke-width: 0.25; fill: none; }}
  .center-line {{ stroke: #000; stroke-width: 0.25; stroke-dasharray: 6,1.5,1.5,1.5; fill: none; }}
  .dim-text {{ font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: middle; }}
  .dim-text-sm {{ font-family: osifont, Arial, sans-serif; font-size: 2.8px; fill: #000; text-anchor: middle; }}
  .view-title {{ font-family: osifont, Arial, sans-serif; font-size: 4.5px; fill: #000; text-anchor: middle; font-weight: bold; }}
  .leader {{ stroke: #000; stroke-width: 0.35; fill: none; }}
</style>

<!-- ==================== РАЗРЕЗ А-А ==================== -->
<text x="130" y="60" class="view-title">А-А</text>

<!-- Осевые линии 5 отверстий -->
<line x1="66.25" y1="92" x2="66.25" y2="112" class="center-line" />
<line x1="96.25" y1="92" x2="96.25" y2="112" class="center-line" />
<line x1="126.25" y1="92" x2="126.25" y2="112" class="center-line" />
<line x1="156.25" y1="92" x2="156.25" y2="112" class="center-line" />
<line x1="186.25" y1="92" x2="186.25" y2="112" class="center-line" />

<!-- Уровень 1 размеров (y = 82): E = 7.5, P = 20, 12.5* -->
<line x1="55" y1="97" x2="55" y2="80" class="dim-ext" />
<line x1="66.25" y1="97" x2="66.25" y2="80" class="dim-ext" />
<line x1="55" y1="82" x2="66.25" y2="82" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="60.6" y="80.5" class="dim-text">7,5</text>

<line x1="96.25" y1="97" x2="96.25" y2="80" class="dim-ext" />
<line x1="66.25" y1="82" x2="96.25" y2="82" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="81.25" y="80.5" class="dim-text">20</text>

<line x1="186.25" y1="97" x2="186.25" y2="80" class="dim-ext" />
<line x1="205" y1="97" x2="205" y2="80" class="dim-ext" />
<line x1="186.25" y1="82" x2="205" y2="82" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="195.6" y="80.5" class="dim-text">12,5*</text>

<!-- Уровень 2 размеров (y = 70): 4 x 20 = 80 -->
<line x1="66.25" y1="80" x2="66.25" y2="68" class="dim-ext" />
<line x1="186.25" y1="80" x2="186.25" y2="68" class="dim-ext" />
<line x1="66.25" y1="70" x2="186.25" y2="70" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="126.25" y="68.5" class="dim-text">4 × 20 = 80</text>

<!-- 5. Полная длина рельса L = 100 (снизу, y = 122) -->
<line x1="55" y1="107" x2="55" y2="125" class="dim-ext" />
<line x1="205" y1="107" x2="205" y2="125" class="dim-ext" />
<line x1="55" y1="122" x2="205" y2="122" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="130" y="120.5" class="dim-text">100</text>

<!-- 6. Высота рельса Hr = 6.5 -->
<line x1="55" y1="97.1" x2="43" y2="97.1" class="dim-ext" />
<line x1="55" y1="106.9" x2="43" y2="106.9" class="dim-ext" />
<line x1="46" y1="97.1" x2="46" y2="106.9" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="43" y="102" transform="rotate(-90 43 102)" class="dim-text">6,5</text>

<!-- 7. Глубина цековки h = 3.5 -->
<line x1="66.25" y1="102.35" x2="75" y2="102.35" class="dim-ext" />
<line x1="66.25" y1="97.1" x2="75" y2="97.1" class="dim-ext" />
<line x1="73" y1="97.1" x2="73" y2="102.35" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="77" y="100.5" class="dim-text">3,5</text>

<!-- ==================== ВИД СВЕРХУ ==================== -->
<text x="130" y="160" class="view-title">Вид сверху</text>

<!-- Продольная осевая линия рельса -->
<line x1="50" y1="187" x2="210" y2="187" class="center-line" />
<!-- Поперечные оси 5 отверстий -->
<line x1="66.25" y1="176" x2="66.25" y2="198" class="center-line" />
<line x1="96.25" y1="176" x2="96.25" y2="198" class="center-line" />
<line x1="126.25" y1="176" x2="126.25" y2="198" class="center-line" />
<line x1="156.25" y1="176" x2="156.25" y2="198" class="center-line" />
<line x1="186.25" y1="176" x2="186.25" y2="198" class="center-line" />

<!-- 8. Ширина рельса Wr = 9 -->
<line x1="55" y1="180.25" x2="43" y2="180.25" class="dim-ext" />
<line x1="55" y1="193.75" x2="43" y2="193.75" class="dim-ext" />
<line x1="46" y1="180.25" x2="46" y2="193.75" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="43" y="187" transform="rotate(-90 43 187)" class="dim-text">9</text>

<!-- Выноска параметров отверстий (5 отв. Ø3.5, цек. Ø6 х 3.5) -->
<path d="M 96.25 187 L 115 170 L 175 170" class="leader" marker-start="url(#dot)" />
<text x="145" y="168" class="dim-text">5 отв. Ø3,5 (скв.)</text>
<text x="145" y="174" class="dim-text-sm">цек. Ø6 глубина 3,5</text>

<!-- ==================== ВИД С ТОРЦА (СЛЕВА) ==================== -->
<text x="250" y="70" class="view-title">Вид с торца (3:1)</text>

<!-- Осевые линии торца -->
<line x1="250" y1="88" x2="250" y2="116" class="center-line" />
<line x1="232" y1="102" x2="268" y2="102" class="center-line" />

<!-- 9. Ширина Wr = 9 на виде с торца -->
<line x1="236.5" y1="92.25" x2="236.5" y2="82" class="dim-ext" />
<line x1="263.5" y1="92.25" x2="263.5" y2="82" class="dim-ext" />
<line x1="236.5" y1="84" x2="263.5" y2="84" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="250" y="82.5" class="dim-text">9</text>

<!-- 10. Высота Hr = 6.5 на виде с торца -->
<line x1="263.5" y1="92.25" x2="275" y2="92.25" class="dim-ext" />
<line x1="263.5" y1="111.75" x2="275" y2="111.75" class="dim-ext" />
<line x1="272" y1="92.25" x2="272" y2="111.75" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="275" y="103" class="dim-text">6,5</text>

<!-- Выноска боковых дорожек под шарики -->
<path d="M 238 102 L 222 92 L 195 92" class="leader" marker-start="url(#dot)" />
<text x="208" y="90" class="dim-text">Дорожка R1,1</text>
<text x="208" y="96" class="dim-text-sm">глубина 0,5</text>

<!-- ==================== ИЗОМЕТРИЯ ==================== -->
<text x="350" y="60" class="view-title">Изометрия</text>

<!-- ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ -->
{notes_svg}

</svg>'''
    
    sym_dim = doc.addObject('TechDraw::DrawViewSymbol', 'OverlayDimensions')
    sym_dim.Symbol = svg_dim
    page.addView(sym_dim)
    doc.recompute()
    
    scale_corr = 420.0 / (1488.0 * 25.4 / 96.0)
    sym_dim.Scale = scale_corr
    sym_dim.X = 210.0
    sym_dim.Y = 148.5
    doc.recompute()
    
    if pdf_name is None:
        pdf_name = f"{part_name}.pdf"
    if fcstd_name is None:
        fcstd_name = f"{part_name}.FCStd"
    if png_name is None:
        png_name = f"{part_name}.png"
        
    export_drawing(doc, page, pdf_name, fcstd_name, png_name)
    print(f"Drawing for {part_name} generated successfully!")

if __name__ == "__main__":
    generate_mgn9_rail_drawing()
