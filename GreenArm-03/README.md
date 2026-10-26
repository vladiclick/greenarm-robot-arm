# GreenArm 03 — revizie cu MG996R

Revizie de proiectare, 22 octombrie 2026. Modelul are carcase cu fețe plane, muchii teșite, capace verzi plate, inele albe înguste și motoare retrase în carcase. MG996R înlocuiește ST3215 la clește. Verdele marmorat este o aproximație vizuală; lumina și lotul filamentului schimbă aspectul piesei imprimate.

## Fișiere pentru verificarea formei

- `GreenArm-03-preview.png`: vedere completă, cu toate piesele interne prezente și ascunse numai prin acoperire geometrică.
- `GreenArm-03-front.png`: vedere aproape perpendiculară pe fețele articulațiilor.
- `GreenArm-03-internal.png`: aceeași geometrie, cu piesele marcate drept capace cosmetice ascunse.
- `GreenArm-03.glb` și `GreenArm-03-internal.glb`: modele 3D pentru inspecție vizuală, în metri, cu grupuri și piese separate. Sunt modele mesh, nu fișiere CAD cu suprafețe analitice.
- `Design-spec.json`: geometria declarată, în milimetri; aceeași sursă generează previzualizările și scriptul Fusion.
- `Design-review.md`: dimensiuni și decizii de integrare.

## Schimbări mecanice incluse

Baza carcasei măsoară 130 × 116 × 78 mm, fără picioare și capete de șurub. Amprenta scade cu aproximativ 53% față de 196 × 164 mm. Grinzile centrale au secțiunea 56 × 73 mm, iar distanțele dintre axe sunt 175 și 155 mm. Nu s-au micșorat artificial motoarele sau mecanismele reductoarelor pentru a obține aceste proporții.

Patru motoare pas cu pas: un NEMA23 la umăr și trei NEMA17 pentru bază, cot și încheietură. Reperele de desen sunt STEPPERONLINE 23HS30-2804S și 17HS16-2004S1. MG996R pozițional comandă cleștele; varianta exactă aleasă și incertitudinile desenului sunt documentate în `vendor/MG996R-180-sources.md`. Modelele motoarelor și servo-ului sunt reconstrucții după desene nominale, nu fișiere originale de producător descărcate din GrabCAD.

Reductoarele cicloidale originale cu două discuri și raport 11:1 sunt păstrate la umăr și cot. Curelele au ieșiri reale din grinzile deschise la capete. Servo-ul se sprijină pe două șine separate, cu găuri alungite și stâlpi până la capacul din spate. Pivoții degetelor au punte și bucșe proprii. Capătul palmei este deschis pentru ieșirea degetelor.

## Stadiul Fusion

**Model generat și deschis în Autodesk Fusion pe22octombrie2026.** Accesul Computer Use a fost restabilit. Generatorul a terminat construirea ansamblului:12componente,4articulații și nicio eroare sau avertizare în istoricul construcției (`timeline_issues: []`).

Fișierele native exportate sunt `GreenArm-03.f3d` și `GreenArm-03.step`; `GreenArm-03-Fusion.png` este imaginea exportată din aplicație. `Fusion-run.json` păstrează rezultatul rulării. Deschiderea și construirea fără erori nu certifică lipsa coliziunilor sau funcționarea mecanismului.

`GreenArm-03.py` este intrarea pentru Fusion Scripts. Creează un document nou la fiecare rulare. Intrarea locală înregistrată `../CleanArm/CleanArm.py` indică acest generator. Fișierele native GreenArm02 sunt păstrate separat. Documentul03 este lăsat deschis în Fusion; copia F3D este salvată local, independent de salvarea unui proiect în cloud.

## Limite înainte de imprimare

Aceasta este o revizie pentru evaluarea formei și a integrării. Nu este o eliberare pentru fabricație. Rămân de verificat:

- Coliziunile întregului ansamblu, limitele mișcării și accesul la montaj în Fusion.
- Dimensiunile exemplarului cumpărat de MG996R, poziția axului, canelurile și prinderile; șinele permit reglaj, dar nu certifică potrivirea.
- Dinții și legătura dintre roțile cleștelui, profilul și fixarea fuliilor, tensionarea și lungimile curelelor, fixările cuplajelor, traseele cablurilor. Piesele numite `envelope`, `pending` sau `routing study` sunt marcate explicit în model.
- Alimentarea, răcirea, calculul sarcinii și prototipul fizic al articulațiilor. Cuplul de blocare al unui motor/servo nu este sarcina utilă a brațului. Fluiditatea și precizia nu sunt garantate printr-o randare.
- **Coșul complet sub 1.000 lei rămâne neconfirmat.** Estimarea GreenArm 02 depășea plafonul; înlocuirea servo-ului nu demonstrează încadrarea noii configurații. Nu s-au cumpărat piese.

## Reproducerea verificării locale

Cu Python 3.10+ și folderul curent setat în rădăcina proiectului:

```sh
PYTHONPATH=outputs/GreenArm-03 python3 -m unittest discover -s outputs/GreenArm-03/tests
PYTHONPATH=outputs/GreenArm-03 python3 outputs/GreenArm-03/preview_geometry.py
PYTHONPATH=outputs/GreenArm-03 python3 outputs/GreenArm-03/export_glb.py
```

`render_cpu.py` folosește NumPy și Pillow, fără GPU. Mesh-urile sunt verificate ca fiind închise și cu volum pozitiv; aceasta verifică validitatea suprafețelor fiecărei piese, nu absența coliziunilor între piese.
