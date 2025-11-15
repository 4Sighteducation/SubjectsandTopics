"""
Universal Hierarchy Text Parser and Uploader
=============================================

Takes pasted hierarchical text and uploads it to Supabase.

Usage:
    1. Edit SUBJECT_INFO and HIERARCHY_TEXT below
    2. Run: python upload-from-hierarchy-text.py

Format detection:
- Detects Components/Topics based on keywords or indentation
- Numbered items (1.1, 1.2) become Level 2
- Bullet points or plain text become Level 3/4
- Auto-generates topic codes
"""

import os
import sys
import re
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client

# Force UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not found!")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

# ===== EDIT THIS SECTION =====

SUBJECT_INFO = {
    'code': 'GCSE-Astronomy',
    'name': 'Astronomy',
    'qualification': 'GCSE',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/GCSE/Astronomy/2017/Specification%20and%20sample%20assessments/gcse-astronomy-specification.pdf'
}

HIERARCHY_TEXT = """
Paper 1: Naked-eye Astronomy
Topic 1 – Planet Earth
1.1 Know that the shape of the Earth is an oblate spheroid.
1.2 Be able to use information about the mean diameter of the Earth (13,000 km).
1.3 Understand the Earth’s major internal divisions and their features:
1.3.1 Crust
1.3.2 Mantle
1.3.3 Outer core
1.3.4 Inner core
1.4 Be able to use the latitude and longitude coordinate system.
1.5 Be able to use the major divisions of the Earth’s surface as astronomical reference points, including:
1.5.1 Equator
1.5.2 Tropic of Cancer
1.5.3 Tropic of Capricorn
1.5.4 Arctic Circle
1.5.5 Antarctic Circle
1.5.6 Prime Meridian
1.5.7 North Pole
1.5.8 South Pole
1.6 Understand the effects of the Earth’s atmosphere on astronomical observations, including:
1.6.1 Sky color
1.6.2 Skyglow (light pollution)
1.6.3 Twinkling (seeing)
Topic 2 – The Lunar Disc
2.1 Know the shape of the Moon.
2.2 Be able to use information about the mean diameter of the Moon (3,500 km).
2.3 Be able to recognize the appearance of the principal naked-eye lunar surface formations, including:
2.3.1 Craters
2.3.2 Maria
2.3.3 Terrae
2.3.4 Mountains
2.3.5 Valleys
2.4 Understand the structure and origin of the principal naked-eye lunar surface formations, including:
2.4.1 Craters
2.4.2 Maria
2.4.3 Terrae
2.4.4 Mountains
2.4.5 Valleys
2.5 Be able to identify the following features on the lunar disc:
2.5.1 Sea of Tranquility
2.5.2 Ocean of Storms
2.5.3 Sea of Crises
2.5.4 Tycho
2.5.5 Copernicus
2.5.6 Kepler
2.5.7 Apennine mountain range
2.6 Be able to use the rotation and revolution (orbital) periods of the Moon.
2.7 Understand the synchronous nature of the Moon’s orbit.
2.8 Understand the causes of lunar libration and its effect on the visibility of the lunar disc.
Topic 3 – The Earth-Moon-Sun System
3.1 Be able to use the relative sizes of the Earth, Moon, and Sun.
3.2 Be able to use the relative distances between the Earth, Moon, and Sun.
3.3 Understand how Eratosthenes and Aristarchus used observations of the Moon and Sun to determine successively:
3.3.1 Diameter of the Earth
3.3.2 Diameter of the Moon
3.3.3 Distance to the Moon
3.3.4 Distance to the Sun
3.3.5 Diameter of the Sun
3.4 Be able to use information about the mean diameter of the Sun (1.4 × 10⁶ km).
3.5 Understand the relative effects of the Sun and Moon in producing:
3.5.1 High and low tides
3.5.2 Spring and neap tides
3.6 Understand how the gradual precession of the Earth’s axis affects:
3.6.1 The appearance of the Sun, Moon, and stars when observed from Earth
3.6.2 Its use in archaeoastronomy
3.7 Be able to use data relating to the rate of precession of the Earth’s axis.
3.8 Understand the appearance of the Sun during:
3.8.1 Partial solar eclipses
3.8.2 Total solar eclipses
3.8.3 Annular solar eclipses
3.9 Understand the appearance of the Moon during:
3.9.1 Partial lunar eclipses
3.9.2 Total lunar eclipses
3.10 Understand the causes of solar and lunar eclipses.
Topic 4 – Time and the Earth-Moon-Sun Cycles
4.1 Understand the difference between sidereal and synodic (solar) days.
4.2 Understand the role of the Sun in determining Apparent Solar Time (AST).
4.3 Understand the role of the Mean Sun in determining:
4.3.1 Mean Solar Time (MST)
4.3.2 Local Mean Time (LMT)
4.4 Be able to use the Equation of Time:
4.4.1 Equation of Time = Apparent Solar Time (AST) − Mean Solar Time (MST)
4.5 Understand the annual variation of the Equation of Time.
4.6 Understand the causes of the annual variation of the Equation of Time.
4.7 Understand how to determine the time of local noon using shadows, including:
4.7.1 Use of a shadow stick
4.8 Understand the structure and use of sundials.
4.9 Understand the lunar phase cycle.
4.10 Understand the difference between sidereal and synodic (solar) months.
4.11 Understand the annual variation in times of sunrise and sunset.
4.12 Understand the astronomical significance of equinoxes and solstices.
4.13 Understand the variation in the Sun’s apparent motion during the year, particularly at the equinoxes and solstices.
4.14 Understand the relationship between sidereal and synodic (solar) time.
4.15 Understand the difference in local time for observers at different longitudes.
4.16 Understand the use of time zones.
4.17 Be able to use data related to time zones.
4.18 Know that mean time at any point along the Prime Meridian is defined as Greenwich Mean Time (GMT), which is the same as Universal Time (UT).
4.19 Be able to use shadow-stick data and the Equation of Time to determine longitude.
4.20 Understand the principles of astronomical methods for the determination of longitude, including:
4.20.1 Lunar distance method


4.21 Understand the principle of the horological method for the determination of longitude (Harrison’s marine chronometer).
Topic 5 – Solar System Observation
5.1 Understand how to use pinhole projection to observe the Sun safely.
5.2 Understand the observed motion of the Sun follows an annual path called the ecliptic.
5.3 Understand the changing position of the planets in the night sky.
5.4 Understand the observed motion of the planets takes place within a narrow Zodiacal Band.
5.5 Understand the observed retrograde motion of planets.
5.6 Understand the terms:
5.6.1 First Point of Aries
5.6.2 First Point of Libra
5.7 Understand the appearance and cause of meteors and meteor showers, including:
5.7.1 Determination of the radiant
5.8 Understand the terms:
5.8.1 Conjunction (superior and inferior)
5.8.2 Opposition
5.8.3 Elongation
5.8.4 Transit
5.8.5 Occultation
Topic 6 – Celestial Observation
6.1 Be able to recognize the following astronomical phenomena visible to the naked eye, including:
6.1.1 Sun
6.1.2 Moon
6.1.3 Stars (including double stars, constellations, and asterisms)
6.1.4 Star clusters
6.1.5 Galaxies and nebulae
6.1.6 Planets
6.1.7 Comets
6.1.8 Meteors
6.1.9 Aurorae
6.1.10 Supernovae
6.1.11 Artificial objects, including:
6.1.11.1 Artificial satellites
6.1.11.2 Aircraft
6.2 Be able to recognize and draw the following constellations and asterisms, including their most prominent stars:
6.2.1 Cassiopeia
6.2.2 Cygnus
6.2.3 Orion
6.2.4 Plough
6.2.5 Southern Cross
6.2.6 Summer Triangle
6.2.7 Square of Pegasus
6.3 Understand the use of asterisms as pointers to locate specific objects in the night sky, including:
6.3.1 Arcturus and Polaris from the Plough
6.3.2 Sirius, Aldebaran, and the Pleiades from Orion’s Belt
6.3.3 Fomalhaut and the Andromeda galaxy from Square of Pegasus
6.4 Understand why there is a range of constellation, asterism, and star names among different cultures.
6.5 Be able to use information from star charts, planispheres, computer programs, or ‘apps’ to identify objects in the night sky.
6.6 Understand the causes and effects of light pollution on observations of the night sky.
6.7 Understand the meaning of the terms:
6.7.1 Celestial sphere
6.7.2 Celestial poles
6.7.3 Celestial equator
6.8 Understand the use of the equatorial coordinate system, including:
6.8.1 Right ascension
6.8.2 Declination
6.9 Understand the use of the horizon coordinate system, including:
6.9.1 Altitude
6.9.2 Azimuth
6.10 Understand how the observer’s latitude can be used to link the equatorial and horizon coordinates of an object for the observer’s meridian.
6.11 Understand how the observer’s meridian defines local sidereal time and an object’s hour angle.
6.12 Be able to use information on equatorial and horizon coordinates to determine:
6.12.1 The best time to observe a particular celestial object
6.12.2 The best object(s) to observe at a particular time
6.13 Understand, in relation to astronomical observations, the terms:
6.13.1 Cardinal points
6.13.2 Culmination
6.13.3 Meridian
6.13.4 Zenith
6.13.5 Circumpolarity
6.14 Understand the diurnal motion of the sky due to the Earth’s rotation.
6.15 Be able to use a star’s declination to determine whether the star will be circumpolar from an observer’s latitude.
6.16 Understand the apparent motion of circumpolar stars, including:
6.16.1 Upper transit (culmination)
6.16.2 Lower transit
6.17 Be able to use information about rising and setting times of stars to predict their approximate position in the sky.
6.18 Be able to find the latitude of an observer using Polaris.
6.19 Understand naked-eye techniques such as:
6.19.1 Dark adaptation
6.19.2 Averted vision
6.20 Understand the factors affecting visibility, including:
6.20.1 Rising and setting
6.20.2 Seeing conditions
6.20.3 Weather conditions
6.20.4 Landscape
6.21 Understand the appearance of the Milky Way from Earth as seen with the naked eye.
Topic 7 – Early Models of the Solar System
7.1 Understand the use of detailed observations of solar and lunar cycles by ancient civilizations around the world for:
7.1.1 Agricultural systems
7.1.2 Religious systems
7.1.3 Time and calendar systems
7.1.4 Alignments of ancient monuments
7.2 Understand that the current celestial alignment of ancient monuments differs from their original celestial alignment due to the precession of the Earth’s axis.
7.3 Understand early geocentric models of the Solar System.
7.4 Understand the advantage of the addition of epicycles, as described by Ptolemy.
7.5 Be able to use information about the scale of the Solar System.
7.6 Be able to use the astronomical unit (1 AU = 1.5 × 10⁸ km), light year (l.y.), and parsec (pc).
Topic 8 – Planetary Motion and Gravity
8.1 Understand the contribution of the observational work of Brahe in the transition from a geocentric to a heliocentric model of the Solar System.
8.2 Understand the contribution of the mathematical modeling of Copernicus and Kepler in the transition from a geocentric to a heliocentric model of the Solar System.
8.3 Understand the role of gravity in creating stable elliptical orbits.
8.4 Understand Kepler's laws of planetary motion.
8.5 Understand the terms for an elliptical orbit:
8.5.1 Aphelion and perihelion (solar orbits)
8.5.2 Apogee and perigee (Earth orbits)
8.6 Be able to use Kepler’s third law in the form:
8.6.1 T² = a constant × r³
Where T is the orbital period of an orbiting body and r is the mean radius of its orbit.
8.7 Understand that the constant in Kepler’s third law depends inversely on the mass of the central body.
8.8 Know that Newton was able to explain Kepler’s laws using his law of universal gravitation.
8.9 Understand that the gravitational force between two bodies is:
8.9.1 Proportional to the product of their masses
8.9.2 Inversely proportional to the square of their separation



Paper 2: Telescopic Astronomy
Topic 9 – Exploring the Moon
9.1 Understand the Moon’s major internal divisions in comparison with those of the Earth.
9.2 Understand the major differences between the appearance of the Moon’s near and far sides.
9.3 Understand how information has been gathered about the Moon's far side.
9.4 Understand that a spacecraft traveling to the Moon must reach the Earth’s escape velocity, the energy requirements of which can be met only by the use of rockets.
9.5 Understand the Giant Impact Hypothesis and alternative theories of the Moon’s origin.
9.5.1 Capture Theory
9.5.2 Co-accretion Theory
Topic 10 – Solar Astronomy
10.1 Understand methods of observing the Sun safely.
10.1.1 Telescopic projection
10.1.2 H-alpha filter
10.2 Know the location and relative temperatures of the Sun’s internal divisions.
10.2.1 Core
10.2.2 Radiative zone
10.2.3 Convective zone
10.2.4 Photosphere
10.3 Understand the role of the Sun’s internal divisions in terms of energy production and transfer.
10.4 Understand the principal nuclear fusion process in the Sun.
10.4.1 Proton-proton cycle
10.5 Know the location, temperature, and relative density of components of the solar atmosphere.
10.5.1 Chromosphere
10.5.2 Corona
10.6 Understand the structure, origin, and evolution of sunspots.
10.7 Be able to use sunspot data to determine the mean solar rotation period.
10.8 Be able to use sunspot data relating to the solar cycle.
10.9 Understand the different appearance of the Sun when observed using radiation from the different regions of the electromagnetic spectrum.
10.10 Understand the nature, composition, and origin of the solar wind.
10.11 Understand the principal effects of the solar wind.
10.11.1 Aurorae
10.11.2 Cometary tails
10.11.3 Geomagnetic storms
10.11.4 Effects on satellites, aircraft travel, and manned missions
10.12 Know the shape and position of the Earth’s magnetosphere, including:
10.12.1 Van Allen Belts
Topic 11 – Exploring the Solar System
11.1 Be able to use data about the names and relative locations of bodies in the Solar System.
11.1.1 Planets
11.1.2 Dwarf planets
11.1.3 Small Solar System Objects (SSSOs): asteroids, meteoroids, and comets
11.2 Understand the structure of comets.
11.2.1 Nucleus
11.2.2 Coma
11.2.3 Tails
11.3 Understand the orbits of short-period comets and their likely origin in the Kuiper Belt.
11.4 Understand the orbits of long-period comets and their likely origin in the Oort Cloud.
11.5 Understand the location and nature of the Kuiper Belt, Oort Cloud, and the heliosphere.
11.6 Understand the following principal characteristics of the planets.
11.6.1 Relative size
11.6.2 Relative mass
11.6.3 Surface temperature
11.6.4 Atmospheric composition
11.6.5 Presence of satellites
11.6.6 Presence of ring systems
11.7 Understand the main theories for the formation and current position of the gas giant planets in our Solar System.
11.8 Be able to use information about the size of the Solar System.
11.9 Be able to use the astronomical unit (1 AU = 1.5 × 10⁸ km), light year (l.y.), and parsec (pc).
11.10 Understand the origin and structure of meteoroids and meteorites.
11.11 Know that most bodies in the Solar System orbit the Sun in, or close to, a plane called the ecliptic.
11.12 Understand the use of transits of Venus (as proposed by Halley) to determine the size of the astronomical unit and thus the absolute size of the Solar System.
11.13 Understand the main theories for the origin of water on Earth.
11.14 Know that the human eye is limited in astronomical observations by its small aperture and limited sensitivity in low light.
11.15 Understand how the objective element of a telescope captures and focuses light so that the image can be magnified by an eyepiece.
11.16 Know that convex (converging) lenses and concave (converging) mirrors can be used to collect and focus light from astronomical objects.
11.17 Understand how simple telescopes can be made by combining an objective (lens or mirror) with an eyepiece.
11.18 Understand the basic design of the following in terms of their key elements.
11.18.1 Galilean refracting telescope
11.18.2 Keplerian refracting telescope
11.18.3 Newtonian reflecting telescope
11.18.4 Cassegrain reflecting telescope
11.19 Understand that the ‘light grasp’ of a telescope is directly proportional to the area of the objective element and thus the square of the diameter of the objective element.
11.20 Know that the aperture of a telescope is related to the diameter of the objective element.
11.21 Know that the field of view is the circle of sky visible through the eyepiece, measured in degrees or arcmin.
11.22 Understand the resolution of a telescope.
11.22.1 Proportional to the diameter of the objective element
11.22.2 Reduced by observing at a longer wavelength
11.23 Be able to use the formula for the magnification of a telescope: magnification = fo/fe (where fo is the focal length of the objective element and fe is the focal length of the eyepiece).
11.24 Understand the importance of Galileo's early telescopic observations in establishing a heliocentric (Sun-centered) model of the Solar System.
11.25 Understand the advantages of reflecting telescopes compared to refracting telescopes, in terms of:
11.25.1 Chromatic aberration
11.25.2 Very long focal lengths
11.25.3 Using large aperture objectives
11.25.4 Use of multiple mirrors


11.26 Understand the advantages and disadvantages of the major types of space probe.
11.26.1 Fly-by
11.26.2 Orbiter
11.26.3 Impactor
11.26.4 Lander
11.27 Know an example of each type of space probe, including target body and major discoveries.
11.27.1 Fly-by – New Horizons (Outer Solar System)
11.27.2 Orbiter – Juno (Jupiter) or Dawn (asteroids Vesta and Ceres)
11.27.3 Impactor – Deep Impact (comet Tempel 1)
11.27.4 Lander – Philae (comet 67P/Churyumov–Gerasimenko)
11.28 Understand that a space probe must reach the Earth’s escape velocity, the energy requirements of which can be met only by the use of rockets.
11.29 Understand the advantages and disadvantages of direct observation via manned missions.
11.30 Understand the main features of the Apollo programme to land astronauts on the Moon.
Topic 12 – Formation of Planetary Systems
12.1 Be able to identify the operation of each of the following in our Solar System.
12.1.1 Gravitational attraction producing regular motion, including the orbits of planets and moons.
12.1.2 Tidal gravitational forces producing effects, including ring systems, asteroid belts, and internal heating.
12.1.3 Gravitational interactions of multiple bodies producing effects such as gradual shifts in orbits, chaotic motion, resonances, and the significance of Lagrangian Points (detailed mathematical descriptions not required).
12.1.4 Accidental collisions causing impact craters, changes to orbital motions, or planetary orientations.
12.1.5 Solar wind affecting comets, planetary atmospheres, and the heliosphere.
12.2 Be able to identify the operation of each of the following interactions in the formation of planets and moons.
12.2.1 The interaction between tidal gravitational and elastic forces to determine whether a body is broken apart (Roche Limit).
12.2.2 The interaction between attractive gravitational and elastic forces in determining a body’s spherical or irregular shape.
12.2.3 The interaction between gravitational and thermal factors in determining the presence of an atmosphere.
12.3 Understand the main theories for the formation of gas giant planets in planetary systems.
12.4 Understand the current methods for discovering systems of exoplanets, including:
12.4.1 Transit method
12.4.2 Astrometry
12.4.3 Radial velocity measurements
12.5 Understand the requirements for life and the possibility of life forms existing elsewhere, including:
12.5.1 On Titan
12.5.2 On Europa
12.5.3 On Enceladus
12.5.4 Outside our Solar System
12.6 Understand the relevance of the Goldilocks (Habitable) Zones.
12.7 Understand how factors in the Drake equation can be used to allow us to estimate the number of civilizations in our Galaxy.
12.8 Understand the search for extra-terrestrial intelligence, by receiving radio waves (SETI), including the benefits and dangers of discovering extra-terrestrial life.
Topic 13 – Exploring Starlight
13.1 Understand the astronomical magnitude scale and how apparent magnitude relates to the brightness of stars as viewed from Earth.
13.2 Understand the term absolute magnitude.
13.3 Be able to use the distance modulus formula to determine the absolute (M) or apparent magnitude (m) of a star, given the distance to the star (d):
13.3.1 M = m + 5 − 5logd (where d is the distance in parsec).
13.4 Understand what information can be obtained from a stellar spectrum, including:
13.4.1 Chemical composition
13.4.2 Temperature
13.4.3 Radial velocity
13.5 Understand how stars can be classified according to spectral type.
13.6 Understand how a star’s color and spectral type are related to its surface temperature.
13.7 Be able to sketch a simple Hertzsprung-Russell diagram, including labeled axes and indicate the positions of the following:
13.7.1 Main sequence stars
13.7.2 The Sun
13.7.3 Red and blue giant stars
13.7.4 White dwarf stars
13.7.5 Supergiant stars
13.8 Understand how a star’s life cycle relates to its position on the Hertzsprung-Russell diagram, for stars similar in mass to the Sun and those with masses that are much greater.
13.9 Understand the inverse square relationship between distance and brightness/intensity.
13.10 Understand that an angle of one degree (°) comprises 60 minutes of arc (arcmin) (60’) and that each arcminute is comprised of 60 seconds of arc (arcsec) (60").
13.11 Understand the term parsec (pc).
13.12 Be able to determine astronomical distances using heliocentric parallax.
13.13 Understand how to use a Hertzsprung-Russell diagram to determine distances to stars.
13.14 Understand the light curves of the following variable stars:
13.14.1 Short/long period
13.14.2 Eclipsing binary
13.14.3 Cepheid
13.14.4 Novae and supernovae
13.15 Understand the causes of variability in the light curve of eclipsing binary stars.
13.16 Understand how Cepheid variables can be used to determine distances.
13.17 Understand the structure of gravitationally bound stellar groupings such as binary stars and clusters.
13.18 Understand how the period of an eclipsing binary star can be deduced from its light curve.
13.19 Be able to use star trail photographs to determine the length of the sidereal day.
13.20 Know that most modern astronomical observations are recorded using digital sensors that convert light into electrical signals, which can then be processed and stored as data files.
13.21 Understand how astronomers obtain and study the patterns of spectral lines in the light from astronomical objects.
13.22 Know that the Earth’s atmosphere blocks almost all of the radiation of different wavelengths in the electromagnetic spectrum, except visible light and radio waves.
13.23 Know that only optical and radio telescopes should be located at sea level on the Earth’s surface.
13.24 Understand how a simple radio telescope operates.
13.25 Understand why radio telescopes need extremely large apertures in order to maintain a useful resolution.
13.26 Understand how multiple radio telescopes can operate as an aperture synthesis system (array).
13.27 Know that radio astronomy has been important in the discovery of:
13.27.1 Quasars
13.27.2 Jets from black holes
13.27.3 The structure of the Milky Way
13.27.4 Protoplanetary discs
13.28 Understand why some infrared telescopes can operate in high-altitude locations on the Earth's surface.
13.29 Know that infrared astronomy has been important in the discovery of:
13.29.1 Protostars
13.29.2 Dust and molecular clouds
13.29.3 Hotspots on moons
13.30 Understand the detrimental effect of the Earth's atmosphere on the quality of images formed by telescopes on the Earth’s surface.
13.31 Understand why telescopes operating outside the optical and radio ‘windows’ need to be sited above the Earth’s atmosphere.
13.32 Understand the advantages and disadvantages of space telescopes and detectors, including orbital observing platforms.
13.33 Understand how gamma ray, x-ray, and ultraviolet astronomy have been important in the discovery of:
13.33.1 Gamma ray bursts
13.33.2 Black hole accretion discs
13.33.3 The corona and chromosphere structure of young stars
13.34 Understand how a telescope alters the appearance of:
13.34.1 Stars
13.34.2 Double stars
13.34.3 Binary stars
13.34.4 Open clusters
13.34.5 Globular clusters
13.34.6 Nebulae
13.34.7 Galaxies
Topic 14 – Stellar Evolution
14.1 Be able to use the Messier and New General Catalogue (NGC) in cataloguing nebulae, clusters, and galaxies.
14.2 Be able to use the Bayer system for naming the brightest stars within a constellation.
14.3 Understand the effects of the interaction between radiation pressure and gravity in a main sequence star.
14.4 Understand changes to the radiation pressure-gravity balance at different stages in the life cycle of a star with a mass similar to the Sun.
14.5 Understand the balance between electron pressure and gravity in a white dwarf star.
14.6 Understand changes to the radiation pressure-gravity balance at different stages in the life cycle of a star with a mass much greater than the Sun.
14.7 Understand the balance between neutron pressure and gravity in a neutron star.
14.8 Understand the effect the Chandrasekhar Limit has on the outcome of the final stages of the life cycle of a star.
14.9 Understand the principal stages and timescales of stellar evolution for stars of similar mass to the Sun, including:
14.9.1 Emission and absorption nebula
14.9.2 Main sequence star
14.9.3 Planetary nebula
14.9.4 Red giant
14.9.5 White dwarf
14.9.6 Black dwarf
14.10 Understand the principal stages and timescales of stellar evolution for stars of much larger mass than the Sun, including:
14.10.1 Emission and absorption nebula
14.10.2 Main sequence star
14.10.3 Red supergiant
14.10.4 Supernova
14.10.5 Neutron star
14.10.6 Black hole
14.11 Understand how astronomers study and gather evidence for the existence of black holes.
Topic 15 – Our Place in the Galaxy
15.1 Understand the appearance of the Milky Way from Earth as seen with binoculars or a small telescope.
15.2 Know the size and shape of our Galaxy and the location of the Sun, dust, sites of star formation, and globular clusters.
15.3 Understand how 21 cm radio waves, rather than visible light, are used to determine the structure and rotation of our Galaxy.
15.4 Know that the group of galaxies gravitationally linked to the Milky Way is called the Local Group.
15.5 Know the composition and scale of the Local Group, including its principal components:
15.5.1 Andromeda Galaxy (M31)
15.5.2 Large and Small Magellanic Clouds (LMC and SMC)
15.5.3 Triangulum Galaxy (M33)
15.6 Be able to classify galaxies using the Hubble classification system, including:
15.6.1 Spiral
15.6.2 Barred spiral
15.6.3 Elliptical
15.6.4 Irregular
15.7 Know how the different types of galaxies were placed by Hubble on his ‘Tuning Fork’ diagram.
15.8 Know that the Milky Way is a barred spiral (SBb) type galaxy.
15.9 Know that some galaxies emit large quantities of radiation in addition to visible light.
15.10 Know that an Active Galactic Nucleus (AGN) is powered by matter falling onto a super-massive black hole.
15.11 Know types of active galaxies, including:
15.11.1 Seyfert galaxies
15.11.2 Quasars
15.11.3 Blazars
15.12 Know that information about AGNs can be obtained from many regions of the electromagnetic spectrum.
15.13 Understand why galaxies are grouped in larger clusters and superclusters.
15.14 Understand the main theories for the formation and evolution of galaxies.
Topic 16 – Cosmology
16.1 Know that observations of galaxies outside the Local Group show that light is shifted to longer wavelengths (redshift).
16.2 Understand that redshift is caused by galaxies receding from us.
16.3 Be able to use the formula:
16.3.1 λ − λ₀ / λ₀ = v / c
Where λ is the observed wavelength, λ₀ is the emitted wavelength, v is the radial velocity of the source, and c is the speed of light.
16.4 Understand the evidence to confirm the discovery of the expanding universe.
16.5 Be able to use the relationship between distance and redshift of distant galaxies (Hubble’s law), including the formula:
16.5.1 v = H₀d
Where v is the radial velocity of the recession of the galaxy, H₀ is the Hubble constant, and d is the distance of the galaxy from Earth.
16.6 Understand the estimation of the age and size of the Universe using the value of the Hubble constant.
16.7 Understand how the expansion of the Universe supports both the Big Bang theory and the Steady State theory.
16.8 Understand the major observational evidence in favor of the Big Bang theory, including:
16.8.1 Quasars (QSOs)
16.8.2 Cosmic microwave background (CMB) radiation
16.8.3 Hubble Deep Field image
16.9 Understand the significance of the fluctuations in the CMB radiation for theories of the evolution of the Universe, including discoveries by:
16.9.1 Wilkinson Microwave Anisotropy Probe (WMAP)
16.9.2 Planck mission
16.10 Understand the significance and possible nature of dark matter and dark energy.
16.11 Understand the difficulties involved in the detection of dark matter and dark energy.
16.12 Understand that current models of the Universe predict different future evolutionary paths.

"""

# ===== END EDIT SECTION =====


def sanitize_code(text):
    """Convert text to safe code format."""
    # Remove special characters, keep alphanumeric and spaces
    safe = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    # Replace spaces with underscores
    safe = re.sub(r'\s+', '_', safe.strip())
    # Limit length
    return safe[:50]


def parse_hierarchy(text):
    """Parse hierarchical text into topic structure."""
    lines = [line.rstrip() for line in text.strip().split('\n') if line.strip()]
    
    topics = []
    current_area = None  # Level 0 area (for RSB format)
    current_component = None
    current_topic = None
    current_section = None
    current_subsection = None
    
    component_num = 0
    topic_num = 0
    section_num = 0
    subsection_num = 0
    item_num = 0
    
    for line in lines:
        # Skip informational headers
        if 'Here is the detailed hierarchy' in line or 'from the Pearson Edexcel' in line:
            continue
        
        # Detect "Area of Study X:" (Religious Studies B - with colon OR dash)
        # Format: "Area of Study 1: Religion and Ethics" OR "Area of Study 1A – Catholic Christianity"
        if re.match(r'^Area of Study\s+\d+', line, re.IGNORECASE):
            # Try format with dash first (Religious Studies A)
            area_match = re.match(r'^Area of Study\s+(\d+)([A-Z]?)\s*[–-]\s*(.+)$', line, re.IGNORECASE)
            if area_match:
                area_number = area_match.group(1)  # "1", "2", "3", "4"
                area_letter = area_match.group(2)  # "A", "B", "C", etc.
                area_name = area_match.group(3).strip()
                
                # Create Level 0 (Area of Study 1, 2, 3, 4) if not exists
                level0_code = f"AreaofStudy{area_number}"
                level0_title = f"Area of Study {area_number}"
                
                # Add Level 0 if not already added
                if not any(t['code'] == level0_code for t in topics):
                    topics.append({
                        'code': level0_code,
                        'title': level0_title,
                        'level': 0,
                        'parent': None
                    })
                    print(f"[L0] {level0_title}")
                
                # Create Level 1 (1A, 1B, 2D, etc.)
                if area_letter:
                    level1_code = f"AreaofStudy{area_number}{area_letter}"
                    level1_title = line.strip()
                    
                    topics.append({
                        'code': level1_code,
                        'title': level1_title,
                        'level': 1,
                        'parent': level0_code
                    })
                    
                    current_component = level1_code
                    current_topic = None
                    current_section = None
                    current_subsection = None
                    print(f"  [L1] {level1_title}")
                else:
                    # No letter, so this IS the main area
                    current_component = level0_code
                    current_topic = None
                    current_section = None
                    current_subsection = None
                
                continue
            
            # Try format with colon (Religious Studies B)
            area_match2 = re.match(r'^Area of Study\s+(\d+):\s*(.+)$', line, re.IGNORECASE)
            if area_match2:
                area_number = area_match2.group(1)
                area_name = area_match2.group(2).strip()
                
                # Create Level 0
                level0_code = f"AreaofStudy{area_number}"
                level0_title = line.strip()
                
                topics.append({
                    'code': level0_code,
                    'title': level0_title,
                    'level': 0,
                    'parent': None
                })
                
                current_area = level0_code  # Track Level 0 separately
                current_component = level0_code
                current_topic = None
                current_section = None
                current_subsection = None
                print(f"[L0] {level0_title}")
                continue
        
        # Detect "1A Name" format (Religious Studies B sub-areas)
        if re.match(r'^(\d+)([A-Z])\s+', line) and current_area:
            subarea_match = re.match(r'^(\d+)([A-Z])\s+(.+)$', line)
            if subarea_match:
                number = subarea_match.group(1)
                letter = subarea_match.group(2)
                name = subarea_match.group(3).strip()
                
                # Always use the Level 0 area as parent, NOT current_component
                parent_area = f"AreaofStudy{number}"
                level1_code = f"{parent_area}_{number}{letter}"
                level1_title = f"{number}{letter} {name}"
                
                topics.append({
                    'code': level1_code,
                    'title': level1_title,
                    'level': 1,
                    'parent': parent_area
                })
                
                # Set current_component to this sub-area (for sections to attach to)
                current_component = level1_code
                current_topic = None
                current_section = None
                current_subsection = None
                print(f"  [L1] {level1_title}")
                continue
        
        # Detect "Section X:" (Level 2 in Religious Studies with Area structure)
        if re.match(r'^Section\s+\d+:', line, re.IGNORECASE):
            section_match = re.match(r'^Section\s+(\d+):\s+(.+)$', line, re.IGNORECASE)
            if section_match and current_component:
                section_num = section_match.group(1)
                section_title = section_match.group(2).strip()
                section_code = f"{current_component}_Section{section_num}"
                
                topics.append({
                    'code': section_code,
                    'title': f"Section {section_num}: {section_title}",
                    'level': 2,
                    'parent': current_component
                })
                
                current_topic = section_code
                current_section = None
                current_subsection = None
                print(f"    [L2] Section {section_num}: {section_title}")
                continue
        
        # Detect "Paper X:" format (Level 0) - Science subjects
        if re.match(r'^Paper\s+\d+:', line, re.IGNORECASE):
            paper_match = re.match(r'^Paper\s+(\d+):\s*(.+)$', line, re.IGNORECASE)
            if paper_match:
                paper_num = paper_match.group(1)
                paper_name = paper_match.group(2).strip()
                paper_code = f"Paper{paper_num}"
                
                topics.append({
                    'code': paper_code,
                    'title': line.strip(),
                    'level': 0,
                    'parent': None
                })
                
                current_component = paper_code
                current_topic = None
                current_section = None
                current_subsection = None
                print(f"[L0] {line.strip()}")
                continue
        
        # Detect Component (Level 0) - "Component X:" format
        if re.match(r'^Component\s+\d+:', line, re.IGNORECASE):
            component_num += 1
            component_code = f"Component{component_num}"
            component_title = line.strip()
            
            topics.append({
                'code': component_code,
                'title': component_title,
                'level': 0,
                'parent': None
            })
            
            current_component = component_code
            current_topic = None
            current_section = None
            current_subsection = None
            topic_num = 0
            print(f"[L0] {component_title}")
            
        # Detect "1. Name" format (Level 0) - Statistics main sections OR Psychology with dash
        elif re.match(r'^\d+\.\s+[A-Z]', line):
            topic_match = re.match(r'^(\d+)\.\s+(.+)$', line)
            if topic_match:
                topic_num = topic_match.group(1)
                topic_title = topic_match.group(2).strip()
                topic_code = f"Section{topic_num}"
                
                topics.append({
                    'code': topic_code,
                    'title': line.strip(),
                    'level': 0,
                    'parent': None
                })
                
                current_component = topic_code
                current_topic = None
                current_section = None
                current_subsection = None
                print(f"[L0] {line.strip()}")
        
        # Detect "(a) Name" format (Level 1) - Statistics subsections
        elif re.match(r'^\([a-z]\)\s+', line) and current_component:
            subsection_match = re.match(r'^\(([a-z])\)\s+(.+)$', line)
            if subsection_match:
                letter = subsection_match.group(1)
                subsection_name = subsection_match.group(2).strip()
                subsection_code = f"{current_component}_Sub{letter}"
                
                topics.append({
                    'code': subsection_code,
                    'title': line.strip(),
                    'level': 1,
                    'parent': current_component
                })
                
                current_topic = subsection_code
                current_section = None
                current_subsection = None
                print(f"  [L1] {line.strip()}")
                continue
        
        # Detect "Optional Topic X:" format (also Level 0)
        elif re.match(r'^Optional\s+Topic\s+\d+:', line, re.IGNORECASE) or re.match(r'^Compulsory\s+Topic\s+\d+:', line, re.IGNORECASE):
            topic_match = re.match(r'^(Optional|Compulsory)\s+Topic\s+(\d+):\s+(.+)$', line, re.IGNORECASE)
            if topic_match:
                topic_num = topic_match.group(2)
                topic_title = line.strip()
                topic_code = f"Topic{topic_num}"
                
                topics.append({
                    'code': topic_code,
                    'title': topic_title,
                    'level': 0,
                    'parent': None
                })
                
                current_component = topic_code
                current_topic = None
                current_section = None
                current_subsection = None
                print(f"[L0] {topic_title}")
            
        # Detect "Topic X:" or "Topic X –" format (Level 1)
        elif re.match(r'^Topic\s+\d+\s*[:\-–]', line, re.IGNORECASE):
            topic_match = re.match(r'^Topic\s+(\d+)\s*[:\-–]\s*(.*)$', line, re.IGNORECASE)
            if topic_match:
                topic_num = topic_match.group(1)
                topic_name = topic_match.group(2).strip() if topic_match.group(2) else ""
                topic_code = f"{current_component}_Topic{topic_num}"
                topic_title = line.strip()
                
                topics.append({
                    'code': topic_code,
                    'title': topic_title,
                    'level': 1,
                    'parent': current_component
                })
                
                current_topic = topic_code
                current_section = None
                current_subsection = None
                section_num = 0
                print(f"  [L1] {topic_title}")
        
        # Detect "1a.01:" format (Level 2) - Statistics topic codes
        elif re.match(r'^\d+[a-z]\.\d+:', line) and current_topic:
            code_match = re.match(r'^(\d+[a-z]\.\d+):\s*(.+)$', line)
            if code_match:
                code_number = code_match.group(1)
                code_title = code_match.group(2).strip()
                code_safe = code_number.replace('.', '_')
                topic_code = f"{current_topic}_T{code_safe}"
                
                topics.append({
                    'code': topic_code,
                    'title': f"{code_number}: {code_title}",
                    'level': 2,
                    'parent': current_topic
                })
                
                current_section = topic_code
                current_subsection = None
                print(f"    [L2] {code_number}: {code_title[:50]}...")
                continue
        
        # Detect "1.1 Name" format or "1.1: Name" format
        elif re.match(r'^\d+\.\d+[\s:]', line) and not re.match(r'^\d+\.\d+\.\d+', line):
            section_match = re.match(r'^(\d+\.\d+)[\s:]+(.+)$', line)
            if section_match:
                section_number = section_match.group(1)
                section_title = section_match.group(2).strip()
                
                # Determine level based on context
                if current_topic:
                    # We have Topic (Level 1), so "1.1" is Level 2
                    section_code = f"{current_topic}_S{section_number.replace('.', '_')}"
                    level = 2
                    parent = current_topic
                elif current_component:
                    # We have Component/Area/Paper (Level 0), so "1.1" depends
                    # Check if this is Religious Studies format (has Area codes)
                    if 'AreaofStudy' in current_component:
                        # Religious Studies: 1.1 is Level 2 under the Area
                        section_code = f"{current_component}_S{section_number.replace('.', '_')}"
                        level = 2
                        parent = current_component
                    elif 'Paper' in current_component:
                        # Science format without Topic detected - treat 1.1 as Level 1
                        section_code = f"{current_component}_S{section_number.replace('.', '_')}"
                        level = 1
                        parent = current_component
                    else:
                        # Psychology/PE format
                        section_code = f"{current_component}_S{section_number.replace('.', '_')}"
                        level = 1
                        parent = current_component
                else:
                    # No component detected yet, skip
                    continue
                
                topics.append({
                    'code': section_code,
                    'title': f"{section_number} {section_title}",
                    'level': level,
                    'parent': parent
                })
                
                current_section = section_code
                current_subsection = None
                indent = "      " if level == 3 else ("    " if level == 2 else "  ")
                print(f"{indent}[L{level}] {section_number} {section_title}")
        
        # Detect "1.1.1.1 Name" format (4-level numbering)
        elif re.match(r'^\d+\.\d+\.\d+\.\d+\s+', line):
            item_match = re.match(r'^(\d+\.\d+\.\d+\.\d+)\s+(.+)$', line)
            if item_match and current_subsection:
                item_number = item_match.group(1)
                item_title = item_match.group(2).strip()
                item_code = f"{current_subsection}_L4{item_number.replace('.', '_')}"
                
                topics.append({
                    'code': item_code,
                    'title': f"{item_number} {item_title}",
                    'level': 4,
                    'parent': current_subsection
                })
                
                indent = "        "
                print(f"{indent}[L4] {item_number} {item_title}")
        
        # Detect "1.1.1 Name" format (3-level numbering)
        elif re.match(r'^\d+\.\d+\.\d+\s+', line):
            subsection_match = re.match(r'^(\d+\.\d+\.\d+)\s+(.+)$', line)
            subsection_number = subsection_match.group(1)
            subsection_title = subsection_match.group(2).strip()
            
            if current_section:
                subsection_code = f"{current_section}_SS{subsection_number.replace('.', '_')}"
                # Level depends on current_section level
                # If current_section is Level 3, this is Level 4
                # If current_section is Level 2, this is Level 3
                if current_topic and 'Section' in current_topic:
                    level = 4  # Religious Studies with Sections
                else:
                    level = 3  # Psychology format
                parent = current_section
                
                topics.append({
                    'code': subsection_code,
                    'title': f"{subsection_number} {subsection_title}",
                    'level': level,
                    'parent': parent
                })
                
                # Only set current_subsection if the title ends with ":" (indicating it's a container)
                if subsection_title.endswith(':'):
                    current_subsection = subsection_code
                else:
                    current_subsection = None
                
                item_num = 0
                indent = "        " if level == 4 else "      "
                print(f"{indent}[L{level}] {subsection_number} {subsection_title}")
            
        # Everything else is a detail item
        elif line and (current_section or current_subsection):
            item_title = line.strip()
            
            # Skip lines that are just colons, very short, or explanatory text
            if item_title in ['', ':']:
                continue
            
            # Skip explanatory text that starts with "Where" (these are formula explanations)
            if item_title.startswith('Where ') or item_title.startswith('where '):
                continue
            
            item_num += 1
            parent = current_subsection or current_section
            item_code = f"{parent}_Item{item_num}"
            
            # Determine level based on what parent we have
            if current_subsection:
                # Subsection (Level 4), so detail is Level 5
                level = 5
            elif current_section:
                # Section level varies, determine from parent
                # If current_section is Level 3, detail is Level 4
                # If current_section is Level 2, detail is Level 3
                # Check if current_section is under a Section (Level 2)
                if current_topic and 'Section' in current_topic:
                    # Section is Level 2, 1.1 is Level 3, detail is Level 4
                    if item_title.endswith(':') and len(item_title) < 80:
                        level = 4
                        item_title = item_title.rstrip(':')
                        current_subsection = item_code
                    else:
                        level = 4
                else:
                    # No explicit Section, so current_section is Level 2-3
                    if item_title.endswith(':') and len(item_title) < 80:
                        level = 3
                        item_title = item_title.rstrip(':')
                        current_subsection = item_code
                    else:
                        level = 3
            else:
                continue
            
            topics.append({
                'code': item_code,
                'title': item_title,
                'level': level,
                'parent': parent
            })
            
            indent = "          " if level == 5 else ("        " if level == 4 else "      ")
            print(f"{indent}[L{level}] {item_title[:60]}...")
    
    return topics


def upload_topics(subject_info, topics):
    """Upload parsed topics to Supabase."""
    print(f"\n[INFO] Uploading {len(topics)} topics for {subject_info['name']}...")
    
    try:
        # Create/update subject
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{subject_info['name']} ({subject_info['qualification']})",
            'subject_code': subject_info['code'],
            'qualification_type': subject_info['qualification'],
            'specification_url': subject_info['pdf_url'],
            'exam_board': subject_info['exam_board']
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Clear old topics
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared old topics")
        
        # Insert topics
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': subject_info['exam_board']
        } for t in topics]
        
        inserted = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted.data)} topics")
        
        # Link parent relationships level by level to ensure parents exist first
        code_to_id = {t['topic_code']: t['id'] for t in inserted.data}
        
        # Process by level to ensure parents linked before children
        for level_num in [1, 2, 3, 4, 5]:
            level_topics = [t for t in topics if t['level'] == level_num and t['parent']]
            linked = 0
            
            for topic in level_topics:
                parent_id = code_to_id.get(topic['parent'])
                child_id = code_to_id.get(topic['code'])
                if parent_id and child_id:
                    supabase.table('staging_aqa_topics').update({
                        'parent_topic_id': parent_id
                    }).eq('id', child_id).execute()
                    linked += 1
            
            if linked > 0:
                print(f"[OK] Linked {linked} Level {level_num} parent relationships")
        
        # Summary
        levels = defaultdict(int)
        for t in topics:
            levels[t['level']] += 1
        
        print("\n" + "=" * 80)
        print(f"[SUCCESS] {subject_info['name'].upper()} - UPLOAD COMPLETE!")
        print("=" * 80)
        for level in sorted(levels.keys()):
            count = levels[level]
            level_names = {
                0: 'Main Areas/Components',
                1: 'Sub-Areas/Topics',
                2: 'Sections',
                3: 'Subsections',
                4: 'Details',
                5: 'Sub-details'
            }
            print(f"   Level {level} ({level_names.get(level, f'Level {level}')}): {count}")
        print(f"\n   Total: {len(topics)} topics")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("UNIVERSAL HIERARCHY TEXT PARSER & UPLOADER")
    print("=" * 80)
    print(f"Subject: {SUBJECT_INFO['name']}")
    print("=" * 80)
    print()
    
    # Parse the hierarchy text
    print("[INFO] Parsing hierarchy text...")
    topics = parse_hierarchy(HIERARCHY_TEXT)
    
    if not topics:
        print("[ERROR] No topics found! Check your HIERARCHY_TEXT format.")
        return
    
    print(f"\n[OK] Parsed {len(topics)} topics")
    
    # Upload to Supabase
    success = upload_topics(SUBJECT_INFO, topics)
    
    if success:
        print("\n✅ COMPLETE!")
        print("\nYou can now:")
        print("  1. Edit SUBJECT_INFO for a new subject")
        print("  2. Paste new hierarchy text into HIERARCHY_TEXT")
        print("  3. Run this script again!")
    else:
        print("\n❌ FAILED")


if __name__ == '__main__':
    main()

