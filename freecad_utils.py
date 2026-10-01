#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
freecad_utils.py
Common utility module for FreeCAD headless automation, B-Rep solid modeling,
and GOST (ESKD) TechDraw engineering drawings.
"""

import sys
import os
import math

# Add FreeCAD paths
sys.path.append('/usr/lib/freecad/lib')
sys.path.append('/usr/share/freecad/Mod/TechDraw')

from PySide2 import QtWidgets, QtGui, QtSvg, QtCore

def init_freecad():
    """Initializes headless Qt and FreeCAD environment."""
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
    
    return FreeCAD, FreeCADGui, Part, TechDraw, TechDrawGui

FreeCAD, FreeCADGui, Part, TechDraw, TechDrawGui = init_freecad()

# ====================================================================
# B-REP SOLID MODELING PRIMITIVES & OPERATORS
# ====================================================================

def make_box(dx, dy, dz, p=(0, 0, 0)):
    return Part.makeBox(dx, dy, dz, FreeCAD.Vector(*p))

def make_cylinder(r, h, p=(0, 0, 0), d=(0, 0, 1)):
    return Part.makeCylinder(r, h, FreeCAD.Vector(*p), FreeCAD.Vector(*d))

def make_cone(r1, r2, h, p=(0, 0, 0), d=(0, 0, 1)):
    return Part.makeCone(r1, r2, h, FreeCAD.Vector(*p), FreeCAD.Vector(*d))

def make_sphere(r, p=(0, 0, 0)):
    return Part.makeSphere(r, FreeCAD.Vector(*p))

def rot_z(shape, deg, center=(0, 0, 0)):
    sh = shape.copy()
    sh.rotate(FreeCAD.Vector(*center), FreeCAD.Vector(0, 0, 1), deg)
    return sh

def rot_axis(shape, axis_pt, axis_dir, deg):
    sh = shape.copy()
    sh.rotate(FreeCAD.Vector(*axis_pt), FreeCAD.Vector(*axis_dir), deg)
    return sh

def trans(shape, dx, dy, dz):
    sh = shape.copy()
    sh.translate(FreeCAD.Vector(dx, dy, dz))
    return sh

# ====================================================================
# TECHDRAW DRAWING PAGE & EXPORT HELPERS
# ====================================================================

GOST_TEMPLATES = {
    "A1_Landscape": "/usr/share/freecad/Mod/TechDraw/Templates/RU_GOST/Leading/Landscape_A1.svg",
    "A2_Landscape": "/usr/share/freecad/Mod/TechDraw/Templates/RU_GOST/Leading/Landscape_A2.svg",
    "A3_Landscape": "/usr/share/freecad/Mod/TechDraw/Templates/RU_GOST/Leading/Landscape_A3.svg",
    "A4_Portrait": "/usr/share/freecad/Mod/TechDraw/Templates/RU_GOST/Leading/Portrait_A4.svg",
}

def create_drawing_page(doc, template_key="A3_Landscape", page_name="Page"):
    """Creates a TechDraw page with a standard GOST SVG template."""
    page = doc.addObject('TechDraw::DrawPage', page_name)
    template = doc.addObject('TechDraw::DrawSVGTemplate', page_name + '_Template')
    template.Template = GOST_TEMPLATES.get(template_key, GOST_TEMPLATES["A3_Landscape"])
    page.Template = template
    doc.recompute()
    return page, template

def add_part_view(doc, page, source_feature, name, direction, scale, x, y, iso_count=0):
    """
    Adds a DrawViewPart to the page safely:
    Adds view first (which resets coordinates), then sets true X, Y, Scale, and edge parameters.
    """
    view = doc.addObject('TechDraw::DrawViewPart', name)
    view.Source = [source_feature]
    view.Direction = direction
    page.addView(view)
    doc.recompute()
    
    view.Scale = scale
    view.X = x
    view.Y = y
    view.CoarseView = False
    view.IsoCount = iso_count
    view.SmoothVisible = False
    view.SeamVisible = False
    doc.recompute()
    return view

def fill_gost_title_block(template, fields):
    """Fills fields in standard RU_GOST template."""
    for key, val in fields.items():
        try:
            template.setEditFieldContent(key, str(val))
        except Exception:
            pass

def export_drawing(doc, page, pdf_path, fcstd_path=None, png_path=None):
    """
    Exports drawing to PDF and optionally saves the native FreeCAD project (.FCStd)
    and renders a high-res PNG preview.
    """
    doc.recompute()
    
    abs_pdf = os.path.abspath(pdf_path)
    print(f"Exporting PDF to {abs_pdf} ...")
    TechDrawGui.exportPageAsPdf(page, abs_pdf)
    if os.path.exists(abs_pdf):
        print(f"SUCCESS: PDF created ({os.path.getsize(abs_pdf)} bytes)")
    
    if fcstd_path:
        abs_fcstd = os.path.abspath(fcstd_path)
        print(f"Saving native FreeCAD project to {abs_fcstd} ...")
        doc.saveAs(abs_fcstd)
        if os.path.exists(abs_fcstd):
            print(f"SUCCESS: Project FreeCAD saved to {abs_fcstd}")
            
    if png_path:
        abs_png = os.path.abspath(png_path)
        rendered = False
        # Render crisp high-resolution preview PNG using poppler & cairo
        try:
            import ctypes
            poppler = ctypes.CDLL('libpoppler-glib.so.8')
            cairo = ctypes.CDLL('libcairo.so.2')

            poppler.poppler_document_new_from_file.restype = ctypes.c_void_p
            poppler.poppler_document_new_from_file.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p]
            poppler.poppler_document_get_page.restype = ctypes.c_void_p
            poppler.poppler_document_get_page.argtypes = [ctypes.c_void_p, ctypes.c_int]
            poppler.poppler_page_get_size.restype = None
            poppler.poppler_page_get_size.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
            poppler.poppler_page_render.restype = None
            poppler.poppler_page_render.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

            cairo.cairo_image_surface_create.restype = ctypes.c_void_p
            cairo.cairo_image_surface_create.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
            cairo.cairo_create.restype = ctypes.c_void_p
            cairo.cairo_create.argtypes = [ctypes.c_void_p]
            cairo.cairo_scale.restype = None
            cairo.cairo_scale.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double]
            cairo.cairo_set_source_rgb.restype = None
            cairo.cairo_set_source_rgb.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_double]
            cairo.cairo_paint.restype = None
            cairo.cairo_paint.argtypes = [ctypes.c_void_p]
            cairo.cairo_surface_write_to_png.restype = ctypes.c_int
            cairo.cairo_surface_write_to_png.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            cairo.cairo_destroy.restype = None
            cairo.cairo_destroy.argtypes = [ctypes.c_void_p]
            cairo.cairo_surface_destroy.restype = None
            cairo.cairo_surface_destroy.argtypes = [ctypes.c_void_p]

            file_uri = 'file://' + abs_pdf
            p_doc = poppler.poppler_document_new_from_file(file_uri.encode('utf-8'), None, None)
            if p_doc:
                p_page = poppler.poppler_document_get_page(p_doc, 0)
                w_pt, h_pt = ctypes.c_double(), ctypes.c_double()
                poppler.poppler_page_get_size(p_page, ctypes.byref(w_pt), ctypes.byref(h_pt))
                dpi = 150.0
                scale = dpi / 72.0
                w_px = int(w_pt.value * scale)
                h_px = int(h_pt.value * scale)
                surface = cairo.cairo_image_surface_create(0, w_px, h_px)
                cr = cairo.cairo_create(surface)
                cairo.cairo_set_source_rgb(cr, 1.0, 1.0, 1.0)
                cairo.cairo_paint(cr)
                cairo.cairo_scale(cr, scale, scale)
                poppler.poppler_page_render(p_page, cr)
                cairo.cairo_surface_write_to_png(surface, abs_png.encode('utf-8'))
                cairo.cairo_destroy(cr)
                cairo.cairo_surface_destroy(surface)
                rendered = os.path.exists(abs_png)
        except Exception as e:
            print(f"Poppler rendering failed: {e}")

        if not rendered:
            try:
                tmp_svg = "/tmp/temp_render.svg"
                TechDrawGui.exportPageAsSvg(page, tmp_svg)
                if os.path.exists(tmp_svg):
                    renderer = QtSvg.QSvgRenderer(tmp_svg)
                    img = QtGui.QImage(2400, 1697, QtGui.QImage.Format_ARGB32)
                    img.fill(QtCore.Qt.white)
                    p = QtGui.QPainter(img)
                    renderer.render(p)
                    p.end()
                    img.save(abs_png)
                    os.remove(tmp_svg)
            except Exception as e:
                print(f"QtSvg fallback rendering failed: {e}")

        if os.path.exists(abs_png):
            print(f"SUCCESS: Preview PNG created ({os.path.getsize(abs_png)} bytes)")

def generate_standard_part_drawing(part_name, part_shape, doc_code, title_name,
                                   material="PETG", scale=1.0, sheet="A3_Landscape",
                                   front_dir=(0, -1, 0), top_dir=(0, 0, 1),
                                   pdf_name=None, fcstd_name=None, notes=None):
    """
    Standard generator for individual part engineering drawings (GOST).
    """
    if pdf_name is None:
        pdf_name = f"{part_name}.pdf"
    if fcstd_name is None:
        fcstd_name = f"{part_name}.FCStd"
        
    doc = FreeCAD.newDocument(f"Doc_{part_name}")
    feat = doc.addObject("Part::Feature", part_name)
    feat.Shape = part_shape
    doc.recompute()
    
    page, template = create_drawing_page(doc, sheet, f"Page_{part_name}")
    
    # Sheet sizes: A3 is 420 x 297 mm
    if sheet == "A3_Landscape":
        w_sheet, h_sheet = 420.0, 297.0
        x_front, y_front = 140.0, 180.0
        x_top, y_top = 140.0, 80.0
        x_iso, y_iso = 300.0, 180.0
        notes_x, notes_y = 325.0, 80.0
    else: # A4 Portrait
        w_sheet, h_sheet = 210.0, 297.0
        x_front, y_front = 105.0, 200.0
        x_top, y_top = 105.0, 120.0
        x_iso, y_iso = 105.0, 60.0
        notes_x, notes_y = 105.0, 100.0
        
    # Front View
    add_part_view(doc, page, feat, "FrontView", front_dir, scale, x_front, y_front)
    
    # Top View (aligned on X)
    add_part_view(doc, page, feat, "TopView", top_dir, scale, x_front, y_top)
    
    # Isometric View
    add_part_view(doc, page, feat, "IsoView", (1.0, -1.2, 0.9), scale * 0.85, x_iso, y_iso)
    
    # Title Block
    title_fields = {
        'Номер': doc_code,
        'Название': title_name,
        'Масштаб': f"{int(scale)}:1" if scale >= 1 else f"1:{int(1/scale)}",
        'Лист': '1',
        'Листов': '1',
        'Материал': material,
        'Разработал': 'Демишкевич Э.Б.',
        'Проверил': 'Контролер',
        'Организация1': 'Проект VISHNI',
        'Организация2': 'VISHNI CAD'
    }
    fill_gost_title_block(template, title_fields)
    
    # Technical notes if provided
    if notes:
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
        sym_notes.X = notes_x
        sym_notes.Y = 55.0 + notes_h / 2.0 + 2.0
        doc.recompute()
        
    png_name = f"{part_name}.png"
    export_drawing(doc, page, pdf_name, fcstd_name, png_name)
    print(f"Drawing for {part_name} generated successfully!")
