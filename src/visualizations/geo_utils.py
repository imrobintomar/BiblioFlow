"""Country name -> approximate centroid (capital city lat/lon) lookup, used
to draw collaboration arcs on the world map. geonamescache doesn't expose
true country centroids, so the capital city's coordinates are used as a
reasonable visual proxy -- accurate enough for an arc's endpoint, not
intended for precise geographic analysis."""

import difflib

import geonamescache

_gc = geonamescache.GeonamesCache()
_countries = _gc.get_countries()
_cities = _gc.get_cities()

_capital_coords: dict[str, tuple[float, float]] = {}
for _code, _country in _countries.items():
    capital_name = _country.get("capital")
    if not capital_name:
        continue
    for _city in _cities.values():
        if _city["countrycode"] == _code and _city["name"] == capital_name:
            _capital_coords[_country["name"]] = (_city["latitude"], _city["longitude"])
            break

_country_names = list(_capital_coords.keys())


def country_coordinates(name: str) -> tuple[float, float] | None:
    if name in _capital_coords:
        return _capital_coords[name]
    matches = difflib.get_close_matches(name, _country_names, n=1, cutoff=0.7)
    return _capital_coords[matches[0]] if matches else None
