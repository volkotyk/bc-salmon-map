"""Hand-maintained knowledge that the DFO tables do not contain.

- which DFO water / place name maps to which map geometry
- district, display names, curated notes
- Ukrainian wording for DFO phrases

Everything the fishing rules *say* (species, dates, limits, gear, closures) comes from the DFO pages.
When DFO uses a name that is not here, dfo/update.py refuses to publish and opens an issue.
"""


def B(uk, en):
    return {"uk": uk, "en": en}


SQUAMISH = B("Басейн Squamish: разом не більше 1 заводського кижуча (Coho) на день.",
             "Squamish watershed: aggregate daily limit of 1 hatchery marked Coho for all non-tidal waters.")
TRIBS = B("Разом з притоками.", "Including tributaries.")

# DFO "Waters" cell -> map entry. id = geometry key in build/geo.json.
FRESH = {
    "Alouette River and tributaries": dict(id="alouette", d="tri", name="Alouette River", sec=TRIBS),
    "Ashlu Creek": dict(id="ashlu", d="sea", name="Ashlu Creek", notes=[SQUAMISH]),
    "Capilano River": dict(id="capilano", d="north", name="Capilano River"),
    "Chapman Creek": dict(id="chapman", d="sun", name="Chapman Creek"),
    "Cheakamus River": dict(id="cheakamus", d="sea", name="Cheakamus River", notes=[SQUAMISH]),
    "Chehalis River": dict(id="chehalis", d="valley", name="Chehalis River"),
    "Chilliwack/Vedder River (including Sumas River)": dict(
        id="chilliwack", d="valley", name=B("Chilliwack / Vedder River (з Sumas River)", "Chilliwack / Vedder River (incl. Sumas River)")),
    "Coquitlam River": dict(id="coquitlam", d="tri", name="Coquitlam River"),
    "De Boville Slough": dict(id="deboville", d="tri", name="De Boville Slough"),
    "Fraser River": dict(id="fraser-closed", d="valley", name=B("Fraser River (основне русло)", "Fraser River (mainstem)"),
                         notes=[B("Нижче мосту CPR у Mission — припливна частина, див. Area 29.",
                                  "Below the CPR bridge at Mission is tidal water, see Area 29.")]),
    "Harrison River": dict(id="harrison", d="valley", name="Harrison River"),
    "Kanaka Creek": dict(id="kanaka", d="tri", name="Kanaka Creek"),
    "Khartoum Lake": dict(id="khartoum", d="sun", name="Khartoum Lake", lake=True),
    "Little Campbell River": dict(id="little-campbell", d="sur", name="Little Campbell River"),
    "Lois Lake": dict(id="lois", d="sun", name="Lois Lake", lake=True),
    "Mamquam River": dict(id="mamquam", d="sea", name="Mamquam River", notes=[SQUAMISH]),
    "Nicomekl River": dict(id="nicomekl", d="sur", name="Nicomekl River"),
    "Nicomen (including Dewdney) Slough": dict(
        id="nicomen", d="valley", name=B("Nicomen Slough (з Dewdney Slough)", "Nicomen Slough (incl. Dewdney Slough)")),
    "Norrish (Suicide) Creek": dict(id="norrish", d="valley", name="Norrish (Suicide) Creek"),
    "Serpentine River": dict(id="serpentine", d="sur", name="Serpentine River"),
    "Squamish River (including Powerhouse Channel)": dict(
        id="squamish", d="sea", name=B("Squamish River (з Powerhouse Channel)", "Squamish River (incl. Powerhouse Channel)"), notes=[SQUAMISH]),
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

# ---------- tidal ----------
AREA_SUBS = {"28": [f"28-{i}" for i in range(1, 15)], "29": [f"29-{i}" for i in range(1, 18)]}

# Display names for groups of subareas that share the same rules. Other groups get a generic name.
GROUP_NAMES = {
    frozenset(s for s in AREA_SUBS["28"] if s != "28-8"): B("Howe Sound і Burrard Inlet", "Howe Sound & Burrard Inlet"),
    frozenset(AREA_SUBS["28"]): B("Howe Sound і Burrard Inlet", "Howe Sound & Burrard Inlet"),
    frozenset({"28-8"}): B("False Creek", "False Creek"),
    frozenset({"29-1", "29-2", "29-3", "29-4", "29-5", "29-8"}): B("Strait of Georgia", "Strait of Georgia"),
    frozenset({"29-6", "29-7"} | {f"29-{i}" for i in range(9, 18)}): B("Припливна Fraser, Roberts Bank, Boundary Bay", "Tidal Fraser, Roberts Bank, Boundary Bay"),
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
# The mouth polygon in build/geo.json is drawn from these DFO coordinates; a changed description blocks publishing.
MOUTH_COORDS = ["49°17.519'N", "123°20.404'W", "49°13.349'N", "123°20.797'W"]
MOUTH_NAME = B("Гирло Fraser: сезонне закриття", "Fraser River mouth: seasonal closure")
MOUTH_SEC = B("Від Point Grey і North Arm Jetty на захід до 123°20.8′ W.", "From Point Grey and the North Arm Jetty west to 123°20.8′ W.")

TYPE_UK = {
    "Closed": "Закрито", "Reminder": "Нагадування", "Gear Restriction": "Обмеження спорядження",
    "Daily Limit Pieces": "Денний ліміт", "Minimum Size (cm)": "Мінімальний розмір (см)", "Annual Limit Pieces": "Річний ліміт",
}
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
