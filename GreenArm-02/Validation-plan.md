# Stadiul real și verificările necesare

GreenArm 02 este un ansamblu CAD de dezvoltare. Carcasele, pozițiile motoarelor și reductoarele au geometrie reală; acest fapt nu validează performanța brațului construit.

## Caz de proiectare propus

500 g la clește și 310 mm între axa umărului și cea a încheieturii, plus distanța de la încheietură la punctul de prindere. Este un caz pentru dimensionare, nu sarcină utilă certificată. Numai obiectul de 500 g produce aproximativ 1,52 Nm la umăr pentru o distanță orizontală de 310 mm. Se adaugă masa brațului, cleștelui, motoarelor și efectul accelerației.

Nu se estimează sarcina utilă folosind doar cuplul de menținere al motorului înmulțit cu raportul. Sunt necesare curba cuplu–turație, eficiența reductorului, rigiditatea pieselor, temperatura și rezerva de accelerație.

## Verificat digital

- Profil cicloidal propriu, două discuri fazate, 12 poziții cu role, 11 lobi, raport 11:1.
- Modul matematic și interpolare NURBS verificate prin 12 teste automate.
- Modelele de motor urmează interfețe nominale din desene; nu sunt fișiere STEP originale ale fabricantului.
- Servoul este STEP oficial Waveshare, importat fără scalare. Dimensiunile sunt auditate în contextul ansamblului; coordonatele native ale pieselor interne nu reprezintă gabaritul montat.
- Raportul separat Assembly-fit-audit.json înregistrează interferențele testate în poziția afișată. Nu reprezintă analiză completă pe toată cursa.

## Înainte de printarea întregului braț

1. Alegerea exactă a variantelor cumpărate și a coșului livrat în maximum 1.000 lei.
2. Probă de ajustaj pentru rulmenți/pini și un singur reductor. Jocurile nominale de CAD trebuie calibrate pentru imprimantă, material și orientare.
3. Finalizarea prinderilor de ieșire, tensionării curelelor, lungimilor comerciale, profilului dinților, canalelor de cabluri, mecanismului de clește și șuruburilor de închidere. Curelele/fuliile actuale sunt volume pentru amplasare.
4. Verificare de coliziune pe toată cursa, verificarea stabilității pe banc și limite mecanice/electrice.
5. Măsurarea jocului, repetabilității și preciziei la clește sub sarcină. La 310 mm, o eroare de numai 0,2° în umăr produce aproximativ 1,08 mm deplasare; erorile celorlalte articulații se adaugă.
6. Test termic în carcase cu sarcină. PLA-ul decorativ nu este considerat suport termic validat pentru motoare.
7. Testarea mișcării cu accelerație și variația accelerației limitate, reglarea curentului și microsteppingului. Absența pașilor vizibili trebuie măsurată pe mecanismul real.

Nu există o garanție onestă de „fără niciun pas vizibil”, precizie milimetrică sau sarcină utilă numai din acest CAD. Acestea rămân criterii de acceptare ale prototipului fizic.
