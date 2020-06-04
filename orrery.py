import numpy as np
import matplotlib.pyplot as plt
from glob import glob
import os
import datetime as dt
from diverging_map import diverge_map
import matplotlib.font_manager as fm
import pandas as pd
from astropy.coordinates import SkyCoord, BarycentricTrueEcliptic

# what KOI file to use
cd = os.path.abspath(os.path.dirname(__file__))
#koilist = os.path.join(cd, 'KOI_List.txt')
koilist = os.path.join(cd, 'download_toi.txt')
#koilist = os.path.join(cd, 'KOI_List_old.txt')

# are we loading in system locations from a previous file (None if not)
#lcenfile = os.path.join(cd, 'orrery_centers.txt')
#lcenfile = os.path.join(cd, 'orrery_centers_old.txt')
#lcenfile = None
lcenfile = os.path.join(cd, 'tess_centers.txt')
# if we're not loading a centers file,
# where do we want to save the one generated (None if don't save)
#scenfile = os.path.join(cd, 'tess_centers.txt')
scenfile = None

# add in the solar system to the plots
addsolar = True
# put it at a fixed location? otherwise use posinlist to place it
fixedpos = True
# fixed x and y positions (in AU) to place the Solar System
# if addsolar and fixedpos are True
ssx = 0.
ssy = 0.
# fraction of the way through the planet list to treat the solar system
# if fixedpos is False.
# 0 puts it first and near the center, 1 puts it last on the outside
posinlist = 0.2

# making rstart smaller or maxtry bigger takes longer but tightens the
# circle
# Radius of the circle (AU) to initially try placing a system
# when generating locations
rstart = 0.5
# number of tries to randomly place a system at a given radius
# before expanding the circle
maxtry = 50
# minimum spacing between systems (AU)
spacing = 0.4

# which font to use for the text
fontfile = os.path.join(cd, 'Avenir-Black.otf')
fontfam = 'normal'
fontcol = 'white'

# font sizes at various resolutions
fszs1 = {480: 12, 720: 14, 1080: 22}
fszs2 = {480: 15, 720: 17, 1080: 27}

# background color
bkcol = 'black'

# color and alpha for the circular orbit paths
orbitcol = '#424242'
orbitalpha = 1.

# add a background to the legend to distinguish it?
legback = True
# if so, use this color and alpha
legbackcol = bkcol
legalpha = 0.7

# are we making the png files for a movie or gif
makemovie = False
# resolution of the images. Currently support 480, 720 or 1080.
reso = 1080

# output directory for the images in the movie
# (will be created if it doesn't yet exist)
#outdir = os.path.join(cd, 'orrery-40s/')
outdir = os.path.join(cd, 'tess-movie/')

# number of frames to produce
# using ffmpeg with the palette at (sec * frames/sec)
# nframes = 40 * 20
nframes = 35 * 30

# times to evaluate the planets at
# Kepler observed from 120.5 to 1591
tstep = 0.2
times = np.arange(1325, 1325 + nframes*tstep, tstep)

# setup for the custom zoom levels
inds = np.arange(len(times))
nmax = inds[-1]
zooms = np.zeros_like(times) - 1.
x0s = np.zeros_like(times) + np.nan
y0s = np.zeros_like(times) + np.nan
startx, starty = 0, 0.2
endx, endy = 0, 0.2
# what zoom level each frame is at (1. means default with everything)

"""
# zoom out once
zooms[inds < 0.25 * nmax] = 0.35
zooms[inds > 0.7 * nmax] = 1.
zooms[zooms < 0.] = np.interp(inds[zooms < 0.], inds[zooms > 0.],
                              zooms[zooms > 0.])
"""
# zoom out then back in
zooms[inds < 0.25 * nmax] = 1.04
x0s[inds < 0.25 * nmax] = startx
y0s[inds < 0.25 * nmax] = starty
zooms[(inds > 0.5 * nmax) & (inds < 0.6 * nmax)] = 1.04
zooms[inds > 0.85 * nmax] = 1.04
x0s[inds > 0.85 * nmax] = endx
y0s[inds > 0.85 * nmax] = endy
zooms[zooms < 0.] = np.interp(inds[zooms < 0.], inds[zooms > 0.],
                              zooms[zooms > 0.])
x0s[~np.isfinite(x0s)] = np.interp(inds[~np.isfinite(x0s)], inds[np.isfinite(x0s)],
                              x0s[np.isfinite(x0s)])
y0s[~np.isfinite(y0s)] = np.interp(inds[~np.isfinite(y0s)], inds[np.isfinite(y0s)],
                              y0s[np.isfinite(y0s)])

# ===================================== #

# reference time for the Kepler data
#time0 = dt.datetime(2009, 1, 1, 12)
time0 = dt.datetime(2014, 12, 8, 12)

# the KIC number given to the solar system
kicsolar = -5

data = pd.read_csv(koilist)
kics = data['TIC ID'].values
pds = data['Period (days)'].values
it0s = data['Epoch (BJD)'].values
idists = data['Stellar Distance (pc)'].values
radius = data['Planet Radius (R_Earth)'].values
inc = data['Planet Insolation (Earth Flux)'].values
srad = data['Stellar Radius (R_Sun)'].values
stemp = data['Stellar Eff Temp (K)'].values
iteqs = data['Planet Equil Temp (K)'].values
tra = data['RA'].values
tdec = data['Dec'].values
slum = (srad**2) * ((stemp/5770)**4)
semi = np.sqrt((slum / inc))

ra = []
dec = []
for ii in np.arange(tra.size):
    ira = tra[ii]
    idec = tdec[ii]
    
    hh, mm, ss = ira.split(':')
    frac = int(hh) + int(mm)/60 + float(ss)/3600
    ra.append(frac * 360/24)
    
    hh, mm, ss = idec.split(':')
    frac = int(hh)
    if int(hh) < 0:
        frac -= int(mm)/60 + float(ss)/3600
    else:
        frac += int(mm)/60 + float(ss)/3600
    dec.append(frac)
ra = np.array(ra)
dec = np.array(dec)

# load in the data from the KOI list
#kics, pds, it0s, radius, iteqs, semi = np.genfromtxt(
#    koilist, unpack=True, usecols=(1, 5, 8, 20, 26, 23), delimiter=',')

# grab the KICs with known parameters
good = (np.isfinite(semi) & np.isfinite(pds) & (pds > 0.) &
        np.isfinite(radius) & np.isfinite(idists) & np.isfinite(inc) & np.isfinite(iteqs))

kics = kics[good]
pds = pds[good]
it0s = it0s[good]
semi = semi[good]
radius = radius[good]
idists = idists[good]
inc = inc[good]
iteqs = iteqs[good]

# if we've already decided where to put each system, load it up
if lcenfile is not None:
    multikics, xcens, ycens, maxsemis = np.loadtxt(lcenfile, unpack=True)
    nplan = len(multikics)
# otherwise figure out how to fit all the planets into a nice distribution
else:
    # we only want to plot multi-planet systems
    multikics, nct = np.unique(kics, return_counts=True)
    multikics = multikics[nct > 1]
    maxsemis = multikics * 0.
    maxdists = multikics * 0.
    maxdecs = multikics * 0.
    maxras = multikics * 0.
    nplan = len(multikics)

    # the maximum size needed for each system
    for ii in np.arange(len(multikics)):
        maxsemis[ii] = np.max(semi[np.where(kics == multikics[ii])[0]])
        maxdists[ii] = np.max(idists[np.where(kics == multikics[ii])[0]])
        maxras[ii] = np.max(ra[np.where(kics == multikics[ii])[0]])
        maxdecs[ii] = np.max(dec[np.where(kics == multikics[ii])[0]])

    inds = np.argsort(maxdists)
    # reorder to place them
    maxsemis = maxsemis[inds]
    multikics = multikics[inds]
    maxdists = maxdists[inds]
    maxras = maxras[inds]
    maxdecs = maxdecs[inds]
    
    
    icrs = SkyCoord(ra=maxras, dec=maxdecs, frame='icrs', unit='deg')
    ecliptic = icrs.transform_to(BarycentricTrueEcliptic)
    maxrasecl = ecliptic.lon.value * 1
    maxdecsecl = ecliptic.lat.value * 1
    
    # add in the solar system if desired
    if addsolar:
        nplan += 1
        # we know where we want the solar system to be placed, place it first
        if fixedpos:
            insind = 0
        # otherwise treat it as any other system
        # and place it at this point through the list
        else:
            insind = int(posinlist * len(maxsemis))
    
        maxsemis = np.insert(maxsemis, insind, 1.524)
        multikics = np.insert(multikics, insind, kicsolar)
        maxdists = np.insert(maxdists, insind, 0)
        maxrasecl = np.insert(maxrasecl, insind, 0)
        maxdecsecl = np.insert(maxdecsecl, insind, 0)
    
    
    phase = maxdecsecl * 1
    phase[maxrasecl > 180] = 180 - phase[maxrasecl > 180]
    
    xcens = np.array([])
    ycens = np.array([])
    # place all the planets without overlapping or violating aspect ratio
    for ii in np.arange(nplan):
        # reset the counters
        repeat = True
        phaseoff = 0
        # AU = parsecs * dscale
        dscale = 1./50
        # radius where a distance of 0 would go
        zerodist = 2.1
    
        # progress bar
        if (ii % 20) == 0:
            print('Placing {0} of {1} planets'.format(ii, nplan))
    
        # put the solar system at its fixed position if desired
        if multikics[ii] == kicsolar and fixedpos:
            xcens = np.concatenate((xcens, [ssx]))
            ycens = np.concatenate((ycens, [ssy]))
            repeat = False
        else:
            xcens = np.concatenate((xcens, [0.]))
            ycens = np.concatenate((ycens, [0.]))
    
        # repeat until we find an open location for this system
        while repeat:
            iphase = (phase[ii] + phaseoff) * np.pi/180
            xcens[ii] = np.cos(iphase) * (maxdists[ii] * dscale + zerodist)
            ycens[ii] = np.sin(iphase) * (maxdists[ii] * dscale + zerodist)
    
            # how far apart are all systems
            rdists = np.sqrt((xcens - xcens[ii]) ** 2. +
                            (ycens - ycens[ii]) ** 2.)
            rsum = maxsemis + maxsemis[ii]
    
            # systems that overlap
            bad = np.where(rdists < rsum[:ii + 1] + spacing)
    
            # either the systems overlap or we've placed a lot and
            # the aspect ratio isn't good enough so try again
            if len(bad[0]) == 1:
                repeat = False
                
            if phaseoff == 0:
                phaseoff = 5
            elif phaseoff > 0:
                phaseoff *= -1
            else:
                phaseoff *= -1
                phaseoff += 5
    
            if phaseoff > 170:
                raise Exception('bad')
        #print(phaseoff)

    # save this placement distribution if desired
    if scenfile is not None:
        np.savetxt(scenfile,
                   np.column_stack((multikics, xcens, ycens, maxsemis)),
                   fmt=['%d', '%f', '%f', '%f'])

plt.close('all')

# make a diagnostic plot showing the distribution of systems
fig = plt.figure()
plt.xlim((xcens - maxsemis).min(), (xcens + maxsemis).max())
plt.ylim((ycens - maxsemis).min(), (ycens + maxsemis).max())
plt.gca().set_aspect('equal', adjustable='box')
plt.xlabel('AU')
plt.ylabel('AU')

for ii in np.arange(nplan):
    c = plt.Circle((xcens[ii], ycens[ii]), maxsemis[ii], clip_on=False,
                   alpha=0.3)
    fig.gca().add_artist(c)

# all of the parameters we need for the plot
t0s = np.array([])
periods = np.array([])
semis = np.array([])
radii = np.array([])
teqs = np.array([])
dists = np.array([])
usedkics = np.array([])
fullxcens = np.array([])
fullycens = np.array([])
incs = np.array([])

for ii in np.arange(nplan):
    # known solar system parameters
    if addsolar and multikics[ii] == kicsolar:
        usedkics = np.concatenate((usedkics, np.ones(8) * kicsolar))
        # always start the outer solar system in the same places
        # for optimial visibility
        t0s = np.concatenate((t0s, [85., 192., 266., 180.,
                                    times[0] + 0.1 * 4332.8,
                                    times[0] - 22. / 360 * 10755.7,
                                    times[0] - 30687 * 145. / 360,
                                    times[0] - 60190 * 202. / 360]))
        periods = np.concatenate((periods, [87.97, 224.70, 365.26, 686.98,
                                            4332.8, 10755.7, 30687, 60190]))
        semis = np.concatenate((semis, [0.387, 0.723, 1.0, 1.524, 5.203,
                                        9.537, 19.19, 30.07]))
        radii = np.concatenate((radii, [0.383, 0.95, 1.0, 0.53, 10.86, 9.00,
                                        3.97, 3.86]))
        dists = np.concatenate((dists, np.ones(8)*0.01))
        fullxcens = np.concatenate((fullxcens, np.zeros(8) + xcens[ii]))
        fullycens = np.concatenate((fullycens, np.zeros(8) + ycens[ii]))
        incs = np.concatenate((incs, [6.68, 1.91, 1, 0.43, 0.037, 0.011,
                                      0.0027, 0.0011]))
        teqs = np.concatenate((teqs, [409, 299, 255, 206, 200,
                                      200, 200, 200]))
        continue

    fd = np.where(kics == multikics[ii])[0]
    # get the values for this system
    usedkics = np.concatenate((usedkics, kics[fd]))
    t0s = np.concatenate((t0s, it0s[fd]))
    periods = np.concatenate((periods, pds[fd]))
    semis = np.concatenate((semis, semi[fd]))
    radii = np.concatenate((radii, radius[fd]))
    incs = np.concatenate((incs, inc[fd]))
    teqs = np.concatenate((teqs, iteqs[fd]))
    dists = np.concatenate((dists, idists[fd]))
    fullxcens = np.concatenate((fullxcens, np.zeros(len(fd)) + xcens[ii]))
    fullycens = np.concatenate((fullycens, np.zeros(len(fd)) + ycens[ii]))
    

# sort by radius so that the large planets are on the bottom and
# don't cover smaller planets
rs = np.argsort(radii)[::-1]
usedkics = usedkics[rs]
t0s = t0s[rs]
periods = periods[rs]
semis = semis[rs]
radii = radii[rs]
incs = incs[rs]
teqs = teqs[rs]
dists = dists[rs]
fullxcens = fullxcens[rs]
fullycens = fullycens[rs]

if makemovie:
    plt.ioff()
else:
    plt.ion()

# create the figure at the right size (this assumes a default pix/inch of 100)
figsizes = {480: (8.54, 4.8), 720: (8.54, 4.8), 1080: (19.2, 10.8)}
fig = plt.figure(figsize=figsizes[reso])

# make the plot cover the entire figure with the right background colors
ax = fig.add_axes([0.0, 0, 1, 1])
ax.axis('off')
fig.patch.set_facecolor(bkcol)
ax.patch.set_facecolor(bkcol)

# don't count the orbits of the outer solar system in finding figure limits
ns = np.where(usedkics != kicsolar)[0]

# this section manually makes the aspect ratio equal
#  but completely fills the figure

# need this much buffer zone so that planets don't get cut off
buffsx = (fullxcens[ns].max() - fullxcens[ns].min()) * 0.007
buffsy = (fullycens[ns].max() - fullycens[ns].min()) * 0.007
# current limits of the figure
xmax = (fullxcens[ns] + semis[ns]).max() + buffsx
xmin = (fullxcens[ns] - semis[ns]).min() - buffsx
ymax = (fullycens[ns] + semis[ns]).max() + buffsy
ymin = (fullycens[ns] - semis[ns]).min() - buffsy

# figure aspect ratio
sr = 16. / 9.

# make the aspect ratio exactly right
if (xmax - xmin) / (ymax - ymin) > sr:
    plt.xlim(xmin, xmax)
    plt.ylim((ymax + ymin) / 2. - (xmax - xmin) / (2. * sr),
             (ymax + ymin) / 2. + (xmax - xmin) / (2. * sr))
else:
    plt.ylim(ymin, ymax)
    plt.xlim((xmax + xmin) / 2. - (ymax - ymin) * sr / 2.,
             (xmax + xmin) / 2. + (ymax - ymin) * sr / 2.)

lws = {480: 1, 720: 1, 1080: 2}
sslws = {480: 2, 720: 2, 1080: 4}
# plot the orbital circles for every planet
for ii in np.arange(len(t0s)):
    # solid, thinner lines for normal planets
    ls = 'solid'
    zo = 0
    lw = lws[reso]
    # dashed, thicker ones for the solar system
    if usedkics[ii] == kicsolar:
        ls = 'dashed'
        zo = -3
        lw = sslws[reso]

    c = plt.Circle((fullxcens[ii], fullycens[ii]), semis[ii], clip_on=False,
                   alpha=orbitalpha, fill=False,
                   color=orbitcol, zorder=zo, ls=ls, lw=lw)
    fig.gca().add_artist(c)

# set up the planet size scale
sscales = {480: 12., 720: 30., 1080: 50.}
sscale = sscales[reso]

rearth = 1.
rnep = 3.856
rjup = 10.864
rmerc = 0.383
# for the planet size legend
solarsys = np.array([rmerc, rearth, rnep, rjup])
pnames = ['Mercury', 'Earth', 'Neptune', 'Jupiter']
csolar = np.array([0.01, 0.01, 0.01, 0.01])

# keep the smallest planets visible and the largest from being too huge
solarsys = np.clip(solarsys, 0.8, 1.3 * rjup)
solarscale = sscale * solarsys

radii = np.clip(radii, 0.8, 1.3 * rjup)
pscale = sscale * radii

# color bar temperature tick values and labels
ticks = np.array([1, 25, 50, 75, 100])
labs = ['1', '25', '50', '75', '100']

# XXX: eq temp = (incident flux)**0.25 * 255

# blue and red colors for the color bar
RGB1 = np.array([1, 185, 252])
RGB2 = np.array([220, 55, 19])

# create the diverging map with a white in the center
mycmap = diverge_map(RGB1=RGB1, RGB2=RGB2, numColors=15)

# just plot the planets at time 0. for this default plot
phase = 2. * np.pi * (0. - t0s) / periods
tmp = plt.scatter(fullxcens + semis * np.cos(phase),
                  fullycens + semis * np.sin(phase), marker='o',
                  edgecolors='none', lw=0, s=pscale, c=incs, vmin=ticks.min(),
                  vmax=ticks.max(), zorder=3, cmap=mycmap, clip_on=False)

fsz1 = fszs1[reso]
fsz2 = fszs2[reso]
prop = fm.FontProperties(fname=fontfile)

# create the 'Solar System' text identification
if addsolar:
    loc = np.where(usedkics == kicsolar)[0][0]
    plt.text(fullxcens[loc], fullycens[loc], 'Solar\nSystem', zorder=-2,
             color=fontcol, family=fontfam, fontproperties=prop, fontsize=fsz1,
             horizontalalignment='center', verticalalignment='center')

# if we're putting in a translucent background behind the text
# to make it easier to read
if legback:
    box1starts = {480: (0., 0.445), 720: (0., 0.46), 1080: (0., 0.47)}
    box1widths = {480: 0.19, 720: 0.147, 1080: 0.172}
    box1heights = {480: 0.555, 720: 0.54, 1080: 0.53}

    box2starts = {480: (0.79, 0.8), 720: (0.83, 0.84), 1080: (0.86, 0.84)}
    box2widths = {480: 0.21, 720: 0.17, 1080: 0.14}
    box2heights = {480: 0.2, 720: 0.16, 1080: 0.16}

    # create the rectangles at the right heights and widths
    # based on the resolution
    c = plt.Rectangle(box1starts[reso], box1widths[reso], box1heights[reso],
                      alpha=legalpha, fc=legbackcol, ec='none', zorder=4,
                      transform=ax.transAxes)
    d = plt.Rectangle(box2starts[reso], box2widths[reso], box2heights[reso],
                      alpha=legalpha, fc=legbackcol, ec='none', zorder=4,
                      transform=ax.transAxes)
    ax.add_artist(c)
    ax.add_artist(d)

# appropriate spacing from the left edge for the color bar
#cbxoffs = {480: 0.09, 720: 0.07, 1080: 0.074}
cbxoffs = {480: 0.09, 720: 0.07, 1080: 0.074}
cbxoff = cbxoffs[reso]

# plot the solar system planet scale
ax.scatter(np.zeros(len(solarscale)) + cbxoff,
           1. - 0.13 + 0.03 * np.arange(len(solarscale)), s=solarscale,
           c=csolar, zorder=5, marker='o',
           edgecolors='none', lw=0, cmap=mycmap, vmin=ticks.min(),
           vmax=ticks.max(), clip_on=False, transform=ax.transAxes)

# put in the text labels for the solar system planet scale
for ii in np.arange(len(solarscale)):
    ax.text(cbxoff + 0.01, 1. - 0.14 + 0.03 * ii,
            pnames[ii], color=fontcol, family=fontfam,
            fontproperties=prop, fontsize=fsz1, zorder=5,
            transform=ax.transAxes)

# colorbar axis on the left centered with the planet scale
ax2 = fig.add_axes([cbxoff - 0.005, 0.54, 0.01, 0.3])
ax2.set_zorder(2)
cbar = plt.colorbar(tmp, cax=ax2, extend='both', ticks=ticks)
# remove the white/black outline around the color bar
cbar.outline.set_linewidth(0)
# allow two different tick scales
cbar.ax.minorticks_on()
# turn off tick lines and put the physical temperature scale on the left
cbar.ax.tick_params(axis='y', which='major', color=fontcol, width=2,
                    left=False, right=False, length=5, labelleft=True,
                    labelright=False, zorder=5)
# turn off tick lines and put the physical temperature approximations
# on the right
cbar.ax.tick_params(axis='y', which='minor', color=fontcol, width=2,
                    left=False, right=False, length=5, labelleft=False,
                    labelright=True, zorder=5)
# say where to put the physical temperature approximations and give them labels
cbar.ax.yaxis.set_ticks(np.array([5, 100, 200, 300, 400])/3.26156, minor=True)
cbar.ax.set_yticklabels(labs, color=fontcol, family=fontfam,
                        fontproperties=prop, fontsize=fsz1, zorder=5)
cbar.ax.set_yticklabels(['5', '100', '200', '300', '400'],
                        minor=True, color=fontcol, family=fontfam,
                        fontproperties=prop, fontsize=fsz1)
cbar.ax.yaxis.set_label('Parsec')
#cbar.ax.yaxis.set_label('Light year', minor=True)

clab = 'Insolation\n(Earths)'
# add the overall label at the bottom of the color bar
cbar.ax.set_xlabel(clab, color=fontcol, family=fontfam, fontproperties=prop,
                   size=fsz1, zorder=5, labelpad=fsz1*1.5)

# switch back to the main plot
plt.sca(ax)
plt.text(cbxoff + 0.01, 0.54 -0.03, 'Light-years', transform=ax.transAxes,color=fontcol,family=fontfam,
                        fontproperties=prop, fontsize=fsz1, zorder=5,horizontalalignment='left')
plt.text(cbxoff - 0.01, 0.54 - 0.03, 'Parsecs', transform=ax.transAxes,color=fontcol,family=fontfam,
                        fontproperties=prop, fontsize=fsz1, zorder=5,horizontalalignment='right')

# upper right credit and labels text offsets
txtxoffs = {480: 0.01, 720: 0.01, 1080: 0.01}
txtyoffs1 = {480: 0.10, 720: 0.08, 1080: 0.08}
txtyoffs2 = {480: 0.18, 720: 0.144, 1080: 0.144}

txtxoff = txtxoffs[reso]
txtyoff1 = txtyoffs1[reso]
txtyoff2 = txtyoffs2[reso]

# put in the credits in the top right
text = plt.text(1. - txtxoff, 1. - txtyoff1,
                time0.strftime('TESS Orrery I\n%d %b %Y'), color=fontcol,
                family=fontfam, fontproperties=prop,
                fontsize=fsz2, zorder=5, transform=ax.transAxes, horizontalalignment='right')
plt.text(1. - txtxoff, 1. - txtyoff2, 'By Ethan Kruse\n@ethan_kruse',
         color=fontcol, family=fontfam,
         fontproperties=prop, fontsize=fsz1,
         zorder=5, transform=ax.transAxes, horizontalalignment='right')

# the center of the figure
x0 = np.mean(plt.xlim())
y0 = np.mean(plt.ylim())

# width of the figure
xdiff = np.diff(plt.xlim()) / 2.
ydiff = np.diff(plt.ylim()) / 2.

# create the output directory if necessary
if makemovie and not os.path.exists(outdir):
    os.mkdir(outdir)

if makemovie:
    # get rid of all old png files so they don't get included in a new movie
    oldfiles = glob(os.path.join(outdir, '*png'))
    for delfile in oldfiles:
        os.remove(delfile)

    # go through all the times and make the planets move
    for ii, time in enumerate(times):
        # remove old planet locations and dates
        tmp.remove()
        text.remove()

        # re-zoom to appropriate level
        plt.xlim([x0s[ii] - xdiff * zooms[ii], x0s[ii] + xdiff * zooms[ii]])
        plt.ylim([y0s[ii] - ydiff * zooms[ii], y0s[ii] + ydiff * zooms[ii]])

        newt = time0 + dt.timedelta(time)
        # put in the credits in the top right
        text = plt.text(1. - txtxoff, 1. - txtyoff1,
                        newt.strftime('TESS Orrery I\n%d %b %Y'),
                        color=fontcol, family=fontfam,
                        fontproperties=prop,
                        fontsize=fsz2, zorder=5, transform=ax.transAxes, horizontalalignment='right')
        # put the planets in the correct location
        phase = 2. * np.pi * (time - t0s) / periods
        tmp = plt.scatter(fullxcens + semis * np.cos(phase),
                          fullycens + semis * np.sin(phase),
                          marker='o', edgecolors='none', lw=0, s=pscale, c=incs,
                          vmin=ticks.min(), vmax=ticks.max(),
                          zorder=3, cmap=mycmap, clip_on=False)

        fig.savefig(os.path.join(outdir, 'fig{0:04d}.png'.format(ii)),
                    facecolor=fig.get_facecolor(), edgecolor='none')
        if not (ii % 10):
            print('{0} of {1} frames'.format(ii, len(times)))








