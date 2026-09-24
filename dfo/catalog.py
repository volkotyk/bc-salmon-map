"""Hand-maintained knowledge that the DFO tables do not contain.

- which DFO water / place name maps to which map geometry
- district, display names, curated notes
- Ukrainian and French wording for DFO phrases

Everything the fishing rules *say* (species, dates, limits, gear, closures) comes from the DFO pages.
When DFO uses a name that is not here, dfo/update.py refuses to publish and opens an issue.
"""


def B(uk, en, fr=None):
    """Page text in three languages. fr defaults to en for proper names that French keeps as they are."""
    return {"uk": uk, "en": en, "fr": en if fr is None else fr}


SQUAMISH = B("Басейн Squamish: разом не більше 1 заводського кижуча (Coho) на день.",
             "Squamish watershed: aggregate daily limit of 1 hatchery marked Coho for all non-tidal waters.",
             "Bassin de la Squamish : au total, 1 coho marqué d'écloserie par jour pour toutes les eaux non soumises à la marée.")
TRIBS = B("Разом з притоками.", "Including tributaries.", "Affluents compris.")

# DFO "Waters" cell -> map entry. id = geometry key in build/geo.json.
FRESH = {
    "Alouette River and tributaries": dict(id="alouette", d="tri", name="Alouette River", sec=TRIBS),
    "Ashlu Creek": dict(id="ashlu", d="sea", name="Ashlu Creek", notes=[SQUAMISH]),
    "Capilano River": dict(id="capilano", d="north", name="Capilano River"),
    "Chapman Creek": dict(id="chapman", d="sun", name="Chapman Creek"),
    "Cheakamus River": dict(id="cheakamus", d="sea", name="Cheakamus River", notes=[SQUAMISH]),
    "Chehalis River": dict(id="chehalis", d="valley", name="Chehalis River"),
    "Chilliwack/Vedder River (including Sumas River)": dict(
        id="chilliwack", d="valley", name=B("Chilliwack / Vedder River (з Sumas River)", "Chilliwack / Vedder River (incl. Sumas River)",
                                          "Chilliwack / Vedder River (avec la Sumas River)")),
    "Coquitlam River": dict(id="coquitlam", d="tri", name="Coquitlam River"),
    "De Boville Slough": dict(id="deboville", d="tri", name="De Boville Slough"),
    "Fraser River": dict(id="fraser-closed", d="valley", name=B("Fraser River (основне русло)", "Fraser River (mainstem)", "Fraser River (cours principal)"),
                         notes=[B("Нижче мосту CPR у Mission — припливна частина, див. Area 29.",
                                  "Below the CPR bridge at Mission is tidal water, see Area 29.",
                                  "En aval du pont du CPR à Mission, ce sont des eaux à marée : voir le secteur 29.")]),
    "Harrison River": dict(id="harrison", d="valley", name="Harrison River"),
    "Kanaka Creek": dict(id="kanaka", d="tri", name="Kanaka Creek"),
    "Khartoum Lake": dict(id="khartoum", d="sun", name="Khartoum Lake", lake=True),
    "Little Campbell River": dict(id="little-campbell", d="sur", name="Little Campbell River"),
    "Lois Lake": dict(id="lois", d="sun", name="Lois Lake", lake=True),
    "Mamquam River": dict(id="mamquam", d="sea", name="Mamquam River", notes=[SQUAMISH]),
    "Nicomekl River": dict(id="nicomekl", d="sur", name="Nicomekl River"),
    "Nicomen (including Dewdney) Slough": dict(
        id="nicomen", d="valley", name=B("Nicomen Slough (з Dewdney Slough)", "Nicomen Slough (incl. Dewdney Slough)",
                                       "Nicomen Slough (avec le Dewdney Slough)")),
    "Norrish (Suicide) Creek": dict(id="norrish", d="valley", name="Norrish (Suicide) Creek"),
    "Serpentine River": dict(id="serpentine", d="sur", name="Serpentine River"),
    "Squamish River (including Powerhouse Channel)": dict(
        id="squamish", d="sea", name=B("Squamish River (з Powerhouse Channel)", "Squamish River (incl. Powerhouse Channel)",
                                        "Squamish River (avec le Powerhouse Channel)"), notes=[SQUAMISH]),
    "Stave River": dict(id="stave", d="valley", name="Stave River"),
}

# DFO "Specific area" rows that are drawn as their own line on the map.
SECTION_WATERS = {
    "North Alouette and tributaries": dict(id="n-alouette", d="tri", name="North Alouette River", sec=TRIBS),
}

# Ukrainian for DFO "Specific area" texts. Missing entries are shown in English.
AREA_UK = {
    "Upstream of the 216th Street bridge to a line between two fishing boundary signs at Allco park":
        "Вище мосту 216th Street до знаків межі в Allco Park",
    "Downstream of the 216th street bridge to the confluence of the Pitt River":
        "Нижче мосту 216th Street до впадіння в Pitt River",
    "including tributaries": "Разом з притоками.",
    "upstream of tidal water fishing boundary signs located below the Hwy 101 Bridge to 100 m below the falls. The falls are located approximately 550 m upstream of the powerline crossing.":
        "Від знаків межі припливних вод нижче мосту Hwy 101 до точки за 100 м нижче водоспаду (приблизно 550 м вище ЛЕП).",
    "downstream of the logging bridge 2.4 km downstream of Chehalis Lake, including tributaries to that part":
        "Нижче лісовозного мосту за 2,4 км від Chehalis Lake, разом з притоками.",
    "from a line between 2 fishing boundary signs on either side of the Chilliwack River 100 m downstream from the confluence of the Chilliwack River and Slesse Creek downstream including that portion of the Sumas River from the Barrow Town Pump Station downstream to fishing boundary signs near the confluence with the Fraser River.":
        "Від знаків за 100 м нижче злиття зі Slesse Creek вниз за течією, разом з Sumas River від насосної станції Barrow Town до знаків біля Fraser.",
    "downstream of the confluence of Cedar Creek and Hyde Creek.": "Нижче злиття Cedar Creek і Hyde Creek.",
    "mainstem waters upstream of the CPR Bridge at Mission, BC": "Основне русло вище залізничного мосту CPR у Mission.",
    "from the outlet of Harrison Lake downstream to the Highway 7 Bridge": "Від витоку з Harrison Lake до мосту Highway 7",
    "from the Highway 7 Bridge downstream to the confluence with the Fraser River": "Від мосту Highway 7 до впадіння у Fraser River",
    "downstream of the 112th Street bridge.": "Нижче мосту 112th Street.",
    "downstream of 12th Avenue, including tributaries to that part.": "Нижче 12th Avenue, разом з притоками цієї частини",
    "downstream of a line between 2 fishing boundary signs on either side of the Little Campbell River to the pedestrian bridge at the foot of Stayte Road.":
        "Від знаків межі до пішохідного мосту в кінці Stayte Road",
    "downstream of 208th Street": "Нижче 208th Street.",
    "from the confluence of Siddle (Bell's) Creek downstream to the Fraser River": "Від злиття з Siddle (Bell's) Creek до Fraser River.",
    "downstream of 168th Street at Bothwell Park": "Нижче 168th Street біля Bothwell Park.",
    "downstream of B.C. Hydro Dam to the CPR Railway Bridge; except you shall not fish for salmon in that portion on the east side of the Stave River, known as the Ruskin Spawning Channel on the east bank of the BC Hydro park from the inlet near the dam, downstream to the boat ramp crossing; and you shall not fish for salmon in that portion on the west side of the Stave River known as the Northrop Spawning Channel from the intake downstream to where the channel joins the Stave River mainstem, including its tributary containing the fishway":
        "Від дамби BC Hydro до залізничного мосту CPR. Не ловіть у нерестових каналах Ruskin (східний берег) і Northrop (західний берег, разом з притокою з рибоходом).",
}

# French for DFO "Specific area" texts. Missing entries are shown in English.
AREA_FR = {
    "Upstream of the 216th Street bridge to a line between two fishing boundary signs at Allco park":
        "En amont du pont de la 216th Street jusqu'aux panneaux de limite de pêche du parc Allco",
    "Downstream of the 216th street bridge to the confluence of the Pitt River":
        "En aval du pont de la 216th Street jusqu'au confluent de la Pitt River",
    "including tributaries": "Affluents compris.",
    "upstream of tidal water fishing boundary signs located below the Hwy 101 Bridge to 100 m below the falls. The falls are located approximately 550 m upstream of the powerline crossing.":
        "Des panneaux de limite des eaux à marée sous le pont de l'autoroute 101 jusqu'à 100 m en aval de la chute (environ 550 m en amont de la ligne électrique).",
    "downstream of the logging bridge 2.4 km downstream of Chehalis Lake, including tributaries to that part":
        "En aval du pont forestier situé à 2,4 km en aval du Chehalis Lake, affluents de ce tronçon compris.",
    "from a line between 2 fishing boundary signs on either side of the Chilliwack River 100 m downstream from the confluence of the Chilliwack River and Slesse Creek downstream including that portion of the Sumas River from the Barrow Town Pump Station downstream to fishing boundary signs near the confluence with the Fraser River.":
        "Des panneaux situés 100 m en aval du confluent avec le Slesse Creek vers l'aval, avec la Sumas River de la station de pompage Barrow Town jusqu'aux panneaux près du Fraser.",
    "downstream of the confluence of Cedar Creek and Hyde Creek.": "En aval du confluent du Cedar Creek et du Hyde Creek.",
    "mainstem waters upstream of the CPR Bridge at Mission, BC": "Cours principal en amont du pont ferroviaire du CPR à Mission.",
    "from the outlet of Harrison Lake downstream to the Highway 7 Bridge": "De la décharge du Harrison Lake jusqu'au pont de l'autoroute 7",
    "from the Highway 7 Bridge downstream to the confluence with the Fraser River": "Du pont de l'autoroute 7 jusqu'au confluent avec le Fraser",
    "downstream of the 112th Street bridge.": "En aval du pont de la 112th Street.",
    "downstream of 12th Avenue, including tributaries to that part.": "En aval de la 12th Avenue, affluents de ce tronçon compris.",
    "downstream of a line between 2 fishing boundary signs on either side of the Little Campbell River to the pedestrian bridge at the foot of Stayte Road.":
        "Des panneaux de limite de pêche jusqu'à la passerelle au bout de Stayte Road.",
    "downstream of 208th Street": "En aval de la 208th Street.",
    "from the confluence of Siddle (Bell's) Creek downstream to the Fraser River": "Du confluent du Siddle (Bell's) Creek jusqu'au Fraser.",
    "downstream of 168th Street at Bothwell Park": "En aval de la 168th Street, au parc Bothwell.",
    "downstream of B.C. Hydro Dam to the CPR Railway Bridge; except you shall not fish for salmon in that portion on the east side of the Stave River, known as the Ruskin Spawning Channel on the east bank of the BC Hydro park from the inlet near the dam, downstream to the boat ramp crossing; and you shall not fish for salmon in that portion on the west side of the Stave River known as the Northrop Spawning Channel from the intake downstream to where the channel joins the Stave River mainstem, including its tributary containing the fishway":
        "Du barrage de BC Hydro jusqu'au pont ferroviaire du CPR. Pêche interdite dans les chenaux de frai Ruskin (rive est) et Northrop (rive ouest, avec son affluent à passe migratoire).",
}

# ---------- tidal ----------
AREA_SUBS = {"28": [f"28-{i}" for i in range(1, 15)], "29": [f"29-{i}" for i in range(1, 18)]}

# Display names for groups of subareas that share the same rules. Other groups get a generic name.
GROUP_NAMES = {
    frozenset(s for s in AREA_SUBS["28"] if s != "28-8"): B("Howe Sound і Burrard Inlet", "Howe Sound & Burrard Inlet", "Howe Sound et Burrard Inlet"),
    frozenset(AREA_SUBS["28"]): B("Howe Sound і Burrard Inlet", "Howe Sound & Burrard Inlet", "Howe Sound et Burrard Inlet"),
    frozenset({"28-8"}): B("False Creek", "False Creek"),
    frozenset({"29-1", "29-2", "29-3", "29-4", "29-5", "29-8"}): B("Strait of Georgia", "Strait of Georgia", "Détroit de Géorgie"),
    frozenset({"29-6", "29-7"} | {f"29-{i}" for i in range(9, 18)}): B("Припливна Fraser, Roberts Bank, Boundary Bay", "Tidal Fraser, Roberts Bank, Boundary Bay",
                                                                           "Fraser à marée, Roberts Bank, Boundary Bay"),
}

# DFO restriction "Areas" names -> subareas (for popup notes). "mouth" = the Mouth of the Fraser closure polygon.
PLACES = {
    "Mannion Bay (Deep Bay)": ["28-2"],
    "Point Atkinson": ["28-6"],
    "Porteau Cove": ["28-4"],
    "Whytecliff Park": ["28-2"],
    "Capilano River": ["28-9"],
    "Seymour River": ["28-10"],
    "Portion of Subarea 29-1 in front of Chapman Creek": ["29-1"],
    "Tidal portion of the Fraser River (in Area 29)": ["29-9", "29-11", "29-12", "29-13", "29-14", "29-15", "29-16", "29-17"],
    "Tidal Portion of Fraser River (Area 29)": ["29-9", "29-11", "29-12", "29-13", "29-14", "29-15", "29-16", "29-17"],
    "Mouth of the Fraser River Salmon Closure": "mouth",
}
PLACE_UK = {
    "Portion of Subarea 29-1 in front of Chapman Creek": "Смуга 29-1 перед Chapman Creek",
    "Tidal portion of the Fraser River (in Area 29)": "Припливна частина Fraser (Area 29)",
    "Tidal Portion of Fraser River (Area 29)": "Припливна частина Fraser (Area 29)",
    "Mouth of the Fraser River Salmon Closure": "Закриття гирла Fraser",
}
PLACE_FR = {
    "Portion of Subarea 29-1 in front of Chapman Creek": "Partie du sous-secteur 29-1 devant le Chapman Creek",
    "Tidal portion of the Fraser River (in Area 29)": "Partie à marée du Fraser (secteur 29)",
    "Tidal Portion of Fraser River (Area 29)": "Partie à marée du Fraser (secteur 29)",
    "Mouth of the Fraser River Salmon Closure": "Fermeture de l'embouchure du Fraser",
}
# The mouth polygon in build/geo.json is drawn from these DFO coordinates; a changed description blocks publishing.
MOUTH_COORDS = ["49°17.519'N", "123°20.404'W", "49°13.349'N", "123°20.797'W"]
MOUTH_NAME = B("Гирло Fraser: сезонне закриття", "Fraser River mouth: seasonal closure", "Embouchure du Fraser : fermeture saisonnière")
MOUTH_SEC = B("Від Point Grey і North Arm Jetty на захід до 123°20.8′ W.", "From Point Grey and the North Arm Jetty west to 123°20.8′ W.",
              "De Point Grey et de la jetée North Arm vers l'ouest jusqu'à 123°20.8′ O.")

TYPE_UK = {
    "Closed": "Закрито", "Reminder": "Нагадування", "Gear Restriction": "Обмеження спорядження",
    "Daily Limit Pieces": "Денний ліміт", "Minimum Size (cm)": "Мінімальний розмір (см)", "Annual Limit Pieces": "Річний ліміт",
}
TYPE_FR = {
    "Closed": "Fermé", "Reminder": "Rappel", "Gear Restriction": "Restriction d'engin",
    "Daily Limit Pieces": "Limite quotidienne", "Minimum Size (cm)": "Taille minimale (cm)", "Annual Limit Pieces": "Limite annuelle",
}
# DFO species names in restriction rows -> French. Missing entries are shown in English.
SPECIES_FR = {"Chinook salmon": "Saumon quinnat", "Coho salmon": "Saumon coho", "Chum salmon": "Saumon kéta",
              "Pink salmon": "Saumon rose", "Sockeye salmon": "Saumon rouge"}
# Restriction detail phrases (dates removed). Missing entries are shown in English.
DETAIL_UK = {
    "any gear or method": "будь-яким способом",
    "barbless hook and line": "вудка з гачком без зазубрини",
    "a hook having a single point greater than 15 mm from point to shank": "гачок з одним вістрям понад 15 мм від вістря до цівки",
    "a hook having a single point greater than 22 mm from point to shank": "гачок з одним вістрям понад 22 мм від вістря до цівки",
    "a hook having more than one point": "гачок з кількома вістрями",
    "barbed hook": "гачок із зазубриною",
    "natural bait": "природна наживка",
    "From one hour after sunset to one hour before sunrise only -": "від години після заходу до години перед сходом сонця",
    "Closed to harvesting per navigational closures in sub-areas 28-8 (False Creek) and 28-10 (Burrard Inlet, partial).":
        "Закрито для вилову через навігаційні закриття в підзонах 28-8 (False Creek) і 28-10 (Burrard Inlet, частково).",
    "As a Condition of Licence, the use of downriggers is prohibited in portions of Subareas 28-1, 28-2, 28-3, 28-4, and 29-3 in the Howe Sound glass sponge reef marine refuges and fishery closure areas, as described at http://www.dfo-mpo.gc.ca/oceans/ceccsr-cerceef/closures-fermetures-eng.html.":
        "Умова ліцензії: даунригери заборонені в частинах підзон 28-1, 28-2, 28-3, 28-4 і 29-3 у зонах захисту скляних губок Howe Sound.",
    "As per the British Columbia Sport Fishing Regulations, 1996 - It is prohibited to fish in the tidal portion of the Fraser River using a fishing line with a barbed hook attached.":
        "У припливній частині Fraser заборонено ловити на волосінь з гачком із зазубриною.",
    "As per the British Columbia Sport Fishing Regulations, 1996 - It is prohibited to use more than one line when sport fishing in the tidal waters of the Fraser River.":
        "У припливних водах Fraser можна використовувати лише одну волосінь.",
}
DETAIL_FR = {
    "any gear or method": "tout engin ou méthode",
    "barbless hook and line": "ligne avec hameçon sans ardillon",
    "a hook having a single point greater than 15 mm from point to shank": "hameçon à une pointe de plus de 15 mm entre la pointe et la tige",
    "a hook having a single point greater than 22 mm from point to shank": "hameçon à une pointe de plus de 22 mm entre la pointe et la tige",
    "a hook having more than one point": "hameçon à plusieurs pointes",
    "barbed hook": "hameçon avec ardillon",
    "natural bait": "appât naturel",
    "From one hour after sunset to one hour before sunrise only -": "d'une heure après le coucher du soleil à une heure avant son lever",
    "Closed to harvesting per navigational closures in sub-areas 28-8 (False Creek) and 28-10 (Burrard Inlet, partial).":
        "Fermé à la récolte en raison des fermetures de navigation dans les sous-secteurs 28-8 (False Creek) et 28-10 (Burrard Inlet, en partie).",
    "As a Condition of Licence, the use of downriggers is prohibited in portions of Subareas 28-1, 28-2, 28-3, 28-4, and 29-3 in the Howe Sound glass sponge reef marine refuges and fishery closure areas, as described at http://www.dfo-mpo.gc.ca/oceans/ceccsr-cerceef/closures-fermetures-eng.html.":
        "Condition de permis : les descendeurs sont interdits dans des parties des sous-secteurs 28-1, 28-2, 28-3, 28-4 et 29-3, dans les refuges des récifs d'éponges siliceuses de Howe Sound.",
    "As per the British Columbia Sport Fishing Regulations, 1996 - It is prohibited to fish in the tidal portion of the Fraser River using a fishing line with a barbed hook attached.":
        "Dans la partie à marée du Fraser, il est interdit de pêcher avec une ligne munie d'un hameçon avec ardillon.",
    "As per the British Columbia Sport Fishing Regulations, 1996 - It is prohibited to use more than one line when sport fishing in the tidal waters of the Fraser River.":
        "Dans les eaux à marée du Fraser, une seule ligne est permise.",
}
