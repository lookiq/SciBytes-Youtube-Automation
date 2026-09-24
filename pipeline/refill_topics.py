import os
import sys
import json
import argparse

DATABASE_FILE = 'pipeline/topics_database.json'

# Curated library of 20 verified authentic NASA deep space, astronomy, and astrophysics topics
CURATED_REFILL_POOL = [
    {
        "id": "dart_asteroid_deflection",
        "type": "SPACE_EXPLORATION",
        "title": "The Day NASA Intentionally Crashed Into an Asteroid #Shorts",
        "top_header": "DEFENDING PLANET EARTH",
        "sub_header": "NASA DART ASTEROID IMPACT!",
        "script": "Seven million miles from Earth, NASA seven-hundred-pound DART spacecraft slammed into an asteroid at fourteen thousand miles per hour. Traveling at four miles per second, the intentional kinetic impact blasted tons of pulverized rock into deep space and successfully changed the space rock orbit forever. Subscribe to SciBytes for daily planetary defense breakthroughs!",
        "framing_mode": "fullscreen",
        "start_offset": 14.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "14,000 MPH ASTEROID IMPACT!", "color": "#00FFFF"},
            {"start": 2.8, "end": 6.0, "text": "NASA DART CRASH MISSION!", "color": "#FFEA00"},
            {"start": 6.0, "end": 9.5, "text": "7 MILLION MILES FROM EARTH!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "DEFLECTING A SPACE ROCK!", "color": "#00FF66"},
            {"start": 13.5, "end": 17.5, "text": "EARTH DEFENSE SUCCESSFUL!", "color": "#FF2A55"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, NASA DART spacecraft slamming into asteroid Dimorphos, massive bright plume of pulverized rock and dust ejecta into deep space, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/20220926-GSFC-DARTs_Impact_with_Asteroid_Dimorphos_REV1a/20220926-GSFC-DARTs_Impact_with_Asteroid_Dimorphos_REV1a~orig.mp4",
        "tags": ["dart mission", "asteroid impact", "planetary defense", "nasa dart", "asteroid dimorphos", "space science", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "osiris_rex_asteroid_sample",
        "type": "SPACE_EXPLORATION",
        "title": "NASA Retrieved 4.5-Billion-Year-Old Stardust #Shorts",
        "top_header": "PRIMORDIAL SPACE DUST",
        "sub_header": "ASTEROID BENNU SAMPLE RETURN!",
        "script": "Two hundred million miles away, NASA OSIRIS-REx spacecraft touched down on asteroid Bennu to collect a pristine sample of our early solar system. Returning through Earth atmosphere at twenty-seven thousand miles per hour, it brought back carbon-rich dust containing water molecules older than our Sun. Subscribe to SciBytes for more mind-bending science!",
        "framing_mode": "fullscreen",
        "start_offset": 12.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "4.5 BILLION YEAR OLD STARDUST!", "color": "#FFEA00"},
            {"start": 2.8, "end": 6.0, "text": "TOUCHDOWN ON ASTEROID BENNU!", "color": "#00FFFF"},
            {"start": 6.0, "end": 9.5, "text": "27,000 MPH EARTH RE-ENTRY!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "CARBON & WATER OLDER THAN SUN!", "color": "#00FF66"},
            {"start": 13.5, "end": 17.5, "text": "SECRETS OF SOLAR SYSTEM DAWN!", "color": "#FF2A55"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, OSIRIS-REx robotic arm collecting rocky regolith from boulder-strewn asteroid Bennu, sunlight glinting off carbonaceous rock surface, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/GSFC_20190812_OSIRIS_REx_m4744_Bennu_Sites/GSFC_20190812_OSIRIS_REx_m4744_Bennu_Sites~orig.mp4",
        "tags": ["osiris rex", "asteroid bennu", "sample return", "early solar system", "nasa sample", "astronomy", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "webb_stephan_five_galaxies",
        "type": "ASTRONOMY",
        "title": "Five Giant Galaxies Trapped in a Cosmic Dance #Shorts",
        "top_header": "TITANIC GALAXY MERGER",
        "sub_header": "WEBB SEES STEPHAN'S QUINTET!",
        "script": "Deep in the constellation Pegasus, five massive galaxies are locked in a violent gravitational battle known as Stephan's Quintet. NASA James Webb revealed titanic shockwaves ripping through gas clouds larger than the Milky Way as one galaxy tears through the group at two million miles per hour. Subscribe to SciBytes for daily astronomy wonders!",
        "framing_mode": "fullscreen",
        "start_offset": 15.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "5 GALAXIES IN TITANIC COLLISION!", "color": "#FF2A55"},
            {"start": 2.8, "end": 6.0, "text": "STEPHAN'S QUINTET GRAVITY DANCE!", "color": "#FFEA00"},
            {"start": 6.0, "end": 9.5, "text": "2 MILLION MPH COSMIC SHOCKWAVES!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "WEBB PIERCES DENSE GAS TRAILS!", "color": "#00FFFF"},
            {"start": 13.5, "end": 17.5, "text": "NEW STARS BORN IN CHAOS!", "color": "#00FF66"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, James Webb infrared image of Stephan's Quintet, five interacting spiral and elliptical galaxies with glowing red shockwave ridges, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/GSFC_NSL_Webb_Images_Ep44/GSFC_NSL_Webb_Images_Ep44~orig.mp4",
        "tags": ["stephans quintet", "james webb", "galaxy merger", "astronomy", "deep space", "cosmic collision", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "psyche_giant_metal_asteroid",
        "type": "ASTROPHYSICS",
        "title": "NASA Is Flying to a $10 Quintillion Metal Asteroid #Shorts",
        "top_header": "WORLD OF PURE METAL",
        "sub_header": "NASA MISSION TO ASTEROID PSYCHE!",
        "script": "Orbiting between Mars and Jupiter lies Psyche, a colossal asteroid made almost entirely of solid iron, nickel, and precious metals worth ten quintillion dollars. Scientists believe Psyche is the exposed metallic heart of a shattered protoplanet from the dawn of our solar system. Subscribe to SciBytes for daily space exploration!",
        "framing_mode": "fullscreen",
        "start_offset": 12.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "10 QUINTILLION DOLLAR ASTEROID!", "color": "#FFEA00"},
            {"start": 2.8, "end": 6.0, "text": "SOLID IRON & PRECIOUS METALS!", "color": "#00FFFF"},
            {"start": 6.0, "end": 9.5, "text": "SHATTERED PROTOPLANET CORE!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "EXPOSED HEART OF AN ALIEN WORLD!", "color": "#FF2A55"},
            {"start": 13.5, "end": 17.5, "text": "NASA PSYCHE MISSION ON THE WAY!", "color": "#00FF66"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, giant metallic asteroid Psyche with reflective metallic iron crater walls and nickel nickel-iron ridges in deep black space, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/JPL-20230929-PSYCHEf-0004-Hype/JPL-20230929-PSYCHEf-0004-Hype~orig.mp4",
        "tags": ["psyche asteroid", "metal asteroid", "nasa psyche", "protoplanet", "iron core", "planetary science", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "lucy_fossil_trojan_asteroids",
        "type": "SPACE_EXPLORATION",
        "title": "The Time Capsule Asteroids Trapped by Jupiter #Shorts",
        "top_header": "TIME CAPSULES OF SPACE",
        "sub_header": "NASA LUCY TO THE TROJANS!",
        "script": "Swarming ahead and behind Jupiter in its orbit are the Trojan asteroids, ancient cosmic fossils trapped by gravity since the birth of the planets four and a half billion years ago. NASA Lucy spacecraft is currently on a twelve-year journey to visit eight of these pristine worlds. Subscribe to SciBytes for daily cosmic mysteries!",
        "framing_mode": "fullscreen",
        "start_offset": 14.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "4.5 BILLION YEAR TIME CAPSULES!", "color": "#00FFFF"},
            {"start": 2.8, "end": 6.0, "text": "JUPITER TROJAN ASTEROID SWARM!", "color": "#FFEA00"},
            {"start": 6.0, "end": 9.5, "text": "FOSSILS OF PLANETARY CREATION!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "TRAPPED IN GRAVITATIONAL LOCK!", "color": "#FF2A55"},
            {"start": 13.5, "end": 17.5, "text": "NASA LUCY 12-YEAR ODYSSEY!", "color": "#00FF66"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, NASA Lucy spacecraft soaring past a cratered red-tinged Trojan asteroid with Jupiter massive banded sphere in distant background, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/GSFC_20211015_NSL_Ep39_Lucy/GSFC_20211015_NSL_Ep39_Lucy~orig.mp4",
        "tags": ["lucy mission", "trojan asteroids", "jupiter trojans", "solar system fossils", "nasa lucy", "astronomy", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "parker_solar_probe_superheat",
        "type": "SOLAR_PHYSICS",
        "title": "The Spacecraft Flying Inside the Sun's Corona #Shorts",
        "top_header": "INTO THE SOLAR FURNACE",
        "sub_header": "PARKER FLIES THROUGH THE SUN!",
        "script": "Traveling at four hundred and thirty thousand miles per hour, NASA Parker Solar Probe repeatedly plunges directly through the blistering atmosphere of the Sun. Enduring temperatures exceeding two million degrees Fahrenheit behind a carbon composite heat shield, it measures solar magnetic fields at close range. Subscribe to SciBytes for daily solar science!",
        "framing_mode": "fullscreen",
        "start_offset": 10.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "430,000 MPH INTO THE SUN!", "color": "#FFEA00"},
            {"start": 2.8, "end": 6.0, "text": "TOUCHING THE SOLAR CORONA!", "color": "#FF2A55"},
            {"start": 6.0, "end": 9.5, "text": "2 MILLION DEGREE FURNACE!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "CARBON COMPOSITE HEAT SHIELD!", "color": "#00FFFF"},
            {"start": 13.5, "end": 17.5, "text": "FASTEST HUMAN OBJECT IN SPACE!", "color": "#00FF66"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, Parker Solar Probe plunging into white-hot solar corona with blistering plasma streams glancing off carbon heat shield, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/GSFC_20180725_Parker_m12903_CoronalHeating_Short/GSFC_20180725_Parker_m12903_CoronalHeating_Short~orig.mp4",
        "tags": ["parker solar probe", "sun corona", "fastest spacecraft", "solar physics", "solar probe", "astrophysics", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "new_horizons_charon_canyons",
        "type": "PLANETARY_SCIENCE",
        "title": "The Colossal Four-Mile-Deep Canyons on Charon #Shorts",
        "top_header": "TITANIC CHASM IN SPACE",
        "sub_header": "PLUTO MOON CHARON CANYONS!",
        "script": "Three billion miles from the Sun, Pluto giant moon Charon is split across its equator by a monstrous canyon system four times deeper than the Grand Canyon. Running for over a thousand miles, this tectonic rift tore open when Charon ancient subsurface ocean froze and expanded from within. Subscribe to SciBytes for daily planetary wonders!",
        "framing_mode": "fullscreen",
        "start_offset": 12.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "4-MILE DEEP ALIEN CANYONS!", "color": "#00FFFF"},
            {"start": 2.8, "end": 6.0, "text": "PLUTO'S GIANT MOON CHARON!", "color": "#FFEA00"},
            {"start": 6.0, "end": 9.5, "text": "4X DEEPER THAN GRAND CANYON!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "ANCIENT SUBSURFACE OCEAN FROZE!", "color": "#FF2A55"},
            {"start": 13.5, "end": 17.5, "text": "TECTONIC CRACKS SPLIT THE MOON!", "color": "#00FF66"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, close-up high-resolution view of Charon giant chasm belt Serenity Chasma splitting gray icy moon, reddish northern tholin cap, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/ksc_120605_nh_overview/ksc_120605_nh_overview~orig.mp4",
        "tags": ["charon", "pluto moon", "new horizons", "canyons in space", "frozen ocean", "kuiper belt", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "swift_gamma_ray_explosion",
        "type": "ASTROPHYSICS",
        "title": "The Most Powerful Explosions in the Universe #Shorts",
        "top_header": "DEADLIEST COSMIC BLAST",
        "sub_header": "GAMMA-RAY BURSTS EXPLAINED!",
        "script": "In just a few seconds, a gamma-ray burst releases more raw energy than our Sun will produce during its entire ten-billion-year lifespan. When a dying supergiant star collapses into a black hole, twin beams of relativistic radiation pierce through space across billions of light years. Subscribe to SciBytes for mind-bending physics!",
        "framing_mode": "fullscreen",
        "start_offset": 12.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "MOST POWERFUL BLAST IN SPACE!", "color": "#FF2A55"},
            {"start": 2.8, "end": 6.0, "text": "MORE ENERGY THAN SUN LIFETIME!", "color": "#FFEA00"},
            {"start": 6.0, "end": 9.5, "text": "MASSIVE STAR COLLAPSES!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "TWIN RELATIVISTIC DEATH BEAMS!", "color": "#00FFFF"},
            {"start": 13.5, "end": 17.5, "text": "PIERCING BILLIONS OF LIGHT YEARS!", "color": "#FF2A55"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, colossal gamma-ray burst erupting from collapsing core of supergiant star, hyper-intense blue relativistic jets searing into space, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/ksc_011805_swift_burst/ksc_011805_swift_burst~orig.mp4",
        "tags": ["gamma ray burst", "swift satellite", "supernova", "black hole birth", "astrophysics", "cosmic blast", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "mars_mount_sharp_rover_climb",
        "type": "PLANETARY_SCIENCE",
        "title": "NASA Rover Climbs a 3-Mile-High Mountain on Mars #Shorts",
        "top_header": "RED PLANET SUMMIT",
        "sub_header": "CURIOSITY CLIMBS MOUNT SHARP!",
        "script": "Inside Gale Crater on Mars, Mount Sharp towers three miles above the surrounding plains. For over twelve years, NASA Curiosity rover has been scaling its rocky slopes, uncovering sedimentary mineral bands that prove Mars was once covered in ancient freshwater lakes and habitable rivers. Subscribe to SciBytes for daily Mars discoveries!",
        "framing_mode": "fullscreen",
        "start_offset": 12.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "3-MILE HIGH MOUNTAIN ON MARS!", "color": "#FFEA00"},
            {"start": 2.8, "end": 6.0, "text": "CURIOSITY SCALING ROCKY PEAKS!", "color": "#00FFFF"},
            {"start": 6.0, "end": 9.5, "text": "12 YEARS OF MARS CLIMBING!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "PROVING ANCIENT LAKES & WATER!", "color": "#00FF66"},
            {"start": 13.5, "end": 17.5, "text": "RED PLANET WAS ONCE HABITABLE!", "color": "#FF2A55"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, Curiosity rover on slope of Mount Sharp on Mars, red dust-covered landscape with towering stratified sulfate layers and Gale crater rim, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/JPL-20210816-MSLf-0001-2160/JPL-20210816-MSLf-0001-2160~orig.mp4",
        "tags": ["mars curiosity", "mount sharp", "gale crater", "mars rover", "ancient water mars", "mars science", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "neutron_star_kilonova_gold",
        "type": "ASTROPHYSICS",
        "title": "Where All the Gold in the Universe Comes From #Shorts",
        "top_header": "COSMIC FORGE OF GOLD",
        "sub_header": "HOW GOLD WAS CREATED IN SPACE!",
        "script": "Every piece of gold and platinum on Earth was created by a cataclysmic cosmic explosion known as a kilonova. When two hyper-dense neutron stars spiral together at half the speed of light, their violent collision unleashes a nuclear furnace hot enough to forge hundreds of Earth masses of pure heavy precious metals. Subscribe to SciBytes for more mind-bending science!",
        "framing_mode": "fullscreen",
        "start_offset": 12.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "ALL GOLD BORN IN SPACE!", "color": "#FFEA00"},
            {"start": 2.8, "end": 6.0, "text": "COLLIDING NEUTRON STARS!", "color": "#FF2A55"},
            {"start": 6.0, "end": 9.5, "text": "HALF SPEED OF LIGHT SPIRAL!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "TITANIC KILONOVA BLAST!", "color": "#00FFFF"},
            {"start": 13.5, "end": 17.5, "text": "HUNDREDS OF EARTHS OF GOLD!", "color": "#FFEA00"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, two glowing blue neutron stars spiraling into a brilliant golden kilonova explosion, gravitational waves warping space, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/ksc_111604_swift_three_theories/ksc_111604_swift_three_theories~orig.mp4",
        "tags": ["kilonova", "gold in space", "neutron star collision", "gravitational waves", "astrophysics", "physics mystery", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "cassini_saturn_rings_dive",
        "type": "SPACE_EXPLORATION",
        "title": "Cassini's Final Death Dive Into Saturn #Shorts",
        "top_header": "THE GRAND FINALE",
        "sub_header": "DIVING INTO SATURN'S RINGS!",
        "script": "After thirteen years exploring the ringed jewel of our solar system, NASA Cassini spacecraft executed a daring grand finale dive between Saturn and its innermost rings. Reaching seventy-five thousand miles per hour, Cassini beamed back high-resolution ring data before vaporizing into Saturn atmosphere. Subscribe to SciBytes for daily space exploration!",
        "framing_mode": "fullscreen",
        "start_offset": 15.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "DARING DIVE THROUGH RINGS!", "color": "#00FFFF"},
            {"start": 2.8, "end": 6.0, "text": "CASSINI'S GRAND FINALE!", "color": "#FFEA00"},
            {"start": 6.0, "end": 9.5, "text": "75,000 MPH FINAL DESCENT!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "PEEKING BETWEEN RINGS & PLANET!", "color": "#00FF66"},
            {"start": 13.5, "end": 17.5, "text": "VAPORIZING IN SATURN CLOUDS!", "color": "#FF2A55"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, Cassini spacecraft plunging between glowing razor-thin icy rings and golden swirling cloud tops of Saturn, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/GSFC_20170912_Cassini_m12709_CIRS_Long/GSFC_20170912_Cassini_m12709_CIRS_Long~orig.mp4",
        "tags": ["cassini finale", "saturn rings", "cassini dive", "nasa saturn", "ringed planet", "space exploration", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "pluto_frozen_nitrogen_mountains",
        "type": "PLANETARY_SCIENCE",
        "title": "The Flowing Ice Glaciers on Frozen Pluto #Shorts",
        "top_header": "FROZEN ALIEN TUNDRA",
        "sub_header": "NITROGEN GLACIERS ON PLUTO!",
        "script": "On the frozen plains of Sputnik Planitia, mountains of water ice tower two miles above shifting glaciers of nitrogen and methane ice. Despite surface temperatures of minus three hundred and eighty degrees Fahrenheit, convective heat from Pluto deep core keeps these alien glaciers slowly churning. Subscribe to SciBytes for daily planetary science!",
        "framing_mode": "fullscreen",
        "start_offset": 12.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "-380 DEGREE NITROGEN GLACIERS!", "color": "#00FFFF"},
            {"start": 2.8, "end": 6.0, "text": "FLOWING ICE ON FROZEN PLUTO!", "color": "#FFEA00"},
            {"start": 6.0, "end": 9.5, "text": "2-MILE HIGH WATER ICE PEAKS!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "CHURNING FROM INTERNAL HEAT!", "color": "#00FF66"},
            {"start": 13.5, "end": 17.5, "text": "PLUTO IS GEOLOGICALLY ALIVE!", "color": "#FF2A55"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, New Horizons high-res view of Sputnik Planitia nitrogen ice cells and towering Hillary Montes water-ice mountains casting long shadows on Pluto, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/GSFC_20150710_NewHorizons_m11941_Enlil/GSFC_20150710_NewHorizons_m11941_Enlil~orig.mp4",
        "tags": ["pluto glaciers", "new horizons pluto", "sputnik planitia", "nitrogen ice", "kuiper belt", "planetary science", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "aurora_borealis_space_station",
        "type": "EARTH_SCIENCE",
        "title": "What Auroras Look Like From Space Station #Shorts",
        "top_header": "GLOWING PLANETARY SHIELD",
        "sub_header": "AURORA FROM 250 MILES UP!",
        "script": "Two hundred and fifty miles above Earth, astronauts aboard the International Space Station fly directly over rivers of emerald green and purple auroras. When solar energetic particles collide with oxygen and nitrogen atoms in our upper atmosphere, they trigger this mesmerizing planetary light show. Subscribe to SciBytes for daily science wonders!",
        "framing_mode": "fullscreen",
        "start_offset": 12.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "AURORA BOREALIS FROM ORBIT!", "color": "#00FF66"},
            {"start": 2.8, "end": 6.0, "text": "250 MILES ABOVE EARTH!", "color": "#00FFFF"},
            {"start": 6.0, "end": 9.5, "text": "SOLAR PARTICLES HIT ATMOSPHERE!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "EMERALD GREEN & VIOLET CURTAINS!", "color": "#FFEA00"},
            {"start": 13.5, "end": 17.5, "text": "EARTH MAGNETIC SHIELD IN ACTION!", "color": "#FF2A55"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, panoramic view from ISS Cupola looking down at Earth curved horizon bathed in brilliant glowing green Aurora Borealis curtain, starry background, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/GSFC_20171107_Ionosphere_m12532_ICON/GSFC_20171107_Ionosphere_m12532_ICON~orig.mp4",
        "tags": ["aurora borealis", "iss view", "space station aurora", "northern lights", "earth magnetic field", "earth science", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "chandra_cassiopeia_supernova",
        "type": "ASTROPHYSICS",
        "title": "The Shattered Remnants of an Exploded Giant Star #Shorts",
        "top_header": "GHOST OF A DEAD STAR",
        "sub_header": "CASSIOPEIA A SUPERNOVA BLAST!",
        "script": "Eleven thousand light years away lies Cassiopeia A, the expanding debris cloud of a massive star that blew apart in a violent supernova. NASA Chandra X-Ray Observatory revealed ten-million-degree shockwaves hurling iron, sulfur, and silicon into interstellar space to seed future solar systems. Subscribe to SciBytes for daily astrophysics!",
        "framing_mode": "fullscreen",
        "start_offset": 12.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "EXPANDING GHOST OF A DEAD STAR!", "color": "#FF2A55"},
            {"start": 2.8, "end": 6.0, "text": "CASSIOPEIA A SUPERNOVA REMNANT!", "color": "#FFEA00"},
            {"start": 6.0, "end": 9.5, "text": "10 MILLION DEGREE SHOCKWAVES!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "HURLING HEAVY ELEMENTS TO SPACE!", "color": "#00FFFF"},
            {"start": 13.5, "end": 17.5, "text": "SEEDING FUTURE SOLAR SYSTEMS!", "color": "#00FF66"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, Chandra X-Ray multi-wavelength view of Cassiopeia A supernova remnant, glowing silicon jets and expanding turquoise and magenta shockwave shell, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/ksc_042507_chandra_2/ksc_042507_chandra_2~orig.mp4",
        "tags": ["cassiopeia a", "chandra x ray", "supernova remnant", "stellar explosion", "astrophysics", "deep space", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "roman_space_dark_matter_web",
        "type": "ASTROPHYSICS",
        "title": "NASA's New Telescope to Map the Dark Universe #Shorts",
        "top_header": "HUNTING INVISIBLE MATTER",
        "sub_header": "ROMAN SPACE TELESCOPE!",
        "script": "Dark matter makes up eighty-five percent of all matter in the universe, yet remains completely invisible. NASA upcoming Nancy Grace Roman Space Telescope features a camera with a field of view one hundred times larger than Hubble, designed to measure cosmic gravitational lensing across billions of galaxies. Subscribe to SciBytes for cosmic breakthroughs!",
        "framing_mode": "fullscreen",
        "start_offset": 12.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "85% OF ALL MATTER IS INVISIBLE!", "color": "#00FFFF"},
            {"start": 2.8, "end": 6.0, "text": "HUNTING COSMIC DARK MATTER!", "color": "#FFEA00"},
            {"start": 6.0, "end": 9.5, "text": "ROMAN TELESCOPE 100X WIDER VIEW!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "MAPPING GRAVITATIONAL LENSING!", "color": "#00FF66"},
            {"start": 13.5, "end": 17.5, "text": "UNVEILING THE INVISIBLE COSMOS!", "color": "#FF2A55"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, wide cosmological panorama showing vast web of invisible dark matter filaments bending starlight from background galaxies, NASA visualization, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/15081-%20Roman%20Mission%20Trailer%20-%20Long/15081-%20Roman%20Mission%20Trailer%20-%20Long~orig.mp4",
        "tags": ["roman space telescope", "dark matter", "cosmic web", "gravitational lensing", "astrophysics", "space telescope", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "black_hole_xray_echo_osiris",
        "type": "ASTROPHYSICS",
        "title": "A Spacecraft Accidentally Detected a Black Hole #Shorts",
        "top_header": "COSMIC X-RAY FLASH",
        "sub_header": "BLACK HOLE FLARE ACCIDENT!",
        "script": "While orbiting asteroid Bennu millions of miles from Earth, NASA OSIRIS-REx spacecraft detected a sudden blinding flash of X-rays from deep space. Instruments confirmed it was a newly flaring black hole thirty thousand light years away, devouring a companion star at near the speed of light. Subscribe to SciBytes for daily astrophysics wonders!",
        "framing_mode": "fullscreen",
        "start_offset": 14.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "ACCIDENTAL BLACK HOLE DISCOVERY!", "color": "#FFEA00"},
            {"start": 2.8, "end": 6.0, "text": "BLINDING X-RAY FLASH IN SPACE!", "color": "#FF2A55"},
            {"start": 6.0, "end": 9.5, "text": "30,000 LIGHT YEARS DISTANT!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "DEVOURING A COMPANION STAR!", "color": "#00FFFF"},
            {"start": 13.5, "end": 17.5, "text": "OSIRIS-REx CATCHES COSMIC FEAST!", "color": "#00FF66"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, luminous accretion disk swirling around black hole emitting intense blue X-ray flares while siphoning gas from companion red giant, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/GSFC_20200302_M13568_OIRISRExBH/GSFC_20200302_M13568_OIRISRExBH~orig.mp4",
        "tags": ["black hole flare", "osiris rex discovery", "x-ray astronomy", "stellar black hole", "astrophysics", "space mystery", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "chandra_relativistic_jet_blasts",
        "type": "ASTROPHYSICS",
        "title": "Monster Black Holes Blasting Jets of Light #Shorts",
        "top_header": "RELATIVISTIC PARTICLE CANNON",
        "sub_header": "BLACK HOLE RELATIVISTIC JETS!",
        "script": "At the centers of giant galaxies, supermassive black holes do not just swallow matter. Magnetic forces funnel gas along the event horizon into twin relativistic beams, shooting out high-energy particles at ninety-nine percent the speed of light across hundreds of thousands of light years. Subscribe to SciBytes for extreme physics facts!",
        "framing_mode": "fullscreen",
        "start_offset": 12.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "99% SPEED OF LIGHT JETS!", "color": "#00FFFF"},
            {"start": 2.8, "end": 6.0, "text": "SUPERMASSIVE BLACK HOLE CANNONS!", "color": "#FFEA00"},
            {"start": 6.0, "end": 9.5, "text": "MAGNETIC FORCES AT EVENT HORIZON!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "STRETCHING ACROSS GALAXIES!", "color": "#FF2A55"},
            {"start": 13.5, "end": 17.5, "text": "CHANDRA X-RAY CAPTURES COSMIC BEAM!", "color": "#00FF66"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, supermassive black hole blasting twin relativistic particle jets across hundreds of thousands of light years, brilliant accretion disk, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/ksc_012505_black_holes/ksc_012505_black_holes~orig.mp4",
        "tags": ["black hole jets", "relativistic jets", "chandra x ray", "supermassive black hole", "event horizon", "astrophysics", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "chandra_isolated_neutron_star",
        "type": "ASTROPHYSICS",
        "title": "A Dead Star Denser Than Any Mountain on Earth #Shorts",
        "top_header": "SUPER-DENSE STAR CORPSE",
        "sub_header": "ISOLATED NEUTRON STAR FACTS!",
        "script": "Packing twice the mass of our Sun into a sphere just twelve miles wide, a neutron star is the densest single object known before a black hole. A single sugar cube of neutron star material would weigh over one billion tons on Earth, crushed under trillions of times Earth gravity. Subscribe to SciBytes for daily cosmic science!",
        "framing_mode": "fullscreen",
        "start_offset": 12.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "1 BILLION TONS PER SUGAR CUBE!", "color": "#FFEA00"},
            {"start": 2.8, "end": 6.0, "text": "DENSEST OBJECT BEFORE BLACK HOLE!", "color": "#00FFFF"},
            {"start": 6.0, "end": 9.5, "text": "2 SUNS CRUSHED INTO 12 MILES!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "TRILLIONS OF TIMES EARTH GRAVITY!", "color": "#FF2A55"},
            {"start": 13.5, "end": 17.5, "text": "CHANDRA PROBES NEUTRON CRUST!", "color": "#00FF66"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, glowing blue hyper-dense neutron star spinning rapidly in space, magnetic field lines arcing over crystalline neutron crust, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/ksc_082604_chandra/ksc_082604_chandra~orig.mp4",
        "tags": ["neutron star", "extreme density", "chandra x ray", "star corpse", "nuclear physics", "astrophysics", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "mars_sample_recovery_rocket",
        "type": "SPACE_EXPLORATION",
        "title": "How NASA Will Launch a Rocket From the Surface of Mars #Shorts",
        "top_header": "FIRST LAUNCH FROM MARS",
        "sub_header": "MARS SAMPLE RETURN ROCKET!",
        "script": "NASA and the European Space Agency are designing the Mars Ascent Vehicle, the first rocket ever built to launch from the surface of another planet. It will blast Martian rock core samples into Mars orbit for robotic rendezvous and return to Earth laboratories. Subscribe to SciBytes for future space engineering!",
        "framing_mode": "fullscreen",
        "start_offset": 14.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "FIRST ROCKET TO LAUNCH FROM MARS!", "color": "#FFEA00"},
            {"start": 2.8, "end": 6.0, "text": "MARS ASCENT VEHICLE MISSION!", "color": "#00FFFF"},
            {"start": 6.0, "end": 9.5, "text": "BLASTING ROCK TUBES TO ORBIT!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "ROBOTIC DOCKING IN DEEP SPACE!", "color": "#00FF66"},
            {"start": 13.5, "end": 17.5, "text": "RETURNING MARS SAMPLES TO EARTH!", "color": "#FF2A55"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, Mars Ascent Vehicle rocket launching from robotic lander platform on Martian surface, red dust plume billowing across crimson desert, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/JPL-20221026-0001-MSRf-How%20to%20Bring%20Mars%20Sample%20Tubes%20Safely%20to%20Earth/JPL-20221026-0001-MSRf-How%20to%20Bring%20Mars%20Sample%20Tubes%20Safely%20to%20Earth~orig.mp4",
        "tags": ["mars sample return", "mars ascent vehicle", "rocket launch mars", "nasa esa", "space engineering", "mars mission", "SciBytes", "shorts"],
        "used": False
    },
    {
        "id": "artemis_moon_crater_flyby",
        "type": "SPACE_EXPLORATION",
        "title": "Orion's Breathtaking Flyby Over Moon Craters #Shorts",
        "top_header": "RETURN TO THE MOON",
        "sub_header": "ARTEMIS ORION LUNAR PASS!",
        "script": "Skimming just eighty miles above the cratered lunar surface, NASA human-rated Orion spacecraft captured ultra-high-definition video of the Moon rugged far side. Traveling beyond any spacecraft designed for astronauts has ever flown, Artemis paves the way for permanent human moon bases. Subscribe to SciBytes for daily lunar exploration!",
        "framing_mode": "fullscreen",
        "start_offset": 12.0,
        "subtitles": [
            {"start": 0.0, "end": 2.8, "text": "80 MILES ABOVE MOON CRATERS!", "color": "#00FFFF"},
            {"start": 2.8, "end": 6.0, "text": "ARTEMIS ORION LUNAR FLYBY!", "color": "#FFEA00"},
            {"start": 6.0, "end": 9.5, "text": "FURTHEST CREW SPACECRAFT IN HISTORY!", "color": "#FFFFFF"},
            {"start": 9.5, "end": 13.5, "text": "HIGH DEFINITION LUNAR FAR SIDE!", "color": "#00FF66"},
            {"start": 13.5, "end": 17.5, "text": "PAVING WAY FOR MOON BASES!", "color": "#FF2A55"},
            {"start": 17.5, "end": 99.0, "text": "SUBSCRIBE TO SCIBYTES!", "color": "#00FF66"}
        ],
        "thumb_prompt": "raw authentic photograph, Artemis Orion solar wing tip camera capturing Orion capsule gliding eighty miles over detailed jagged lunar craters with Earth rising in black background, 8k photorealistic, zero cgi, zero cartoon",
        "footage_url": "https://images-assets.nasa.gov/video/jsc2026m000354-Artemis-II-Orion-Mission-Evaluation-Room-Team-During-Splashdown/jsc2026m000354-Artemis-II-Orion-Mission-Evaluation-Room-Team-During-Splashdown~orig.mp4",
        "tags": ["artemis orion", "moon flyby", "lunar craters", "nasa artemis", "human spaceflight", "moon exploration", "SciBytes", "shorts"],
        "used": False
    }
]

def refill_database(dry_run=False):
    if not os.path.exists(DATABASE_FILE):
        print(f"ERROR: Database file '{DATABASE_FILE}' not found.")
        sys.exit(1)

    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        topics = json.load(f)

    existing_ids = {t.get('id') for t in topics}
    used_footage_urls = {t.get('footage_url') for t in topics if t.get('footage_url')}
    
    # Also collect upload history
    if os.path.exists('upload_history.log'):
        with open('upload_history.log', 'r', encoding='utf-8') as f:
            for line in f:
                if 'Footage: ' in line:
                    parts = line.split('Footage: ')
                    if len(parts) > 1:
                        u = parts[1].split(' | ')[0].strip()
                        if u and u != 'N/A':
                            used_footage_urls.add(u)

    print("=" * 60)
    print("SciBytes - Safe Topic Refill Generator")
    print("=" * 60)
    print(f"Current total topics in DB: {len(topics)}")
    unused_before = len([t for t in topics if not t.get('used', False)])
    print(f"Currently unused in queue : {unused_before}")
    print("=" * 60)

    added_topics = []
    for topic in CURATED_REFILL_POOL:
        t_id = topic['id']
        t_footage = topic.get('footage_url')

        # Safety Check 1: ID must not exist
        if t_id in existing_ids:
            print(f"Skipping '{t_id}' - ID already exists.")
            continue

        # Safety Check 2: Footage URL must not be in use
        if t_footage and (t_footage in used_footage_urls or t_footage.replace('https://', 'http://') in used_footage_urls):
            print(f"Skipping '{t_id}' - Footage URL already used.")
            continue

        added_topics.append(topic)
        existing_ids.add(t_id)
        if t_footage:
            used_footage_urls.add(t_footage)

    print(f"\nEligible new unique topics to add: {len(added_topics)}")

    if dry_run:
        print("[DRY RUN] No changes were written to database.")
        return len(added_topics)

    if added_topics:
        topics.extend(added_topics)
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(topics, f, indent=2)
        print(f"SUCCESS: Appended {len(added_topics)} new topics to {DATABASE_FILE}")
        unused_after = len([t for t in topics if not t.get('used', False)])
        print(f"New total unused in queue: {unused_after}")
    else:
        print("Notice: No new topics added (all topics in pool already exist in DB).")

    return len(added_topics)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SciBytes Topic Refill Generator")
    parser.add_argument('--dry-run', action='store_true', help="Simulate refill without saving to disk")
    args = parser.parse_args()
    refill_database(dry_run=args.dry_run)
