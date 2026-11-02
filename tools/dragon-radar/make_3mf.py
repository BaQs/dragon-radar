# Assemble les STL du radar en un 3MF Bambu Studio : pièces nommées, 2 plateaux,
# supports arbre (depuis le plateau) sur la face uniquement.
# Usage : python make_3mf.py <dossier_des_stl> <fichier.3mf> [projet_bambu_modele.3mf] [sans-reglages-objet]
# Le projet modèle (un vrai projet Bambu Studio pour la même imprimante) fournit project_settings.config :
# sans lui, Bambu Studio 2.08 refuse le fichier (« configuration invalide ») sur une X2D à deux buses.
import sys, uuid, zipfile, pathlib, json, datetime, numpy as np, trimesh

D = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
TEMPLATE = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else None
OBJ_SETTINGS = not (len(sys.argv) > 4 and sys.argv[4] == 'sans-reglages-objet')
APP = 'BambuStudio-02.08.02.61'
LOGO_COLOUR = '#2E3192FF'   # bleu Capsule Corp
BED = 'Textured PEI Plate'
SCREEN = '1.43' if '143' in str(D) else '1.75'
PLATE_PITCH = 307.2   # 256 × 1,2 : décalage entre plateaux dans Bambu Studio

def rot_x(deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def rot_y(deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

# (fichier, nom affiché, rotation d'impression, plateau, position XY sur le plateau, réglages propres)
SUPPORT = {'enable_support': '1', 'support_type': 'tree(auto)', 'support_on_build_plate_only': '1',
           'support_filament': '1', 'support_interface_filament': '1', 'support_top_z_distance': '0.2'}   # même filament que la face, 0,2 mm d'écart
WALLS = {'wall_loops': '3'}
# Un seul plateau 256 × 256 (X2D) : tout à x ≥ 22 mm (la buse droite ne va pas sous 20,5 mm),
# coin de la tour de purge (≈ x 165-200, y 210-245) laissé libre.
OBJECTS = [
    ('face.stl', 'Face (lèvre en haut)', np.eye(3), 1, (62, 50), {**SUPPORT, **WALLS}),
    ([('dos.stl', 'Dos', 1), ('logo.stl', 'Logo Capsule Corp', 2)], 'Dos', np.eye(3), 1, (145, 50), WALLS),
    ('berceau.stl', 'Berceau de la carte', np.eye(3), 1, (60, 150), {}),
    ('support_pied.stl', 'Support - pied', rot_x(180), 1, (135, 155), {}),
    ('support_berceau.stl', 'Support - berceau', rot_x(90), 1, (215, 128), {}),
    ('molette.stl', 'Molette (roue en bas)', rot_y(-90), 1, (215, 162), {}),
]
PLATES = {1: 'Radar complet - supports sur la face seulement'}

# Noms en anglais (publication MakerWorld) : variable d'environnement DRAGON_3MF_LANG=en
import os
if os.environ.get('DRAGON_3MF_LANG') == 'en':
    EN = {'Face (lèvre en haut)': 'Front (lip up)', 'Dos': 'Back', 'Logo Capsule Corp': 'Capsule Corp logo',
          'Berceau de la carte': 'Board cradle', 'Support - pied': 'Stand - base', 'Support - berceau': 'Stand - cradle',
          'Molette (roue en bas)': 'Crown (wheel down)'}
    OBJECTS = [([(f, EN.get(n, n), e) for f, n, e in o[0]] if isinstance(o[0], list) else o[0], EN.get(o[1], o[1])) + tuple(o[2:]) for o in OBJECTS]
    PLATES = {1: 'Dragon Radar - all parts (supports on the front only)'}

def fmt(v): return f'{v:.5f}'.rstrip('0').rstrip('.')

objs = []
for i, (fn, name, R, plate, (px, py), extra) in enumerate(OBJECTS, start=1):
    specs = fn if isinstance(fn, list) else [(fn, name, 1)]
    specs = [s for s in specs if (D / s[0]).exists()]
    meshes = [(trimesh.load(str(D / f)), pn, ex) for f, pn, ex in specs]
    V0 = meshes[0][0].vertices @ R.T             # le premier maillage fixe le centrage
    lo, hi = V0.min(0), V0.max(0); c = (lo + hi) / 2
    parts = [dict(comp_id=i * 10 + j, name=pn, extruder=ex, V=m.vertices @ R.T - c, F=m.faces) for j, (m, pn, ex) in enumerate(meshes)]
    tx = (plate - 1) * PLATE_PITCH + px
    objs.append(dict(id=i, name=name, parts=parts, plate=plate,
                     t=(tx, py, (hi[2] - lo[2]) / 2), extra=extra, path=f'3D/Objects/object_{i}.model'))

def obj_model(o):
    blocks = []
    for pt in o['parts']:
        vs = '\n'.join(f'     <vertex x="{fmt(x)}" y="{fmt(y)}" z="{fmt(z)}"/>' for x, y, z in pt['V'])
        ts = '\n'.join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in pt['F'])
        blocks.append(f'''  <object id="{pt['comp_id']}" p:UUID="{uuid.uuid4()}" type="model">
   <mesh>
    <vertices>
{vs}
    </vertices>
    <triangles>
{ts}
    </triangles>
   </mesh>
  </object>''')
    body = '\n'.join(blocks)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <resources>
{body}
 </resources>
 <build/>
</model>
'''

res = '\n'.join(f'''  <object id="{o['id']}" p:UUID="{uuid.uuid4()}" type="model">
   <components>
''' + '\n'.join(f'''    <component p:path="/{o['path']}" objectid="{pt['comp_id']}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>''' for pt in o['parts']) + '''
   </components>
  </object>''' for o in objs)
items = '\n'.join(f'''  <item objectid="{o['id']}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 {o['t'][0]:.4f} {o['t'][1]:.4f} {o['t'][2]:.5f}" printable="1"/>''' for o in objs)
today = datetime.date.today().isoformat()
DESC = (f'Dragon Radar for the Waveshare ESP32-S3-Touch-AMOLED-{SCREEN} - https://github.com/BaQs/dragon-radar (based on socquique/capsule-radar)'
        if os.environ.get('DRAGON_3MF_LANG') == 'en' else
        f'Dragon Radar pour la Waveshare ESP32-S3-Touch-AMOLED-{SCREEN} - https://github.com/BaQs/dragon-radar (base : socquique/capsule-radar)')
main = f'''<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">
 <metadata name="Application">{APP}</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="Copyright"></metadata>
 <metadata name="CreationDate">{today}</metadata>
 <metadata name="Description">{DESC}</metadata>
 <metadata name="Designer"></metadata>
 <metadata name="DesignerCover"></metadata>
 <metadata name="DesignerUserId"></metadata>
 <metadata name="License"></metadata>
 <metadata name="ModificationDate">{today}</metadata>
 <metadata name="Origin"></metadata>
 <metadata name="ProfileCover"></metadata>
 <metadata name="ProfileDescription"></metadata>
 <metadata name="ProfileTitle"></metadata>
 <metadata name="Title">Radar Dragon Ball {SCREEN}</metadata>
 <resources>
{res}
 </resources>
 <build p:UUID="{uuid.uuid4()}">
{items}
 </build>
</model>
'''
rels_model = '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n' + \
    '\n'.join(f' <Relationship Target="/{o["path"]}" Id="rel-{o["id"]}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>' for o in objs) + '\n</Relationships>\n'
rels_root = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
'''
ctypes = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="png" ContentType="image/png"/>
</Types>
'''
def esc(s): return s.replace('&', '&amp;').replace('"', '&quot;')
proj = None; N_FIL = 2
if TEMPLATE is not None:
    with zipfile.ZipFile(TEMPLATE) as tz:
        proj = json.loads(tz.read('Metadata/project_settings.config'))
    N_FIL = len(proj['filament_settings_id'])
    assert N_FIL >= 2, 'le projet modèle doit avoir au moins 2 filaments'
    proj['filament_colour'][1] = LOGO_COLOUR       # filament 2 = logo
    if 'filament_multi_colour' in proj: proj['filament_multi_colour'][1] = LOGO_COLOUR
    proj['curr_bed_type'] = BED
    proj['enable_support'] = '0'                   # supports seulement sur la face (réglage d'objet)
    proj['reduce_crossing_wall'] = '1'             # contourner la fenêtre de la face au lieu de la survoler (fils)
    proj['max_travel_detour_distance'] = '0'       # détour sans limite
cfg = ['<?xml version="1.0" encoding="UTF-8"?>', '<config>']
for o in objs:
    cfg += [f'  <object id="{o["id"]}">', f'    <metadata key="name" value="{esc(o["name"])}"/>', '    <metadata key="extruder" value="1"/>']
    if OBJ_SETTINGS:
        cfg += [f'    <metadata key="{k}" value="{v}"/>' for k, v in o['extra'].items()]
    cfg += [f'    <metadata face_count="{sum(len(pt["F"]) for pt in o["parts"])}"/>']
    for pt in o['parts']:
        cfg += [f'    <part id="{pt["comp_id"]}" subtype="normal_part">', f'      <metadata key="name" value="{esc(pt["name"])}"/>',
                '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>', f'      <metadata key="extruder" value="{pt["extruder"]}"/>',
                f'      <mesh_stat face_count="{len(pt["F"])}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>',
                '    </part>']
    cfg += ['  </object>']
for pid, pname in PLATES.items():
    cfg += ['  <plate>', f'    <metadata key="plater_id" value="{pid}"/>', f'    <metadata key="plater_name" value="{esc(pname)}"/>', '    <metadata key="locked" value="false"/>',
            '    <metadata key="filament_map_mode" value="Auto For Flush"/>', f'    <metadata key="filament_maps" value="{" ".join(["1"] * N_FIL)}"/>',
            f'    <metadata key="filament_volume_maps" value="{" ".join(["0"] * N_FIL)}"/>', '    <metadata key="gcode_file" value=""/>']
    for o in objs:
        if o['plate'] == pid:
            cfg += ['    <model_instance>', f'      <metadata key="object_id" value="{o["id"]}"/>', '      <metadata key="instance_id" value="0"/>',
                    f'      <metadata key="identify_id" value="{100 + o["id"]}"/>', '    </model_instance>']
    cfg += ['  </plate>']
cfg += ['  <assemble>', '  </assemble>', '</config>', '']

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', ctypes)
    z.writestr('_rels/.rels', rels_root)
    z.writestr('3D/3dmodel.model', main)
    z.writestr('3D/_rels/3dmodel.model.rels', rels_model)
    for o in objs: z.writestr(o['path'], obj_model(o))
    z.writestr('Metadata/model_settings.config', '\n'.join(cfg))
    if proj is not None:
        z.writestr('Metadata/project_settings.config', json.dumps(proj, indent=4))
        z.writestr('Metadata/slice_info.config', '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n  <header>\n    <header_item key="X-BBL-Client-Type" value="slicer"/>\n    <header_item key="X-BBL-Client-Version" value="02.08.02.61"/>\n  </header>\n</config>\n')
for o in objs:
    print(f"plateau {o['plate']}  {o['name']:28s} position=({o['t'][0]:.1f}, {o['t'][1]:.1f})  pièces={[pt['name'] for pt in o['parts']]}")
print('écrit', OUT, OUT.stat().st_size // 1024, 'Ko')
