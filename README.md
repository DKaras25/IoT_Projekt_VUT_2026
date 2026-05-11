# BPC-IoT Projekt #10 Systém monitoringu a ovládání klimatizovaného rackového systému

Tým: 
- Martin Smejkal
- Michal Horák
- David Karas

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

# Designová rozhodnutí:
V této kapitole jsou zdůvodněné rozhodnutí s ohledem na předpoklady a omezení. 

## Zvolená technologie
S ohledem na zadání jsou sbírané data odeslány na Thingsboard server. 

Na Thingsboard server jsou odesílány:
- power_kw: pro aktuální změřený výkon
- total_energy_kwh: pro kumulativná spotřebu racku. 
- temperature: pro naměřenou teplotu
- pwm: pro signál odesílaný na PWM pin. 

## Zvolený transportní a aplikační protokol
Vzhledem k umístění v serverové místnosti s předpokladem WiFi sítě bylo bylo zvolené MQTT přes WiFi na lokální Thingsboard server.

## Zvolené napájení
S ohledem na silnoproudé i datové rozvody v místnosti nebyla zvolena žádná baterie, místo toho bylo zvolené napájení ze silnoproudé sítě. 

## Zdůvodnění parametrů/postupů (např. interval vysílání, nedostatky řešení atp).



# Komponenty:
V této kapitole budou popsané navrhované komponenty použité pro správnou funkci zařízení. 

## Monitorování spotřeby racku

![Schéma zapojení pro měření proudu](/etc/img/Scheme_curr.png)

https://dratek.cz/arduino-platforma/1588-15a-ac-proudova-sonda-neinvazivni-sct-013-015.html
Pro měření proudu je použita Neinvazivní proudová sonda SCT-013-015. 

Jelikož napětí je 230V tak dále můžeme vypočítat odebraný výkon: $$P=\frac{U \cdot I_{RMS}}{1000}\qquad[W]$$

Výpočet kumulativní spotřeby se dále spočítá pomocí: $$E=E_0+\left(P\cdot \frac{\Delta t}{3600}\right)$$