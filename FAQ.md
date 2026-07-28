# SondeAlert — Questions and Answers

This page answers common questions about SondeAlert, its radiosonde data, detection system and Android behaviour.

---

## General

### What is SondeAlert?

SondeAlert is an Android application for locating and recovering radiosondes that have already landed.

The app downloads radiosonde information, stores it locally and compares the stored locations with your current GPS position.

### Is SondeAlert a live radiosonde tracker?

No. SondeAlert is primarily designed to locate previously landed radiosondes.

The position shown in the app is the last known position provided by Radiosondy.info. A radiosonde may have moved after that position was recorded.

### Is SondeAlert an official Radiosondy.info application?

No. SondeAlert is an independent application developed by Sc0ps Owl Designs.

Radiosonde information is provided by Radiosondy.info, but SondeAlert is not developed or maintained by Radiosondy.info.

### Where can I download SondeAlert?

SondeAlert is currently available to invited testers through a closed Google Play testing programme.

A public Google Play release may follow after testing has been completed.

---

## Radiosonde data

### Where does the radiosonde data come from?

Radiosonde records are downloaded from Radiosondy.info.

SondeAlert stores the downloaded information locally so that filtering, distance calculations and detection can be performed efficiently.

### What is the difference between the Full and Lite datasets?

The **Full** dataset contains available records from 19 March 2017 through today.

The **Lite** dataset contains records from 1 January 2022 through today.

Both datasets currently use:

- A maximum download radius of 600 km
- `Unknown` and `Needs Attention` statuses
- A maximum last known altitude of 2,000 metres

The Lite dataset requires less data and is suitable for devices with limited storage or processing capacity.

### Why are only Unknown and Needs Attention radiosondes downloaded?

SondeAlert focuses on radiosondes that may still need to be located or recovered.

Radiosondes with a `Found` status are therefore not part of the standard local recovery dataset.

### Why does “Records received” differ from “Stored locally”?

**Records received** is the number of rows returned by the Radiosondy.info data service.

**Stored locally** is the number of usable, unique radiosondes that remain after SondeAlert applies its local dataset rules.

SondeAlert currently requests data using a regional coordinate rounded to the nearest half degree. It then checks the downloaded records against the exact selected location.

Because the regional request centre and the exact local centre are slightly different, some radiosondes near the edge of the 600 km radius can be received by the app but excluded from local storage.

This means a difference between the two counters does not automatically indicate missing or corrupted data.

Other possible reasons for a difference include:

- A duplicate radiosonde ID
- An invalid or incomplete record
- A record outside the exact local radius
- A record outside the selected status or altitude rules
- An update record that refers to a radiosonde already stored locally

### Why can the size of the difference change with location?

The API request coordinate is rounded to a regional half-degree coordinate. The distance between that coordinate and the exact selected location differs by location.

This changes how much the two 600 km selection areas overlap, so the number of edge records that are excluded can also change.

### Does “Shown on map” represent the entire local database?

No. It only represents the radiosondes that currently pass the map filters and are within the selected map radius.

The local database can contain many more radiosondes than are currently displayed.

### Why are only 200 radiosondes shown in the Sonde list?

The Sonde list is limited to 200 results to keep the interface responsive.

Use the search field and filters to find a specific radiosonde. The map and local database are not limited to these 200 list results.

### When are database updates performed?

Manual updates start when you press the database update button.

Automatic updates are scheduled through Android. Android may run a scheduled update within a flexible system window instead of at an exact time.

If Wi-Fi-only updates are enabled, the automatic update will wait until a suitable Wi-Fi connection is available.

### Why might the last update time not match the selected interval exactly?

Android controls the final execution time of scheduled background work.

Battery optimisation, network availability, device usage and manufacturer-specific background restrictions can delay an automatic update.

---

## Map and location

### Why does SondeAlert need location permission?

Location is used to:

- Display your position on the map
- Calculate the nearest radiosonde
- Position the detection rings
- Calculate distances to radiosondes
- Perform radiosonde detection
- Request data for the surrounding region

### Is my exact GPS location sent with a radiosonde database request?

SondeAlert rounds the database request location to a regional coordinate.

Your exact GPS position is used locally for distance calculations and detection.

Map services may receive information about the map area being viewed when map tiles are requested.

### Does the map work offline?

Radiosonde records are stored locally, but map tiles normally require an internet connection unless they are already present in the map cache.

Detection and local distance calculations can continue using the locally stored radiosonde database and an available GPS position.

### What does “Distance to nearest sonde” show?

It shows the distance from your latest GPS position to the nearest radiosonde that:

- Is stored in the selected local dataset
- Passes the active rules
- Is not on the Sonde blocklist

The nearest-sonde distance can remain visible even when the radiosonde is outside the configured detection rings.

### What happens when I tap “Distance to nearest sonde”?

The map centres on the radiosonde currently identified as the nearest sonde so you can see its location.

### What happens when I tap a radiosonde marker?

A detail window opens with the available radiosonde information.

From this window you can:

- Open the radiosonde on Radiosondy.info
- Add or remove it from favourites
- Add it to the Sonde blocklist
- Show it on the map where applicable

### Why might the map initially show a large area?

SondeAlert must wait for Android to provide a valid GPS position.

Once a location is available, the app centres the map and detection rings on that position. Location permission and Android location services must both be enabled.

---

## Detection and notifications

### How does radiosonde detection work?

SondeAlert compares your current GPS position with locally stored radiosonde positions.

When a radiosonde enters a configured detection ring, the app can produce an audio alert and a radiosonde detection notification.

Each detection ring has its own audio pattern.

### Why does each ring use a different audio pattern?

A separate pattern lets you recognise how close the detected radiosonde is without continuously looking at the screen.

The pattern represents the active detection ring. It does not represent whether you are approaching, stationary or moving away.

### Can audio alerts and detection notifications be controlled separately?

Yes.

You can enable or disable:

- Audio alerts
- Radiosonde detection notifications

These settings apply to radiosonde detection alerts.

They do not disable the persistent Android notification that may be required while GPS background detection is active.

### Which Android volume control is used for the detection sound?

SondeAlert uses the Android media volume for its detection audio.

If Audio Alert is disabled, the app should not play the detection sound. Device-specific sound modes and connected Bluetooth or Android Auto devices can affect where the audio is played.

### What does the bell button on the home screen mean?

The bell indicates the current radiosonde alert state:

- **Green bell:** audio and detection notifications are enabled
- **Red bell:** audio is disabled, but detection notifications are enabled
- **Grey crossed-out bell:** audio and detection notifications are disabled

### Why can background behaviour differ between Android devices?

Android manufacturers apply different battery and background-process restrictions.

For reliable background detection:

- Allow location access as required
- Allow notifications
- Exclude SondeAlert from aggressive battery optimisation where necessary
- Keep Android location services enabled

The exact names of these settings differ between device manufacturers.

---

## Favourites and blocklist

### What happens when I add a radiosonde to favourites?

The radiosonde is stored in the Favourites list.

On the map, favourite radiosondes use a star-shaped marker:

- Yellow for `Unknown`
- Purple for `Needs Attention`

The marker retains a white outline for visibility.

### What does the Sonde blocklist do?

A blocked radiosonde is:

- Hidden from the map
- Excluded from nearest-sonde calculations
- Excluded from detection
- Excluded from detection notifications and audio alerts

Blocking a radiosonde does not remove it from the Radiosondy.info database.

### Can I remove a radiosonde from the blocklist?

Yes. You can remove radiosondes individually or clear the complete Sonde blocklist.

After removing a radiosonde, it can become visible again if it passes the active map filters.

### What happens when I block a sonde from its detail window?

The radiosonde is added to the Sonde blocklist, removed from the map and excluded from detection. The detail window closes automatically.

---

## Filters

### Why are map-filter changes not applied immediately?

Filter changes are prepared inside the Map filters screen.

Press **Apply filters** to apply all changes together. This avoids repeatedly rebuilding the map while several options are being changed and keeps the app responsive.

### What is the maximum last known altitude?

The maximum supported value is 2,000 metres.

This matches the maximum altitude used for the radiosonde dataset downloaded by the app.

### Why are several related sonde types grouped together?

Radiosonde decoders can report different variations of the same basic sonde family.

SondeAlert groups related values by their starting characters. For example, multiple RS41 variations can be included in the RS41 family.

Types that do not match one of the listed families can be selected using **Other**.

### What period can be selected?

The visible data period can be selected by start year and end year.

Available records begin on 19 March 2017. The end of the selected period can be set to **Today**.

The available start period can be more limited when the Lite dataset is selected.

---

## Troubleshooting

### The app does not centre on my location. What should I check?

Check that:

- Location permission is enabled
- Android location services are enabled
- SondeAlert is allowed to access location
- The device has received a valid GPS or network location
- Battery optimisation is not preventing location updates

Use the location button on the map to centre it on your current position.

### A radiosonde is not visible on the map. Why?

Check whether:

- The radiosonde is on the Sonde blocklist
- Its status is included in the dataset
- It is below the 2,000-metre dataset limit
- It is inside the selected map radius
- Its type is enabled
- Its date is inside the selected period
- Its altitude passes the active map filter
- You pressed **Apply filters** after changing filters

### Why can a radiosonde’s actual location differ from the map?

SondeAlert displays the last known position supplied by Radiosondy.info.

Wind, water, people, vehicles or other circumstances may have moved the radiosonde after its final reported position.

Always respect private property, local regulations and personal safety while recovering radiosondes.

### The app is slow or closes unexpectedly. What information should I report?

Please include:

- Device manufacturer and model
- Android version
- SondeAlert version
- What screen was open
- What action was performed
- Whether the app had just returned from the background
- Selected dataset and map radius
- Screenshots or a screen recording where possible

Do not publicly include your exact home address or other sensitive location information.

---

## Support and feedback

SondeAlert is still being tested. Feedback from testers helps improve stability, detection behaviour, data handling and usability.

Please use the repository’s issue section or the communication channel provided to your testing group.

When reporting a data problem, include the radiosonde ID and the approximate region, but avoid sharing unnecessary personal location information.
