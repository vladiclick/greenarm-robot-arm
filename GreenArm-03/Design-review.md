# GreenArm 03 — revizia arhitecturii

Direcția aleasă este un braț industrial compact, cu fețe plane, muchii teșite, motoare ascunse și capace de service detașabile. Formele umflate și capacele albe supradimensionate din GreenArm 02 sunt înlocuite cu grinzi drepte și capace verde închis, aproape la nivelul carcasei, cu un inel alb subțire.

## Dimensiuni de proiectare

Toate valorile sunt în milimetri. Coloana propusă provine din specificația geometrică comună GreenArm 03, nu din măsurători ale unui ansamblu Fusion final sau din ajustaje validate.

| Zonă | GreenArm 02 — reper | GreenArm 03 — propunere |
|---|---:|---:|
| Bază, lungime × lățime × înălțime | 196 × 164 × 85 | 130 × 116 × 78, fără picioare TPU și capete de șurub |
| Trunchi, lățime pe direcția axei umărului | aproximativ 124 | 113, dictată de integrarea NEMA23 |
| Înălțime în zona mediană a grinzilor | aproximativ 70 | 56 |
| Lățime transversală a grinzilor | aproximativ 86–110 | 73 în zona motorului |
| Distanță între axele umăr–cot | 165 | 175 |
| Distanță între axele cot–încheietură | 145 | 155 |
| Diametru exterior reductor umăr | 98 | 98, păstrat exact |
| Diametru exterior reductor cot | 76 | 76, păstrat exact |
| Carcasă palmă MG996R180, fără degete și hardware | nerelevantă pentru vechiul servo | 104 × 54 × 56; secțiunea îngustă din zona servoului are lățime 34 |

Cei 10 mm suplimentari pe fiecare segment oferă loc pentru separarea volumelor și o proporție mai suplă. Nu reprezintă o promisiune de performanță: distanța suplimentară poate crește momentul cerut la umăr. Carcasa palmei ocupă coordonatele locale x = −16…88, y = −27…27 și z = −25…31. Secțiunea îngustă de 34 mm nu este lățimea întregii palme. Aceste anvelope nu substituie desenul tehnic al exemplarului MG996R180 cumpărat.

## Integrare mecanică

- Baza conține motorul NEMA17 și transmisia de rotație; noua amprentă cere verificarea fuliei, rulmentului, conectorilor și accesului la șuruburi.
- NEMA23 rămâne în trunchi. Motoarele NEMA17 pentru cot și încheietură rămân retrase în segmente și transmit prin curele interne; nu sunt mutate imaginar în bază fără o transmisie prin articulații.
- Grinzile sunt secțiuni plane teșite, cu capace plane separate, șine pentru compartimentul motorului deschis la capete, urechi de sprijin separate și o punte de pivot ancorată în spate. Lățimea de 73 mm este o țintă de integrare pentru motor, ax, montaj și curea; se confirmă pe geometria completă.
- Diametrele reductoarelor nu se reduc cosmetic. Capacele ascund mecanismul cu adaos minim și păstrează accesul la fixări.
- MG996R180 comandă cleștele; degetele drepte au suprafețe de prindere înlocuibile. Încărcarea degetelor trebuie sprijinită mecanic și verificată separat de angrenajul servoului.

## Verificări obligatorii înainte de fabricație

Trebuie măsurate anvelopele finale și verificate interferențele, traseele curelelor, tensionarea, rulmenții, accesul de montaj și cablurile. Validarea mișcării și a limitelor este în așteptare pentru toate articulațiile. Calculul de sarcină și testele pe o articulație fizică sunt necesare pentru cuplu, încălzire, joc, fluiditate și precizia la clește.

Plafonul de **1.000 lei rămâne neconfirmat**. Estimarea vechii configurații depășea plafonul; schimbarea servoului și reducerea carcaselor nu demonstrează încadrarea. Este necesar un BOM complet, cu transport și consumabile.

## Stadiul livrării

Accesul Computer Use a fost restabilit, iar generatorul a fost rulat în Fusion pe22octombrie2026. Modelul03 este deschis în aplicație; F3D,STEP și imaginea nativă sunt exportate. Rularea raportează12componente,4articulații și zero probleme în istoricul construcției. Verificarea întregii mișcări, mecanismul cleștelui, ajustajele pieselor cumpărate, sarcina, fluiditatea și încadrarea în1.000lei rămân neconfirmate. Fișierele nu sunt declarate pregătite pentru fabricație.
