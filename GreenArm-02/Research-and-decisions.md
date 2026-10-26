# GreenArm 02 — cercetare și decizii de proiectare

Scopul acestei revizii este un braț compact cu motoare integrate în volum, carcase verde marble și alb și un reductor cicloidal proiectat explicit. Cerințele de mișcare rapidă, fluiditate și precizie rămân ținte care trebuie măsurate pe hardware. Modelul CAD poate verifica geometria și montajul; nu poate certifica uzura, temperatura, vibrațiile sau precizia unui print fizic.

## Ce am comparat

| Referință | Dovezi disponibile | Utilitate pentru GreenArm |
|---|---|---|
| Faze4, Source Robotics | Braț complet, instrucțiuni, BOM, STL și STEP; 911 stele și 152 fork-uri GitHub la verificare | Referință relevantă pentru integrarea cablurilor și articulațiilor în carcase |
| Roozing & Roozing, IROS 2022 | Geometrie publicată, CAD, generator și măsurători experimentale pentru un cicloidal 11:1 | Bază tehnică pentru parametrizare și sprijinirea componentelor |
| Roozing & Roozing, ICRA 2024 | Comparație experimentală între reductoare pe role și reductoare cu profil interior conjugat | Arată compromisurile între cost, complexitate, joc și uzură |
| HowToMechatronics | Tutorial de construcție, formule, STEP, STL și demonstrație 15:1 | Explică o implementare accesibilă cu două discuri și rulmenți |
| James Bruton, openDog V3 | CAD, BOM și software publicate | Referință de integrare și fabricație, pentru o aplicație diferită |
| RepRap Ltd | Generator FreeCAD pentru cicloide contractate | Referință pentru parametrizare și profiluri, nu un test al acestui braț |

[Faze4](https://github.com/Source-Robotics/Faze4-Robotic-arm) este un exemplu cunoscut de braț cu transmisii cicloidale și cabluri ascunse. Autorul indică aproximativ 15 kg și un cost sub 1.000 USD. Dimensiunea și costul îl fac nepotrivit pentru copiere integrală în proiectul de 1.000 lei. Popularitatea confirmă interesul comunității, nu performanța unei versiuni modificate. Fișierul actual [LICENSE](https://github.com/Source-Robotics/Faze4-Robotic-arm/blob/master/LICENSE) este CERN-OHL-S-2.0, deși README păstrează o mențiune contradictorie despre MIT. GreenArm folosește geometrie proprie, nu piese Faze4 copiate.

În [studiul IROS 2022](https://ris.utwente.nl/ws/portalfiles/portal/295490006/3D_printable_low_reduction_cycloidal_gearing_for_robotics.pdf), un reductor 11:1 a fost testat pentru joc, rigiditate și eroare de transmisie. Sunt relevante arborele de intrare sprijinit suplimentar, ieșirea cu rulment propriu și legarea capetelor pinilor. Prototipul autorilor avea aproximativ 0,35° joc maxim și 0,92° eroare RMS de transmisie. Costul declarat al reductorului era 98 EUR, separat de motor și electronică. Aceste rezultate aparțin acelui prototip; nu sunt specificații GreenArm. [CAD și generatorul](https://github.com/geez0x1/2022-cycloidal-drive) sunt publicate sub MIT.

[Continuarea ICRA 2024](https://ris.utwente.nl/ws/portalfiles/portal/459833656/Experimental_comparison_of_pinwheel_and_non-pinwheel_designs_of_3D-printed_cycloidal_gearing_for_robotics.pdf) raportează costuri de 98 EUR pentru versiunea pe role și 65 EUR pentru cea cu profil interior. Rezultatele sunt apropiate; versiunea fără role are 0,30° joc maxim și 0,56° eroare RMS. După zece ore de test, jocul crește aproximativ de două ori, cu uzură legată inclusiv de imperfecțiunile printării. Concluzia utilă este că nici un design publicat și testat nu justifică promisiunea de joc zero pentru orice imprimantă și material.

[HowToMechatronics](https://howtomechatronics.com/how-it-works/what-is-cycloidal-driver-designing-3d-printing-and-testing/) prezintă o variantă 15:1: 16 role, cerc de pas de 90 mm, rulmenți periferici de 13 mm și excentricitate de 1,5 mm. Tutorialul explică folosirea a două discuri pentru echilibrarea mișcării excentrice. [Videoul oficial](https://www.youtube.com/watch?v=OsS9-FzKN6s) avea aproximativ 1,23 milioane de vizualizări la verificare. Este o demonstrație utilă și populară; nu reprezintă un clasament universal sau o certificare a preciziei.

[openDog V3](https://github.com/XRobots/openDogV3) avea 489 stele și 105 fork-uri, cu fișiere sub MIT. Utilizează o arhitectură pentru un robot patruped, deci nu dimensionează direct umărul nostru. [RepRap Ltd](https://reprapltd.com/cycloidal-gearboxes/) explică generarea parametrică și utilizarea rulmenților în locul contactelor cu frecare de alunecare; [repository-ul](https://github.com/RepRapLtd/RobotComponents) este GPL-3.0. Pentru principiul industrial cu două excentricități opuse există și [documentația Nabtesco](https://www.nabtesco.de/fileadmin/04_Service/05_Downloads/01_Produktkataloge/RV_Katalog_EN.pdf).

## Varianta aleasă pentru modelare

Am ales un reductor original cu o singură treaptă, **11:1 și două discuri**, pentru a păstra un compromis între cuplu, viteză, spațiu și numărul componentelor. Raportul nu este o dovadă că motorul ales va atinge viteza sau sarcina dorită. Față de 30:1, 11:1 cere mai puține rotații ale motorului pentru aceeași mișcare a articulației; cuplul disponibil trebuie calculat la turația efectivă.

| Parametru nominal | Valoare în design |
|---|---:|
| Role fixe periferice | 12 |
| Lobi pe fiecare disc | 11 |
| Raport cinematic | 11:1, sens invers față de intrare |
| Raza cercului rolelor | 40 mm |
| Role | Rulmenți 623ZZ, diametru exterior nominal 10 mm |
| Raza rolelor | 5 mm |
| Excentricitate | 1,5 mm |
| Faza excentricităților | 180° |
| Pini de ieșire | Metal, diametru 4 mm |
| Raza cercului pinilor de ieșire | 22 mm |
| Raza nominală a găurilor de ieșire | 3,65 mm |
| Rulment de intrare excentrică | 6801 |

Găurile de ieșire includ raza pinului de 2 mm, cursa excentrică de 1,5 mm și un adaos radial inițial de 0,15 mm. Acest adaos este un punct de pornire pentru cupoane de calibrare, nu o toleranță validată. Poate produce joc prea mare sau poate necesita ajustare după măsurarea pieselor reale.

Profilul este calculat din parametrii cicloidali, cu formule documentate în [tutorialul oficial SOLIDWORKS](https://blogs.solidworks.com/products/solidworks/building-a-cycloidal-drive-with-solidworks/), care citează lucrarea Shin/Kwon. Nu este o roată cu lobi desenați aproximativ. Verificarea geometrică urmărește conturul închis, distanțele între elemente și mișcarea ideală. Nu reprezintă analiză de contact, analiză structurală sau test de durabilitate.

Pinii și axele rămân metalici. Pinii trebuie fixați și sprijiniți, evitând solicitarea unor șuruburi lungi în consolă. Ieșirea articulației trebuie susținută separat, astfel încât axul motorului să nu poarte direct greutatea brațului. Faza discurilor și poziția găurilor trebuie tratate împreună; duplicarea vizuală a unui disc nu verifică funcționarea mecanismului.

## Motoare ascunse și carcase

Motoarele sunt mutate spre interiorul volumului brațului și spre bază, în măsura permisă de cinematica transmisiei. Curelele interne pot transmite mișcarea către excentrice, permițând un aspect compact și reducerea masei purtate spre clește. Această amplasare cere verificarea tensiunii curelei, a sarcinilor pe rulmenți și a accesului pentru reglaj. O curea ascunsă trebuie să poată fi înlocuită fără distrugerea carcasei.

Înclinarea motorului la un anumit unghi nu îi crește singură cuplul. Avantajul real poate apărea dacă mută masa mai aproape de umăr sau permite o transmisie și un suport mai bune. Capacele trebuie să fie detașabile, cu spațiu pentru conectori, cabluri și disiparea căldurii. Aspectul exterior nu trebuie obținut prin blocarea motorului într-o cavitate fără acces.

Verde marble și alb definesc piesele cosmetice. Textura trebuie să semene cu filament printat: suprafață predominant mată, particule și straturi fine, fără vene mari de piatră lucioasă. Această alegere estetică nu certifică materialul pentru discuri sau scaune de rulmenți. Piesele de uzură vor fi evaluate separat pentru precizie dimensională, frecare, temperatură și rezistență.

## Ce rămâne de demonstrat

Bugetul de 1.000 lei rămâne un risc: costurile academice citate sunt pentru câte un reductor, nu pentru braț complet. Nu există încă un BOM GreenArm cotat și verificat cu transport. Nu declarăm că proiectul se încadrează până când motoarele, driverele, sursa, rulmenții, pinii, curelele, șuruburile și filamentul sunt însumate.

Prototipul unei articulații trebuie măsurat pentru joc la schimbarea sensului, cuplu în mișcare, temperatură și vibrații. Precizia se verifică la clește, sub sarcină, în mai multe poziții. La 200 mm, doar 0,35° corespund aproximativ la 1,22 mm deplasare; erorile mai multor articulații se pot combina. Designul selectat este o bază geometrică documentată și adaptabilă. Nu este încă un mecanism validat ca fiind „cel mai bun”, fără joc sau cu fluiditate garantată.
