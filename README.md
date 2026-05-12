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


# Komponenty:
V této kapitole budou popsané navrhované komponenty použité pro správnou funkci zařízení. 

## Monitorování spotřeby racku

![Schéma zapojení pro měření proudu](/etc/img/Scheme_curr.png)


Pro neinvazivní měření odběru elektrického proudu rackového systému byla zvolena proudová sonda SCT-013-020 s nominálním rozsahem 20 A a výstupním napětím 1 V RMS. Jelikož je sonda zakončena standardním 3,5mm konektorem (Jack), je pro spolehlivé propojení s mikrokontrolerem využit modul SparkFun TRRS 3.5mm Jack Breakout.

### Úprava signálu (DC Bias)

Vzhledem k tomu, že sonda generuje střídavý (AC) signál a analogově-digitální převodník (ADC) mikrokontroléru Raspberry Pi Pico pracuje pouze v kladném rozsahu 0–3,3 V, bylo nutné implementovat obvod pro stejnosměrný posun signálu (DC Bias).

* Pin S (Sleeve) breakout boardu je připojen k napěťovému děliči tvořenému dvěma rezistory o odporu 10 kΩ. Tento dělič je napájen z pinu 3V3 mikrokontroléru, čímž vytváří referenční střed o hodnotě 1,65 V.


* Pin T (Tip), který nese samotný měřicí signál, je připojen k analogovému pinu GP26 (ADC0). Signál ze sondy se tak vlní kolem uměle vytvořeného středu 1,65 V, což umožňuje bezpečné vzorkování kladné i záporné půlvlny.

### Matematické zpracování dat

Výpočet výsledných hodnot probíhá v několika krocích:

#### 1. Výpočet efektivní hodnoty proudu ($I_{RMS}$)

Systém nejprve během vzorkovacího okna (100 ms) sbírá surová data z ADC (rozsah 0–65535). Z těchto hodnot je vypočítána efektivní digitální hodnota ($ADC_{RMS}$) po odečtení stejnosměrného posunu:

$$ADC_{RMS} = \sqrt{\frac{\sum_{i=1}^{n} val_i^2}{n} - \left(\frac{\sum_{i=1}^{n} val_i}{n}\right)^2}$$

Kde $val_i$ jsou jednotlivé vzorky a $n$ je jejich celkový počet. Následně se hodnota převede na reálné střídavé napětí ($U_{AC}$) a proud ($I_{RMS}$) pomocí kalibračního faktoru sondy (20 A / 1 V):

$$U_{AC} = \frac{ADC_{RMS}}{65535} \cdot 3,3\,V$$
$$I_{RMS} = U_{AC} \cdot 20$$

#### 2. Výpočet okamžitého výkonu ($P_{kW}$)
Okamžitý výkon v kilowattech je vypočítán s uvažovaným síťovým napětím **230 V**:

$$P_{kW} = \frac{230\,V \cdot I_{RMS}}{1000}$$

#### 3. Výpočet kumulativní spotřeby ($E_{kWh}$)
Celková odebraná energie se počítá numerickou integrací okamžitého výkonu v čase. V každém měřicím cyklu je k celkové hodnotě přičten přírůstek energie za uplynulý časový úsek ($\Delta t$):

$$E_{kWh_{nová}} = E_{kWh_{stará}} + \left( P_{kW} \cdot \frac{\Delta t_{ms}}{3\,600\,000} \right)$$

Kde $\Delta t_{ms}$ je čas v milisekundách uplynulý od posledního měření. Tato hodnota je následně odesílána jako telemetrický údaj na server Thingsboard.


### Délka měřicího okna (100 ms)

Pro výpočet efektivní hodnoty proudu ($I_{RMS}$) uvnitř funkce measure_rms_current bylo navrženo časové vzorkovací okno o fixní délce 100 ms. Toto rozhodnutí přímo vychází z fyzikálních vlastností distribuční elektrické sítě, která operuje na standardní frekvenci 50 Hz.

Délka jedné periody střídavého signálu ($T$) je definována vztahem:


$$T = \frac{1}{f} = \frac{1}{50\text{ Hz}} = 0,02\text{ s} = 20\text{ ms}$$

Zvolený časový úsek 100 ms tedy pokrývá přesně 5 celých period střídavé sinusoidy.


## Měření teploty
Pro monitorování teploty uvnitř rackového systému byl zvolen digitální senzor AHT20 (integrovaný na modulu společně se senzorem vlhkosti). Tento čip byl vybrán díky své vysoké spolehlivosti, široké podpoře v rámci komunitních i profesionálních knihoven a měřicímu rozsahu -40 °C až +85 °C, což plně vyhovuje požadavkům na provoz v serverové místnosti.

### Hardwarové zapojení senzoru

Senzor AHT20 komunikuje s mikrokontrolérem prostřednictvím standardní sériové sběrnice I2C. Propojení pinů modulu s řídicí deskou je realizováno následovně:

- VCC: Připojeno na výstupní pin 3V3 mikrokontroléru, který poskytuje stabilní napájecí napětí 3,3 V.
- GND: Připojeno na libovolný pin GND mikrokontroléru pro uzavření napájecího a signálového obvodu.
- SDA: Připojeno na pin GP2, který je hardwarově namapován jako datový kanál I2C1 SDA.
- SCL (Hodinová linka):** Připojeno na pin GP3, který slouží jako hodinový kanál sběrnice I2C1 SCL.









