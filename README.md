# Aerona Companion — v0.3.0 beta

A separate Home Assistant companion for the unofficial Grant Aerona3 integration. Adds a bundled Heating Studio sidebar, UI entity mapping, SQLite history and authenticated CSV downloads. It reads existing Home Assistant entities; it does not connect to Modbus, modify the Grant integration or automatically change heat-pump settings.

## Install through HACS

Add this repository as a custom **Integration** repository, download Aerona Companion, then restart Home Assistant. Go to Settings → Devices & services → Add integration → **Aerona Companion**. Select the Grant integration, confirm suggested entities, and choose optional readings. Open **Aerona Companion** in the sidebar. No dashboard YAML, separate themes or resource registration is required. Existing dashboards remain intact.

The dashboard is a bundled sidebar panel rather than a replacement Lovelace dashboard. Curve fields intentionally call `number.set_value` only when you edit them. Your existing tariff helpers may be selected during setup; their automations remain yours.

## What to record

Core: compressor state/frequency, flow, return and outdoor temperature. Optional: defrost, heating/DHW activity, curve endpoints, room temperatures, metered power/energy, electricity price and existing tariff helpers.

Default sampling is 60 seconds. State transitions are recorded when Home Assistant observes them. The Grant integration's polling interval remains the limit on resolution; sampling faster does not reveal transitions it missed. Use notes for comfort, thermostat changes and experiments.

## Retention and export

Retention **0** means no automatic deletion; finite retention prunes old records during recording. Switching to indefinite cannot restore deleted records. Recording begins at setup. The file `/config/aerona_companion.sqlite` should be backed up and free disk space monitored. Graphs use Home Assistant Recorder history; long-term companion data is available via CSV export. Administrator access is required for the panel, downloads and settings.

Downloads are paginated over Home Assistant's authenticated WebSocket connection and assembled in your browser; export large archives in monthly batches to reduce browser memory use. Nothing is uploaded to GitHub. CSV retains unavailable values and startup markers for interpreting gaps.

## Updates

Update the companion independently of the Grant plugin. Configuration lives in Home Assistant's config entry and the database remains outside the integration folder. If Grant entities change, use Configure to remap them. Suggested mappings use known unique-ID suffixes and can be overridden. This cannot guarantee compatibility with future changes in Grant entity semantics.

## Prototype migration

If you installed the earlier `aerona_logger` YAML prototype, disable that YAML logger before activating this companion to avoid duplicate collection. Keep its database and exports. This release does not automatically migrate the prototype database. Earlier dashboard files can be kept for comparison.

## Validation and beta limits

Python/JavaScript syntax and SQLite behaviour are tested locally. This release has not been exercised in a live Home Assistant installation. No automatic cycling scores, inferred savings or recommendations are claimed. Export observed data for analysis. Missing sensor data must not be interpreted as zero or as a confirmed compressor stop.

After installation, provide a sidebar screenshot, full logs for any errors, and a short CSV export. Then collect comparable 3–7 day periods before/after a single curve change.
