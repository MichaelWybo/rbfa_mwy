import logging
from datetime import datetime, timedelta
import json
import requests
from zoneinfo import ZoneInfo
from homeassistant.util import dt as dt_util
from .const import DOMAIN, VARIABLES, HASHES, REQUIRED, TZ, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

_LOGGER = logging.getLogger(__name__)

# Un match terminé depuis plus longtemps que ceci ne verra plus jamais son
# lieu ou son arbitre changer : on peut donc se fier au cache et arrêter de
# le re-télécharger à chaque cycle du coordinator.
MATCH_DETAIL_CACHE_AGE = timedelta(hours=3)

REQUEST_TIMEOUT = 15  # seconds


class RbfaUpdateError(Exception):
    """Raised when a required RBFA API call genuinely fails.

    This is only raised for real failures (network error, HTTP error,
    malformed/erroring GraphQL response) - never for a legitimate "no data"
    response (e.g. no matches scheduled), which is a normal state.
    """


class TeamApp(object):

    def __init__(self, hass, my_api):
        self.hass = hass
        self.team = my_api.data['team']

        # Utilise la langue configurée dans Home Assistant quand l'API RBFA
        # la supporte, sinon retombe sur le néerlandais. Recalculé à chaque
        # (re)démarrage : un changement de langue HA est donc pris en compte
        # automatiquement, sans jamais toucher entity_id/unique_id.
        hass_language = getattr(hass.config, 'language', None)
        self.language = hass_language if hass_language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        _LOGGER.debug('RBFA API language: %r (HA language: %r)', self.language, hass_language)

        # Valeurs par défaut pour éviter tout AttributeError si le tout
        # premier appel à update() échoue avant d'avoir pu les définir.
        self.teamdata = {}
        self.collections = []
        self.matchdata = {'upcoming': None, 'lastmatch': None}

        # Cache des détails (lieu + arbitre) des matchs déjà joués, par id
        # de match : {'location': ..., 'referee': ...}
        self._match_detail_cache = {}

    def __get_url(self, operation, value):
        main_url = 'https://datalake-prod2018.rbfa.be/graphql'
        payload = {"operationName": operation,
        "variables": {VARIABLES[operation]: value, "language": self.language},
        "extensions": {"persistedQuery": {"version":1, "sha256Hash": HASHES[operation]}}}
        headers = {'content-type': 'application/json'}

        try:
            response = self.s.post(main_url, data=json.dumps(payload), headers=headers, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as exc:
            _LOGGER.error('Error occurred while fetching data for %s: %r', operation, exc)
            raise RbfaUpdateError(f"Network error calling {operation}: {exc}") from exc

        if response.status_code != 200:
            _LOGGER.debug('Invalid response from server for collection data')
            raise RbfaUpdateError(f"RBFA API returned HTTP {response.status_code} for {operation}")

        rj = response.json()
        if rj.get('data') is None:
            error_message = rj.get('errors', [{}])[0].get('message', 'unknown error')
            _LOGGER.debug("Error for operation {}: {}".format(operation, error_message))
            raise RbfaUpdateError(f"RBFA API error for {operation}: {error_message}")

        if rj['data'][REQUIRED[operation]] is None:
            # Réponse valide mais vide (ex. aucun match programmé) : ce
            # n'est pas une erreur, juste un résultat vide.
            _LOGGER.debug('no results for %s', operation)
            return None

        return rj

    def __get_team(self):
        response = self.__get_url('GetTeam', self.team)
        return response

    def __get_data(self):
        response = self.__get_url('GetTeamCalendar', self.team)
        return response

    def __get_match(self):
        response = self.__get_url('GetMatchDetail', self.match)
        return response

    def __get_ranking(self):
        response = self.__get_url('GetSeriesRankings', self.series)
        return response

    async def __get_match_detail(self, match_id, starttime, endtime, now):
        """Return {'location': ..., 'referee': ...} for a match.

        Uses a cache for matches that ended a while ago, since their
        location/referee never change afterwards. Falls back to the cached
        value (if any) when a fresh fetch fails, so a transient network
        error on one old match doesn't wipe previously known data.
        """
        cached = self._match_detail_cache.get(match_id)
        if cached is not None and endtime < now - MATCH_DETAIL_CACHE_AGE:
            return cached

        self.match = match_id
        try:
            r = await self.hass.async_add_executor_job(self.__get_match)
        except RbfaUpdateError as exc:
            _LOGGER.warning('Could not fetch match detail for %s: %s', match_id, exc)
            return cached or {'location': None, 'referee': None}

        location = None
        referee = None
        if r is not None:
            match_location = r['data']['matchDetail']['location']
            location = '{}\n{} {}\nBelgium'.format(
                match_location['address'],
                match_location['postalCode'],
                match_location['city'],
            )
            officials = r['data']['matchDetail']['officials']
            for x in officials:
                if x['function'] == 'referee':
                    referee = f"{x['firstName']} {x['lastName']}"

        detail = {'location': location, 'referee': referee}
        self._match_detail_cache[match_id] = detail
        return detail

    async def update(self, my_api):
        with requests.Session() as self.s:
            _LOGGER.debug('Updating match details using Rest API')

            _LOGGER_LEVEL = logging.getLogger(__name__).getEffectiveLevel()
            _LOGGER_DEFAULT = logging.getLogger("default").getEffectiveLevel()

            if _LOGGER_LEVEL == 10:
                logging.getLogger("urllib3").setLevel(logging.DEBUG)
            else:
                logging.getLogger("urllib3").setLevel(_LOGGER_DEFAULT)

            if 'duration' in my_api.options:
                self.duration = my_api.options['duration']
            else:
                self.duration = my_api.data['duration']

            if 'show_ranking' in my_api.options:
                self.show_ranking = my_api.options['show_ranking']
            elif 'show_ranking' in my_api.data:
                self.show_ranking = my_api.data['show_ranking']
            else:
                self.show_ranking = True

            if 'show_referee' in my_api.options:
                self.show_referee = my_api.options['show_referee']
            elif 'show_referee' in my_api.data:
                self.show_referee = my_api.data['show_referee']
            else:
                self.show_referee = True

            self.collections = [];
            _LOGGER.debug('duration: %r', self.duration)
            _LOGGER.debug('show ranking: %r', self.show_ranking)

            now = dt_util.utcnow()

            # Echec critique : sans les infos de l'équipe, il n'y a rien à
            # afficher de fiable -> on laisse l'exception remonter pour que
            # le coordinator marque les entités "unavailable".
            r = await self.hass.async_add_executor_job(self.__get_team)
            if r is not None:
                self.teamdata = r['data']['team']

            # Echec critique également : sans le calendrier, aucune donnée
            # de match n'est disponible cette fois-ci.
            r = await self.hass.async_add_executor_job(self.__get_data)
            if r is not None:
                upcoming = False
                previous = None

                self.collections = []

                for item in r['data']['teamCalendar']:
                    match_id = item['id']

                    naive_dt  = datetime.strptime(item['startTime'], '%Y-%m-%dT%H:%M:%S')
                    starttime = naive_dt.replace(tzinfo = ZoneInfo(TZ))
                    endtime = starttime + timedelta(minutes=self.duration)

                    detail = await self.__get_match_detail(match_id, starttime, endtime, now)
                    location = detail['location']
                    # Le cache garde toujours l'arbitre s'il a été trouvé un
                    # jour, indépendamment de l'option show_referee : on ne
                    # l'expose ici que si l'option est active, pour ne pas
                    # perdre l'info si l'utilisateur la réactive plus tard.
                    referee = detail['referee'] if self.show_referee else None

                    matchdata = {
                        'matchid': item['id'],
                        'team': self.team,
                        'channel': item['channel'],
                        'starttime': starttime,
                        'endtime': endtime,
                        'location': location,
                        'referee': referee,
                        'hometeam': item['homeTeam']['name'],
                        'hometeamid': item['homeTeam']['id'],
                        'hometeamlogo': item['homeTeam']['logo'],
                        'hometeamgoals': item['outcome']['homeTeamGoals'],
                        'hometeampenalties': item['outcome']['homeTeamPenaltiesScored'],
                        'hometeamposition': None,
                        'awayteam': item['awayTeam']['name'],
                        'awayteamid': item['awayTeam']['id'],
                        'awayteamlogo': item['awayTeam']['logo'],
                        'awayteamgoals': item['outcome']['awayTeamGoals'],
                        'awayteampenalties': item['outcome']['awayTeamPenaltiesScored'],
                        'awayteamposition': None,
                        'series': item['series']['name'],
                        'seriesid': item['series']['id'],
                        'ranking': [],
                    }

                    if endtime >= now and not upcoming:

                        upcoming = True
                        self.matchdata = {
                            'upcoming': matchdata,
                            'lastmatch': previous
                        }
                        if self.show_ranking:
                            await self.get_ranking('upcoming')
                            if previous is not None:
                                await self.get_ranking('lastmatch')

                    summary = item['homeTeam']['name'] + ' - ' + item['awayTeam']['name']
                    description = item['series']['name'] + ' (state: ' + item['state'] + ')'

                    if self.show_ranking:
                        result = 'No match score'
                        if item['outcome']['homeTeamGoals'] is not None:
                            result = 'Goals: ' + str(item['outcome']['homeTeamGoals']) + ' - ' + str(item['outcome']['awayTeamGoals'])
                        if item['outcome']['homeTeamPenaltiesScored'] is not None:
                            result += '; Penalties: ' + str(item['outcome']['homeTeamPenaltiesScored']) + ' - '
                            result += str(item['outcome']['awayTeamPenaltiesScored'])
                        description += "; " + result

                    collection = {
                        'uid': item['id'],
                        'starttime': starttime,
                        'endtime': endtime,
                        'summary': summary,
                        'location': location,
                        'description': description,
                    }

                    self.collections.append(collection)
                    previous = matchdata

                if not upcoming:
                    _LOGGER.debug('previous=last')
                    self.matchdata = {
                        'upcoming': None,
                        'lastmatch': previous
                    }
                    if self.show_ranking:
                        await self.get_ranking('lastmatch')

    async def get_ranking(self, tag):
        _LOGGER.debug('show ranking')

        self.series = self.matchdata[tag]['seriesid']
        try:
            r = await self.hass.async_add_executor_job(self.__get_ranking)
        except RbfaUpdateError as exc:
            # Le classement est une info secondaire : on ne fait pas
            # échouer tout le cycle de mise à jour pour ça.
            _LOGGER.warning('Could not fetch ranking for series %s: %s', self.series, exc)
            return

        if r is not None:
            for rank in r['data']['seriesRankings']['rankings'][0]['teams']:
                rankteam = {
                    'position': rank['position'],
                    'team': rank['name'],
                    'id': rank['teamId'],
                    'clubid': rank.get('clubId'),
                    'clubregistrationnumber': rank.get('clubRegistrationNumber'),
                    'logo': rank.get('logo'),
                    'points': rank.get('points'),
                    'played': rank.get('matchesPlayed'),
                    'won': rank.get('matchesWon'),
                    'drawn': rank.get('matchesDrawn'),
                    'lost': rank.get('matchesLost'),
                    'goalsfor': rank.get('goalsFor'),
                    'goalsagainst': rank.get('goalsAgainst'),
                    'goaldifference': rank.get('goalDifference'),
                    'fairplaypercentage': rank.get('fairplayPercentage'),
                }
                self.matchdata[tag]['ranking'].append(rankteam)
                if rank['teamId'] == self.matchdata[tag]['hometeamid']:
                    self.matchdata[tag]['hometeamposition'] = rank['position']
                if rank['teamId'] == self.matchdata[tag]['awayteamid']:
                    self.matchdata[tag]['awayteamposition'] = rank['position']
