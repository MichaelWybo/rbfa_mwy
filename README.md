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

Example card
-
![Example](https://github.com/rgerbranda/rbfa/blob/main/images/example.png)

Match card
-
<img src="https://github.com/rgerbranda/rbfa/blob/main/images/match_sheet.png" alt="Match card" width=528>

The match card is based on the [Markdown card](https://www.home-assistant.io/dashboards/markdown/).

Entity IDs are now built from your team ID and are the same regardless of the Home Assistant language, following the pattern `sensor.<team>_<upcoming|lastmatch>_<key>` (e.g. `sensor.300872_upcoming_hometeam`) and `calendar.<team>` for the calendar (e.g. `calendar.300872`). Check **Developer tools > States** to find yours, then replace the sensor names below.

Add a Markdown card with the following content. Note: replace `300872` by your own team ID.

```
<table width="100%">
<tr>
<th colspan=2>{{states('sensor.300872_upcoming_series')}}</th>
</tr>
<tr>
<th colspan=2>
<a href="https://www.rbfa.be/nl/wedstrijd/{{ states('sensor.300872_upcoming_matchid') }}">{{as_timestamp(states('sensor.300872_upcoming_starttime'))|timestamp_custom('%d-%m-%y om %H:%M uur')}}</a></th>
</tr>
<tr>
<td align="center"><img src="{{state_attr('sensor.300872_upcoming_hometeam','entity_picture')}}" width="64"></td>
<td align="center"><img src="{{state_attr('sensor.300872_upcoming_awayteam','entity_picture')}}" width="64"></td>
</tr>
<tr>
<td align="center">{{states('sensor.300872_upcoming_hometeam')}}</td>
<td align="center">{{states('sensor.300872_upcoming_awayteam')}}</td>
</tr>
<tr>
<td align="center">Positie: {{state_attr('sensor.300872_upcoming_hometeam','position')}}</td>
<td align="center">Positie: {{state_attr('sensor.300872_upcoming_awayteam', 'position')}}</td>
</tr>
<tr>
<td align="center" colspan="2">{{states('sensor.300872_upcoming_location') | replace("\n",", ")}}</td>
</tr>
<tr>
<td align="center" colspan="2">Scheidsrechter: {{states('sensor.300872_upcoming_referee') }}</td>
</table>
```


Ranking card
-

```
type: markdown
title: Ranking
content: >-
  {% set sensor = "sensor.300872_upcoming_series" %}

  {{state_attr(sensor, "Series") }}

  -

  {% if state_attr(sensor, "ranking") != None %}
  {% for item in state_attr(sensor, "ranking") %}

  {{ item.position }}. {% if item.id == state_attr(sensor, "baseid") %}**{{item.team}}**
  {% else %}{{item.team}}
  {% endif %}
  {% endfor %} 
  {% endif %}
```

<img src="https://github.com/rgerbranda/rbfa/blob/main/images/ranking.png" alt="Ranking" width=528>

<img src="https://github.com/home-assistant/brands/blob/c359584cf6719b89aee0428cdb55da55c5b34593/custom_integrations/rbfa/logo.png" alt="Royal Belgian Football Association" height=128>
