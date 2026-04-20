# BPC-IoT Projekt #10 Systém monitoringu a ovládání klimatizovaného rackového systému

Tým: 

# Zadání:
Cílem projektu je navrhnout systém pro monitorování a ovládání klimatizovaného rackového systému s podporou proudové odběru rackového systému a teplotu uvnitř.

Jsou předpokládány:
- Umístění zařízení v serverové místnosti.
- Silnoproudé i datové rozvody jsou zřízeny.
- Součástí vybavení racku je klimatizační jednotka ovládaná signálem PWM.

![Návrh serveru](/etc/img/img1.png)

Pro monitorování spotřeby bude využitý A/D převodník s měření v určitých intervalech. Bude se zaznamenávat okamžitá spotřeba v kw a celková spotřeba v kWh (pro rozvody 230 V/50 Hz). 

V racku bude umístěný senzor teploty, který při přechodu určené teploty zapne klimatizační systém s různou intenzitou podle potřeby. 

Všechna data budou odesílána na vzdálený server Thingsboard, kde budou zobrazeny a následně bude možné s nimi pracovat. 

