# Home-Assistant City-Mind Water Meter (Israel only)

This is a [Home Assistant](https://www.home-assistant.io/) integration for the Israeli online water meters service that serves many water services.

## Breaking Change - v1 to v2

Version 1.x of integration created to support [cp.city-mind.com](https://cp.city-mind.com) portal,
this portal is end of life set to 31/12/2022.

Version 2.x of integration is to support the new portal of [Read Your Meter Pro](https://rym-pro.com/#/),
Please note that if credentials for 2 portals are different and requires registration,
Please follow the prerequisites section below to make sure the integration will work for you.

If your city is not supported by new Read Your Meter Pro portal, you can keep using v1.x of integration up until the previous portal is EOL.

## Requirements

You need to sign-up for the service at **[Read Your Meter Pro](https://rym-pro.com/#/)**.
If your registration was successful, then you can use this integration.

Registration may not succeed for one of the following reasons:

- Your home water meters is not made by the brand "ARAD", as shown in the image above.
- Your water utility company does not allow residents access to the [Read Your Meter Pro](https://rym-pro.com/#/) service that is offered by Arad Technologies.

## Installation

Make sure you have signed up at [Read Your Meter Pro](https://rym-pro.com/#/) as mentioned above, and have a working credentials.

It is recommended to install using HACS, but it is also easy to install manually

#### Installations via HACS

- In HACS, look for `City-Mind Water Meter` and install and restart
- In Settings --> Devices & Services - (Lower Right) "Add Integration"

#### Setup

To add integration use Configuration -> Integrations -> Add `City-Mind Water Meter`
Integration supports **multiple** City Mind accounts

| Fields name | Type    | Required | Default | Description                                        |
| ----------- | ------- | -------- | ------- | -------------------------------------------------- |
| Email       | Textbox | +        | -       | Email registered to City Mind v2                   |
| Password    | Textbox | +        | -       | Password of the account registered to City Mind v2 |

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
| ----------- | ------- | -------- | ------- | -------------------------------------------------- |
| Email       | Textbox | +        | -       | Email registered to City Mind v2                   |
| Password    | Textbox | +        | -       | Password of the account registered to City Mind v2 |

## Components

### Account

| Entity Name                                                        | Type          | Description                                                                                | Additional information           |
| ------------------------------------------------------------------ | ------------- | ------------------------------------------------------------------------------------------ | -------------------------------- |
| {Owner} {Account ID} Alerts                                        | Sensor        | Indicates number of alerts set in the portal                                               | Attributes holds the alerts list |
| {Owner} {Account ID} Consumption Alert Leak (Email)                | Binary Sensor | Allows to control which communication channel should receive an alert when leak identified |                                  |
| {Owner} {Account ID} Consumption Alert Leak (SMS)                  | Switch        | Allows to control which communication channel should receive an alert when leak identified |                                  |
| {Owner} {Account ID} Consumption Alert While Away (Email)          | Switch        | Allows to control which communication channel should receive an alert when leak identified |                                  |
| {Owner} {Account ID} Consumption Alert While Away (SMS)            | Switch        | Allows to control which communication channel should receive an alert when leak identified |                                  |
| {Owner} {Account ID} Consumption Alert Exceeded Threshould (Email) | Switch        | Allows to control which communication channel should receive an alert when leak identified |                                  |
| {Owner} {Account ID} Consumption Alert Exceeded Threshould (SMS)   | Switch        | Allows to control which communication channel should receive an alert when leak identified |                                  |

### Per meter

| Entity Name                                            | Type   | Description                                                                      | Additional information                                 |
| ------------------------------------------------------ | ------ | -------------------------------------------------------------------------------- | ------------------------------------------------------ |
| {Address} {Meter Count} Last Read                      | Sensor | Represents the last read in m³                                                   | Statistics: Total Increment                            |
| {Address} {Meter Count} Monthly Consumption            | Sensor | Represents the monthly consumption in m³                                         | Statistics: Total Increment                            |
| {Address} {Meter Count} Today's Consumption            | Sensor | Represents the daily consumption in m³                                           | Statistics: Total Increment                            |
| {Address} {Meter Count} Yesterday's Consumption        | Sensor | Represents the yesterday's consumption in m³                                     | Statistics: Total Increment                            |
| {Address} {Meter Count} Consumption Forecast           | Sensor | Represents the monthly consumption forecast in m³                                | Statistics: Total, reset at the beginning of the month |
| {Address} {Meter Count} Low Rate Consumption           | Sensor | Represents the consumption below the threshold in m³                             | Statistics: Measurement                                |
| {Address} {Meter Count} High Rate Consumption          | Sensor | Represents the consumption above the threshold in m³                             | Statistics: Measurement                                |
| {Address} {Meter Count} Low Rate Consumption Threshold | Number | Represents the configuration parameter of low rate consumption's threshold in m³ | Statistics: Measurement                                |
| {Address} {Meter Count} Low Rate Cost                  | Number | Represents the configuration parameter of low rate in ILS/m³                     | Statistics: Measurement                                |
| {Address} {Meter Count} High Rate Cost                 | Number | Represents the configuration parameter of high rate configuration in ILS/m³      | Statistics: Measurement                                |
| {Address} {Meter Count} Sewage Cost                    | Number | Represents the configuration parameter of sewage rate configuration in ILS/m³    | Statistics: Measurement                                |

_Last read and daily, monthly, low / high rate consumption's sensors are supporting Water energy_

Cost configuration into meter device (per meter) using number entities

- Low Rate Cost - Default 7.955 ILS/m³
- High Rate Cost - Default 14.6 ILS/m³
- Low Rate Cost - Default 7.955 ILS/m³
- Sewage Cost - Default 0 ILS/m³
- Low Rate Consumption Threshold - Default 3.5 m³ (Equivalent to 7m³ per 2 months of 1 person in property)

_Default values taken from [gov.il](https://www.gov.il/he/pages/rates_general1) and up to date to January 1st 2024_

## Troubleshooting

### Debug logs

To set the log level of the component to DEBUG, please set it from the options of the component if installed, otherwise, set it within configuration YAML of HA:

```yaml
logger:
  default: warning
  logs:
    custom_components.citymind_water_meter: debug
```

### Diagnostic file

In Settings -> Devices & services, look for the device, click on the 3 dots menu and download diagnostic file,

Diagnostic file contains sensitive details, go over it and clean it or send it directly to my [email](elad.bar@hotmail)

## Example of a History Chart

Below is a history graph of a 24 hours meter readings.

Notice that the system only shows usage in "steps" of 100 liters.
That's the provided resolution by City-Mind service:

![Water Meter Reading Chart](https://user-images.githubusercontent.com/255973/87365060-eada9980-c57d-11ea-915a-0c1da95c2d4f.png "Water Meter Reading")

### Example of Lovelace Charts

For this example you would need to have the [Lovelace Mini Graph Card](https://github.com/kalkih/mini-graph-card "mini-graph-card GitHub repository") installed.
It is a highly recommended UI feature.
Install it using HACS.

In the UI, add the following card to see a 24-hours, and a 7-days charts. Replace the XXXXXXXXX with the Meter ID (מספר מונה):

```yaml
type: entities
title: Water Meter
entities:
  - type: "custom:mini-graph-card"
    name: 24 Hours Water Meter
    entities:
      - entity: sensor.citymind_XXXXXXXX_meter_last_read
        name: Water Meter
    points_per_hour: 12
    smoothing: false
    show:
      labels: true
  - type: "custom:mini-graph-card"
    name: 7 Days Water Consumption
    hours_to_show: 168
    group_by: date
    aggregate_func: delta
    entities:
      - sensor.citymind_XXXXXXXX_meter_last_read
    show:
      graph: bar
      state: false
  - type: weblink
    url: "https://rym-pro.com/#/"
```

## Why water meters in Israel have the 100-Liter tics? (Only in Israel)

Almost all water meters in Israel have the minimum resolution that is no less than 100 liters.

The reason for that is religious.
It allows normal use of water during a Saturday to not always triggers an electric pulse.
You can find all kosher water meters reasoning [in this article](https://www.zomet.org.il/?CategoryID=198&ArticleID=697#_Toc334393456).

Unfortunately, the 100 liter limitation in Israel reduces the water meter capabilities to identify water leaks.

_Glatt Kosher water meters_ can support fine metering resolution because they have automatic timers that shut the meter down completely during Saturdays.

---

## Credits

This project was inspired by the [Read Your Meter](https://github.com/eyalcha/read_your_meter "Read Your Meter")
project, made by my neighbor [eyalcha](https://github.com/eyalcha/).

Kudos to [Elad Bar](https://github.com/elad-bar/) for his help, a wonderful code contribution, and refactoring.

[![Israel](https://raw.githubusercontent.com/hjnilsson/country-flags/master/png250px/il.png "Water Meter by Arad Technologies")](https://arad.co.il/products/residential/ "Israel Flag")
