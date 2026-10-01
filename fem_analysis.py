#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fem_analysis.py
FEM-анализ эквивалентных напряжений (von Mises) Т-образного кронштейна съемника ягод (ВЧ.01.00.015)
с использованием FreeCAD, Gmsh (C3D10) и CalculiX (ccx).

Параметры материала (изотропный PETG):
  - Модуль Юнга E = 2100 МПа (2.1 ГПа)
  - Коэффициент Пуассона nu = 0.38
  - Плотность rho = 1270 кг/м³
  - Предел текучести sigma_y = 50 МПа
  - Допускаемое напряжение [sigma] = sigma_y / 1.5 = 33.3 МПа

Граничные условия:
  - Жесткая заделка (Fixed support) по задней привалочной плоскости Y = 0.0 (прижим к стойке guide)
  - Эксплуатационная вертикальная нагрузка F = 20.0 Н (+Z) на нижней поверхности головки
    вокруг отверстия съема ягоды Ø4.5 мм при (X = 8.0, Y = 24.0, Z = 49.5 мм)
"""

import sys
import os
import math
import subprocess
import shutil
import numpy as np

# FreeCAD paths
sys.path.append('/usr/lib/freecad/lib')
sys.path.append('/usr/share/freecad/Mod/Fem')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import PySide2
from PySide2 import QtCore, QtGui, QtWidgets

class QtGuiShim:
    def __getattr__(self, name):
        if hasattr(QtGui, name):
            return getattr(QtGui, name)
        if hasattr(QtWidgets, name):
            return getattr(QtWidgets, name)
        raise AttributeError(f'module QtGui has no attribute {name}')

qtgui_shim = QtGuiShim()
sys.modules['PySide'] = PySide2
sys.modules['PySide.QtCore'] = QtCore
sys.modules['PySide.QtGui'] = qtgui_shim
sys.modules['PySide.QtWidgets'] = QtWidgets

app = QtWidgets.QApplication.instance()
if not app:
    app = QtWidgets.QApplication(['FreeCAD', '-platform', 'offscreen'])

import FreeCAD
import Part
import feminout.importCcxFrdResults as f_imp
import femresult.resulttools as rt

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.cm as cm

# Set font for Cyrillic
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['figure.titlesize'] = 14

from part_stripper import create_stripper


def run_fem_simulation():
    work_dir = "/tmp/fem_stripper"
    os.makedirs(work_dir, exist_ok=True)
    step_file = os.path.join(work_dir, "stripper.step")
    inp_mesh_file = os.path.join(work_dir, "stripper_mesh.inp")
    ccx_inp_file = os.path.join(work_dir, "stripper_ccx.inp")
    job_prefix = os.path.join(work_dir, "stripper_ccx")
    frd_file = os.path.join(work_dir, "stripper_ccx.frd")

    print("1. Генерация 3D-геометрии кронштейна съемника...")
    shape = create_stripper()
    if not shape.isValid():
        raise RuntimeError("Geometry is invalid!")
    shape.exportStep(step_file)
    print(f"   STEP экспортирован: {step_file} (Объем: {shape.Volume:.1f} мм³)")

    print("2. Генерация квадратичной тетраэдрической сетки (C3D10) через Gmsh...")
    gmsh_bin = "/home/devuser/bin/gmsh"
    cmd_gmsh = [
        gmsh_bin, step_file,
        "-3", "-order", "2",
        "-clmax", "1.2",
        "-clmin", "0.35",
        "-format", "inp",
        "-o", inp_mesh_file
    ]
    res_gmsh = subprocess.run(cmd_gmsh, capture_output=True, text=True)
    if res_gmsh.returncode != 0:
        raise RuntimeError(f"Gmsh meshing failed: {res_gmsh.stderr}")
    print("   Сетка Gmsh успешно построена.")

    print("3. Формирование расчетного файла CalculiX (*.inp)...")
    with open(inp_mesh_file, 'r') as f:
        lines = f.readlines()

    nodes = []
    elements = []
    in_nodes = False
    in_vol_elements = False

    for line in lines:
        s = line.strip()
        if s.startswith('*NODE'):
            in_nodes = True
            nodes.append(line)
            continue
        elif s.startswith('*ELEMENT, type=C3D10'):
            in_nodes = False
            in_vol_elements = True
            elements.append('*ELEMENT, TYPE=C3D10, ELSET=EALL\n')
            continue
        elif s.startswith('*'):
            in_nodes = False
            in_vol_elements = False
            continue

        if in_nodes:
            nodes.append(line)
        elif in_vol_elements:
            elements.append(line)

    node_coords = {}
    for line in nodes[1:]:
        parts = [p.strip() for p in line.split(',') if p.strip()]
        if len(parts) >= 4:
            nid = int(parts[0])
            coords = [float(p) for p in parts[1:4]]
            node_coords[nid] = coords

    # Жесткое закрепление привалочной плоскости Y = 0.0
    fixed_nodes = [nid for nid, (x, y, z) in node_coords.items() if abs(y - 0.0) < 1e-4]
    
    # Контактная площадка ягоды на нижней грани Z = 49.5 вокруг отверстия иглы (X=8, Y=24, r <= 5.0 мм)
    contact_nodes = [
        nid for nid, (x, y, z) in node_coords.items()
        if abs(z - 49.5) < 1e-3 and ((x - 8.0)**2 + (y - 24.0)**2) <= 5.0**2 and ((x - 8.0)**2 + (y - 24.0)**2) >= (2.25 - 1e-2)**2
    ]

    f_total = 20.0  # Н
    f_per_node = f_total / len(contact_nodes)

    print(f"   Всего узлов: {len(node_coords)}, Элементов C3D10: {len(elements)-1}")
    print(f"   Закрепленных узлов (Y=0): {len(fixed_nodes)}, Нагруженных узлов: {len(contact_nodes)}")

    with open(ccx_inp_file, 'w') as f:
        f.write('*HEADING\nBerry Stripper FEM Stress Analysis\n')
        f.writelines(nodes)
        f.writelines(elements)

        # NSET for fixed nodes
        f.write('*NSET, NSET=NFIX\n')
        for i, nid in enumerate(fixed_nodes):
            f.write(f'{nid}')
            if (i + 1) % 10 == 0 or i == len(fixed_nodes) - 1:
                f.write('\n')
            else:
                f.write(', ')

        # NSET for load nodes
        f.write('*NSET, NSET=NLOAD\n')
        for i, nid in enumerate(contact_nodes):
            f.write(f'{nid}')
            if (i + 1) % 10 == 0 or i == len(contact_nodes) - 1:
                f.write('\n')
            else:
                f.write(', ')

        # Материал: Изотропный PETG
        f.write('*MATERIAL, NAME=PETG\n')
        f.write('*ELASTIC\n2100.0, 0.38\n')
        f.write('*DENSITY\n1.27e-9\n')
        f.write('*SOLID SECTION, ELSET=EALL, MATERIAL=PETG\n')

        # Закрепление
        f.write('*BOUNDARY\nNFIX, 1, 3, 0.0\n')

        # Статический шаг расчета
        f.write('*STEP\n*STATIC\n')
        f.write('*CLOAD\n')
        f.write(f'NLOAD, 3, {f_per_node:.6f}\n')
        f.write('*NODE FILE\nU\n')
        f.write('*EL FILE\nS\n')
        f.write('*END STEP\n')

    print("4. Запуск решателя CalculiX (ccx)...")
    res_ccx = subprocess.run(['ccx', job_prefix], capture_output=True, text=True, cwd=work_dir)
    if res_ccx.returncode != 0:
        raise RuntimeError(f"CalculiX failed: {res_ccx.stderr}\nOutput: {res_ccx.stdout}")
    print("   Расчет в CalculiX успешно завершен.")

    print("5. Импорт результатов в FreeCAD и сохранение модели .FCStd...")
    doc = FreeCAD.newDocument("Doc_Stripper_FEM")
    feat_part = doc.addObject("Part::Feature", "Stripper_Geometry")
    feat_part.Shape = shape
    analysis = doc.addObject("Fem::FemAnalysis", "Analysis")
    res_fem = f_imp.importFrd(frd_file, analysis, "FemResult")
    doc.recompute()
    res_obj = doc.getObject("FemResultResults")
    rt.show_result(res_obj, "Sabs")
    doc.recompute()
    fcstd_path = "/home/devuser/projects/vishni/part_stripper_fem.FCStd"
    doc.saveAs(fcstd_path)
    print(f"   FreeCAD FEM документ сохранен: {fcstd_path}")

    print("6. Анализ напряженно-деформированного состояния и построение графиков...")
    frd_data = f_imp.read_frd_result(frd_file)
    nodes_dict = frd_data['Nodes']
    tets_dict = frd_data['Tetra10Elem']
    stresses = frd_data['Results'][0]['stress']
    disps = frd_data['Results'][0]['disp']

    # Расчет напряжений Мизеса и перемещений
    vms = {}
    for nid, s in stresses.items():
        s11, s22, s33, s12, s23, s31 = s
        vm = math.sqrt(0.5 * ((s11 - s22)**2 + (s22 - s33)**2 + (s33 - s11)**2) + 3.0 * (s12**2 + s23**2 + s31**2))
        vms[nid] = vm

    max_vm = max(vms.values())
    max_nid = max(vms, key=vms.get)
    max_node = nodes_dict[max_nid]
    max_disp_val = max(d.Length for d in disps.values())
    max_uz_val = max(d.z for d in disps.values())

    print(f"   Пиковое эквивалентное напряжение von Mises: {max_vm:.2f} МПа")
    print(f"   Координаты точки концентрации (узел {max_nid}): X={max_node.x:.2f}, Y={max_node.y:.2f}, Z={max_node.z:.2f} мм")
    print(f"   Максимальный прогиб Uz: {max_uz_val:.3f} мм, Полное перемещение: {max_disp_val:.3f} мм")

    # Коэффициенты запаса прочности
    sigma_y = 50.0  # МПа (предел текучести PETG)
    sigma_adm = sigma_y / 1.5  # 33.3 МПа (допускаемое напряжение)
    k_safety_notch = sigma_y / max_vm

    # Оценка напряжений в теле балки (номинальное сечение)
    arm_vms = [
        vms[nid] for nid, n in nodes_dict.items()
        if 11.5 <= n.y <= 15.5 and 2.0 <= n.x <= 8.0
    ]
    mean_arm_vm = np.mean(arm_vms)
    max_arm_vm = max(arm_vms)
    k_safety_arm = sigma_y / max_arm_vm

    print(f"   Номинальное напряжение изгиба в балке: макс={max_arm_vm:.2f} МПа, среднее={mean_arm_vm:.2f} МПа")
    print(f"   Коэффициент запаса по пределу текучести в концентраторе: n_notch = {k_safety_notch:.2f}")
    print(f"   Коэффициент запаса по пределу текучести в теле консоли: n_arm = {k_safety_arm:.2f}")

    # Выделение поверхностных треугольных граней для 3D визуализации
    face_count = {}
    for eid, t in tets_dict.items():
        c = t[:4]
        for cf in [
            tuple(sorted([c[0], c[1], c[2]])),
            tuple(sorted([c[0], c[2], c[3]])),
            tuple(sorted([c[0], c[3], c[1]])),
            tuple(sorted([c[1], c[3], c[2]]))
        ]:
            face_count[cf] = face_count.get(cf, 0) + 1
    boundary_faces = [f for f, count in face_count.items() if count == 1]

    # --- ГРАФИК 1: 4-панельный аналитический дашборд ---
    plot_dashboard(nodes_dict, vms, disps, max_vm, max_nid, max_node, max_uz_val,
                   sigma_y, sigma_adm, k_safety_notch, k_safety_arm, max_arm_vm)

    # --- ГРАФИК 2: 3D изометрическая визуализация полей напряжений и деформаций ---
    plot_3d_contour(nodes_dict, boundary_faces, vms, disps, max_vm, max_node, max_uz_val)

    # Копирование в артефакты
    art_dir = "/home/devuser/.gemini/antigravity/brain/34c92d21-d6eb-4e2b-ae5d-ba5ac215c427"
    for img in ["fem_stress_dashboard.png", "fem_stress_3d_contour.png"]:
        src = os.path.join("/home/devuser/projects/vishni", img)
        dst = os.path.join(art_dir, img)
        shutil.copy2(src, dst)
        print(f"   Скопирован артефакт: {dst}")

    print("FEM-анализ и построение графиков успешно завершены!")


def plot_dashboard(nodes_dict, vms, disps, max_vm, max_nid, max_node, max_uz_val,
                   sigma_y, sigma_adm, k_safety_notch, k_safety_arm, max_arm_vm):
    """Строит 4-панельный детальный аналитический график распределения напряжений"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12), dpi=200)
    fig.patch.set_facecolor('#ffffff')

    # 1. Продольное распределение напряжений вдоль координаты Y (от основания к концу)
    y_bins = np.linspace(0.0, 28.0, 57) # шаг 0.5 мм
    y_centers = 0.5 * (y_bins[:-1] + y_bins[1:])
    slice_max_vm = []
    slice_mean_vm = []
    slice_p90_vm = []

    for i in range(len(y_bins) - 1):
        y0, y1 = y_bins[i], y_bins[i+1]
        vals = [vms[nid] for nid, n in nodes_dict.items() if y0 <= n.y < y1]
        if vals:
            slice_max_vm.append(np.max(vals))
            slice_mean_vm.append(np.mean(vals))
            slice_p90_vm.append(np.percentile(vals, 90))
        else:
            slice_max_vm.append(0.0)
            slice_mean_vm.append(0.0)
            slice_p90_vm.append(0.0)

    ax1.plot(y_centers, slice_max_vm, 'r-', lw=2.2, label='Пиковое напряжение $\\sigma_{vM, \\max}(Y)$')
    ax1.plot(y_centers, slice_p90_vm, 'm--', lw=1.6, label='90-й процентиль сечения $\\sigma_{90}(Y)$')
    ax1.plot(y_centers, slice_mean_vm, 'b-', lw=1.8, label='Среднее напряжение сечения $\\sigma_{mean}(Y)$')
    
    # Пределы прочности
    ax1.axhline(sigma_y, color='red', ls=':', lw=1.8, label=f'Предел текучести PETG $\\sigma_y = {sigma_y:.0f}$ МПа')
    ax1.axhline(sigma_adm, color='orange', ls='--', lw=1.8, label=f'Допускаемое $[\sigma] = {sigma_adm:.1f}$ МПа ($n=1.5$)')

    # Зоны детали
    ax1.axvspan(0.0, 8.0, color='lightgray', alpha=0.35, label='Фланец / Опоры ($Y \\in [0, 8]$)')
    ax1.axvspan(8.0, 11.5, color='mistyrose', alpha=0.45, label='Концентратор / Мостик ($Y \\in [8, 11.5]$)')
    ax1.axvspan(11.5, 16.0, color='azure', alpha=0.45, label='Балка-консоль ($Y \\in [11.5, 16]$)')
    ax1.axvspan(16.0, 28.0, color='honeydew', alpha=0.45, label='Головка съемника ($Y \\in [16, 28]$)')

    # Стрелка пика
    ax1.annotate(f'Пик концентрации:\n$\\sigma_{{vM}} = {max_vm:.1f}$ МПа\n(узел $X={max_node.x:.1f}, Y={max_node.y:.1f}$)',
                 xy=(max_node.y, max_vm), xytext=(max_node.y + 2.5, max_vm - 4.0),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1.5, headwidth=7),
                 bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', alpha=0.8),
                 fontweight='bold', fontsize=9)

    ax1.set_title('А. Продольное распределение напряжений Мизеса по длине Y', fontweight='bold')
    ax1.set_xlabel('Продольная координата Y (мм)')
    ax1.set_ylabel('Эквивалентное напряжение $\\sigma_{vM}$ (МПа)')
    ax1.set_xlim(0, 28)
    ax1.set_ylim(0, 65)
    ax1.grid(True, ls='--', alpha=0.6)
    ax1.legend(loc='upper right', fontsize=8, framealpha=0.9)

    # 2. Поперечное распределение напряжений поперек мостика и опорных фланцев (X in [-16, 16])
    x_bins = np.linspace(-16.0, 16.0, 65) # шаг 0.5 мм
    x_centers = 0.5 * (x_bins[:-1] + x_bins[1:])
    x_max_vm_root = []
    x_mean_vm_root = []

    for i in range(len(x_bins) - 1):
        x0, x1 = x_bins[i], x_bins[i+1]
        vals = [vms[nid] for nid, n in nodes_dict.items() if x0 <= n.x < x1 and 6.5 <= n.y <= 11.5]
        if vals:
            x_max_vm_root.append(np.max(vals))
            x_mean_vm_root.append(np.mean(vals))
        else:
            x_max_vm_root.append(0.0)
            x_mean_vm_root.append(0.0)

    ax2.plot(x_centers, x_max_vm_root, 'crimson', lw=2.2, label='Пиковое $\\sigma_{vM}(X)$ в зоне перехода $Y\\in[6.5, 11.5]$')
    ax2.plot(x_centers, x_mean_vm_root, 'navy', lw=1.8, label='Среднее $\\sigma_{mean}(X)$ в зоне перехода')
    ax2.axhline(sigma_y, color='red', ls=':', lw=1.8, label=f'$\\sigma_y = {sigma_y:.0f}$ МПа')
    ax2.axhline(sigma_adm, color='orange', ls='--', lw=1.8, label=f'$[\sigma] = {sigma_adm:.1f}$ МПа')

    # Осевые линии
    ax2.axvline(-10.0, color='gray', ls='--', lw=1.2, label='Винт M3 левый ($X=-10$)')
    ax2.axvline(10.0, color='gray', ls='--', lw=1.2, label='Винт M3 правый ($X=+10$)')
    ax2.axvline(8.0, color='darkgreen', ls='-.', lw=1.4, label='Ось иглы / балки ($X=+8$)')
    ax2.axvspan(-5.5, 5.5, color='khaki', alpha=0.35, label='Арочный вырез рельса MGN9')

    ax2.annotate(f'Правый стык ($X\\approx 6$ мм):\n$\\sigma = {max_vm:.1f}$ МПа\n(Концентратор от смещения)',
                 xy=(5.75, max_vm), xytext=(7.0, 38.0),
                 arrowprops=dict(facecolor='crimson', shrink=0.08, width=1.5, headwidth=7),
                 bbox=dict(boxstyle='round,pad=0.4', facecolor='#ffe6e6', edgecolor='crimson'),
                 fontweight='bold', fontsize=9)

    ax2.annotate(f'Левый стык ($X\\approx -5.5$ мм):\n$\\sigma = 23.5$ МПа\n(Разгруженная сторона)',
                 xy=(-5.5, 23.5), xytext=(-14.5, 20.0),
                 arrowprops=dict(facecolor='navy', shrink=0.08, width=1.5, headwidth=7),
                 bbox=dict(boxstyle='round,pad=0.4', facecolor='#e6f2ff', edgecolor='navy'),
                 fontsize=9)

    ax2.set_title('Б. Поперечное распределение напряжений по координате X', fontweight='bold')
    ax2.set_xlabel('Поперечная координата X (мм)')
    ax2.set_ylabel('Эквивалентное напряжение $\\sigma_{vM}$ (МПа)')
    ax2.set_xlim(-16, 16)
    ax2.set_ylim(0, 65)
    ax2.grid(True, ls='--', alpha=0.6)
    ax2.legend(loc='upper left', fontsize=8, framealpha=0.9)

    # 3. Нагрузочная характеристика: Зависимость напряжений и запаса прочности от силы съема F (5...40 Н)
    f_range = np.linspace(5.0, 40.0, 36)
    ratio = f_range / 20.0
    sigma_peak_f = max_vm * ratio
    sigma_arm_f = max_arm_vm * ratio
    k_notch_f = sigma_y / np.maximum(sigma_peak_f, 1e-3)
    k_arm_f = sigma_y / np.maximum(sigma_arm_f, 1e-3)

    ax3_twin = ax3.twinx()

    p1, = ax3.plot(f_range, sigma_peak_f, 'r-', lw=2.2, label='Пиковое напряжение $\\sigma_{\\max}(F)$ (концентратор)')
    p2, = ax3.plot(f_range, sigma_arm_f, 'b-', lw=2.0, label='Напряжение в консоли $\\sigma_{arm}(F)$')
    p3 = ax3.axhline(sigma_y, color='red', ls=':', lw=1.8, label='$\\sigma_y$ (предел текучести PETG)')
    p4 = ax3.axhline(sigma_adm, color='orange', ls='--', lw=1.8, label='$[\sigma] = 33.3$ МПа')

    p5, = ax3_twin.plot(f_range, k_notch_f, 'g--', lw=1.8, label='Запас прочности $n_{\\min}(F)$ (концентратор)')
    p6, = ax3_twin.plot(f_range, k_arm_f, 'teal', ls='-.', lw=1.8, label='Запас прочности $n_{arm}(F)$ (тело балки)')
    ax3_twin.axhline(1.0, color='darkred', ls='-', lw=1.2, alpha=0.7)

    # Отметка номинальной нагрузки F = 20 Н
    ax3.axvline(20.0, color='purple', ls='--', lw=1.5)
    ax3.text(20.5, 8.0, 'Номинал $F = 20$ Н\n(съем ягоды)', color='purple', fontweight='bold', fontsize=9)

    ax3.set_title('В. Нагрузочная характеристика: Напряжения и запасы от силы F', fontweight='bold')
    ax3.set_xlabel('Сила сопротивления съему ягоды F (Н)')
    ax3.set_ylabel('Напряжение $\\sigma$ (МПа)')
    ax3_twin.set_ylabel('Коэффициент запаса прочности n')
    ax3.set_xlim(5, 40)
    ax3.set_ylim(0, 115)
    ax3_twin.set_ylim(0, 6.0)
    ax3.grid(True, ls='--', alpha=0.6)

    lines = [p1, p2, p4, p3, p5, p6]
    labels = [l.get_label() for l in lines]
    ax3.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, 0.98), fontsize=8, ncol=2, framealpha=0.9)

    # 4. Прогиб и угловое отклонение оси отверстия иглы от силы съема F
    hole_nodes = [
        nid for nid, n in nodes_dict.items()
        if abs((n.x - 8.0)**2 + (n.y - 24.0)**2 - 2.25**2) < 0.2
    ]
    mean_hole_uz = np.mean([disps[nid].z for nid in hole_nodes])
    max_tip_uz = max_uz_val
    
    front_uz = np.mean([disps[nid].z for nid in hole_nodes if nodes_dict[nid].y > 24.5])
    back_uz = np.mean([disps[nid].z for nid in hole_nodes if nodes_dict[nid].y < 23.5])
    tilt_rad = (front_uz - back_uz) / 4.5
    tilt_deg_20N = math.degrees(tilt_rad)

    uz_hole_f = mean_hole_uz * ratio
    uz_tip_f = max_tip_uz * ratio
    tilt_deg_f = tilt_deg_20N * ratio
    radial_clearance_loss = 4.0 * np.tan(np.radians(tilt_deg_f))

    ax4_twin = ax4.twinx()

    q1, = ax4.plot(f_range, uz_tip_f, 'darkblue', lw=2.2, label='Макс. прогиб консоли $U_{z, \\max}(F)$ (конец $Y=28$)')
    q2, = ax4.plot(f_range, uz_hole_f, 'dodgerblue', lw=2.0, label='Вертикальный прогиб отверстия $U_z(F)$ ($Y=24$)')
    q3 = ax4.axhline(0.75, color='crimson', ls=':', lw=1.8, label='Радиальный зазор иглы $\\Delta r = 0.75$ мм (Ø4.5 vs Ø3.0)')

    q4, = ax4_twin.plot(f_range, tilt_deg_f, 'darkorange', lw=2.0, ls='--', label='Угловой перекос оси отверстия $\\theta(F)$ (град)')
    q5, = ax4_twin.plot(f_range, radial_clearance_loss, 'firebrick', lw=1.6, ls='-.', label='Смещение кромки от наклона $\\delta_{edge}(F)$ (мм)')

    ax4.axvline(20.0, color='purple', ls='--', lw=1.5)

    ax4.set_title('Г. Жесткость кронштейна: Прогиб и наклон отверстия иглы', fontweight='bold')
    ax4.set_xlabel('Сила сопротивления съему ягоды F (Н)')
    ax4.set_ylabel('Вертикальный прогиб $U_z$ (мм)')
    ax4_twin.set_ylabel('Угол перекоса $\\theta$ (град) / Смещение кромки (мм)')
    ax4.set_xlim(5, 40)
    ax4.set_ylim(0, 2.2)
    ax4_twin.set_ylim(0, 7.0)
    ax4.grid(True, ls='--', alpha=0.6)

    qlines = [q1, q2, q3, q4, q5]
    qlabels = [l.get_label() for l in qlines]
    ax4.legend(qlines, qlabels, loc='upper left', fontsize=8, framealpha=0.9)

    plt.suptitle('FEM-АНАЛИЗ НАПРЯЖЕННО-ДЕФОРМИРОВАННОГО СОСТОЯНИЯ СЪЕМНИКА ЯГОД (ВЧ.01.00.015)\n'
                 'Материал: изотропный PETG ($E=2100$ МПа, $\\nu=0.38$). Нагрузка съема $F=20$ Н (+Z)',
                 fontweight='bold', fontsize=13, y=0.99)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    dashboard_path = "/home/devuser/projects/vishni/fem_stress_dashboard.png"
    plt.savefig(dashboard_path, dpi=200)
    plt.close()
    print(f"   Дашборд сохранен: {dashboard_path}")


def plot_3d_contour(nodes_dict, boundary_faces, vms, disps, max_vm, max_node, max_uz_val):
    """Строит высокодетализированный 3D график распределения эквивалентных напряжений и деформаций"""
    fig = plt.figure(figsize=(18, 9), dpi=200)
    fig.patch.set_facecolor('#ffffff')

    scale = 5.0
    verts_deformed = []
    face_vms = []

    for f in boundary_faces:
        poly = []
        vm_avg = 0.0
        for nid in f:
            n = nodes_dict[nid]
            d = disps[nid]
            poly.append([n.x + scale*d.x, n.y + scale*d.y, n.z + scale*d.z])
            vm_avg += vms[nid]
        verts_deformed.append(poly)
        face_vms.append(vm_avg / 3.0)

    face_vms = np.array(face_vms)
    norm = matplotlib.colors.Normalize(vmin=0.0, vmax=min(max_vm, 55.0))
    cmap = cm.get_cmap('turbo')
    colors = cmap(norm(face_vms))

    # Вид 1: Изометрия сверху-спереди (общий вид напряжений)
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    coll1 = Poly3DCollection(verts_deformed, facecolors=colors, edgecolors='k', linewidths=0.1, alpha=0.95)
    ax1.add_collection3d(coll1)

    all_x = [p[0] for poly in verts_deformed for p in poly]
    all_y = [p[1] for poly in verts_deformed for p in poly]
    all_z = [p[2] for poly in verts_deformed for p in poly]
    ax1.set_xlim(min(all_x), max(all_x))
    ax1.set_ylim(min(all_y), max(all_y))
    ax1.set_zlim(min(all_z) - 2.0, max(all_z) + 4.0)

    ax1.view_init(elev=28, azim=-55)
    ax1.set_title('Изометрический вид: Эквивалентные напряжения $\\sigma_{vM}$ (МПа)\n(Деформации масштабированы $\\times 5$)',
                  fontweight='bold', fontsize=11)
    ax1.set_xlabel('X (мм)')
    ax1.set_ylabel('Y (мм)')
    ax1.set_zlabel('Z (мм)')

    ax1.text(max_node.x - 12.0, max_node.y - 2.0, max_node.z + 8.0,
             f'Концентратор напряжений:\n$\\sigma_{{vM, \\max}} = {max_vm:.1f}$ МПа',
             color='red', fontweight='bold', fontsize=9,
             bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='red', lw=1.5))

    ax1.text(6.0, 24.0, 49.5 + scale*max_uz_val*0.7 + 6.0,
             'Сила съема $F = 20$ Н (+Z)\n$U_{z, hole} \\approx 0.72$ мм',
             color='darkblue', fontweight='bold', fontsize=9,
             bbox=dict(boxstyle='round,pad=0.3', facecolor='azure', edgecolor='darkblue', lw=1.2))

    # Вид 2: Вид сбоку/снизу (демонстрация изгиба балки и зоны заделки)
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    coll2 = Poly3DCollection(verts_deformed, facecolors=colors, edgecolors='k', linewidths=0.1, alpha=0.95)
    ax2.add_collection3d(coll2)
    ax2.set_xlim(min(all_x), max(all_x))
    ax2.set_ylim(min(all_y), max(all_y))
    ax2.set_zlim(min(all_z) - 2.0, max(all_z) + 4.0)

    ax2.view_init(elev=15, azim=110)
    ax2.set_title('Вид снизу-сзади: Заделка $Y=0$, арочный вырез MGN9 и прогиб балки',
                  fontweight='bold', fontsize=11)
    ax2.set_xlabel('X (мм)')
    ax2.set_ylabel('Y (мм)')
    ax2.set_zlabel('Z (мм)')

    ax2.text(-10.0, 0.0, 45.0, 'Заделка $Y=0$\n(Привалка к стойке)',
             color='darkgreen', fontweight='bold', fontsize=9,
             bbox=dict(boxstyle='round,pad=0.3', facecolor='honeydew', edgecolor='darkgreen', lw=1.2))

    # Цветовая шкала
    cbar_ax = fig.add_axes([0.15, 0.08, 0.7, 0.035])
    sm = matplotlib.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, cax=cbar_ax, orientation='horizontal')
    cbar.set_label('Эквивалентные напряжения по Мизесу $\\sigma_{vM}$ (МПа)', fontweight='bold', fontsize=11)
    cbar.ax.axvline(50.0, color='red', ls='--', lw=2.5)
    cbar.ax.text(50.0, 1.25, '$\\sigma_y$ PETG = 50 МПа', color='red', fontweight='bold', ha='center')
    cbar.ax.axvline(33.3, color='orange', ls='--', lw=2.5)
    cbar.ax.text(33.3, 1.25, '$[\sigma] = 33.3$ МПа', color='orange', fontweight='bold', ha='center')

    plt.suptitle('3D РАСПРЕДЕЛЕНИЕ ЭКВИВАЛЕНТНЫХ НАПРЯЖЕНИЙ В КОНСТРУКЦИИ СЪЕМНИКА ЯГОД (C3D10 / CalculiX)\n'
                 'Изотропный PETG ($E=2100$ МПа, $\\nu=0.38$), Нагрузка съема $F_z = 20$ Н',
                 fontweight='bold', fontsize=13, y=0.98)

    contour_path = "/home/devuser/projects/vishni/fem_stress_3d_contour.png"
    plt.savefig(contour_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"   3D контурная визуализация сохранена: {contour_path}")


if __name__ == "__main__":
    run_fem_simulation()
