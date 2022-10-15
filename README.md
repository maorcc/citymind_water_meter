# Home-Assistant City-Mind Water Meter (Israel only)

This is a [Home Assistant](https://www.home-assistant.io/) integration for the Israeli [cp.city-mind.com](https://cp.city-mind.com)
online water meters service that serves many water services.

## Requirements

You need to sign-up for the service at **[https://cp.city-mind.com](https://cp.city-mind.com/ "cp.city-mind.com")**.
If your registration was successful, then you can use this integration.

Registration may not succeed for one of the following reasons:

- Your home water meters is not made by the brand "ARAD", as shown in the image above.
- Your water utility company does not allow residents access to the ["Read Your Meter"](https://cp.city-mind.com/ "https://cp.city-mind.com/") service (website cp.city-mind.com) that is offered by Arad Technologies.

Here is an outdated map showing water utilities companies in Israel that use Arad's water meters:

## Installation

Make sure you have signed up at [https://cp.city-mind.com](https://cp.city-mind.com/ "cp.city-mind.com") as mentioned above, and have a working username/password.  The username is usually your email address.

It is recommended to install using HACS, but it is also easy to install manually

#### Installations via HACS
- In HACS, look for "Citymind-water-meter" and install and restart
- In Settings  --> Devices & Services - (Lower Right) "Add Integration"

#### Setup

To add integration use Configuration -> Integrations -> Add `City-Mind Water Meter`
Integration supports **multiple** City Mind accounts

| Fields name | Type      | Required | Default | Description                                        |
|-------------|-----------|----------|---------|----------------------------------------------------|
| Email       | Textbox   | +        | -       | Email registered to City Mind v2                   |
| Password    | Textbox   | +        | -       | Password of the account registered to City Mind v2 |


###### Encryption key got corrupted

If a persistent notification popped up with the following message:

```
Encryption key got corrupted, please remove the integration and re-add it
```

It means that encryption key was modified from outside the code,
Please remove the integration and re-add it to make it work again.

#### Options

_Configuration -> Integrations -> {Integration} -> Options_ <br />

| Fields name | Type    | Required | Default | Description                                        |
|-------------|---------|----------|---------|----------------------------------------------------|
| Email       | Textbox | +        | -       | Email registered to City Mind v2                   |
| Password    | Textbox | +        | -       | Password of the account registered to City Mind v2 |

#### Debugging

To set the log level of the component to DEBUG, please set it from the options of the component if installed, otherwise, set it within configuration YAML of HA:

```yaml
logger:
  default: warning
  logs:
    custom_components.citymind_water_meter: debug
```

## Components

### Account
| Entity Name                                            | Type   | Description                                                                                                         | Additional information                       |
|--------------------------------------------------------|--------|---------------------------------------------------------------------------------------------------------------------|----------------------------------------------|
| CityMind {Account ID} Account Store Debug Data         | Select | Sets whether to store API latest data for debugging                                                                 |                                              |
| CityMind {Account ID} Account Alert Exceeded threshold | Select | Allows to control which communication channel should receive an alert when daily consumption exceeded threshold     | Available options are: None, Email, SMS, All |
| CityMind {Account ID} Account Alert Leak               | Select | Allows to control which communication channel should receive an alert when leak identified                          | Available options are: None, Email, SMS, All |
| CityMind {Account ID} Account Alert Leak While Away    | Select | Allows to control which communication channel should receive an alert when leak identified when vacation is defined | Available options are: None, Email, SMS, All |
| CityMind {Account ID} Account Alerts                   | Sensor | Indicates number of alerts set in the portal                                                                        | Attributes holds the alerts list             |
| CityMind {Account ID} Account Messages                 | Sensor | Indicates number of messages set in the portal                                                                      | Attributes holds the messages list           |
| CityMind {Account ID} Account Vacations                | Sensor | Indicates number of vacations set in the portal                                                                     | Attributes holds the vacations list          |

### Per meter
| Entity Name                                          | Type   | Description                                      | Additional information                    |
|------------------------------------------------------|--------|--------------------------------------------------|-------------------------------------------|
| CityMind {Meter Count} Meter Last Read               | Sensor | Represents the last read in m³                   | Statistics: Total Increment               |
| CityMind {Meter Count} Meter Daily Consumption       | Sensor | Represents the daily consumption in m³           | Statistics: Total, reset on daily basis   |
| CityMind {Meter Count} Meter Monthly Consumption     | Sensor | Represents the monthly consumption in m³         | Statistics: Total, reset on monthly basis |
| CityMind {Meter Count} Meter Yesterday's Consumption | Sensor | Represents the yesterday's consumption in m³     | Statistics: Total, reset on daily basis   |
| CityMind {Meter Count} Meter Consumption Forcast     | Sensor | Represents the monthly consumption forcast in m³ | Statistics: Total, reset on monthly basis |

## Example of a History Chart

Below is a history graph of a 24 hours meter readings.

Notice that the system only shows usage in "steps" of 100 liters.
That's the provided resolution by City-Mind service:

![Water Meter Reading Chart](https://user-images.githubusercontent.com/255973/87365060-eada9980-c57d-11ea-915a-0c1da95c2d4f.png "Water Meter Reading")

### Example of Lovelace Charts

For this example you would need to have the [Lovelace Mini Graph Card](https://github.com/kalkih/mini-graph-card "mini-graph-card GitHub repository") installed.
It is a highly recommended UI feature.
Install it using HACS.

In the UI, add the following card to see a 24-hours, and a 7-days charts.  Replace the XXXXXXXXX with the Meter ID (מספר מונה):

```yaml
type: entities
title: Water Meter
entities:
  - type: 'custom:mini-graph-card'
    name: 24 Hours Water Meter
    entities:
      - entity: sensor.water_meter_XXXXXXXXX_last_reading
        name: Water Meter
    points_per_hour: 12
    smoothing: false
    show:
      labels: true
  - type: 'custom:mini-graph-card'
    name: 7 Days Water Consumption
    hours_to_show: 168
    group_by: date
    aggregate_func: delta
    entities:
      - sensor.water_meter_XXXXXXXXX_last_reading
    show:
      graph: bar
      state: false
  - type: weblink
    url: 'https://cp.city-mind.com/Default.aspx'
```

<img src =
  "https://user-images.githubusercontent.com/255973/95665125-f70ecc80-0b55-11eb-887f-edb3e1463051.png"
  height="459" width="367"
  alt="Sample charts using mini-graph-card">

## Why water meters in Israel have the 100-Liter tics? (Only in Israel)

Almost all water meters in Israel have the minimum resolution that is no less than 100 liters.

The reason for that is religious.
It allows normal use of water during a Saturday to not always triggers an electric pulse.
You can find all kosher water meters reasoning [in this article](https://www.zomet.org.il/?CategoryID=198&ArticleID=697#_Toc334393456).

Unfortunately, the 100 liter limitation in Israel reduces the water meter capabilities to identify water leaks.

*Glatt Kosher water meters* can support fine metering resolution because they have automatic timers that shut the meter down completely during Saturdays.

---

## Credits

This project was inspired by the [Read Your Meter](https://github.com/eyalcha/read_your_meter "Read Your Meter")
project, made by my neighbor [eyalcha](https://github.com/eyalcha/).

I created this alternative project because I wanted it lighter, quicker, and easy to
setup.  Mostly, I wanted to avoid the manual installation of a Selenium docker on Hass.io.

Kudos to [Elad Bar](https://github.com/elad-bar/) for his help, a wonderful code contribution, and refactoring.

[![Israel](https://raw.githubusercontent.com/hjnilsson/country-flags/master/png250px/il.png "Water Meter by Arad Technologies")](https://arad.co.il/products/residential/ "Israel Flag")
