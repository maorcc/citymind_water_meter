# Home-Assistant City-Mind Water Meter (Israel only)
This is a [Home Assistant](https://www.home-assistant.io/) integration for the Israeli [cp.city-mind.com](https://cp.city-mind.com) 
online water meters service. 

This integration provides Home Assistant with two **sensors** for water consumption in a minimum resolution of 100 liters:
  - Water meter reading in cubic meters.
  - Current consumption value in liters. (Multiplications of 100L.)

<img src="https://user-images.githubusercontent.com/255973/88915377-d3352d80-d26c-11ea-8ffc-58d7adcca3b5.png" height="300" width="451" alt="24 hours water meter graph">

This project is not associated in any way with Arad Group or any of its companies that own and operate the City Mind water services.

<a href="https://user-images.githubusercontent.com/255973/87365347-ab607d00-c57e-11ea-9440-19e7805cf9ac.png" target="_blank"><img src="https://user-images.githubusercontent.com/255973/87365347-ab607d00-c57e-11ea-9440-19e7805cf9ac.png" height="300" width="450" alt="Water Meter by Arad Technologies"></a>

## Requirements
You need to sign-up for the service at
 **[https://cp.city-mind.com](https://cp.city-mind.com/ "cp.city-mind.com")**.
 
 If your registration is successful, then you can use this integration.

[![Self signup](https://user-images.githubusercontent.com/255973/88737784-c536be00-d141-11ea-819c-2199816e3511.png "https://cp.city-mind.com/")](https://cp.city-mind.com/)

Registration may not succeed for one of the following reasons:
- Your home water meters is not made by the brand "ARAD",
 as shown in the image above.
- Your water utility company does not allow residents access to
 the ["Read Your Meter"](https://cp.city-mind.com/ "https://cp.city-mind.com/") 
 service (website cp.city-mind.com) that is offered by Arad Technologies.
 
Here is an outdated map showing water utilities companies in Israel that use
 Arad's water meters:

![map](https://user-images.githubusercontent.com/255973/87733202-c4b03600-c7d7-11ea-9c8c-7aff8c1f9e81.png "Supported water utilities")

Here is a partial list (may also be outdated) of supported water utilities and cities:

אפשרי רק ללקוח של אחד **מתאגידי המים** שמקבלים שרותי קריאת מונים אונליין מארד טכנולוגיות, לדוגמא:
  - מיתב: פתח תקווה, אלעד
  - מי-נעם: נצרת עילית, עפולה, מגדל העמק
  - פלג הגליל: צפת ועוד
  - מעיינות הדרום: דימונה, ערד, ירוחם, ומצפה רמון
  - מי-מודיעין
  - מי ציונה: נס ציונה, מזכרת בתיה, קריית עקרון
  - מי התנור: קריית שמונה, מטולה, קצרין
  - מי רקת טבריה
  - מי עכו
  - מעיינות זיו: מעלות
  - מעיינות העמקים: יוקנעם, זכרון יעקב
  - מניב ראשון: ראשון לציון
  - יובלים בשומרון

## Installation
Make sure you have signed up at
 [https://cp.city-mind.com](https://cp.city-mind.com/ "cp.city-mind.com")
  as mentioned above, and have a working username/password.

It is recommended to install using HACS, but it is also easy to install
 manually
 
#### Install using HACS (Recommended)
Add this repository to HACS as a custom repository.
 After few seconds (be patient), the option to install this integration
 will show up. 

#### Install Manually
Copy the `/custom_components/citymind_water_meter` folder from this
 repository to your `<config_dir>/custom_components/` folder.
 Restart Home Assistant.

## Configuration:
Add the following entry in your `configuration.yaml`:

```yaml
sensor:
  - platform: citymind_water_meter
    scan_interval: 1800                     # 30 minutes in Seconds
    username: !secret citymind_username     # Usually your email address
    password: !secret citymind_password     # Your password to cp.city-mind.com website
```
## Example of a History Chart
Below is a history graph of a 24 hours meter readings.

Notice that the system only shows usage in "steps" of 100 liters. That's the provided resolution by City-Mind service:

![Water Meter Reading Chart](https://user-images.githubusercontent.com/255973/87365060-eada9980-c57d-11ea-915a-0c1da95c2d4f.png "Water Meter Reading")

### Example of Lovelace Charts:
For this example you would need to have the
 [Lovelace Mini Graph Card](https://github.com/kalkih/mini-graph-card "mini-graph-card GitHub repository")
 installed. It is a highly recommended UI feature.
 Install it using HACS. 

In the UI, add the following card to see a 24-hours, and a 7-days charts:

```yaml
type: entities
title: Water Meter
entities:
  - type: 'custom:mini-graph-card'
    name: 24 Hours Water Meter
    entities:
      - entity: sensor.water_meter_reading
        name: Water Meter
      - entity: sensor.water_consumption
        name: Consumption Tics
        y_axis: secondary
    points_per_hour: 12
    smoothing: false
    show:
      labels: true    
  - type: 'custom:mini-graph-card'
    name: 7 Days Water Consumption
    hours_to_show: 168
    group_by: date
    aggregate_func: sum
    entities:
      - sensor.water_consumption
    show:
      graph: bar
      state: false
```

## Why water meters in Israel have the 100-Liter tics? (Only in Israel)
Almost all water meters in Israel have the minimum resolution that is no less than 100 liters.

The reason for that is religious.
It allows normal use of water during a Saturday to not always triggers an electric pulse.
You can find all kosher water meters reasoning [in this article](https://www.zomet.org.il/?CategoryID=198&ArticleID=697#_Toc334393456).

Unfortunately, the 100 liter limitation in Israel reduces the water meter capabilities to identify water leaks.

*Glatt Kosher water meters* can support fine metering resolution because they have automatic timers that shut the meter down completely during Saturdays.

## Credits
This project was inspired by the [Read Your Meter](https://github.com/eyalcha/read_your_meter "Read Your Meter") 
project, made by my neighbor [eyalcha](https://github.com/eyalcha/).

I created this alternative project because I wanted it lighter, quicker, and easy to
setup.  Mostly, I wanted to avoid the manual installation of a Selenium docker on Hass.io.

[![Israel](https://raw.githubusercontent.com/hjnilsson/country-flags/master/png250px/il.png "Water Meter by Arad Technologies")](https://arad.co.il/products/residential/ "Israel Flag")
