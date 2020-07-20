# Home-Assistant City-Mind Water Meter
This is a [Home Assistant](https://www.home-assistant.io/) integration for the **Israeli** [cp.city-mind.com](https://cp.city-mind.com) 
online water meters service. 

This integration provides Home Assistant with two **sensors** for water consumption in a minimum resolution of 100 liters:
  - Water meter reading in cubic meters.
  - Current consumption value in liters. (Multiplications of 100L.)

This project is not associated in any way with Arad Group or any of its companies that own and operate the City Mind water services.

![Water Meter by Arad Technologies](https://user-images.githubusercontent.com/255973/87365347-ab607d00-c57e-11ea-9440-19e7805cf9ac.png "Water Meter by Arad Technologies")

## Requirements
You need to have a username and password for the [cp.city-mind.com](https://cp.city-mind.com/ "cp.city-mind.com") website.  

If you pay for your water to one of the organizations shown on the map, then you 
 can probably get a username/password from your water service provider. 

![map](https://user-images.githubusercontent.com/255973/87733202-c4b03600-c7d7-11ea-9c8c-7aff8c1f9e81.png "Supported water utilities")

Here is a partial list of water providers and cities:

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
It is recommended to use HACS, but you can also install manually 
#### Install using HACS (Recommended)
Add this custom repository to HACS, after few seconds, the option to install
this integration will appear. 

#### Install Manually
Copy the `/custom_components/citymind_water_meter` folder to your `<config_dir>/custom_components/`.
And restart Home Assistant.

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

### Why the 100 liter limitation? (Only in Israel)
Almost all water meters in Israel have the minimum resolution that is no less than 100 liters.

The reason for that is religious.
It allows normal use of water during a Saturday to not always triggers an electric pulse.
You can find all kosher water meters reasoning [in this article](https://www.zomet.org.il/?CategoryID=198&ArticleID=697#_Toc334393456).

Unfortunately, the 100 liter limitation in Israel reduces the water meter capabilities to identify water leaks.

*Glatt Kosher water meters* can support fine metering resolution because they have automatic timers that shut the meter down completely during Saturdays.

### Credits
This project was inspired by the [Read Your Meter](https://github.com/eyalcha/read_your_meter "Read Your Meter") 
project, made by my neighbor [eyalcha](https://github.com/eyalcha/).

I created this alternative project because I wanted it lighter, quicker, and easy to
setup.  Mostly, I wanted to avoid the manual installation of a Selenium docker on Hass.io.

[![Israel](https://raw.githubusercontent.com/hjnilsson/country-flags/master/png250px/il.png "Water Meter by Arad Technologies")](https://arad.co.il/products/residential/ "Israel Flag")
