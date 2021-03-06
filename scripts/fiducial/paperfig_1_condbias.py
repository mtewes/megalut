import config
import measfcts
import os
import numpy as np
import matplotlib.ticker as ticker

import momentsml.plot
from momentsml.tools.feature import Feature
import matplotlib.pyplot as plt

import logging
logger = logging.getLogger(__name__)


#momentsml.plot.figures.set_fancy(14)
from matplotlib import rc
rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
## for Palatino and other serif fonts use:
#rc('font',**{'family':'serif','serif':['Palatino']})
rc('text', usetex=True)


###############################

select = True # will be set to False if useweights is True

useweights = False # <--- to be used with a "VP" like structure in place of "VO".
regressmethod = 1 # Only matters if useweights.
# For a VP-like dataset, it only makes sense to use regressmethod1 here, as we want the weights to act over the different true galaxies within each bin.
# Regressmethod 2 would kill the effect of weights, only use it if cases contain different gals.

###############################

if useweights is False:
	valname = config.valname
else:
	valname = config.wvalname
	select = False

valcat = os.path.join(config.valdir, valname + ".pkl")
cat = momentsml.tools.io.readpickle(valcat)
momentsml.tools.table.addstats(cat, "snr") # We need this even without select, to show the snr_mean axis

if select:
	
	s = momentsml.tools.table.Selector("snr_mean > 10", [
		("min", "snr_mean", 10.0),
	])
	cat = s.select(cat)


if select:
	snr_mean = Feature("snr_mean", 5, 75, nicename=r"$\langle$S/N$\rangle$")
else:
	snr_mean = Feature("snr_mean", 0, 75, nicename=r"$\langle$S/N$\rangle$")
tru_flux = Feature("tru_flux", nicename=r"$F$ [counts]")
tru_rad = Feature("tru_rad", 1.8, 8.5, nicename=r"Half-light radius $R$ [pix]")
tru_radwrtPSF = Feature("tru_radwrtPSF", 0.5, 3.5, nicename=r"$R/R_\mathrm{PSF}$")
tru_sersicn = Feature("tru_sersicn", 0.5, 4.5, nicename=r"S\'ersic index $n$")
tru_g = Feature("tru_g", -0.02, 0.62, nicename=r"Galaxy ellipticity $|\varepsilon|$")


cat["tru_radwrtPSF"] = cat["tru_rad"] / (cat["tru_psf_sigma"] * 1.1774)

tru_s1 = Feature("tru_s1")
tru_s2 = Feature("tru_s2")
pre_s1 = Feature("pre_s1", rea="all")
pre_s2 = Feature("pre_s2", rea="all")


if useweights:
	pre_s1w = Feature("pre_s1w", rea="all")
	pre_s2w = Feature("pre_s2w", rea="all")
else:
	pre_s1w = None
	pre_s2w = None
	
	

def make_plot(ax, featbin, showlegend=False, sersic=False):
	ax.axhline(0.0, color='gray', lw=0.5)	
	if sersic: # We don't let the code make bins, but provide binlims to separate the discrete cases:
		binlims = np.linspace(0.9, 4.1, 11)
		showbins = False
	else:
		showbins = True
		binlims = None
	# The first component
	momentsml.plot.mcbin.mcbin(ax, cat, tru_s1, pre_s1, featbin, featprew=pre_s1w, comp=1, binlims=binlims, showbins=showbins, regressmethod=regressmethod)
	# For the second component, we do not overplot bins again, but we might show the legend
	momentsml.plot.mcbin.mcbin(ax, cat, tru_s2, pre_s2, featbin, featprew=pre_s2w, comp=2, binlims=binlims, showbins=False, showlegend=showlegend, regressmethod=regressmethod)
	momentsml.plot.mcbin.make_symlog(ax, featbin)
	ax.set_xlabel(featbin.nicename)


fig = plt.figure(figsize=(8, 6))
plt.subplots_adjust(
	left  = 0.12,  # the left side of the subplots of the figure
	right = 0.99,    # the right side of the subplots of the figure
	bottom = 0.1,   # the bottom of the subplots of the figure
	top = 0.95,      # the top of the subplots of the figure
	wspace = 0.08,   # the amount of width reserved for blank space between subplots,
	                # expressed as a fraction of the average axis width
	hspace = 0.25,   # the amount of height reserved for white space between subplots,
					# expressed as a fraction of the average axis heightbottom=0.1, right=0.8, top=0.9)
	)

ax = plt.subplot(2, 2, 1)
make_plot(ax, snr_mean, showlegend=True)
ax.set_ylabel("Metric value")

ax = plt.subplot(2, 2, 2)
make_plot(ax, tru_rad)
ax.set_yticklabels([])

ax = plt.subplot(2, 2, 3)
make_plot(ax, tru_sersicn, sersic=True)
ax.set_ylabel("Metric value")

ax = plt.subplot(2, 2, 4)
make_plot(ax, tru_g)
ax.set_yticklabels([])


momentsml.plot.figures.savefig(os.path.join(config.valdir, valname + "_cond_biases"), fig, fancy=True)
#plt.show()











"""
for comp in ["1","2"]:

	# If no weights are in the catalog (or not yet), we add ones
	if not "pre_s{}w".format(comp) in cat.colnames:
		
		# First putting all weights to 1.0:
		cat["pre_s{}w".format(comp)] = np.ones(cat["adamom_g1"].shape)
		
	cat["pre_s{}w_norm".format(comp)] = cat["pre_s{}w".format(comp)] / np.max(cat["pre_s{}w".format(comp)])

	momentsml.tools.table.addrmsd(cat, "pre_s{}".format(comp), "tru_s{}".format(comp))
	momentsml.tools.table.addstats(cat, "pre_s{}".format(comp), "pre_s{}w".format(comp))
	cat["pre_s{}_wbias".format(comp)] = cat["pre_s{}_wmean".format(comp)] - cat["tru_s{}".format(comp)]
"""

"""
#for comp in ["1", "2"]:
#	pass
	#cat["pre_g{}".format(comp)] = cat["pre_g{}_adamom".format(comp)]
	#momentsml.tools.table.addstats(cat, "pre_g{}".format(comp))
	#momentsml.tools.table.addrmsd(cat, "pre_g{}".format(comp), "tru_s{}".format(comp))
"""


"""
s = momentsml.tools.table.Selector("ok", [
	("min", "snr_mean", 10),
	#("in", "tru_rad", 0, 10.),
	#("max", "adamom_frac", 0.005)
	]
)
cat = s.select(cat)
"""

"""
#--------------------------------------------------------------------------------------------------
fig = plt.figure(figsize=(8.5, 3))
plt.subplots_adjust(wspace=0.0)
plt.subplots_adjust(bottom=0.2)
plt.subplots_adjust(right=0.92)
plt.subplots_adjust(left=0.11)

#------------------------------------------------------------
maxy = 0.015#cat["pre_g{}_bias".format(component)].max() * 1.06
miny = -0.015#cat["pre_g{}_bias".format(component)].min() * 1.02

maxsnr = cat["snr_mean"].max()
minsnr = cat["snr_mean"].min()

minshear = -0.12
maxshear = 0.12
#------------------------------------------------------------

ax = fig.add_subplot(1, 2, 1)
ax.fill_between([-1, 1], -2e-3, 2e-3, alpha=0.2, facecolor='darkgrey')
ax.axhline(0, ls='--', color='k')
momentsml.plot.scatter.scatter(ax, cat, main_feat,  Feature("pre_s{}_bias".format(component)), \
	featc=Feature("snr_mean"), marker='.', cmap="plasma", hidecbar=True, vmin=minsnr, vmax=maxsnr)
ax.set_xlabel(r"True shear $g_{%s}$" % component)
ax.set_ylabel(r"Shear bias")


metrics = momentsml.tools.metrics.metrics(cat, main_feat,  Feature("pre_s{}_bias".format(component)), pre_is_res=True)

ax.annotate(r"$\mathrm{RMSD=%.5f}$" % metrics["rmsd"], xy=(0.0, 1.0), xycoords='axes fraction', xytext=(8, -4), textcoords='offset points', ha='left', va='top')
ax.annotate(r"$10^3\mu=%.1f \pm %.1f;\,10^3c=%.1f \pm %.1f$" % (metrics["m"]*1000.0, metrics["merr"]*1000.0, \
	metrics["c"]*1000.0, metrics["cerr"]*1000.0), xy=(0.0, 1.0), xycoords='axes fraction', xytext=(8, -19), textcoords='offset points', ha='left', va='top')
#ax.annotate(r"$10^3c=%.1f \pm %.1f$" % (metrics["c"]*1000.0, metrics["cerr"]*1000.0), xy=(0.0, 1.0), xycoords='axes fraction', xytext=(8, -35), textcoords='offset points', ha='left', va='top')
ax.set_ylim([miny, maxy])
ax.set_xlim([minshear, maxshear])

#------------------------------------------------------------

ax = fig.add_subplot(1, 2, 2)
ax.fill_between([-1, 1], -2e-3, 2e-3, alpha=0.2, facecolor='darkgrey')
ax.axhline(0, ls='--', color='k')
momentsml.plot.scatter.scatter(ax, cat, main_feat,  Feature("pre_s{}_bias".format(component2)), 
	featc=Feature("snr_mean", nicename=r"S/N"), marker='.', cmap="plasma", vmin=minsnr, vmax=maxsnr)
ax.set_xlabel(r"True shear $g_{%s}$" % component2)
metrics = momentsml.tools.metrics.metrics(cat, main_feat,  Feature("pre_s{}_bias".format(component2)), pre_is_res=True)

ax.annotate(r"$\mathrm{RMSD=%.5f}$" % metrics["rmsd"], xy=(0.0, 1.0), xycoords='axes fraction', xytext=(8, -4), textcoords='offset points', ha='left', va='top')
ax.annotate(r"$10^3\mu=%.1f \pm %.1f;\,10^3c=%.1f \pm %.1f$" % (metrics["m"]*1000.0, metrics["merr"]*1000.0, \
	metrics["c"]*1000.0, metrics["cerr"]*1000.0), xy=(0.0, 1.0), xycoords='axes fraction', xytext=(8, -19), textcoords='offset points', ha='left', va='top')
ax.set_ylim([miny, maxy])
ax.set_xlim([minshear, maxshear])
ax.set_yticklabels([])
ax.set_ylabel("")

momentsml.plot.figures.savefig(os.path.join(config.valdir, valname + "_plot_6a"), fig, fancy=True, pdf_transparence=True)
#------------------------------------------------------------
"""

"""




#------------------------------------------------------------
isubfig = 1
ncol = 2
nlines = int(np.ceil(len(param_feats) / (ncol*1.)))
fig = plt.figure(figsize=(4.1*ncol, 3 * nlines))
plt.subplots_adjust(wspace=0.07)
plt.subplots_adjust(hspace=0.27)
plt.subplots_adjust(right=0.98)
plt.subplots_adjust(top=0.98)
import matplotlib.transforms as mtransforms
no_legend = True

assert "res" not in cat.colnames
lintresh = 2e-3

coln = 0
for iplot, featc in enumerate(param_feats):
	
	ax = fig.add_subplot(nlines, ncol, isubfig + iplot)
	
	trans = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
	ax.fill_between([0, 1], -lintresh, lintresh, alpha=0.2, facecolor='darkgrey', transform=trans)
	ax.axhline(0, ls='--', color='k')
	ax.set_ylabel(r"Shear bias")
	
	for icomp, comp in enumerate(["1", "2"]):
		
		main_pred = "s{}".format(comp)
		maincol = "tru_{}".format(main_pred)
		main_feat = Feature(maincol)
	
		cat["res"] = cat["pre_s{}_bias".format(comp)]
		
		#xbinrange = momentsml.plot.utils.getrange(cat, featc)
		#binsumma = momentsml.plot.utils.summabin(cat[maincol], cat["res"], xbinrange=xbinrange, nbins=nbins)
		
		cbinrange = momentsml.plot.utils.getrange(cat, featc)
		
		if featc.colname is "tru_sersicn":
			cbinlims = np.linspace(1-0.1, 4+0.1, 11)	
		else:
			cbinlims = np.array([np.percentile(cat[featc.colname], q) for q in np.linspace(0.0, 100.0, ncbins+1)])
	
		#print cbinlims
		
		cbinlows = cbinlims[0:-1]
		cbinhighs = cbinlims[1:]
		#cbincenters = 0.5 * (cbinlows + cbinhighs)
		#assert len(cbincenters) == ncbins
		
		#print cbincenters
		
		
		#offsetscale = 0.5*((xbinrange[1] - xbinrange[0])/float(nbins))/float(ncbins)
		
		cbinpointcenters = []
		ms = []
		merrs = []
		cs = []
		cerrs = []
		for i in range(ncbins):
			
			#offset = (i - float(ncbins)/2) * offsetscale
			
			# We build the subset of data that is in this color bin:
			selcbin = momentsml.tools.table.Selector(featc.colname, [("in", featc.colname, cbinlows[i], cbinhighs[i])])
			cbindata = selcbin.select(cat)
			
			#if len(cbindata) == 0:
			#	continue
			# WTF dangerous!
			
			cbinfrac = float(len(cbindata)) / float(len(cat))
			
			# And we perform the linear regression
			md = momentsml.tools.metrics.metrics(cbindata,
				main_feat, # Redefining those to get rid of any rea settings that don't apply to cbindata
				momentsml.tools.feature.Feature("res"),
				pre_is_res=True)
			
			ms.append(md["m"])
			merrs.append(md["merr"])
			cs.append(md["c"])
			cerrs.append(md["cerr"])
			
			cbinpointcenters.append(np.mean(cbindata[featc.colname]))
			
			#ax.plot(np.array(xbinrange), md["m"]*np.array(xbinrange)+md["c"], color=color, ls="-")
			
			
			
			# And now bin this in x:
			#cbinsumma = momentsml.plot.utils.summabin(cbindata[maincol], cbindata["res"], xbinrange=xbinrange, nbins=nbins, equalcount=False)
			
		if icomp == 0:
			markm = '*'
			markc = '^'
			color = 'k'
		elif icomp == 1:
			markm = 's'
			markc = 'v'
			color = 'r'
		labelc = r"$c_{%s}$" % (comp)
		labelm = r"$\mu_{%s}$" % (comp)
			
		ax.errorbar(cbinpointcenters, ms, yerr=merrs, color=color, marker=markm, label=labelm)
		ax.errorbar(cbinpointcenters, cs, yerr=cerrs, color=color, marker=markc, ls=':', label=labelc)


	# Outside of the "comp" loop, we add bins
	for x in cbinlims:
		ax.axvline(x, color='gray', lw=0.5)

	#if (isubfig + iplot)/2+1 == nlines:
	#	ax.set_xlabel(r"$\mathrm{True\ shear}$")
	#else:
	#	ax.set_xticklabels([])
	
	
	ax.set_yscale('symlog', linthreshy=lintresh)
	ax.set_xlabel(featc.nicename)
	if featc.colname == "tru_g" or (iplot == len(param_feats) + 1 and no_legend):
		plt.legend(loc="best", handletextpad=0.07,fontsize="small", framealpha=0.5, columnspacing=0.1, ncol=2)
		no_legend = False
	
	ax.set_ylim([-1e-1, 1e-1])
	
	ticks = np.concatenate([np.arange(-lintresh, lintresh, 1e-3)])#, np.arange(lintresh, 1e-2, 9)])
	s = ax.yaxis._scale
	ax.yaxis.set_minor_locator(ticker.SymmetricalLogLocator(s, subs=[1., 2.,3.,4.,5.,6.,7.,8.,9.,-2.,-3.,-4.,-5.,-6.,-7.,-8.,-9.]))
	ticks = np.concatenate([ticks, ax.yaxis.get_minor_locator().tick_values(-.1, .1)])
	ax.yaxis.set_minor_locator(ticker.FixedLocator(ticks))
	
	if featc.low is not None and featc.high is not None:
		ax.set_xlim([featc.low, featc.high])
		#ax.locator_params(axis='x', nticks=2)
		#tick_spacing = (featc.high - featc.low) / 5.
		#ax.xaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))
		#ax.xaxis.set_major_formatter(ticker.FormatStrFormatter(r'$%0.3f$'))
		#ax.xaxis.set_major_formatter(ticker.FormatStrFormatter(r'$%0.3f$'))
		
	if coln > 0:
		ax.set_ylabel("")
		ax.set_yticklabels([])

	coln += 1
	if coln == ncol: coln = 0


momentsml.plot.figures.savefig(os.path.join(config.valdir, valname + "_condbias_b"), fig, fancy=True, pdf_transparence=True)
plt.show()
"""
