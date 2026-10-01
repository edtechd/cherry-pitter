#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_mgn9h_carriage.py
Поз. 20: Каретка линейной направляющей MGN9H (Extended Miniature Carriage Block)
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

def create_mgn9h_carriage(H=10.0, H1=2.0, Wr=9.0, Hr=6.5, W=20.0, B=15.0, B1=2.5,
                          C=16.0, L1=29.9, L=39.9, Gn_dia=0.8, H2=1.8,
                          M_dia=3.0, l_thread=3.0):
    """
    Создает аналитический B-Rep солид каретки MGN9H.
    Координаты:
    - Начало координат (0,0,0) привязано к подошве рельса:
      - Z = H1 = 2.0 мм - нижняя плоскость боковых крыльев каретки;
      - Z = H = 10.0 мм - верхняя монтажная плоскость каретки;
      - Высота блока = H - H1 = 8.0 мм;
    - Ось X: продольная ось движения, каретка центрирована: X в [-L/2, L/2] = [-19.95, +19.95];
      Металлический корпус L1 = 29.9 мм: X в [-L1/2, L1/2] = [-14.95, +14.95];
      Торцевые крышки: толщина по 5.0 мм на обоих концах;
    - Ось Y: поперечная ось, каретка центрирована: Y в [-W/2, W/2] = [-10.0, +10.0];
    - Внутренний паз под рельс Wr = 9.0 мм с зазором и канавками под шарики;
    - 4 резьбовых крепежных отверстия M3 глубина 3.0 мм (сетка C=16.0 мм вдоль X, B=15.0 мм вдоль Y);
    - Смазочные отверстия Gn (Ø0.8 мм) на торцах на расстоянии H2 = 1.8 мм от верха (Z = 8.2 мм).
    """
    body_h = H - H1  # 8.0 мм
    # 1. Основной габаритный блок
    body = make_box(L, W, body_h, (-L / 2.0, -W / 2.0, H1))
    
    # 2. Внутренний паз под рельс (ширина 9.4 мм, потолок на Z = Hr + 0.3 = 6.8 мм)
    slot_w = 9.4
    slot_ceil = Hr + 0.3  # 6.8 мм
    slot_h = slot_ceil - (H1 - 1.0)
    slot = make_box(L + 2.0, slot_w, slot_h, (-L / 2.0 - 1.0, -slot_w / 2.0, H1 - 1.0))
    carriage = body.cut(slot)
    
    # 3. Беговые дорожки под шарики на внутренних стенках (Z = Hr / 2.0 = 3.25 мм)
    groove_r = 1.1
    y_groove_offset = (slot_w / 2.0) - groove_r + 0.4
    z_groove = Hr / 2.0  # 3.25 мм
    
    gr_pos = Part.makeCylinder(groove_r, L + 2.0, FreeCAD.Vector(-L / 2.0 - 1.0, y_groove_offset, z_groove), FreeCAD.Vector(1, 0, 0))
    gr_neg = Part.makeCylinder(groove_r, L + 2.0, FreeCAD.Vector(-L / 2.0 - 1.0, -y_groove_offset, z_groove), FreeCAD.Vector(1, 0, 0))
    carriage = carriage.cut(gr_pos).cut(gr_neg)
    
    # 4. 4 резьбовых отверстия M3 x 3 мм на верхней плоскости (Z = H = 10.0 мм)
    # Координаты отверстий: X = +/- C/2 = +/- 8.0, Y = +/- B/2 = +/- 7.5
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            hx = sx * (C / 2.0)
            hy = sy * (B / 2.0)
            hole = make_cylinder(M_dia / 2.0, l_thread + 0.5, (hx, hy, H - l_thread), (0, 0, 1))
            carriage = carriage.cut(hole)
            
    # 5. Смазочные отверстия Gn Ø0.8 мм на обоих торцах (Z = H - H2 = 8.2 мм, Y = 0)
    z_gn = H - H2  # 8.2 мм
    gn_front = Part.makeCylinder(Gn_dia / 2.0, 5.0, FreeCAD.Vector(L / 2.0 - 4.5, 0, z_gn), FreeCAD.Vector(1, 0, 0))
    gn_back = Part.makeCylinder(Gn_dia / 2.0, 5.0, FreeCAD.Vector(-L / 2.0 - 0.5, 0, z_gn), FreeCAD.Vector(1, 0, 0))
    carriage = carriage.cut(gn_front).cut(gn_back)
    
    # 6. Четкая визуальная линия раздела между металлом (L1=29.9) и торцевыми крышками (по 5 мм)
    for seam_x in [-L1 / 2.0, L1 / 2.0]:
        seam_top = make_box(0.25, W + 2.0, 0.25, (seam_x - 0.125, -W / 2.0 - 1.0, H - 0.2))
        seam_s1 = make_box(0.25, 0.25, body_h + 1.0, (seam_x - 0.125, W / 2.0 - 0.15, H1 - 0.5))
        seam_s2 = make_box(0.25, 0.25, body_h + 1.0, (seam_x - 0.125, -W / 2.0 - 0.1, H1 - 0.5))
        carriage = carriage.cut(seam_top).cut(seam_s1).cut(seam_s2)
        
    if not carriage.isValid():
        raise ValueError("Carriage solid shape is invalid!")
        
    return carriage

create_part = create_mgn9h_carriage

def generate_mgn9h_carriage_drawing(part_name="part_mgn9h_carriage",
                                    doc_code="ВЧ.02.00.001",
                                    title_name="Каретка MGN9H",
                                    material="Сталь GCr15 / POM",
                                    scale=2.0,
                                    sheet="A3_Landscape",
                                    pdf_name=None,
                                    fcstd_name=None,
                                    png_name=None,
                                    notes=None):
    """
    Генерирует рабочий чертеж каретки MGN9H по ГОСТ (ЕСКД):
    - Формат А3, масштаб 2:1;
    - Главный вид (вид сбоку): длина L=39.9, блок L1=29.9, высота 8.0, шаг C=16.0;
    - Вид сверху (проекционная связь по X): ширина W=20.0, 4 отв. M3, B=15.0, B1=2.5, C=16.0;
    - Вид слева (вид с торца, связь по Y): профиль, паз, смазочное отв. Gn Ø0.8, H2=1.8, H-H1=8.0;
    - Аксонометрический вид (изометрия);
    - Векторный оверлей размеров и надписей по ГОСТ 2.307 с компенсацией DPI;
    - Основная надпись по ГОСТ 2.104 и техтребования по ГОСТ 2.316.
    """
    shape = create_mgn9h_carriage()
    
    doc = FreeCAD.newDocument(f"Doc_{part_name}")
    feat = doc.addObject("Part::Feature", part_name)
    feat.Shape = shape
    doc.recompute()
    
    page, template = create_drawing_page(doc, sheet, f"Page_{part_name}")
    
    # Координаты видов на листе А3 (420 x 297 мм), масштаб 2:1
    # TechDraw: начало координат снизу-слева
    x_front = 115.0
    y_front_td = 195.0
    
    x_top = 115.0   # Строгая проекционная связь по X
    y_top_td = 100.0
    
    x_left = 225.0  # Строгая проекционная связь по Y с Главным видом
    y_left_td = 195.0
    
    x_iso = 315.0
    y_iso_td = 195.0
    
    # 1. Главный вид (вид сбоку вдоль Y)
    v_front = add_part_view(doc, page, feat, "FrontView", (0.0, -1.0, 0.0), scale, x_front, y_front_td)
    
    # 2. Вид сверху (вид вдоль Z)
    v_top = add_part_view(doc, page, feat, "TopView", (0.0, 0.0, 1.0), scale, x_top, y_top_td)
    
    # 3. Вид слева (вид с торца вдоль X)
    v_left = add_part_view(doc, page, feat, "LeftView", (1.0, 0.0, 0.0), scale, x_left, y_left_td)
    
    # 4. Изометрический вид
    v_iso = add_part_view(doc, page, feat, "IsoView", (1.0, -1.2, 0.9), scale * 0.9, x_iso, y_iso_td)
    
    # 5. Основная надпись (штамп ГОСТ 2.104)
    title_fields = {
        'Номер': doc_code,
        'Название': 'Каретка шариковая',
        'Информация': 'MGN9H',
        'Масштаб': f"{int(scale)}:1" if scale >= 1 else f"1:{int(1/scale)}",
        'Лист': '1',
        'Листов': '1',
        'Материал1': 'Сталь GCr15',
        'Материал2': 'ГОСТ 801-78',
        'Материал3': 'крышки: POM',
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
            "2. Материал корпуса: сталь подшипниковая GCr15 (ШХ15) ГОСТ 801-78.",
            "3. Твердость дорожек качения: 58...62 HRC.",
            "4. Торцевые уплотнения и сепаратор: полиацеталь (POM).",
            "5. Резьба метрическая: 4 отв. М3-7H, глубина резьбы 3,0 мм.",
            "6. Смазочные отверстия Gn: Ø0,8 мм под наконечник масленки.",
            "7. Допуск параллельности базовых плоскостей: 0,005 мм."
        ]
        
    notes_svg_lines = ['<text x="230" y="160" font-family="osifont, Arial, sans-serif" font-size="3.6px" font-weight="bold" fill="#000">Технические требования:</text>']
    for idx, line in enumerate(notes):
        notes_svg_lines.append(f'<text x="230" y="{167 + idx * 5.5}" font-family="osifont, Arial, sans-serif" font-size="3.0px" fill="#000">{line}</text>')
    notes_svg = '\n'.join(notes_svg_lines)
    
    # 7. Векторный оверлей размеров (ГОСТ 2.307-2011)
    # Преобразование координат в SVG:
    # FrontView: center (x=115, y_svg = 297 - 195 = 102)
    # TopView: center (x=115, y_svg = 297 - 100 = 197)
    # LeftView: center (x=225, y_svg = 297 - 195 = 102)
    #
    # На виде FrontView (масштаб 2:1):
    # L = 39.9 -> 79.8 mm (x от 115 - 39.9 = 75.1 до 115 + 39.9 = 154.9)
    # L1 = 29.9 -> 59.8 mm (x от 115 - 29.9 = 85.1 до 115 + 29.9 = 144.9)
    # C = 16.0 -> 32.0 mm (x от 115 - 16.0 = 99.0 до 115 + 16.0 = 131.0)
    # Высота 8.0 -> 16.0 mm (y_svg от 102 - 8.0 = 94.0 до 102 + 8.0 = 110.0)
    #
    # На виде TopView (масштаб 2:1):
    # L = 39.9 -> 79.8 mm (x от 75.1 до 154.9)
    # W = 20.0 -> 40.0 mm (y_svg от 197 - 20.0 = 177.0 до 197 + 20.0 = 217.0)
    # B = 15.0 -> 30.0 mm (y_svg от 197 - 15.0 = 182.0 до 197 + 15.0 = 212.0)
    #
    # На виде LeftView (масштаб 2:1):
    # W = 20.0 -> 40.0 mm (x от 225 - 20.0 = 205.0 до 225 + 20.0 = 245.0)
    # Высота 8.0 -> 16.0 mm (y_svg от 102 - 8.0 = 94.0 до 102 + 8.0 = 110.0)
    # Gn на y_svg = 94.0 + 1.8 * 2 = 97.6, x = 225.0
    
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

<!-- ==================== ГЛАВНЫЙ ВИД (ВИД СБОКУ) ==================== -->
<text x="115" y="65" class="view-title">Главный вид</text>

<!-- Осевые линии отверстий C = 16 (x = 99 и 131) -->
<line x1="99" y1="91" x2="99" y2="105" class="center-line" />
<line x1="131" y1="91" x2="131" y2="105" class="center-line" />

<!-- 1. Размер C = 16 -->
<line x1="99" y1="94" x2="99" y2="78" class="dim-ext" />
<line x1="131" y1="94" x2="131" y2="78" class="dim-ext" />
<line x1="99" y1="80" x2="131" y2="80" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="115" y="78.5" class="dim-text">16</text>

<!-- 2. Длина блока L1 = 29.9 -->
<line x1="85.1" y1="94" x2="85.1" y2="71" class="dim-ext" />
<line x1="144.9" y1="94" x2="144.9" y2="71" class="dim-ext" />
<line x1="85.1" y1="73" x2="144.9" y2="73" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="115" y="71.5" class="dim-text">29,9</text>

<!-- 3. Полная длина L = 39.9 -->
<line x1="75.1" y1="110" x2="75.1" y2="122" class="dim-ext" />
<line x1="154.9" y1="110" x2="154.9" y2="122" class="dim-ext" />
<line x1="75.1" y1="120" x2="154.9" y2="120" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="115" y="118.5" class="dim-text">39,9</text>

<!-- 4. Высота корпуса 8 (H - H1 = 10 - 2) -->
<line x1="75.1" y1="94" x2="64" y2="94" class="dim-ext" />
<line x1="75.1" y1="110" x2="64" y2="110" class="dim-ext" />
<line x1="66" y1="94" x2="66" y2="110" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="63" y="103" transform="rotate(-90 63 103)" class="dim-text">8*</text>

<!-- ==================== ВИД СВЕРХУ ==================== -->
<text x="115" y="152" class="view-title">Вид сверху</text>

<!-- Осевые линии сетки 4 отверстий -->
<line x1="70" y1="197" x2="160" y2="197" class="center-line" />
<line x1="99" y1="172" x2="99" y2="222" class="center-line" />
<line x1="131" y1="172" x2="131" y2="222" class="center-line" />
<line x1="85" y1="182" x2="145" y2="182" class="center-line" />
<line x1="85" y1="212" x2="145" y2="212" class="center-line" />

<!-- 5. Размер B = 15 -->
<line x1="99" y1="182" x2="60" y2="182" class="dim-ext" />
<line x1="99" y1="212" x2="60" y2="212" class="dim-ext" />
<line x1="63" y1="182" x2="63" y2="212" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="60" y="198" transform="rotate(-90 60 198)" class="dim-text">15</text>

<!-- 6. Ширина W = 20 -->
<line x1="75.1" y1="177" x2="48" y2="177" class="dim-ext" />
<line x1="75.1" y1="217" x2="48" y2="217" class="dim-ext" />
<line x1="51" y1="177" x2="51" y2="217" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="48" y="198" transform="rotate(-90 48 198)" class="dim-text">20</text>

<!-- 7. Отступ B1 = 2.5 (от верхней кромки до оси отверстий по ширине Y) -->
<line x1="131" y1="177" x2="148" y2="177" class="dim-ext" />
<line x1="131" y1="182" x2="148" y2="182" class="dim-ext" />
<line x1="145" y1="171" x2="145" y2="177" class="dim-line" marker-end="url(#arrow)" />
<line x1="145" y1="188" x2="145" y2="182" class="dim-line" marker-end="url(#arrow)" />
<text x="154" y="181" class="dim-text">2,5</text>

<!-- Выноска 4 отв. M3 x 3 -->
<path d="M 131 182 L 155 165 L 185 165" class="leader" marker-start="url(#dot)" />
<text x="170" y="163" class="dim-text">4 отв. М3-7Н</text>
<text x="170" y="169" class="dim-text-sm">глубина резьбы 3,0</text>

<!-- ==================== ВИД СЛЕВА (ТОРЦЕВОЙ ВИД) ==================== -->
<text x="225" y="65" class="view-title">Вид слева</text>

<!-- Осевая линия симметрии каретки -->
<line x1="225" y1="88" x2="225" y2="114" class="center-line" />
<!-- Горизонтальная ось смазочного отверстия Gn (H2 = 1.8 -> y_svg = 97.6) -->
<line x1="215" y1="97.6" x2="235" y2="97.6" class="center-line" />

<!-- 8. Размер H2 = 1.8 -->
<line x1="245" y1="94" x2="258" y2="94" class="dim-ext" />
<line x1="225" y1="97.6" x2="258" y2="97.6" class="dim-ext" />
<line x1="255" y1="89" x2="255" y2="94" class="dim-line" marker-end="url(#arrow)" />
<line x1="255" y1="103" x2="255" y2="97.6" class="dim-line" marker-end="url(#arrow)" />
<text x="264" y="97" class="dim-text">1,8</text>

<!-- 9. Выноска смазочного отверстия Gn Ø0.8 -->
<path d="M 225 97.6 L 242 85 L 268 85" class="leader" marker-start="url(#dot)" />
<text x="255" y="83" class="dim-text">Gn Ø0,8</text>

<!-- 10. Ширина паза 9.4 под рельс Wr = 9 -->
<line x1="215.6" y1="110" x2="215.6" y2="124" class="dim-ext" />
<line x1="234.4" y1="110" x2="234.4" y2="124" class="dim-ext" />
<line x1="215.6" y1="121" x2="234.4" y2="121" class="dim-line" marker-start="url(#arrow)" marker-end="url(#arrow-rev)" />
<text x="225" y="119.5" class="dim-text">9,4</text>
<text x="225" y="126" class="dim-text-sm">(под рельс Wr=9*)</text>

<!-- ==================== ИЗОМЕТРИЯ ==================== -->
<text x="315" y="152" class="view-title">Изометрия</text>

<!-- ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ -->
{notes_svg}

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
    
    if pdf_name is None:
        pdf_name = f"{part_name}.pdf"
    if fcstd_name is None:
        fcstd_name = f"{part_name}.FCStd"
    if png_name is None:
        png_name = f"{part_name}.png"
        
    export_drawing(doc, page, pdf_name, fcstd_name, png_name)
    print(f"Drawing for {part_name} generated successfully!")

if __name__ == "__main__":
    generate_mgn9h_carriage_drawing()
