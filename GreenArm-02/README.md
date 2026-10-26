> **Notă pentru acest repository:** `GreenArm-02.f3d` și `GreenArm-02.step` nu sunt incluse, deoarece conțin modelul CAD oficial Waveshare ST3215. Se regenerează cu `GreenArm-02.py` după descărcarea STEP-ului furnizorului în `vendor/` (vezi [vendor/Sources.md](vendor/Sources.md)). Revizia curentă este în [../GreenArm-03](../GreenArm-03).

# GreenArm 02

**Stadiu: ansamblu CAD de dezvoltare, nu set final pentru fabricație.**

Fișierul principal este [GreenArm-02.f3d](GreenArm-02.f3d). Păstrează componentele, operațiile native, aparențele și articulațiile din Fusion. [GreenArm-02.step](GreenArm-02.step) este exportul geometric pentru alte aplicații.

- [Vedere asamblată](GreenArm-02-assembled.png), [spate](GreenArm-02-rear.png), [interior](GreenArm-02-internal.png).
- [Detaliu CAD al reductorului](Shoulder-cycloidal-cutaway.png), [STEP separat al reductorului](Shoulder-cycloidal-11to1.step).
- [Cercetarea și alegerea reductorului](Research-and-decisions.md).
- [Proveniența CAD-ului de componente](vendor/Sources.md).
- [Calculul de buget și diferența față de plafon](Budget.md).
- [Criteriile de validare și elementele mecanice încă nefinalizate](Validation-plan.md).
- CAD-audit.json: sănătatea operațiilor din Fusion. Assembly-fit-audit.json: interferențele din domeniul verificat, în poziția afișată.

Motorul NEMA23 este amplasat în trunchi; trei NEMA17 comandă baza, cotul și încheietura. Motorul cotului și cel al încheieturii sunt retrase pe segmente și transmit prin curele interne. Servo ST3215 provine din STEP-ul oficial Waveshare. Stepperele sunt reconstrucții după desene tehnice, etichetate explicit.

Reductoarele de umăr și cot au profile cicloidale originale 11:1, cu două discuri. Pinii/axele și rulmenții sunt metalici; carcasele pot fi printate. Piesele funcționale și ajustajele necesită calibrare și test termic.

## Regenerare

Directorul include punctul de intrare Fusion Scripts `GreenArm-02.py` și manifestul corespunzător. Creează un document nou; nu modifică un proiect existent. Generarea poate dura câteva minute. Dimensiunile sunt în milimetri la interfața scripturilor. Parametrii globali expuși în document sunt informativi: schimbările majore de geometrie se fac în generator și cer regenerarea modelului.

Testele matematice se rulează din acest director cu:

```sh
PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_*.py'
```

Cele 12 teste verifică geometria și interpolarea. Nu reprezintă test de sarcină, durabilitate sau precizie a unui braț fizic.
