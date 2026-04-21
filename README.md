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

Všechna data budou odesílán a na vzdálený server Thingsboard, kde budou zobrazeny a následně bude možné s nimi pracovat. 

# Komponenty:
V této kapitole budou popsané navrhované komponenty použité pro správnou funkci zařízení. 

## Monitorování spotřeby racku
Pro měření proudu je použita Neinvazivní proudová sonda SCT-013. 

Jelikož napětí je 230V tak dále můžeme vypočítat odebraný výkon: $$P=\frac{U \cdot I_{RMS}}{1000}\qquad[W]$$

Kvůli ukončení sondy SCT-013 v TTRS je použita TTRS 3.5mm Jack Breakout Board (TTRS 3.5mm Jack Breakout Headphone Video Audio MP3 Jack Professional)

Výpočet kumulativní spotřeby se dále spočítá pomocí: $$E=E_0+\left(P\cdot \frac{\Delta t}{3600}\right)$$