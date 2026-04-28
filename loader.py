import ujson

# kdybyscohm chteli menit nastaveni, tak by to potom pres import neslo
def save_settings(creds):
    with open('settings.json', 'w') as outfile:
        ujson.dump(creds, outfile)

def load_settings():
    with open('settings.json', 'r') as infile:
        return  ujson.load(infile)

# showcase:


set = {
    "WIFI_SSID":"LPWAN-IoT-XY",
    "WIFI_PWD":"LPWAN-IoT-XY-WiFi",

    "_MQTT_REMOTE_SERVER_IP_": "147.229.148.105",
    "_MQTT_REMOTE_SERVER_PORT_":1883,

    "_MQTT_CLIENT_ID_":"Your Client ID",
    "_MQTT_ACCESS_TOKEN_":"Your Access Token",
    "_MQTT_PASSWORD_":"",

}
# save_settings(set)
cred = load_settings()
# for key in cred.keys():
#     print(cred[key])
cred["WIFI_SSID"]