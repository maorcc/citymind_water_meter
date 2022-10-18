# Changelog

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
