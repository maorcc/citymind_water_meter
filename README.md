# City-Mind Water Meter
City-Mind is a water technology service provider, serving many monicipalities **in Israel**, using the website https://cp.city-mind.com.


[![Water Meter by Arad Technologies](https://arad.co.il/assets/Copy-of-OE-register.jpg "Water Meter by Arad Technologies")](https://arad.co.il/products/residential/ "Water Meter by Arad Technologies")

### About
This component integrates with the Israeli https://cp.city-mind.com online water meters service.
This integration provides a sensor for water consumption in minimal resoluton of 100 litters.

The authors of this integration are not associated in any way with Arad Technologies who own and operate the City Mind water services.

###Requirements
Need to have a username and password for the [cp.city-mind.com](https://cp.city-mind.com/ "cp.city-mind.com") website.  This is only available in Israel. Get the username and password from your water service provider.

אפשרי רק ללקוח של אחד **מתאגידי המים** או **יישובים** שמקבלים שרותי קריאת מונים אונליין מארד טכנולוגיות, לדוגמא:
  - "מעיינות העמקים"
  - "מניב ראשון"
  - "מעיינות הדרום"
  - "יובלים בשומרון"


### Installation
Copy the `/custom_components/citymind_water_meter` folder to your `<config_dir>/custom_components/`.

### Configuration:

Add the following entry in your `configuration.yaml`:

```yaml
sensor:
  - platform: citymind_water_meter
    scan_interval: 1800                     # 30 minutes in Seconds
    username: !secret citymind_username     # Usually your email address
    password: !secret citymind_password     # Your password to cp.city-mind.com website
```
### Credits
This project was inspired by the [Read Your Meter](https://github.com/eyalcha/read_your_meter "Read Your Meter") 
project, made by my neighbour [eyalcha](https://github.com/eyalcha/).

I created this alternative project because I wanted it lighter, quicker, and easy to
setup.  Mostly, I wanted to avoid the manual installation of a Selenium docker on Hass.io.

[![Israel](https://raw.githubusercontent.com/hjnilsson/country-flags/master/png250px/il.png "Water Meter by Arad Technologies")](https://arad.co.il/products/residential/ "Israel Flag")
