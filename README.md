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
V této kapitole jsou zdůvodněna klíčová návrhová rozhodnutí s ohledem na předpoklady, omezení a požadavky cílového prostředí.

## Zvolená technologie
Zadání předpokládá umístění zařízení v serverové místnosti, kde jsou standardně zřízeny datové i silnoproudé rozvody. Na základě tohoto předpokladu byla jako komunikační technologie zvolena síť Wi-Fi (IEEE 802.11).

Důvod volby: V prostředí serverovny je Wi-Fi síť běžně dostupná a nabízí vysokou přenosovou rychlost s minimální latencí. To je klíčové pro včasnou reakci na teplotní výkyvy a plynulé řízení klimatizace. Použití LPWAN technologií (LoRaWAN, Sigfox) by zde bylo neefektivní kvůli datovým omezením a nutnosti okamžité odezvy systému. Naměřená data jsou přes místní síť agregována a odesílána na vzdálený server Thingsboard.

Odesílaná telemetrie obsahuje následující parametry:
- power_kw: okamžitý naměřený příkon rackové jednotky v kW
- total_energy_kwh: celková kumulativní spotřeba elektrické energie v kWh
- temperature: aktuální teplota uvnitř rackového systému v °C
- pwm: aktuální hodnota buzení klimatizační jednotky vyjádřená v procentech

## Zvolený transportní a aplikační protokol
Pro transportní vrstvu byl zvolen protokol TCP a nad ním aplikační protokol MQTT.

Důvod volby: Jelikož zařízení operuje v lokální Wi-Fi síti s trvalým napájením, není nutné striktně minimalizovat režii (overhead) přenášených paketů, jak by tomu bylo u bateriově napájených senzorů. Výhody protokolu MQTT v tomto řešení jasně převažují:

1. Obousměrná komunikace: Umožňuje trvalé spojení se serverem, což je nezbytné pro okamžité zachycení vzdálených RPC příkazů z Thingsboardu (vzdálené spuštění klimatizace a vynulování kumulativní spotřeby).
2. Spolehlivost: Využití spojového protokolu TCP zaručuje spolehlivé doručení datových paketů.
3. Nativní integrace: Platforma Thingsboard protokol MQTT plně a nativně podporuje, což zjednodušuje formátování zpráv (JSON) a správu zařízení.

Jako odlehčená alternativa by přicházel v úvahu protokol CoAP (běžící na nespojovém UDP), nicméně pro daný případ použití s nutností okamžitého příjmu řídicích povelů je MQTT vhodnější architektonickou volbou.

## Zvolené napájení
S ohledem na přítomnost stabilních silnoproudých rozvodů (230 V / 50 Hz) v rackové skříni bylo zvoleno trvalé síťové napájení (realizované pomocí standardního AC/DC adaptéru na 5 V pro napájení řídicí desky).

Důvod volby: Implementace napájecí baterie by v tomto uspořádání nedávala ekonomický ani technický smysl, jelikož by vyžadovala pravidelnou údržbu. Trvalé napájení ze sítě navíc umožňuje ponechat Wi-Fi modul neustále aktivní a připravený přijímat povely pro klimatizaci. Z tohoto důvodu nebyly implementovány režimy hlubokého spánku mikrokontroléru (Deep Sleep), které by znemožňovaly plynulou integraci spotřeby a okamžité zásahy do chlazení

## Zdůvodnění parametrů/postupů (např. interval vysílání, nedostatky řešení atp).



# Komponenty:
V této kapitole budou popsané navrhované komponenty použité pro správnou funkci zařízení. 

## Monitorování spotřeby racku

![Schéma zapojení pro měření proudu](/etc/img/Scheme_curr.png)

https://dratek.cz/arduino-platforma/1588-15a-ac-proudova-sonda-neinvazivni-sct-013-015.html
Pro měření proudu je použita Neinvazivní proudová sonda SCT-013-015. 

Jelikož napětí je 230V tak dále můžeme vypočítat odebraný výkon: $$P=\frac{U \cdot I_{RMS}}{1000}\qquad[W]$$

Výpočet kumulativní spotřeby se dále spočítá pomocí: $$E=E_0+\left(P\cdot \frac{\Delta t}{3600}\right)$$