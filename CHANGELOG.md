# SondeAlert Changelog

All notable changes to SondeAlert are documented on this page.

SondeAlert is currently distributed through a closed Google Play testing programme. Test builds may be replaced quickly when an important issue is discovered.

---

## Unreleased

### Documentation

- Updated the public SondeAlert project description.
- Added a Questions and Answers page.
- Expanded the Privacy Policy.
- Expanded the Security Policy.
- Added an explanation of the difference between records received and radiosondes stored locally.

---

## 1.0.6 (40) — Closed test

### Performance

- Significantly improved map responsiveness.
- Reduced unnecessary map rebuilding and marker updates.
- Improved responsiveness after restoring SondeAlert from the background.
- Improved performance when displaying radiosondes over a large map radius.
- Reduced unnecessary work during frequent GPS updates.
- Improved Android 16 stability.
- Reduced the risk of application freezes and unexpected closures.

### GPS and detection

- Detection rings now remain synchronised with the current GPS marker.
- Improved nearest-sonde calculations while the device is moving.
- Prevented new GPS updates from repeatedly cancelling an active nearest-sonde calculation.
- Improved foreground detection while travelling.
- Corrected inconsistent nearest-sonde behaviour after GPS movement.

### Testing

- Completed unit tests and Android lint checks.
- Completed release-build verification.
- Tested foreground and background transitions.
- Tested repeated restore-from-background cycles.
- Tested map, detection and location behaviour on multiple Android versions.

---

## 1.0.5 (39) — Closed test

### Interface

- Introduced the redesigned SondeAlert interface.
- Added light, dark and follow-system themes.
- Improved text contrast and readability.
- Improved spacing and alignment throughout the application.
- Updated map controls for light and dark themes.
- Updated the home-screen Menu button.
- Added a home-screen bell indicating the current detection-alert state.
- Redesigned the nearest-sonde information panel.
- Improved radiosonde detail windows.
- Added consistent outlined action buttons.
- Moved the main Database section to the top of the Database screen.

### Map

- Added improved map filtering.
- Added a single **Apply filters** action so multiple filter changes are processed together.
- Added year-based start and end period selection.
- Added configurable status, sonde family, altitude and radius filters.
- Added grouped sonde families to handle decoder-specific type variations.
- Added an **Other** sonde-type category.
- Added favourite star markers.
- Added status-specific favourite marker colours.
- Added the ability to centre the map on a radiosonde selected from the Sonde list or Favourites.
- Added navigation to the nearest radiosonde by pressing the distance panel.
- Improved return-to-current-location behaviour.
- Fixed map focus remaining on a previously selected radiosonde.
- Fixed blocked radiosondes remaining visible after being blocked.
- Radiosonde detail windows now close after the radiosonde is blocked.

### Nearest sonde

- The nearest-sonde distance is now always visible, including when the sonde is outside the configured detection rings.
- Added navigation from the distance panel to the nearest radiosonde.
- Added sonde type, last known altitude, launch site and date/time information.
- Added direct access to the corresponding Radiosondy.info page.
- Added an action for placing the nearest radiosonde on the Sonde blocklist.
- Improved layout for long labels and values.

### Sonde list

- Limited the visible result list to 200 radiosondes for better performance.
- Added search by radiosonde ID.
- Added detailed radiosonde information.
- Added **Show on map**.
- Added support for favourites.
- Added support for blocking radiosondes.
- Removed unnecessary type and ID filter controls from the previous list layout.

### Favourites

- Added a dedicated Favourites list.
- Added the ability to save and remove favourite radiosondes.
- Added direct navigation from a favourite to its map location.
- Added star-shaped map markers for favourite radiosondes.
- Yellow stars represent `Unknown` radiosondes.
- Purple stars represent `Needs Attention` radiosondes.

### Sonde blocklist

- Added the Sonde blocklist.
- Blocked radiosondes are hidden from the map.
- Blocked radiosondes are excluded from nearest-sonde calculations.
- Blocked radiosondes are excluded from detection and alerts.
- Added manual blocking by radiosonde ID.
- Added removal of individual blocked radiosondes.
- Added an option to clear the complete blocklist.

### Database

- Added Full and Lite dataset selection.
- Full contains available records from 19 March 2017 through today.
- Lite contains records from 1 January 2022 through today.
- Both datasets use a maximum radius of 600 km.
- Both datasets include `Unknown` and `Needs Attention` statuses.
- Both datasets use a maximum last known altitude of 2,000 metres.
- Added manual database download and update controls.
- Added optional automatic updates.
- Added optional Wi-Fi-only automatic updates.
- Improved incremental update date and time handling.
- Added database summary information for received, stored and displayed records.

### Detection and notifications

- Detection settings are now stored automatically without a Save button.
- Added a separate audio pattern for each detection ring.
- Audio patterns continue until they receive a stop or ring-change command.
- Added independent control of radiosonde detection notifications.
- The radiosonde notification setting does not disable Android's required ongoing GPS-service notification.
- Added a home-screen bell for quickly viewing or changing the alert state.
- Green indicates audio and radiosonde notifications are enabled.
- Red indicates audio is disabled while radiosonde notifications remain enabled.
- Grey indicates audio and radiosonde notifications are disabled.
- Detection audio uses the Android media volume.
- Improved notification tap handling so tapping a radiosonde alert opens SondeAlert.

### Drive Mode

- Simplified the Drive Mode interface.
- Removed an unused action button.
- Improved map visibility while driving.

### Fixes

- Fixed the map initially remaining on a world view after a valid location became available.
- Fixed selected radiosonde map focus returning after leaving and reopening the menu.
- Fixed blocked radiosondes continuing to participate in map or detection behaviour.
- Fixed inconsistent status colours between lists and map markers.
- Improved long-text handling in the nearest-sonde panel.
- Improved light-theme panel backgrounds and contrast.

---

## 1.0.2 (36) — Previous closed test

Version 1.0.2 was the earlier closed-test baseline.

It included:

- Interactive radiosonde map;
- GPS positioning;
- Detection radius and detection rings;
- Basic background detection;
- Audio alerts;
- Radiosonde list;
- Map filters;
- Local radiosonde database;
- Manual data updates;
- Drive Mode; and
- Direct links to Radiosondy.info.

Feedback from this version formed the basis of the interface, database, detection and performance work introduced in later test releases.

---

## Data source

Radiosonde information is provided by [Radiosondy.info](https://radiosondy.info/).

SondeAlert is independently developed. Radiosondy.info is not responsible for the operation, availability or use of SondeAlert.
