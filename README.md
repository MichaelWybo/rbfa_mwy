TEST CODE MODIF FROM [@rgerbranda](https://github.com/rgerbranda/rbfa/)


Add the calendar of your soccer team to Home Assistant. The data is gathered from the Royal Belgian Football Association ([RBFA](https://www.rbfa.be/)) website in cooporation with Association Clubs Francophones de Football ([ACFF](https://www.acff.be/)) and [Voetbal Vlaanderen](https://www.voetbalvlaanderen.be/).

[![Hacs validation](https://github.com/rgerbranda/rbfa/actions/workflows/validate.yaml/badge.svg)](https://github.com/rgerbranda/rbfa/actions/workflows/validate.yaml)
[![Hassfest validation](https://github.com/rgerbranda/rbfa/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/rgerbranda/rbfa/actions/workflows/hassfest.yaml)

[![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=rgerbranda&repository=rbfa&category=integration)

Configuration
-
![Example](https://github.com/rgerbranda/rbfa/blob/main/images/configuration.png)

The team number is the number after 'ploeg': https://www.rbfa.be/nl/club/2438/ploeg/300872/overzicht

Language
-
The integration automatically fetches match data (series name, referee, ...) in the language configured in Home Assistant (French, Dutch or English). Any other Home Assistant language falls back to Dutch. This only affects the *content* of the sensors, never their entity_id: entities are identical no matter which language Home Assistant runs in.

Enabling the sensors
-
To limit clutter and unnecessary recorder writes, the match/team sensors (not the calendar) are **disabled by default**. Before building a dashboard card, enable the ones you need in **Settings > Devices & services > Entities**, search for your team ID, select the sensors, and click **Enable**. After enabling, you may need to reload the integration for the entities to become available.

Example card
-
![Example](https://github.com/rgerbranda/rbfa/blob/main/images/example.png)

Match card
-
<img src="https://github.com/rgerbranda/rbfa/blob/main/images/match_sheet.png" alt="Match card" width=528>

The match card is based on the [Markdown card](https://www.home-assistant.io/dashboards/markdown/).

Entity IDs are built from your team ID and stay the same regardless of the Home Assistant language, following the pattern `sensor.<team>_<upcoming|lastmatch>_<key>` (e.g. `sensor.300872_upcoming_hometeam`) and `calendar.<team>` for the calendar (e.g. `calendar.300872`). Check **Developer tools > States** to confirm yours.

The card only sets the team ID once (`{% set team = '300872' %}`) and builds every entity_id from it — change that single line if you use several teams. The static labels (`Positie`, `Scheidsrechter`, ...) are plain text in the card, they are **not** auto-translated like the entity names are, so pick the variant matching your language, or edit the labels yourself.

<details>
<summary>Dutch (NL)</summary>

```
{% set team = '300872' %}
{% set thuis = 'sensor.' ~ team ~ '_upcoming_hometeam' %}
{% set uit = 'sensor.' ~ team ~ '_upcoming_awayteam' %}
{% set reeks = 'sensor.' ~ team ~ '_upcoming_series' %}
{% set locatie = 'sensor.' ~ team ~ '_upcoming_location' %}
{% set wedstrijd_id = 'sensor.' ~ team ~ '_upcoming_matchid' %}
{% set start = 'sensor.' ~ team ~ '_upcoming_starttime' %}
{% set scheidsrechter = 'sensor.' ~ team ~ '_upcoming_referee' %}
<table width="100%">
<tr>
<th colspan="2">{{ states(reeks) }}</th>
</tr>
<tr>
<th colspan="2">
<a href="https://www.rbfa.be/nl/wedstrijd/{{ states(wedstrijd_id) }}">{{ as_timestamp(states(start)) | timestamp_custom('%d-%m-%y om %H:%M uur') }}</a>
</th>
</tr>
<tr>
<td align="center"><img src="{{ state_attr(thuis, 'entity_picture') }}" width="64"></td>
<td align="center"><img src="{{ state_attr(uit, 'entity_picture') }}" width="64"></td>
</tr>
<tr>
<td align="center">{{ states(thuis) }}</td>
<td align="center">{{ states(uit) }}</td>
</tr>
<tr>
<td align="center">Positie: {{ state_attr(thuis, 'position') }}</td>
<td align="center">Positie: {{ state_attr(uit, 'position') }}</td>
</tr>
<tr>
<td align="center" colspan="2">{{ states(locatie) | replace("\n", ", ") }}</td>
</tr>
{% if states(scheidsrechter) not in ['unknown', 'unavailable'] %}
<tr>
<td align="center" colspan="2">Scheidsrechter: {{ states(scheidsrechter) }}</td>
</tr>
{% endif %}
</table>
```
</details>

<details>
<summary>French (FR)</summary>

```
{% set team = '300872' %}
{% set domicile = 'sensor.' ~ team ~ '_upcoming_hometeam' %}
{% set exterieur = 'sensor.' ~ team ~ '_upcoming_awayteam' %}
{% set competition = 'sensor.' ~ team ~ '_upcoming_series' %}
{% set lieu = 'sensor.' ~ team ~ '_upcoming_location' %}
{% set match_id = 'sensor.' ~ team ~ '_upcoming_matchid' %}
{% set debut = 'sensor.' ~ team ~ '_upcoming_starttime' %}
{% set arbitre = 'sensor.' ~ team ~ '_upcoming_referee' %}
<table width="100%">
<tr>
<th colspan="2">{{ states(competition) }}</th>
</tr>
<tr>
<th colspan="2">
<a href="https://www.rbfa.be/fr/match/{{ states(match_id) }}">{{ as_timestamp(states(debut)) | timestamp_custom('%d-%m-%y à %H:%M') }}</a>
</th>
</tr>
<tr>
<td align="center"><img src="{{ state_attr(domicile, 'entity_picture') }}" width="64"></td>
<td align="center"><img src="{{ state_attr(exterieur, 'entity_picture') }}" width="64"></td>
</tr>
<tr>
<td align="center">{{ states(domicile) }}</td>
<td align="center">{{ states(exterieur) }}</td>
</tr>
<tr>
<td align="center">Position : {{ state_attr(domicile, 'position') }}</td>
<td align="center">Position : {{ state_attr(exterieur, 'position') }}</td>
</tr>
<tr>
<td align="center" colspan="2">{{ states(lieu) | replace("\n", ", ") }}</td>
</tr>
{% if states(arbitre) not in ['unknown', 'unavailable'] %}
<tr>
<td align="center" colspan="2">Arbitre : {{ states(arbitre) }}</td>
</tr>
{% endif %}
</table>
```
</details>

<details>
<summary>English (EN)</summary>

```
{% set team = '300872' %}
{% set home = 'sensor.' ~ team ~ '_upcoming_hometeam' %}
{% set away = 'sensor.' ~ team ~ '_upcoming_awayteam' %}
{% set series = 'sensor.' ~ team ~ '_upcoming_series' %}
{% set location = 'sensor.' ~ team ~ '_upcoming_location' %}
{% set match_id = 'sensor.' ~ team ~ '_upcoming_matchid' %}
{% set start = 'sensor.' ~ team ~ '_upcoming_starttime' %}
{% set referee = 'sensor.' ~ team ~ '_upcoming_referee' %}
<table width="100%">
<tr>
<th colspan="2">{{ states(series) }}</th>
</tr>
<tr>
<th colspan="2">
<a href="https://www.rbfa.be/en/match/{{ states(match_id) }}">{{ as_timestamp(states(start)) | timestamp_custom('%d-%m-%y at %H:%M') }}</a>
</th>
</tr>
<tr>
<td align="center"><img src="{{ state_attr(home, 'entity_picture') }}" width="64"></td>
<td align="center"><img src="{{ state_attr(away, 'entity_picture') }}" width="64"></td>
</tr>
<tr>
<td align="center">{{ states(home) }}</td>
<td align="center">{{ states(away) }}</td>
</tr>
<tr>
<td align="center">Position: {{ state_attr(home, 'position') }}</td>
<td align="center">Position: {{ state_attr(away, 'position') }}</td>
</tr>
<tr>
<td align="center" colspan="2">{{ states(location) | replace("\n", ", ") }}</td>
</tr>
{% if states(referee) not in ['unknown', 'unavailable'] %}
<tr>
<td align="center" colspan="2">Referee: {{ states(referee) }}</td>
</tr>
{% endif %}
</table>
```
</details>

Ranking card
-

Same principle: the team ID is set once, and the series name now comes from `states(...)` (the sensor's own state) instead of a non-existent `"Series"` attribute.

```
type: markdown
title: Ranking
content: >-
  {% set team = '300872' %}
  {% set reeks = 'sensor.' ~ team ~ '_upcoming_series' %}

  {{ states(reeks) }}

  -

  {% if state_attr(reeks, "ranking") is not none %}
  {% for item in state_attr(reeks, "ranking") %}

  {{ item.position }}. {% if item.id == state_attr(reeks, "baseid") %}**{{ item.team }}**
  {% else %}{{ item.team }}
  {% endif %}
  {% endfor %} 
  {% endif %}
```

<img src="https://github.com/rgerbranda/rbfa/blob/main/images/ranking.png" alt="Ranking" width=528>

<img src="https://github.com/home-assistant/brands/blob/c359584cf6719b89aee0428cdb55da55c5b34593/custom_integrations/rbfa/logo.png" alt="Royal Belgian Football Association" height=128>
