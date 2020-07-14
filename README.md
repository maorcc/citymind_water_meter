# Home-Assistant City-Mind Water Meter
This is a [Home Assistant](https://www.home-assistant.io/) integration for the **Israeli** [cp.city-mind.com](https://cp.city-mind.com) 
online water meters service. 

This integration provides Home Assistant with two **sensors** for water consumption in a minimum resolution of 100 liters:
  - Water meter reading in cubic meters.
  - Current consumption value in liters. (Multiplications of 100L.)

This project is not associated in any way with Arad Group or any of its companies that own and operate the City Mind water services.

![Water Meter by Arad Technologies](https://user-images.githubusercontent.com/255973/87365347-ab607d00-c57e-11ea-9440-19e7805cf9ac.png "Water Meter by Arad Technologies")

### Requirements
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
### Example of a History Chart
![Water Meter Reading Chart](https://user-images.githubusercontent.com/255973/87365060-eada9980-c57d-11ea-915a-0c1da95c2d4f.png "Water Meter Reading")

### Credits
This project was inspired by the [Read Your Meter](https://github.com/eyalcha/read_your_meter "Read Your Meter") 
project, made by my neighbor [eyalcha](https://github.com/eyalcha/).

I created this alternative project because I wanted it lighter, quicker, and easy to
setup.  Mostly, I wanted to avoid the manual installation of a Selenium docker on Hass.io.

[![Israel](https://raw.githubusercontent.com/hjnilsson/country-flags/master/png250px/il.png "Water Meter by Arad Technologies")](https://arad.co.il/products/residential/ "Israel Flag")
