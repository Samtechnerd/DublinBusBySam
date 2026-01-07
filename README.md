# Dublin Bus by Sam

A custom Home Assistant integration to track real-time bus departures.

![Logo](logo.png)

## ✨ Features
* **Real-time Tracking:** Updates every minute using live data.
* **Smart Filtering:** Option to filter specifically for the routes you take (e.g., "H3, 6").
* **Multiple Entities:**
  * **Main Sensor:** Minutes until the next bus (Graphable!).
  * **Detail Sensors:** Separate sensors for `Next Route`, `Next Destination`, and `Next Time`.
  * **Route Sensors:** Tracks specific routes individually if you set a filter.

## 🛠 Installation

1.  Open **HACS** > Integrations.
2.  Menu > **Custom Repositories**.
3.  Add this repository URL and select **Integration**.
4.  Click **Install** and restart Home Assistant.

## ⚙️ Configuration

1.  Go to **Settings** > **Devices & Services** > **Add Integration**.
2.  Search for **Dublin Bus by Sam**.

### How to find your Stop ID 🕵️‍♂️
1.  Go to [bustimes.org](https://bustimes.org/).
2.  Search for your location and find your specific stop on the map.
3.  Click the stop. The ID will be at the top or in the URL.
4.  It should look something like `8240DB007210`.
5.  Paste that ID into the setup box and you're all set!
<img width="769" height="693" alt="image" src="https://github.com/user-attachments/assets/58b76d3e-d28e-491e-b341-b5cab92fec41" />

---
*Data provided by https://busfinder.fly.dev/. and National transport authority*
