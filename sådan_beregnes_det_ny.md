Trinvis beregning, baseret på designmanualer og intern forsøgsdata fra Byggros:

Der beregnes en bærelagstykkelse, ud fra 1 eller 2 lag armering, ud fra et reference net. Den beregnede bærelagstykkelse korrigeres for friktionsvinkler forskellig fra φ = 35° samt effektindeks af forskellige geonet.

1. 	Bundmodulet Eu, vælges eller beregnes via sammenhæng med Cv
2. 	Krav til overflademodulet E0 vælges, alt efter belastningsklasse
3. 	Der laves opslag i designdiagrammerne i forhold til valg af Bund- og overflademodul, til fastlæggelse af bærelagstykkelse, uarmeret og armeret med 1-2 lag geonet. 
	Der laves lineær interpolation, hvis det valgte/beregnede Eu ikke er en direkte tabelværdi.
4. 	På baggrund af opslaget/interpolation, bestemmes basistykkelsen, T_basis:
		* Uarmeret: xx mm
		* 1 lag armering (reference net): xx mm
		* 2 lag armering (reference net): xx mm
5. 	Korrektionsfaktorer for friktionsvinkel og effektivitet af geonet
	Friktionsvinkel:
	Friktionsvinkel-korrektionen justerer basis-tykkelsen fra opslagstabellen, som er baseret på et standardmateriale med φ ≈ 35°. For hver grad over 35° reduceres tykkelsen med 2 %, og for φ under 35° øges tykkelsen tilsvarende.
	I standard beregningen sættes bærelagets friktionsvinkel φ = 35°.
	I den brugerdefinerede beregning beregnes en vægtet friktionsvinkel ud fra den angivne procentvægtning, eller lagtykkelser af lagene, som er prædefinerede materialer med forskellige friktionsvinkler.
	   
		Eksempel på beregning i brugerdefineret tilstand, ud fra lagtykkelser:
		
		📐 φ-beregning fra materialelagene

		Lag	Materiale	Tykkelse	φ (°)	Vægtet bidrag
		1	SG I 0-32	300 mm		40,0	12000
		2	Bundsand	450 mm		35,0	15750
		
		Vægtet φ = Σ(tᵢ × φᵢ) / Σ(tᵢ) = 27750 / 750 = 37,00°

		φ-korrektion = −0,02 × (φ − 35°) = −0,02 × (37,00 − 35) = −0,0400 (dvs der reduceres −4,00 % af basistykkelsen, T_basis)
	
	Net-korrektion:
	Designdiagrammerne bruger GS-GRID SX160 / E'GRID T6 eller Tensar TriAx TX160 som reference-armering (effektindeks 100). Hvis der er valgt en anden armering, skaleres tykkelsen op eller ned med op til 20% alt efter produkt. 
	En positiv korrektionsfaktor = tykkere bærelag (mindre effektiv armering), negativ = tyndere bærelag (mere effektiv armering).
		
6.	Den endelige bærelagstykkelse beregnes som: T_armeret = T_basis × (1 + φ-kor + net-kor)

		