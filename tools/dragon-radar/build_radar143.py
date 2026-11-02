# Radar Dragon Ball (MakerWorld 2776400) adapté à la Waveshare ESP32-S3-Touch-AMOLED-1.43.
# Coques d'origine réduites ×0,63 (même bande noire visible qu'avec la 1.75), épaisseur augmentée
# pour une LiPo 603040 sous la carte, carte vissée sur un berceau posé sur 3 plots,
# molette qui appuie sur BOOT (la 1.43 n'a pas de bouton PWR), logo Capsule Corp incrusté au dos.
#
# Usage : python build_radar143.py <dragon-radar-beitian.step> <DB Radar stand.step> <carte_1_43.stp> <dossier_sortie>
import sys, math, json, pathlib
from build123d import *

RADAR_STEP, STAND_STEP, BOARD_STEP, OUT = sys.argv[1:5]
OUT = pathlib.Path(OUT); OUT.mkdir(parents=True, exist_ok=True)

P = dict(
    s=0.63,                  # réduction des coques d'origine
    board_rot=180 - 113.5,   # BOOT (113,5° sur la carte) tourné face à la molette (180°)
    glass_front=1.10,        # face avant de la vitre (modèle Waveshare, axe Z)
    pcb_back=-5.10,          # dos du circuit imprimé
    standoff_tip=-9.10,      # bout des entretoises M2 H4
    pmma_r=22.75,            # cadre de l'écran (Z -3,9 à -0,1)
    pcb_r=21.75,
    boot_tip_r=20.95,        # pointe du bouton BOOT
    boot_z=(-7.75, -5.75),
    usb_z=(-8.35, -5.19),    # USB-C à 180° sur la carte
    standoffs=[(11.59, -15.75), (11.59, 15.75), (-11.61, 15.75), (-11.51, -15.75)],
    headers=[(0.0, 16.25), (0.0, -16.25)],   # connecteurs 2×7 broches 1,27 mm (9,2 × 4,5, jusqu'à Z -9,6)
    header_z_min=-9.60,
    spider_t=1.6,
    bat=(40.0, 30.0, 6.0), bat_tol=0.3, bat_gap=0.25, bat_angle=5.0,
    floor_t=1.8,             # fond du dos épaissi (logo incrusté dessous)
    floor_fillet=2.0,        # petit arrondi intérieur : fond plat jusqu'à r = 25,5
    collar_d=46.7, collar_h=1.2,   # collerette de centrage (vitre Ø46)
    joint_r_orig=41.2, joint_angles=[20, 80, 130, 165, 195, 300],
    post_r=24.0, post_angles=[5, 110, 270],
    boss_d=5.2, pilot_d=1.7, clear_d=2.3, head_cb_d=4.2, joint_screw=10.0,
    crown_rest_gap=0.45, crown_travel=0.9,
    flange=5.4, flange_len=1.8, neck_d=4.0,
    usb_open=(13.0, 7.4),
    skirt_clear=0.15, skirt_t=1.0,
    preload=0.1,
    logo_scale=1.0, logo_depth=0.6,   # logo redessiné à neuf (logo_capsule_corp_v2.py), cotes finales
)
s = P['s']; th = P['board_rot']

# ---------------------------------------------------------------- cotes de base
lip_under = 3.6 * s
dz_board = lip_under - P['glass_front']
pcb_back = P['pcb_back'] + dz_board
standoff_tip = P['standoff_tip'] + dz_board
spider_top = standoff_tip
spider_bot = spider_top - P['spider_t']
bat_top = spider_bot - P['bat_gap']
floor_in = bat_top - (P['bat'][2] + P['bat_tol'])
zj = -5.4 * s
R_out, R_in = 45.722 * s, 43.722 * s
c_out = 36.722 * s; Ro = 9 * s
fr = P['floor_fillet']
z_bot_out = floor_in - P['floor_t']
z_v_out = z_bot_out + Ro            # centre de l'arrondi extérieur
z_v_in = floor_in + fr              # centre de l'arrondi intérieur (r = R_in - fr)
skirt_bot = -7.2 * s
skirt_out = R_in - P['skirt_clear']
joint_r = P['joint_r_orig'] * s

def polar(r, deg, z=0):
    a = math.radians(deg); return Pos(r * math.cos(a), r * math.sin(a), z)
def b2r(x, y):
    a = math.radians(th); return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))
def zcyl(d, z0, z1, x=0, y=0):
    return Pos(x, y, z0) * Cylinder(d / 2, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
def xcyl(d, x0, x1, y=0, z=0):
    return Pos(x0, y, z) * Rot(0, 90, 0) * Cylinder(d / 2, x1 - x0, align=(Align.CENTER, Align.CENTER, Align.MIN))
def xcone(r0, r1, x0, x1, z):
    return Pos(x0, 0, z) * Rot(0, 90, 0) * Cone(r0, r1, x1 - x0, align=(Align.CENTER, Align.CENTER, Align.MIN))
def box(x0, x1, y0, y1, z0, z1):
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN, Align.MIN, Align.MIN))
def arc_mid(c, r, a0, a1):
    a = math.radians((a0 + a1) / 2); return (c[0] + r * math.cos(a), c[1] + r * math.sin(a))

orig = import_step(RADAR_STEP).solids()
crown_orig, front_orig = orig[0], orig[4]

# ---------------------------------------------------------------- face : profil exact d'origine, ×s, refait tourner
ang = math.radians(250)
d = Vector(math.cos(ang), math.sin(ang), 0)
half = Plane(origin=(0, 0, 0), x_dir=d, z_dir=Vector(-math.sin(ang), math.cos(ang), 0)) * Pos(30, 0) * Rectangle(60, 60)
front = revolve((front_orig & half).faces()[0].rotate(Axis.Z, -250).scale(s), Axis.Z, 360)
# jupe : 0,15 de jeu dans le dos, épaissie vers l'intérieur à 1 mm
front -= zcyl(100, skirt_bot - 1, zj) - zcyl(2 * skirt_out, skirt_bot - 2, zj + 1)
front += zcyl(2 * skirt_out, skirt_bot, zj) - zcyl(2 * (skirt_out - P['skirt_t']), skirt_bot - 1, zj + 1)

# ---------------------------------------------------------------- dos : profil d'origine ×s, bande ajoutée, fond 1,8 mm, petit arrondi intérieur
with BuildSketch(Plane.XZ) as back_sk:
    with BuildLine():
        Polyline((0, z_bot_out), (c_out, z_bot_out))
        ThreePointArc((c_out, z_bot_out), arc_mid((c_out, z_v_out), Ro, -90, 0), (R_out, z_v_out))
        Polyline((R_out, z_v_out), (R_out, zj), (R_in, zj), (R_in, z_v_in))
        ThreePointArc((R_in, z_v_in), arc_mid((R_in - fr, z_v_in), fr, 0, -90), (R_in - fr, floor_in))
        Polyline((R_in - fr, floor_in), (0, floor_in), (0, z_bot_out))
    make_face()
back = revolve(back_sk.sketch.faces()[0], Axis.Z, 360)
with BuildSketch(Plane.XZ) as env_sk:
    with BuildLine():
        Polyline((0, z_bot_out), (c_out, z_bot_out))
        ThreePointArc((c_out, z_bot_out), arc_mid((c_out, z_v_out), Ro, -90, 0), (R_out, z_v_out))
        Polyline((R_out, z_v_out), (R_out, zj), (0, zj), (0, z_bot_out))
    make_face()
back_env = revolve(env_sk.sketch.faces()[0], Axis.Z, 360)

# ---------------------------------------------------------------- excroissance de la molette (à -X), allongée de 0,5 mm vers l'extérieur
ear_x0, ear_hw, ear_z0, ear_z1 = -51.25 * s - 0.5, P['flange'] / 2 + 0.2 + 1.2, -12.3 * s, 1.5 * s
ear = fillet(box(ear_x0, -R_in + 1.2, -ear_hw, ear_hw, ear_z0, ear_z1).edges().group_by(Axis.X)[0], 0.8)
front += ear & box(-60, -R_in + 1.2, -10, 10, zj, 10)
back += ear & box(-60, -(R_in + 0.3), -10, 10, -40, zj)

# ---------------------------------------------------------------- collerette de centrage de la vitre
front += zcyl(P['collar_d'] + 2.2, lip_under - P['collar_h'], lip_under + 0.2) - zcyl(P['collar_d'], lip_under - 5, lip_under + 1)

# ---------------------------------------------------------------- intérieur caché de la face rempli à 45° : imprimée lèvre en haut,
# la face n'a plus de surplomb dans le dôme ; il ne reste à supporter que le dessous de la lèvre (appui de la vitre) et l'excroissance.
with BuildSketch(Plane.XZ) as fenv_sk:
    with BuildLine():
        Polyline((0, zj), (R_out, zj), (R_out, -3.4 * s))
        ThreePointArc((R_out, -3.4 * s), arc_mid((c_out, -3.4 * s), Ro, 0, 90), (c_out, 5.6 * s))
        Polyline((c_out, 5.6 * s), (0, 5.6 * s), (0, zj))
    make_face()
front_env = revolve(fenv_sk.sketch.faces()[0], Axis.Z, 360)
seat_r = P['collar_d'] / 2                       # le cône rejoint la collerette au niveau de la vitre
cone_bot = lip_under - (R_in + 0.05 - seat_r)    # 45° : départ sur la paroi intérieure
with BuildSketch(Plane.XZ) as fill_sk:
    with BuildLine():
        Polyline((seat_r, lip_under), (R_in + 0.05, cone_bot), (R_out + 1, cone_bot), (R_out + 1, 6), (seat_r, 6), (seat_r, lip_under))
    make_face()
front += revolve(fill_sk.sketch.faces()[0], Axis.Z, 360) & front_env

# ---------------------------------------------------------------- vis de fermeture (M2×10) : plots de la face, bossages du dos
def z_front_out(r):   # surface extérieure de la face (tore) au rayon r
    return -3.4 * s + math.sqrt(max(Ro ** 2 - (r - c_out) ** 2, 0))
def z_back_out(r):
    return z_v_out - math.sqrt(max(Ro ** 2 - (r - c_out) ** 2, 0)) if r > c_out else z_bot_out
front_post_top = z_front_out(joint_r + P['boss_d'] / 2) - 0.2
pilot_end = front_post_top - 0.1
seat_z = pilot_end - P['joint_screw'] - 0.3
head_ok = seat_z - 1.6 > z_back_out(joint_r + 1.9)
for a in P['joint_angles']:
    pos = polar(joint_r, a)
    front += pos * zcyl(P['boss_d'], skirt_bot, front_post_top) & (zcyl(2 * skirt_out, -40, zj) + zcyl(200, zj, 40))
    front -= pos * zcyl(P['pilot_d'], skirt_bot - 1, pilot_end)
    back += pos * zcyl(P['boss_d'], z_bot_out - 1, skirt_bot - 0.1) & back_env
    back -= pos * zcyl(P['clear_d'], z_bot_out - 2, 0)
    back -= pos * zcyl(P['head_cb_d'], z_bot_out - 5, seat_z)

# ---------------------------------------------------------------- carte dans le repère du radar
standoffs = [b2r(*p) for p in P['standoffs']]
st_ang = [math.degrees(math.atan2(y, x)) for x, y in standoffs]
headers = [b2r(*p) for p in P['headers']]
usb_ang = (180 + th) % 360

# ---------------------------------------------------------------- plots du berceau
for a in P['post_angles']:
    pos = polar(P['post_r'], a)
    back += pos * zcyl(P['boss_d'], floor_in - 0.8, spider_bot + P['preload']) & back_env
    back -= pos * zcyl(P['pilot_d'], spider_bot - 6, spider_bot + 1)

# ---------------------------------------------------------------- berceau : anneau en C (r 21-22,7) + pattes vers les entretoises + appuis sur les plots
sp_z0, sp_h = spider_bot, P['spider_t']
gap0, gap1 = usb_ang - 18, usb_ang + 18
a0, a1 = gap1, gap0 + 360
wedge = extrude(Plane.XY.offset(sp_z0 - 1) * Polygon(*([(0, 0)] + [(45 * math.cos(math.radians(a0 + (a1 - a0) * i / 60)), 45 * math.sin(math.radians(a0 + (a1 - a0) * i / 60))) for i in range(61)]), align=None), sp_h + 2)
spider = (zcyl(2 * 22.7, sp_z0, sp_z0 + sp_h) - zcyl(2 * 21.0, sp_z0 - 1, sp_z0 + sp_h + 1)) & wedge
for (x, y), a in zip(standoffs, st_ang):
    r0 = math.hypot(x, y)
    spider += zcyl(5.0, sp_z0, sp_z0 + sp_h, x, y)
    spider += Rot(0, 0, a) * Pos((r0 + 21.6) / 2, 0, sp_z0) * Box(21.6 - r0, 3.4, sp_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
for a in P['post_angles']:
    spider += polar(P['post_r'], a) * zcyl(5.6, sp_z0, sp_z0 + sp_h)
    spider += Rot(0, 0, a) * Pos(22.5, 0, sp_z0) * Box(3.2, 3.4, sp_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
for hx, hy in headers:   # dégagement des broches 2×7 (descendent sous le haut du berceau)
    ha = math.degrees(math.atan2(hy, hx))
    spider -= Rot(0, 0, ha) * Pos(16.25, 0, sp_z0 - 1) * Box(5.5, 10.2, sp_h + 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
for x, y in standoffs:   # vis fraisées M2×5 par-dessous
    spider -= zcyl(2.3, sp_z0 - 1, sp_z0 + sp_h + 1, x, y)
    spider -= Pos(x, y, sp_z0 - 0.001) * Cone(4.6 / 2, 2.3 / 2, 1.15, align=(Align.CENTER, Align.CENTER, Align.MIN))
for a in P['post_angles']:   # vis M2×6 tête fraisée par-dessus dans les plots (têtes noyées : rien ne dépasse vers la carte)
    spider -= polar(P['post_r'], a) * zcyl(2.3, sp_z0 - 1, sp_z0 + sp_h + 1)
    spider -= polar(P['post_r'], a, sp_z0 + sp_h - 1.15) * Cone(2.3 / 2, 4.6 / 2, 1.151, align=(Align.CENTER, Align.CENTER, Align.MIN))

# ---------------------------------------------------------------- passage de la molette : col rond, logement carré à entrée conique, fente pour la lame
fl, fhalf = P['flange_len'], P['flange'] / 2
cb_out = ear_x0 + 1.2
cb_in = cb_out + fl + P['crown_travel']
neck_r = P['neck_d'] / 2
blade_z = (zj + 0.47, zj - 1.53)           # lame plate : sous le cadre de l'écran, au-dessus du patin
slot = box(cb_in - 0.01, -22.5, -1.5, 1.5, blade_z[1] - 0.3, blade_z[0] + 0.3)
bore = xcyl(P['neck_d'] + 0.5, ear_x0 - 1, cb_out + 0.01, 0, zj) \
       + (box(cb_out, cb_in, -fhalf - 0.2, fhalf + 0.2, zj - fhalf - 0.2, zj + fhalf + 0.2) & xcone(neck_r, neck_r + (cb_in - cb_out), cb_out, cb_in, zj)) + slot
front -= bore
back -= bore

# ---------------------------------------------------------------- molette : roue moletée d'origine + col + bride + lame + patin sur BOOT
crown_s = crown_orig.scale(s)
wheel_in = -55.9 * s
wheel = crown_s & box(-80, wheel_in, -20, 20, -40, 40)
rod_end = -(P['pcb_r'] + P['crown_travel'] + 0.2)      # la lame ne touche jamais le circuit imprimé
pad_tip = -(P['boot_tip_r'] + P['crown_rest_gap'])
bz0, bz1 = P['boot_z'][0] + dz_board, P['boot_z'][1] + dz_board
pad_top = pcb_back - 0.2                     # jusqu'à 0,2 mm sous le circuit imprimé : bonne liaison avec la lame
pad = box(rod_end - 1.5, pad_tip, -1.2, 1.2, bz0 - 0.3, pad_top)
pad = chamfer(pad.edges().group_by(Axis.X)[-1].filter_by(Axis.Y), 0.25)
crown = wheel + xcyl(P['neck_d'], wheel_in - 2.0, cb_out + 0.01, 0, zj) \
        + (box(cb_out, cb_out + fl, -fhalf, fhalf, zj - fhalf, zj + fhalf) & xcone(neck_r, neck_r + fl, cb_out, cb_out + fl, zj)) \
        + box(cb_out + fl - 0.01, rod_end, -1.2, 1.2, blade_z[1], blade_z[0]) + pad

# ---------------------------------------------------------------- ouverture USB-C
usb_zc = sum(P['usb_z']) / 2 + dz_board
uw, uh = P['usb_open']
usb_cut = Box(8.0, uw, uh)
usb_cut = Rot(0, 0, usb_ang) * Pos(R_in + 1.0, 0, usb_zc) * fillet(usb_cut.edges().filter_by(Axis.X), 2.0)
front -= usb_cut
back -= usb_cut

# ---------------------------------------------------------------- logo Capsule Corp incrusté au dos
LOGO_JSON = pathlib.Path(__file__).with_name('logo_capsule_corp_v2.json')
logo = None
if LOGO_JSON.exists():
    L = json.loads(LOGO_JSON.read_text()); k = P['logo_scale']
    logo = Part()
    for poly in L['polygons']:
        outer = Wire.make_polygon([Vector(k * x, k * y, 0) for x, y in poly['outer']], close=True)
        holes = [Wire.make_polygon([Vector(k * x, k * y, 0) for x, y in h], close=True) for h in poly['holes']]
        logo += extrude(Face(outer, holes), P['logo_depth'])
    logo = logo.rotate(Axis.Z, 90).translate((0, 0, z_bot_out))
    back -= logo

# ---------------------------------------------------------------- support réduit ×s
stand = [so.scale(s) for so in import_step(STAND_STEP).solids()]
# berceau du support élargi dans l'épaisseur du radar : même proportion qu'à l'origine (17,87 / 22)
cb_ = stand[1].bounding_box(); f_ = (17.87 / 22.0) * (5.6 * s - z_bot_out) / cb_.size.Y; cy_ = cb_.center().Y
stand[1] = stand[1].transform_geometry(Matrix([[1, 0, 0, 0], [0, f_, 0, cy_ * (1 - f_)], [0, 0, 1, 0], [0, 0, 0, 1]]))

# ---------------------------------------------------------------- carte et volumes témoins
board = import_step(BOARD_STEP).translate((0, 0, dz_board)).rotate(Axis.Z, th)
bw, bl, bt = P['bat']
battery = Rot(0, 0, P['bat_angle']) * Pos(0, 0, floor_in) * Box(bw, bl, bt + P['bat_tol'], align=(Align.CENTER, Align.CENTER, Align.MIN))
overmold = fillet(Box(15, 12.0, 6.5).edges().filter_by(Axis.X), 1.5)
plug = Rot(0, 0, usb_ang) * (Pos(22.51 + 0.4 + 7.5, 0, usb_zc) * overmold + Pos(22.51 - 6.0 + 3.25 + 0.4, 0, usb_zc) * Box(6.5, 8.3, 2.6))

parts = dict(face=front, dos=back, molette=crown, berceau=spider, support_pied=stand[0], support_berceau=stand[1])
if logo is not None: parts['logo'] = logo
for k_, v in parts.items():
    export_step(v, str(OUT / f'{k_}.step'))
    export_stl(v, str(OUT / f'{k_}.stl'), tolerance=0.02, angular_tolerance=0.15)
(OUT / 'controle').mkdir(exist_ok=True)
export_step(board, str(OUT / 'controle/_carte_placee.step'))
export_step(battery, str(OUT / 'controle/_batterie.step'))
export_step(plug, str(OUT / 'controle/_fiche_usb.step'))
export_step(crown.translate((P['crown_travel'], 0, 0)), str(OUT / 'controle/_molette_enfoncee.step'))

info = dict(P, h_total=round(5.6 * s - z_bot_out, 3), outer_diameter=round(2 * R_out, 2), zj=round(zj, 3), lip_under=round(lip_under, 3),
            dz_board=round(dz_board, 3), floor_in=round(floor_in, 3), z_bot_out=round(z_bot_out, 3), seat_z=round(seat_z, 3),
            front_post_top=round(front_post_top, 3), head_recessed=head_ok, standoffs_radar=[tuple(round(c, 2) for c in p) for p in standoffs],
            standoff_angles=[round(a, 1) for a in st_ang], usb_angle=round(usb_ang, 1), usb_zc=round(usb_zc, 3),
            cb_out=round(cb_out, 3), cb_in=round(cb_in, 3), wall_behind_stop=round(-(cb_in + R_in), 3),
            rod_end=round(rod_end, 3), pad_tip=round(pad_tip, 3), pad_z=(round(bz0 - 0.3, 3), round(pad_top, 3)), blade_z=[round(z, 3) for z in blade_z])
(OUT / 'cotes.json').write_text(json.dumps(info, indent=1, ensure_ascii=False))
print(json.dumps({k_: info[k_] for k_ in ('outer_diameter', 'h_total', 'floor_in', 'seat_z', 'head_recessed', 'standoff_angles', 'usb_angle', 'cb_out', 'cb_in', 'rod_end', 'pad_tip', 'pad_z', 'blade_z')}, ensure_ascii=False))
