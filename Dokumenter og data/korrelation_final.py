# -*- coding: utf-8 -*-
"""Endelig korrelation: Eo_aekv(T, Eu) fra det samlede VejDim-datasaet.

Reproducerer Fase B (Korrelation_trafikklasse_Eo.md). Koeres fra repo-roden med
projektets .venv:  .venv\\Scripts\\python.exe "Dokumenter og data\\korrelation_final.py"

Laeser standardkoerslerne (VEJDIM_KOERSLER_STANDARD_RAEKKER) og appens live
T_BASIS_TABLE fra core/data.py. Bemaerk: scriptet bruger de INDBYGGEDE
standardkoersler — aendringer, du har lavet i appens redigerbare tabel, ligger i
appens egen gemte fil og indgaar ikke her. Ingen skrivning; printer
korrelations- og reduktionstabellen samt konsistenschecks.
"""
import math, sys, os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from core.data import (
    T_BASIS_TABLE, EO_KOLONNER, VEJDIM_KOERSLER_STANDARD_RAEKKER,
)

NU = 0.35
A = 150.0                 # pladeradius mm (Ø300)
P = 0.20                  # MPa (Eo lineaer i p)
E_BASE_DIAGRAM = 300.0    # antaget granulaer basemodul i diagrammet (MSL/SG-kvalitet)

def num(v):
    if v in (None, ""):
        return None
    return float(str(v).replace(",", "."))

# Samlet datasaet: standardkoerslerne, opslag paa (T, Eu)
data = {
    (r["T"], int(r["eu"])): {
        "t_SG_mm": r["t_SG_mm"],
        "t_BL_mm": r["t_BL_mm"],
        "t_bundet_mm": r["t_bundet_mm"],
    }
    for r in VEJDIM_KOERSLER_STANDARD_RAEKKER
}

def interp_eo(eu, tyk, felt="uarmeret"):
    row = T_BASIS_TABLE[eu]
    pts = sorted([(eo, row[eo][felt]*10.0) for eo in EO_KOLONNER if row[eo][felt] is not None],
                 key=lambda p: p[1])
    if not pts: return None, "raekke tom"
    if tyk < pts[0][1]: return None, f"under Eo30 ({pts[0][1]:.0f})"
    if tyk > pts[-1][1]: return None, f"over Eo150 ({pts[-1][1]:.0f})"
    for (e1,t1),(e2,t2) in zip(pts, pts[1:]):
        if t1 <= tyk <= t2:
            return (e1 + (tyk-t1)/(t2-t1)*(e2-e1)) if t2>t1 else float(e1), "ok"
    return None, "?"

def opslag(eu, eo_x, felt):
    row = T_BASIS_TABLE[eu]
    pts = [(eo, row[eo][felt]*10.0) for eo in EO_KOLONNER if row[eo][felt] is not None]
    if not pts or eo_x < pts[0][0] or eo_x > pts[-1][0]: return None
    for (e1,t1),(e2,t2) in zip(pts, pts[1:]):
        if e1 <= eo_x <= e2:
            return t1 + (eo_x-e1)/(e2-e1)*(t2-t1)
    return None

def w_bouss(z, E):
    R = math.sqrt(A*A + z*z)
    return (P*(1+NU)*A/E) * (A/R + (1-2*NU)*(R-z)/A)

def overflademodul(lag, E_hs):
    w = 0.0
    for i,(h,E) in enumerate(lag):
        z0 = sum(hj*(Ej/E)**(1/3) for hj,Ej in lag[:i])
        w += w_bouss(z0, E) - w_bouss(z0+h, E)
    z = sum(hj*(Ej/E_hs)**(1/3) for hj,Ej in lag)
    w += w_bouss(z, E_hs)
    return 2*(1-NU*NU)*P*A / w

def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"{'T':4}{'Eu':>4}{'bund':>6}{'SG':>5}{'BL':>5}{'ubund':>6}"
          f"{'Eo_aekv':>8}{'zone':>16}{'Eo_1lag':>8}{'Eo_2lag':>8}{'arm1':>6}{'red%':>6}")
    ud = []
    for T in ["T1","T2","T3","T4","T5","T6"]:
        for eu in [5,10,15,20,30,40]:
            r = data[(T, eu)]
            sg, bl = num(r["t_SG_mm"]), num(r["t_BL_mm"])
            bund = num(r["t_bundet_mm"]) or 0
            ub = sg + bl
            eo_x, zone = interp_eo(eu, ub)
            eo1 = overflademodul([(ub, E_BASE_DIAGRAM)], float(eu))
            eo2 = overflademodul([(sg,300.0),(bl,100.0)], float(eu))
            arm = opslag(eu, eo_x, "1_lag") if eo_x else None
            red = (ub-arm)/ub*100 if arm else None
            ud.append((T,eu,ub,eo_x,zone,eo1,eo2,arm,red))
            f = lambda v,w,d=1: (f"{v:{w}.{d}f}" if v is not None else " "*(w-1)+"-")
            print(f"{T:4}{eu:>4}{bund:>6.0f}{sg:>5.0f}{bl:>5.0f}{ub:>6.0f}"
                  f"{f(eo_x,8)}{zone:>16}{eo1:>8.0f}{eo2:>8.0f}{f(arm,6,0)}{f(red,6)}")
        print()

    # konsistenstjek
    par1 = [(x,e1) for _,_,_,x,z,e1,e2,_,_ in ud if x is not None]
    par2 = [(x,e2) for _,_,_,x,z,e1,e2,_,_ in ud if x is not None]
    r1 = [e/x for x,e in par1]; r2 = [e/x for x,e in par2]
    print(f"Eo_1lag(E=300)/Eo_aekv (n={len(par1)}): middel {sum(r1)/len(r1):.2f} "
          f"[{min(r1):.2f}-{max(r1):.2f}]")
    print(f"Eo_2lag(SG+BL)/Eo_aekv (n={len(par2)}): middel {sum(r2)/len(r2):.2f} "
          f"[{min(r2):.2f}-{max(r2):.2f}]")
    # kalibrer implicit basemodul
    for Eb in [150,200,250,300,350,400]:
        rr = [overflademodul([(ub, float(Eb))], float(eu))/x
              for T,eu,ub,x,z,e1,e2,arm,red in ud if x is not None]
        print(f"  E_base={Eb}: Eo_1lag/Eo_aekv middel {sum(rr)/len(rr):.2f} [{min(rr):.2f}-{max(rr):.2f}]")

    reds = [red for *_ ,arm,red in ud if red is not None]
    print(f"\nReduktion (1 net, ref): middel {sum(reds)/len(reds):.0f}% "
          f"[{min(reds):.0f}-{max(reds):.0f}%], n={len(reds)}")

if __name__ == "__main__":
    main()
