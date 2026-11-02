import sys, pathlib, itertools, numpy as np, trimesh
from build123d import import_step
D = pathlib.Path(sys.argv[1])
L = lambda n: import_step(str((D / 'controle' if n.startswith('_') else D) / f'{n}.step'))
parts = {n: L(n) for n in ('face', 'dos', 'logo', 'molette', 'berceau', 'support_pied', 'support_berceau')}
print('== pièces')
for n, p in parts.items():
    m = trimesh.load(str(D / f'{n}.stl'))
    print(f'{n:16s} solides={len(p.solids())} valide={p.is_valid} vol={p.volume/1000:6.2f} cm3 étanche_stl={m.is_watertight} bbox={np.round(m.extents, 2)}')
board = L('_carte_placee'); bat = L('_batterie'); plug = L('_fiche_usb'); pushed = L('_molette_enfoncee')
bsol = [s for s in board.solids() if s.volume > 0.01]
print('carte : solides retenus', len(bsol))
def inter(a, b_list, name):
    tot = 0; hits = []
    for b in b_list:
        A, B = a.bounding_box(), b.bounding_box()
        if (A.max.X < B.min.X - 0.01 or B.max.X < A.min.X - 0.01 or A.max.Y < B.min.Y - 0.01 or B.max.Y < A.min.Y - 0.01
                or A.max.Z < B.min.Z - 0.01 or B.max.Z < A.min.Z - 0.01):
            continue
        try:
            r = a & b
            v = r.volume if r is not None else 0.0
        except Exception as e:
            print(f'    !! échec booléen ({name}) : {e}'); continue
        if v != v: print(f'    !! volume NaN ({name})'); continue
        if v > 1e-4:
            tot += v; c = r.bounding_box().center(); hits.append((round(v, 4), (round(c.X, 2), round(c.Y, 2), round(c.Z, 2))))
    print(f'  {name:34s} volume commun = {tot:.4f} mm3' + (f'  {hits[:4]}' if hits else ''))
    return hits
print('== contacts avec la carte')
for n in ('face', 'dos', 'molette', 'berceau'):
    inter(parts[n], bsol, f'{n} ∩ carte')
h = inter(pushed, bsol, 'molette ENFONCÉE ∩ carte')
print('== batterie et fiche USB')
for n in ('face', 'dos', 'molette', 'berceau'):
    inter(parts[n], bat.solids(), f'{n} ∩ batterie')
inter(bat, bsol, 'batterie ∩ carte')
for n in ('face', 'dos', 'berceau'):
    inter(parts[n], plug.solids(), f'{n} ∩ fiche USB-C')
print('== pièces entre elles')
for a, b in itertools.combinations(('face', 'dos', 'logo', 'molette', 'berceau'), 2):
    inter(parts[a], parts[b].solids(), f'{a} ∩ {b}')
inter(pushed, parts['face'].solids() + parts['dos'].solids(), 'molette enfoncée ∩ coques')
