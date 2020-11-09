# Project Description
This mini-project scraped the NYT county level 2020 election data and generates a map that shows vote share between Biden and Trump as well as the turnout in each county a la [the muddy map](https://stemlounge.com/muddy-america-color-balancing-trumps-election-map-infographic/).

# The County Map
The lightness of each color in this county map shows the number of voters in each county (lighter is fewer) while the hue shows the relative stregth of each candidate (gray is a split decision). This presentation avoids the trap of showing large, but largely uninhabited areas as being bright red (or blue, but due to the correlation between rural voters and republican leaning, often red), thus misleading the viewer.

![County Map](https://raw.githubusercontent.com/dangrenell/2020-Election-Map/master/county_muddy_map.png)

# Data Sources
- Census shape data from [the census website](https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html)
- County/town returns from the [NYT coverage](https://www.nytimes.com/interactive/2020/11/03/us/elections/results-president.html?action=click&module=Spotlight&pgtype=Homepage)