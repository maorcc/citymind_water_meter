# Changelog

## 2.0.6

New feature: Monthly cost per meter for the water energy dashboard

In v2.0.5 running at HA v2022.11.0 and above introduced the support for water energy dashboard,
since in Israel has 3 rates (low, high and sewage) that defines the monthly cost based on consumption and thresholds - introducing new set of configurations to provide the costs breakdown in dashboard.

Configuration is per meter to support the multiple meter that can have different rates and thresholds

### New Sensors per meter
| Entity Name                                           | Type   | Description                                                                                | Additional information  |
|-------------------------------------------------------|--------|--------------------------------------------------------------------------------------------|-------------------------|
| CityMind {Meter Count} Low Rate Consumption Threshold | Sensor | Represents the configuration parameter of low rate consumption's threshold in m³           | Statistics: Measurement |
| CityMind {Meter Count} Low Rate                       | Sensor | Represents the configuration parameter of low rate in ILS/m³                               | Statistics: Measurement |
| CityMind {Meter Count} High Rate                      | Sensor | Represents the configuration parameter of high rate configuration in ILS/m³                | Statistics: Measurement |
| CityMind {Meter Count} Sewage Rate                    | Sensor | Represents the configuration parameter of sewage rate configuration in ILS/m³              | Statistics: Measurement |
| CityMind {Meter Count} Low Rate Consumption           | Sensor | Represents the consumption below the threshold in m³                                       | Statistics: Measurement |
| CityMind {Meter Count} High Rate Consumption          | Sensor | Represents the consumption above the threshold in m³                                       | Statistics: Measurement |

*Last read and daily, monthly, low / high rate consumption's sensors are supporting Water energy*
*Low, High, Sewage rates and threshold sensors category is configuration and will be available only when set by the service*

### New Services

#### Set Cost Parameters
Set cost's parameters for specific meter:
- Low Rate Consumption Threshold - Time to consider a device without activity as AWAY (any value between 10 and 1800 in seconds)
- Low Rate - Low rate per cubic meter (m³) for consumption below the threshold
- High Rate - High rate per cubic meter (m³) for consumption above the threshold
- Sewage Rate - Sewage rate in ILS per cubic meter (m³)

More details available in `Developer tools` -> `Services` -> `citymind_water_meter.set_cost_parameters`

```yaml
service: citymind_water_meter.set_cost_parameters
data:
  device_id: {Meter device ID}
  low_rate_consumption_threshold: 7
  low_rate: 6.5
  high_rate: 13.5
  sewage_rate: 3.5
```

*Will reload the integration*

#### Remove Cost Parameters
Remove cost's parameters for specific meter

More details available in `Developer tools` -> `Services` -> `citymind_water_meter.remove_cost_parameters`

```yaml
service: citymind_water_meter.remove_cost_parameters
data:
  device_id: {Meter device ID}
```

*Will reload the integration*


## 2.0.5

**Version requires HA v2022.11.0 and above**

- Add support for HA energy, daily consumption device class changed to water
- Aligned *Core Select* according to new HA *SelectEntityDescription* object

## 2.0.4

- Fix error when consumption value is empty

## 2.0.3

- Fix multi-meter support [#34](https://github.com/maorcc/citymind_water_meter/issues/34)
- Removed store debug data to files and its configuration
- Add endpoints to expose data from `Read Your Meter Pro` API

| Endpoint Name                            | Method | Description                                                                                         |
|------------------------------------------|--------|-----------------------------------------------------------------------------------------------------|
| /api/citymind_water_meter/list           | GET    | List all the endpoints available (supporting multiple integrations), available once for integration |
| /api/citymind_water_meter/{ENTRY_ID}/api | GET    | JSON of all raw data from the Read Your Meter Pro API, per integration                              |

**Authentication: Requires long-living token from HA**


## 2.0.2

- Add error handling for failed login
- Updated documentation
- Fixed login error message on installation / configuration UI

## 2.0.1

- Fix data loading

## 2.0.0

***Breaking Changes inside!***

- Switched to new API of City Mind
- Add ability to change media for each alert
- Add switch to store debug data from API
- Changed entities:
-
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



## 1.0.5

- Device and Entity registry - `async_get_registry` is deprecated, change to `async_get`
- Update pre-commit

## v1.0.4

- Whitespace cleanup from consumer, provider and serial number

## v1.0.2

- Support breaking changes of HA v2012.12.0
- Fixed division by zero errors [#22](https://github.com/maorcc/citymind_water_meter/issues/22)
- Added support for Long-term Statistics [#21](https://github.com/maorcc/citymind_water_meter/issues/21)
