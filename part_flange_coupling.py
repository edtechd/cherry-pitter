#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
part_flange_coupling.py
Поз. 18: Фланец переходный жесткий (Rigid Flange Coupling Connector ID: 6mm)
Стандартное изделие для передачи крутящего момента от вала привода к ведущему колесу мальтийского механизма.
Модернизировано под 6 мм вал мотор-редуктора JGY-370 (Строка 5 каталога AliExpress: d=6, D=22, L=16, d2=M3).
"""

import sys
import os
import math
from freecad_utils import (
    FreeCAD, Part, TechDraw, TechDrawGui,
    make_cylinder, make_box,
    create_drawing_page, add_part_view,
    fill_gost_title_block, export_drawing
)

def create_flange_coupling():
    """
    Constructs the 6mm Rigid Flange Coupling connector at local origin (0,0,0).
    - Base flange: Ø22.0 mm, thickness 2.0 mm (Z in [0, 2.0])
    - Cylindrical hub: Ø10.0 mm, height 10.0 mm (Z in [2.0, 12.0], total height 12.0 mm)
    - Central bore: Ø6.0 mm through (Z in [-1.0, 14.0])
    - 4 mounting holes: Ø3.2 mm on PCD Ø16.0 mm for M3 screws
    - 2 set screw holes: M3 radial threaded holes at 90 deg on the hub (at Z = 7.0 mm)
    """
    # 1. Base flange (Ø22 mm, thickness 2 mm)
    flange = make_cylinder(11.0, 2.0, (0, 0, 0))
    
    # 2. Cylindrical hub (Ø10 mm, height 10 mm)
    hub = make_cylinder(5.0, 10.0, (0, 0, 2.0))
    coupling = flange.fuse(hub)
    
    # 3. Central shaft bore (Ø6 mm through)
    bore = make_cylinder(3.0, 15.0, (0, 0, -1.0))
    coupling = coupling.cut(bore)
    
    # 4. 4 Flange mounting holes (Ø3.2 mm on PCD 16 mm, R = 8.0 mm)
    for ang in [0, 90, 180, 270]:
        rad = math.radians(ang)
        hole = make_cylinder(1.6, 5.0, (8.0 * math.cos(rad), 8.0 * math.sin(rad), -1.0))
        coupling = coupling.cut(hole)
        
    # 5. 2 M3 radial set screw holes on the hub (at Z = 7.0 mm, 90 deg apart)
    for ang in [45, 135]:
        rad = math.radians(ang)
        set_screw = Part.makeCylinder(1.5, 8.0, FreeCAD.Vector(0, 0, 7.0), FreeCAD.Vector(math.cos(rad), math.sin(rad), 0))
        coupling = coupling.cut(set_screw)
        
    if not coupling.isValid():
        print("WARNING: Flange coupling shape is topologically invalid!")
        
    return coupling

create_part = create_flange_coupling

def generate_flange_coupling_drawing(part_name="part_flange_coupling",
                                     doc_code="ВЧ.00.00.011",
                                     title_name="Фланец переходный ф6",
                                     material="Сталь 45 оцинк.",
                                     scale=2.0,
                                     sheet="A3_Landscape",
                                     notes=None):
    """
    Генерирует рабочий чертеж фланцевого коннектора по ГОСТ (ЕСКД):
    - Вид сверху с секущей плоскостью А-А;
    - Вертикальный разрез А-А вместо вида спереди;
    - Аксонометрический вид (изометрия);
    - Нанесение основных размеров и выносок (ГОСТ 2.307);
    - Штамп по ГОСТ 2.104 и технические требования по ГОСТ 2.316.
    """
    shape = create_flange_coupling()
    
    doc = FreeCAD.newDocument(f"Doc_{part_name}")
    feat = doc.addObject("Part::Feature", part_name)
    feat.Shape = shape
    doc.recompute()
    
    page, template = create_drawing_page(doc, sheet, f"Page_{part_name}")
    
    # Координаты для формата А3 (масштаб 2:1)
    x_c = 135.0
    y_top_td = 200.0   # SVG y = 97.0
    y_sec_td = 90.0    # SVG y = 207.0
    
    # 1. Вид сверху (Top View с секущей линией А-А)
    v_top = add_part_view(doc, page, feat, "TopView", (0, 0, 1), scale, x_c, y_top_td)
    
    # 2. Вертикальный диаметральный разрез А-А
    sec = doc.addObject("TechDraw::DrawViewSection", "SectionView")
    sec.BaseView = v_top
    sec.ScaleType = "Custom"
    sec.Scale = scale
    sec.SectionNormal = FreeCAD.Vector(0.0, -1.0, 0.0)
    sec.SectionOrigin = FreeCAD.Vector(0.0, 0.0, 1.0)
    sec.SectionDirection = "Down"
    sec.SectionSymbol = "A"
    page.addView(sec)
    doc.recompute()
    
    sec.Direction = FreeCAD.Vector(0.0, -1.0, 0.0)
    sec.XDirection = FreeCAD.Vector(1.0, 0.0, 0.0)
    sec.Rotation = 0.0
    sec.X = x_c
    sec.Y = y_sec_td
    sec.IsoCount = 0
    sec.ViewObject.HatchColor = (0.0, 0.0, 0.0, 1.0)
    doc.recompute()
    
    # 3. Аксонометрический вид (Iso View)
    add_part_view(doc, page, feat, "IsoView", (1.0, -1.2, 0.9), 2.0, 315.0, 200.0)
    
    # 4. Основная надпись (штамп ГОСТ 2.104)
    title_fields = {
        'Номер': doc_code,
        'Название': title_name,
        'Масштаб': f"{int(scale)}:1" if scale >= 1 else f"1:{int(1/scale)}",
        'Лист': '1',
        'Листов': '1',
        'Материал1': 'Сталь 45',
        'Материал2': 'оцинк.',
        'Материал3': '',
        'Организация1': 'Проект VISHNI',
        'Организация2': '',
        'Разработал': 'Инженер',
        'Проверил': 'Контролер'
    }
    fill_gost_title_block(template, title_fields)
    doc.recompute()
    
    # 5. Технические требования (ГОСТ 2.316)
    notes_svg = ""
    if notes:
        notes_lines = ['<text x="230" y="145" font-family="osifont, Arial, sans-serif" font-size="3.6px" font-weight="bold" fill="#000">Технические требования:</text>']
        for idx, line in enumerate(notes):
            notes_lines.append(f'<text x="230" y="{152 + idx * 5.8}" font-family="osifont, Arial, sans-serif" font-size="3.2px" fill="#000">{line}</text>')
        notes_svg = '\n'.join(notes_lines)
        
    # 6. Векторный оверлей размеров и надписей (ГОСТ 2.307)
    # Масштаб 2:1 -> 1 мм модели = 2 мм на чертеже
    def h_dim(x1, x2, y, text, is_dia=False, tol=''):
        prefix = 'Ø' if is_dia else ''
        t_str = f'{prefix}{text}{tol}'
        p1 = f'{x1},{y} {x1+3.5},{y-0.7} {x1+3.5},{y+0.7}'
        p2 = f'{x2},{y} {x2-3.5},{y-0.7} {x2-3.5},{y+0.7}'
        w_box = max(len(t_str) * 2.4, 8.0)
        xm = (x1 + x2) / 2.0
        return f'''<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" class="dim-line" />
<polygon points="{p1}" fill="#000" />
<polygon points="{p2}" fill="#000" />
<rect x="{xm - w_box/2.0}" y="{y - 2.5}" width="{w_box}" height="4.5" fill="white" stroke="none" />
<text x="{xm}" y="{y - 0.8}" class="dim-text">{t_str}</text>'''

    def v_dim(y1, y2, x, text, text_side='left'):
        p1 = f'{x},{y1} {x-0.7},{y1+3.5} {x+0.7},{y1+3.5}'
        p2 = f'{x},{y2} {x-0.7},{y2-3.5} {x+0.7},{y2-3.5}'
        ym = (y1 + y2) / 2.0
        xt = x - 2.5 if text_side == 'left' else x + 2.5
        return f'''<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" class="dim-line" />
<polygon points="{p1}" fill="#000" />
<polygon points="{p2}" fill="#000" />
<text x="{xt}" y="{ym}" transform="rotate(-90 {xt} {ym})" class="dim-text">{text}</text>'''

    d_hub = h_dim(125, 145, 174, '10', is_dia=True)
    d_bore = h_dim(129, 141, 184, '6H8', is_dia=True)
    d_flange = h_dim(113, 157, 230, '22', is_dia=True)
    d_h_tot = v_dim(195, 219, 102, '12', 'left')
    d_h_hub = v_dim(195, 215, 173, '10', 'right')

    svg_dim = f'''<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">
<style>
  .dim-line {{ stroke: #000; stroke-width: 0.35; fill: none; }}
  .dim-ext {{ stroke: #000; stroke-width: 0.25; fill: none; }}
  .center-line {{ stroke: #000; stroke-width: 0.25; stroke-dasharray: 6,1.5,1.5,1.5; fill: none; }}
  .dim-text {{ font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: middle; }}
  .dim-text-left {{ font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: start; }}
  .dim-text-right {{ font-family: osifont, Arial, sans-serif; font-size: 3.5px; fill: #000; text-anchor: end; }}
  .view-title {{ font-family: osifont, Arial, sans-serif; font-size: 5.0px; fill: #000; text-anchor: middle; font-weight: bold; }}
  .leader {{ stroke: #000; stroke-width: 0.35; fill: none; }}
</style>

<!-- ==================== РАЗРЕЗ А-А ==================== -->
<text x="135" y="164" class="view-title">А-А</text>

<!-- Осевые линии разреза -->
<line x1="135" y1="168" x2="135" y2="234" class="center-line" />
<line x1="119" y1="211" x2="119" y2="223" class="center-line" />
<line x1="151" y1="211" x2="151" y2="223" class="center-line" />

<!-- 1. Ø10 (ступица) -->
<line x1="125" y1="195" x2="125" y2="171" class="dim-ext" />
<line x1="145" y1="195" x2="145" y2="171" class="dim-ext" />
{d_hub}

<!-- 2. Ø6H8 (отверстие) -->
<line x1="129" y1="195" x2="129" y2="181" class="dim-ext" />
<line x1="141" y1="195" x2="141" y2="181" class="dim-ext" />
{d_bore}

<!-- 3. Ø22 (фланец) -->
<line x1="113" y1="219" x2="113" y2="234" class="dim-ext" />
<line x1="157" y1="219" x2="157" y2="234" class="dim-ext" />
{d_flange}

<!-- 4. Высота общая 12 (слева) -->
<line x1="125" y1="195" x2="99" y2="195" class="dim-ext" />
<line x1="113" y1="219" x2="99" y2="219" class="dim-ext" />
{d_h_tot}

<!-- 5. Высота ступицы 10 (справа дальше) -->
<line x1="145" y1="195" x2="176" y2="195" class="dim-ext" />
<line x1="145" y1="215" x2="176" y2="215" class="dim-ext" />
{d_h_hub}

<!-- 6. Толщина фланца 2 (справа ближе к фланцу) -->
<line x1="157" y1="215" x2="166" y2="215" class="dim-ext" />
<line x1="157" y1="219" x2="166" y2="219" class="dim-ext" />
<line x1="163" y1="210" x2="163" y2="215" class="dim-line" />
<polygon points="163,215 162.3,211.5 163.7,211.5" fill="#000" />
<line x1="163" y1="224" x2="163" y2="219" class="dim-line" />
<polygon points="163,219 162.3,222.5 163.7,222.5" fill="#000" />
<line x1="163" y1="215" x2="163" y2="219" class="dim-line" />
<line x1="163" y1="217" x2="171" y2="217" class="dim-line" />
<text x="172" y="218.5" class="dim-text-left">2</text>

<!-- ==================== ВИД СВЕРХУ ==================== -->
<line x1="135" y1="60" x2="135" y2="134" class="center-line" />
<line x1="98" y1="97" x2="172" y2="97" class="center-line" />
<circle cx="135" cy="97" r="16" class="center-line" />

<line x1="119" y1="93" x2="119" y2="101" class="center-line" />
<line x1="151" y1="93" x2="151" y2="101" class="center-line" />
<line x1="131" y1="81" x2="139" y2="81" class="center-line" />
<line x1="131" y1="113" x2="139" y2="113" class="center-line" />

<!-- Выноска отверстий фланца -->
<circle cx="132.8" cy="78.8" r="0.8" fill="#000" />
<path d="M 132.8 78.8 L 105 55 L 45 55" class="leader" />
<text x="75" y="53" class="dim-text">4 отв. Ø3,2</text>
<text x="75" y="59" class="dim-text" font-size="2.8px">на Ø16* (под винты М3)</text>

<!-- Выноска отверстий ступицы -->
<circle cx="142.1" cy="89.9" r="0.8" fill="#000" />
<path d="M 142.1 89.9 L 165 72 L 235 72" class="leader" />
<text x="200" y="70" class="dim-text">2 отв. М3 (установочные)</text>
<text x="200" y="76" class="dim-text" font-size="2.8px">угол между осями 90°</text>

<!-- ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ -->
{notes_svg}

</svg>'''

    sym_dim = doc.addObject('TechDraw::DrawViewSymbol', 'OverlayDimensions')
    sym_dim.Symbol = svg_dim
    page.addView(sym_dim)
    doc.recompute()
    
    sym_dim.Scale = 420.0 / (1488.0 * 25.4 / 96.0)
    sym_dim.X = 210.0
    sym_dim.Y = 148.5
    doc.recompute()
    
    pdf_name = f"{part_name}.pdf"
    fcstd_name = f"{part_name}.FCStd"
    png_name = f"{part_name}.png"
    export_drawing(doc, page, pdf_name, fcstd_name, png_name)
    print(f"Drawing for {part_name} generated successfully!")

if __name__ == "__main__":
    notes = [
        "1. * Размеры для справок.",
        "2. Материал: Сталь 45 ГОСТ 1050-88.",
        "3. Покрытие: Ц9.хр ГОСТ 9.301-86.",
        "4. Резьба метрическая: М3-7H ГОСТ 24705-2004.",
        "5. Неуказанные предельные отклонения: ±IT14/2.",
        "6. Острые кромки притупить R 0.3."
    ]
    generate_flange_coupling_drawing(notes=notes)
