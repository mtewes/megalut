"""
Helper functions to create scatter-like plots from an astropy table and Feature objects.
"""

import matplotlib.pyplot as plt
import matplotlib.cm
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.ticker import MaxNLocator
from matplotlib.ticker import AutoMinorLocator
from matplotlib.lines import Line2D



import logging
logger = logging.getLogger(__name__)



def scatter(ax, cat, featx, featy, featc=None, cmap="jet", title=None, showdiag=False, sidehists=False, sidehistkwargs=None, **kwargs):
	"""
	A simple scatter plot of cat, between two Features. A third Feature, featc, gives an optional colorbar.

	:param ax: a matplotlib.axes.Axes object
	:param cat: an astropy table 
	:param featx: a Feature object telling me what to draw on my x axis
	:param featy: idem for y
	:param featc: a Feature to use for the colorbar
	:param cmap: the color bar to use
	:param title: the title to place on top of the axis.
		The reason why we do not leave this to the user is that the placement changes when sidehists is True.
	:param showdiag: draws an "identity" line
	:param sidehists: adds projection histograms on the top and the left (probably not compatible with the colorbar)
	:param sidehistkwargs: a dict of keywordarguments to be passed to these histograms
	
	Any further kwargs are either passed to plot() (if no featc is given) or to scatter()
	Some commonly used kwargs for plot() are
	
	* **marker**: default is ".", you can switch to single pixel (",") or anything else...
	* **ms**: marker size in points
	* **color**: e.g. "red"
	* **label**: for the legend

	Some commonly used kwargs for scatter() are:
	* **s**: marker size
	* **label**: for the legend

	"""

	xdata = cat[featx.colname]
	ydata = cat[featy.colname]
	
	if featc is not None: # We will use scatter(), to have a colorbar
		
		logger.debug("Preparing scatter plot of %i points with colorbar" % (len(cat))) # Log it as this might be slow
		cdata = cat[featc.colname]
		
		# We prepare to use scatter, with a colorbar
		cmap = matplotlib.cm.get_cmap(cmap)
		mykwargs = {"marker":"o", "lw":0, "s":15, "cmap":cmap, "vmin":featc.low, "vmax":featc.high}
		
		# We overwrite these mykwargs with any user-specified kwargs:
		mykwargs.update(kwargs)
		
		# And make the plot:
		stuff = ax.scatter(xdata, ydata, c=cdata, **mykwargs)
		divider = make_axes_locatable(ax)
		cax = divider.append_axes("right", "5%", pad="3%")
		cax = plt.colorbar(stuff, cax)
		cax.set_label(featc.nicename)
	
			
	else: # We will use plot()
	
		logger.debug("Preparing plain plot of %i points without colorbar" % (len(cat)))
		mykwargs = {"marker":".", "ms":5, "color":"black", "ls":"None", "mec":"None", "alpha":0.3}
	
		# We overwrite these mykwargs with any user-specified kwargs:
		mykwargs.update(kwargs)

		# Plain plot:
		ax.plot(xdata, ydata, **mykwargs)

	
	# We want minor ticks:
	ax.xaxis.set_minor_locator(AutoMinorLocator(5))
	ax.yaxis.set_minor_locator(AutoMinorLocator(5))
	
	if sidehists:
	
		# Same as for kwargs: we first define some defaults, and then update these defaults:
		mysidehistkwargs = {"histtype":"stepfilled", "bins":100, "ec":"none", "color":"gray"}
		if sidehistkwargs is None:
			sidehistkwargs = {}
		mysidehistkwargs.update(sidehistkwargs)
		
		divider = make_axes_locatable(ax)
		axhistx = divider.append_axes("top", 1.0, pad=0.1, sharex=ax)
		axhisty = divider.append_axes("right", 1.0, pad=0.1, sharey=ax)
		
		axhistx.hist(xdata, **mysidehistkwargs)
		axhisty.hist(ydata, orientation='horizontal', **mysidehistkwargs)
		
		# Hiding the ticklabels
		for tl in axhistx.get_xticklabels():
			tl.set_visible(False)
		for tl in axhisty.get_yticklabels():
			tl.set_visible(False)
		
		# Reducing the number of major ticks...
		#axhistx.yaxis.set_major_locator(MaxNLocator(nbins = 2))
		#axhisty.xaxis.set_major_locator(MaxNLocator(nbins = 2))
		# Or hide them completely
		axhistx.yaxis.set_ticks([]) # or set_ticklabels([])
		axhisty.xaxis.set_ticks([])
	
		if title:
			axhistx.set_title(title)
		
	else:
		if title:
			ax.set_title(title)
	
	
	ax.set_xlim(featx.low, featx.high)
	ax.set_ylim(featy.low, featy.high)
	ax.set_xlabel(featx.nicename)
	ax.set_ylabel(featy.nicename)

	# Once the limits are set, we can draw the diagonal:
	if showdiag:
		ax.plot(ax.get_xlim(), ax.get_ylim(), ls="--", color="gray", lw=1)





def simobs(ax, simcat, obscat, featx, featy, **kwargs):
	"""
	A scatter plot overplotting simulations and observations in two different colors.
	
	:param ax: a matplotlib Axes object
	:param simcat: simulation catalog
	:param obscat: observation catalog
	:param featx: a Feature object telling me what to draw on my x axis
	:param featy: idem for y
	
	All further kwargs are directly passed to scatter().
	
	"""
	
	print "To be developed, in a dedicated module..."
	
	scatter(ax, simcat, featx, featy, color="red", label="Simulations", **kwargs)
	scatter(ax, obscat, featx, featy, color="green", label="Observations", **kwargs)
	ax.legend()


# The old one can probably be deleted:
#
#def scatter(ax, cat, featx, featy, **kwargs):
#	"""
#	Simple 2D scatter plot of one feature against another, for a single catalog.
#	
#	:param ax: a matplotlib.axes.Axes object
#	:param cat: an astropy table 
#	:param featx: a Feature object telling me what to draw on my x axis
#	:param featy: idem for y
#	
#	Any further kwargs are passed to plot().
#	Some commonly used kwargs:
#	
#	* **marker**: default is ".", you can switch to single pixel (",") or anything else...
#	* **ms**: marker size in points
#	* **color**: e.g. "red"
#	* **label**: for the legend
#	
#	"""
#	
#	if cat.masked is True:
#		logger.warning("Input catalog is masked, some points might not be shown !")
#	
#	xdata = cat[featx.colname].data
#	ydata = cat[featy.colname].data
#	
#	assert len(xdata) == len(ydata)
#	logger.info("%i datapoints to plot on (%s, %s)" % (len(xdata), featx.colname, featy.colname))
#	
#	plotkwargs = {"marker":".", "ms":5, "color":"red", "ls":"None", "mec":"None"}
#	plotkwargs.update(kwargs)
#	
#	ax.plot(xdata, ydata, **plotkwargs)
#	# The rendering of plot is much faster than the rendering of scatter.
#	# So use plot if possible.
#	
#	ax.set_xlim(featx.low, featx.high)
#	ax.set_ylim(featy.low, featy.high)
#	ax.set_xlabel(featx.nicename)
#	ax.set_ylabel(featy.nicename)
#
#
