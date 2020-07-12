"""The cp.city-mind.com website for water meters integration.

This component integrates with the Israeli https://cp.city-mind.com municipal water meters.
It provides a sensor of water consumption in resoluton of 0.1 cube meters, which is 100 litters.

The authors of this integration are not associated in any way with Arad Technologies who own and operate
the City Mind water services.

Configuration:

To use the hello_word component you will need to add the following to your
configuration.yaml file.

sensor:
  - platform: citymind_water_meter
    scan_interval: 600
    username: !secret citymind_username     # Usually your email address
    password: !secret citymind_password

"""
