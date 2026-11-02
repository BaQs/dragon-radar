# Logo « Capsule Corp » dessiné à neuf (formes simples + police système), pour remplacer celui
# repris du Capsule Radar (fichier MakerWorld sous licence exclusive, non redistribuable).
# Sortie : même format JSON que logo_capsule_corp.json (polygones + trous), cotes finales en mm,
# dans le repère « ancien » attendu par build_radar143.py (x = -u, y = v, u/v = lecture depuis
# l'extérieur du dos, v vers le haut) ; à utiliser avec logo_scale = 1.
# Usage : python logo_capsule_corp_v2.py <sortie.json> [aperçu.png]
import sys, json, math
import numpy as np
from shapely.geometry import Polygon, Point, box, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

FONT = '/System/Library/Fonts/Supplemental/Arial Black.ttf'

def ring(r0, r1):
    return Point(0, 0).buffer(r1, 256).difference(Point(0, 0).buffer(r0, 256))

def sector(r0, r1, a0, a1, n=200):
    pts = [(r1 * math.cos(math.radians(a0 + (a1 - a0) * i / n)), r1 * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    pts += [(r0 * math.cos(math.radians(a1 - (a1 - a0) * i / n)), r0 * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return Polygon(pts)

def glyph(ch, height):
    """Contours d'un caractère (hauteur de capitale = height), origine en bas à gauche."""
    tp = TextPath((0, 0), ch, size=1.0, prop=FontProperties(fname=FONT))
    polys = [Polygon(p) for p in tp.to_polygons() if len(p) >= 3]
    polys = [p.buffer(0) for p in polys if p.area > 1e-6]
    # pair/impair : un contour contenu dans un nombre impair d'autres est un trou
    shape = Polygon()
    for p in sorted(polys, key=lambda q: -q.area):
        depth = sum(1 for q in polys if q is not p and q.area > p.area and q.contains(p.representative_point()))
        shape = shape.union(p) if depth % 2 == 0 else shape.difference(p)
    cap = TextPath((0, 0), 'H', size=1.0, prop=FontProperties(fname=FONT)).get_extents().height
    adv = TextPath((0, 0), ch + 'H', size=1.0, prop=FontProperties(fname=FONT)).get_extents().width - \
          TextPath((0, 0), 'H', size=1.0, prop=FontProperties(fname=FONT)).get_extents().width
    k = height / cap
    return affinity.scale(shape, k, k, origin=(0, 0)), adv * k

# --- emblème (cotes finales, mm) -------------------------------------------------------------
R_OUT, R_OUT_IN = 13.6, 11.2        # anneau extérieur
R_C, R_C_IN = 8.8, 6.4              # « C » intérieur, ouvert à droite
R_DISC = 4.2                        # disque central
BAR = 0.9                           # demi-épaisseur de la barre horizontale
GAP = 2.0                           # demi-hauteur de l'ouverture du C

emblem = unary_union([
    ring(R_OUT_IN, R_OUT),
    ring(R_C_IN, R_C).difference(box(0, -GAP, R_C + 1, GAP)),
    Point(0, 0).buffer(R_DISC, 256),
    box(0, -BAR, R_OUT - 0.2, BAR),
])

# --- bandeau sous le cercle, lettres le long de l'arc ----------------------------------------
B0, B1, A0, A1, T = 14.6, 21.2, 206.0, 334.0, 0.9   # rayons, angles (bas = 270°), épaisseur du cadre
frame = sector(B0, B1, A0, A1).difference(sector(B0 + T, B1 - T, A0 + math.degrees(T / ((B0 + B1) / 2)) * 1.2, A1 - math.degrees(T / ((B0 + B1) / 2)) * 1.2))
frame = frame.difference(Point(0, 0).buffer(R_OUT + 0.6, 256))      # liseré clair entre cercle et bandeau

TEXT, CAP = 'CAPSULE CORP.', 2.8
r_mid = (B0 + T + B1 - T) / 2
r_base = r_mid + CAP / 2            # les lettres « regardent » le centre : base à l'extérieur
glyphs = [glyph(c, CAP) if c != ' ' else (Polygon(), CAP * 0.35) for c in TEXT]
track = 0.12                        # espacement ajouté entre lettres (mm)
total = sum(a for _, a in glyphs) + track * (len(glyphs) - 1)
ang_span = math.degrees(total / r_base)
a = 270 - ang_span / 2              # centré en bas, lecture de gauche (212°) à droite (328°)
letters = []
for g, adv in glyphs:
    a_mid = a + math.degrees(adv / 2 / r_base)
    if not g.is_empty:
        # glyphe centré horizontalement, base sur y=0, haut vers le centre : tourné de a_mid - 270°, posé au rayon de base
        g0 = affinity.translate(g, -adv / 2, 0)
        g0 = affinity.rotate(g0, a_mid - 270, origin=(0, 0))
        x, y = r_base * math.cos(math.radians(a_mid)), r_base * math.sin(math.radians(a_mid))
        letters.append(affinity.translate(g0, x, y))
    a += math.degrees((adv + track) / r_base)

ink = unary_union([emblem, frame] + letters).buffer(0)
ink = ink.simplify(0.01)
geoms = list(ink.geoms) if isinstance(ink, MultiPolygon) else [ink]

out = []
for g in geoms:
    flip = lambda cs: [[-x, y] for x, y in cs]   # lecture (u, v) -> repère attendu (x = -u, y = v)
    out.append({'outer': flip(list(g.exterior.coords)[:-1]), 'holes': [flip(list(h.coords)[:-1]) for h in g.interiors]})
r_max = max(math.hypot(x, y) for g in geoms for x, y in g.exterior.coords)
json.dump({'source': 'dessiné à neuf (logo_capsule_corp_v2.py), Arial Black', 'thickness': 0.6, 'polygons': out}, open(sys.argv[1], 'w'))
print(f'{len(geoms)} polygones, aire {ink.area:.1f} mm², rayon max {r_max:.2f} mm, arc du texte {ang_span:.0f}°')

if len(sys.argv) > 2:
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.add_patch(plt.Circle((0, 0), 28.8, color='#f2f2f2', ec='#999'))
    for g in geoms:
        verts, codes = [], []
        for r in [g.exterior] + list(g.interiors):
            c = list(r.coords); verts += c; codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), facecolor='#2E3192', edgecolor='none'))
    ax.set_xlim(-30, 30); ax.set_ylim(-30, 30); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title('Logo redessiné, vu de l\'extérieur du dos (molette en haut)', fontsize=9)
    plt.tight_layout(); plt.savefig(sys.argv[2], dpi=110)
