"""
================================================================================
 vejdim_ubundne_lag.py
 -------------------------------------------------------------------------------
 Parametrisk tilbageberegning af de UBUNDNE lag (ubundet baerelag + bundsikring)
 efter VejDims analytisk-empiriske metode (Vejregel-haandbog jan. 2022 / aug. 2025).

 IDE:  saet den faste opbygning EEN gang i CONFIG, og kald derefter
       thicknesses(E_underbund, frostklasse) for at faa (SG, BL) ud.
       Alt andet (asfalt, baerelag-materiale, bundsikrings-materiale, trafik)
       holdes konstant.

 MOTOR (valideret): Odemark aekvivalent tykkelse + Busch-2014 f-faktor +
       Boussinesq spaending/toejning. Reproducerer Bolet & Busch's regneeksempel
       (Figur 43) til praktisk talt eksakte vaerdier:
          he = 353 mm | f = 1.10 | R = 388 mm | eps = -120 ustr | sigma_BL = 0.028 MPa

 VIGTIG NOTE om SG-tykkelsen:
   I Odemark-metoden afhaenger spaendingen paa TOP af et lag kun af lagene
   OVENOVER. Derfor er SG-tykkelsen (som styres af at beskytte bundsikringen)
   UAFHAENGIG af underbundens E. Hele E-afhaengigheden ligger i BUNDSIKRINGEN
   - baade via frost-koblingshojden og via underbundsbeskyttelsen.
   Den fulde VejDim bruger en koblet lineaerelastisk model, hvor en stivere
   underbund kan give en lille forhojelse af SG (jf. MMOPP-brugervejledningen);
   dette vaerktoej giver foerste-ordens minimumstykkelser.
================================================================================
"""
import math

# ----------------------------- MOTOR (rør ikke) ------------------------------
P   = 60_000.0                          # N   - 6-tons cirkulaer enkeltlast (Ae10)
p0  = 0.70e6                            # Pa  - kontakttryk
a_mm= math.sqrt(P/(math.pi*p0))*1000    # mm  - kontaktradius (~165 mm)
nu  = 0.35

def _Ecomb(layers):                     # vaegtet E af bundne dellag  [16]
    num = sum(h*E**(1/3) for h, E in layers); den = sum(h for h, _ in layers)
    return (num/den)**3
def _f(he):                             # Busch 2014 korrektionsfaktor [27]
    return 0.80 + 0.98*(he/a_mm)**(-1.54)
def _sig_top(above, Et):                # lodret trykspaending [Pa] paa top af lag m. modul Et
    he = sum(h*(E/Et)**(1/3) for h, E in above); R = _f(he)*he/1000
    return 3*P/(2*math.pi*R**2)
def _eps_asph(Hb, Eb, Ebelow):          # vandret traektoejning i underside asfalt
    he = Hb*(Eb/Ebelow)**(1/3); R = _f(he)*he/1000
    return -((1+nu)*(1+2*nu)*P)/(4*math.pi*R**2*Ebelow*1e6)
def _sig_allow(E, N):                   # tilladelig trykspaending [Pa]  [28]
    return 0.086*(E/160)**1.06*(N/1e6)**(-0.25)*1e6
def _eps_allow(N):                      # tilladelig asfalttoejning      [35]
    return -0.000250*(N/1e6)**(-0.191)

# Frost-koblingshojde, Figur 5.3 [mm]; None = ingen fast hojde (kun baereevne)
KOBLINGSHOJDE = {
    'frostfarlig':  {'T0':500,'T1':500,'T2':700,'T3':800,'T4':900,'T5':900,'T6':900,'T7':900},
    'frosttvivlsom':{'T0':400,'T1':400,'T2':500,'T3':600,'T4':700,'T5':700,'T6':700,'T7':700},
    'frostsikker':  {tk: None for tk in 'T0 T1 T2 T3 T4 T5 T6 T7'.split()},
}

def dimension(bound, E_SG, E_BL, E_underbund, N, trafikklasse, frostklasse, draenet=False):
    """Returnerer dict med SG- og BL-tykkelse samt diagnostik."""
    Eb = _Ecomb(bound); Hb = sum(h for h, _ in bound)
    # --- kriterier der KUN afhaenger af det bundne lag (uafh. af underbund) ---
    eps   = _eps_asph(Hb, Eb, E_SG);  ok_asfalt = eps   >= _eps_allow(N)
    sigSG = _sig_top(bound, E_SG);    ok_SGtop  = sigSG <= _sig_allow(E_SG, N)
    # --- SG: spred lasten saa spaending paa TOP af BL er ok (uafh. af underbund) ---
    SG = 100
    while SG < 1500 and _sig_top(bound+[(SG, E_SG)], E_BL) > _sig_allow(E_BL, N):
        SG += 1
    # --- BL strukturelt: beskyt underbunden (afhaenger af underbundens E) ---
    BLs = 0
    while BLs < 2500 and _sig_top(bound+[(SG, E_SG), (BLs, E_BL)], E_underbund) > _sig_allow(E_underbund, N):
        BLs += 1
    # --- frost ---
    kob = KOBLINGSHOJDE[frostklasse][trafikklasse]
    if kob is not None and draenet and frostklasse != 'frostsikker':
        kob -= 100
    BLf = 0 if kob is None else max(0, kob - Hb - SG)
    BL  = max(BLs, BLf, 200)            # 200 mm = absolut min for bundsikring (Fig. 6.5)
    gov = 'frost' if BLf >= max(BLs, 200) else ('underbund' if BLs >= 200 else 'min 200 mm')
    return dict(E_bundet=round(Eb), H_bundet=Hb,
                eps_asfalt=round(eps*1e6), ok_asfalt=ok_asfalt,
                sigma_topSG=round(sigSG/1e6, 3), ok_SGtop=ok_SGtop,
                SG=SG, BL=BL, total=Hb+SG+BL,
                BL_struktur=BLs, BL_frost=BLf, BL_styres_af=gov,
                SG_lift=math.ceil(SG/250), BL_lift=math.ceil(BL/300))

# =============================================================================
#  CONFIG  -  saet din faste opbygning her; aendr derefter kun E_underbund
# =============================================================================
# Bundet lag, dybdekorrekt E-split ved 100 mm (top: t=30C, under: t=25C, Fig. 6.2)
#   40 AB 2000 (0-40, E=2000) + 40 ABB 3000 (40-80, E=3000)
#   + 150 GAB I 3000 (80-100 -> 20mm@3000 ; 100-230 -> 130mm@5000)
BOUND        = [(40, 2000), (40, 3000), (20, 3000), (130, 5000)]
E_SG         = 300      # SG II
E_BL         = 100      # BL II, U <= 3
N            = 3.6e6    # T5, 20 aar (NAe10/aar 180.000 x 20)
TRAFIKKLASSE = 'T5'
DRAENET      = False

def thicknesses(E_underbund, frostklasse):
    """Det 'lette' kald: giv E + frostklasse -> faa (SG, BL) i mm."""
    r = dimension(BOUND, E_SG, E_BL, E_underbund, N, TRAFIKKLASSE, frostklasse, DRAENET)
    return r['SG'], r['BL']

if __name__ == '__main__':
    print(f"Bundet lag: {sum(h for h,_ in BOUND)} mm, vaegtet E={_Ecomb(BOUND):.0f} MPa")
    print(f"Asfaltkriterium (uafh. af underbund): "
          f"{_eps_asph(sum(h for h,_ in BOUND), _Ecomb(BOUND), E_SG)*1e6:.0f} / {_eps_allow(N)*1e6:.0f} ustr\n")
    print(f"{'frostklasse':<14}{'E_und':>6}{'koblh':>7} | {'SG':>4}{'BL':>5}{'total':>7} | "
          f"{'BL styres af':<12}{'lift SG/BL':>11}")
    print('-'*68)
    for frost, E in [('frostfarlig',20), ('frosttvivlsom',40), ('frostsikker',100),
                     ('frosttvivlsom',30), ('frostsikker',70)]:
        r = dimension(BOUND, E_SG, E_BL, E, N, TRAFIKKLASSE, frost, DRAENET)
        kob = '-' if r['BL_frost'] == 0 and KOBLINGSHOJDE[frost][TRAFIKKLASSE] is None else KOBLINGSHOJDE[frost][TRAFIKKLASSE]
        print(f"{frost:<14}{E:>6}{str(kob):>7} | {r['SG']:>4}{r['BL']:>5}{r['total']:>7} | "
              f"{r['BL_styres_af']:<12}{str(r['SG_lift'])+'/'+str(r['BL_lift']):>11}")