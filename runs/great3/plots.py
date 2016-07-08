import numpy as np
import matplotlib.pyplot as plt

import megalut
import megalut.plot

import os

import logging
logger = logging.getLogger(__name__)



def compute_snr(cat):
	cat["snr"] = cat["sewpy_FLUX_AUTO"] / cat["sewpy_FLUXERR_AUTO"]


def measfrac_adamom(cat):
	"""
	Measurement success fraction
	"""
	return float(np.sum(cat["adamom_flag"] == 0)) / float(len(cat))


def simobscompa(run, simparams):
	"""
	In feature space
	"""
			
	flux = megalut.tools.feature.Feature("adamom_flux", 0.1, 150, "Some flux")
	tru_flux = megalut.tools.feature.Feature("tru_flux", 0.1, 150, "True flux")
	
	
	sigma = megalut.tools.feature.Feature("adamom_sigma", 0.1, 11, "Some measured width")
	rho4 = megalut.tools.feature.Feature("adamom_rho4", 1.6, 2.8, "Some measured concentration")
	g1 = megalut.tools.feature.Feature("adamom_g1", -0.6, 0.6, "HSM g1")
	g2 = megalut.tools.feature.Feature("adamom_g2", -0.6, 0.6, "HSM g2")
	skymad = megalut.tools.feature.Feature("adamom_skymad", 0.01, 0.07)
	skystd = megalut.tools.feature.Feature("adamom_skystd", 0.01, 0.07)
	skymed = megalut.tools.feature.Feature("adamom_skymed", -0.05, 0.05)
	skymean = megalut.tools.feature.Feature("adamom_skymean", -0.05, 0.05)
	
	snr = megalut.tools.feature.Feature("snr", 0.1, 150, "SExtractor SNR")
	snr_narrow = megalut.tools.feature.Feature("snr", 0.1, 60, "SExtractor SNR")
	
	for subfield in run.subfields:
	
		simcat = megalut.tools.io.readpickle(run._get_path("simmeas", "%03i" % subfield, simparams.name, "rea0cat.pkl"))
		obscat = megalut.tools.io.readpickle(run._get_path("obs", "img_%i_meascat.pkl" % subfield))
		
		compute_snr(simcat)
		compute_snr(obscat)
	
		# measurement sucess fraction:
		txt = "Subfield %i, simparams '%s', measfrac_adamom_sim = %.3f, measfrac_adamom_obs = %.3f"\
			 % (subfield, simparams.name, measfrac_adamom(simcat), measfrac_adamom(obscat))
	
		fig = plt.figure(figsize=(18, 12))
		fig.subplots_adjust(bottom=0.07, top=0.92, left=0.05, right=0.95, wspace=0.2)

		fig.text(0.05, 0.95, txt, {"fontsize":15})
		
		ax1 = fig.add_subplot(231)
		megalut.plot.scatter.simobs(ax1, simcat, obscat, snr, sigma, legend=True)

		ax2 = fig.add_subplot(232)
		megalut.plot.scatter.simobs(ax2, simcat, obscat, sigma, rho4)

		ax3 = fig.add_subplot(233)
		megalut.plot.scatter.simobs(ax3, simcat, obscat, g1, g2)
		
		
		ax4 = fig.add_subplot(234)
		megalut.plot.scatter.simobs(ax4, simcat, obscat, snr_narrow, rho4)
	
		
		ax5 = fig.add_subplot(235)
		megalut.plot.scatter.simobs(ax5, simcat, obscat, skymad, skystd)
	
		#ax5 = fig.add_subplot(235)
		#megalut.plot.scatter.simobs(ax5, simcat, obscat, skymed, skymean)
		
		#ax6 = fig.add_subplot(236)
		#megalut.plot.scatter.scatter(ax6, simcat, tru_flux, flux_, sidehists=True, text="Simulations")
		
		#plt.tight_layout()
		plt.show()	
		plt.close(fig) # Helps releasing memory when calling in large loops.





def presimcheck(run, trainname, simname, outdir=None, show=True):
	"""
	Visualize predictions obtained on simulations
	"""
		
	
	
	for subfield in run.subfields:

		# We load the self-predicted (on rea0) catalog:
	
		traindir = run._get_path("ml", "%03i" % subfield, trainname, simname)
		cat = megalut.tools.io.readpickle(os.path.join(traindir, "pretraincat_rea0.pkl"))
		
		cat["snr"] = cat["sewpy_FLUX_AUTO_mean"] / cat["sewpy_FLUXERR_AUTO_mean"]
		snr = megalut.tools.feature.Feature("snr", 0.1, 150, "SExtractor SNR")
		snr_narrow = megalut.tools.feature.Feature("snr", 10, 40, "SExtractor SNR")
		
		ngroupstats = cat.meta["ngroupstats"]
		logger.info("Preparing predsimcheck of %i galaxies, ngroupstats (nrea) is %i" % (len(cat), ngroupstats))
		
		cat["measfrac"] = cat["adamom_flux_n"] / float(ngroupstats)
		measfrac = megalut.tools.feature.Feature("measfrac", 0.0, 1.0, "Measurement success fraction")
		
		
		# Not currently used in the plots:
		"""
		cat["g1prerr"] = cat["pre_g1"] - cat["tru_g1"]
		cat["g2prerr"] = cat["pre_g2"] - cat["tru_g2"]
		cat["gprerr"] = np.hypot(cat["g1prerr"], cat["g2prerr"])
		gprerr = megalut.tools.feature.Feature("gprerr", 0.0, 0.2, "$|g|$ error")
	
		cat["radprerr"] = cat["pre_rad"] - cat["tru_rad"]
		radprerr = megalut.tools.feature.Feature("radprerr", -0.5, 0.5, "pre_rad - tru_rad")
		radbias = megalut.tools.feature.Feature("radprerr", -0.5, 0.5, "rad bias")
		radrmsd = megalut.tools.feature.Feature("radprerr", 0.0, 0.5, "rad RMSD")
	
	
		cat["sersicnprerr"] = cat["pre_sersicn"] - cat["tru_sersicn"]
		sersicnprerr = megalut.tools.feature.Feature("sersicnprerr", -1.5, 1.5, "pre_sersicn - tru_sersicn")
		sersicnbias = megalut.tools.feature.Feature("sersicnprerr", -0.5, 0.5, "sersicn bias")
		sersicnrmsd = megalut.tools.feature.Feature("sersicnprerr", 0.0, 1.0, "sersicn RMSD")
		"""
		
		tru_g1 = megalut.tools.feature.Feature("tru_g1", -1.0, 1.0)
		tru_g2 = megalut.tools.feature.Feature("tru_g2", -1.0, 1.0)
		tru_flux = megalut.tools.feature.Feature("tru_flux", 0.0, 200.0)
		tru_rad = megalut.tools.feature.Feature("tru_rad", 0, 13)
		tru_sersicn = megalut.tools.feature.Feature("tru_sersicn", 0.3, 4.5)
	
		pre_g1 = megalut.tools.feature.Feature("pre_g1", -1.0, 1.0)
		pre_g2 = megalut.tools.feature.Feature("pre_g2", -1.0, 1.0)
		pre_flux = megalut.tools.feature.Feature("pre_flux", 0.0, 200.0)
		pre_rad = megalut.tools.feature.Feature("pre_rad", 0, 13)
		pre_sersicn = megalut.tools.feature.Feature("pre_sersicn", 0.3, 4.5)
		
		
		txt = "Subfield %i, sim '%s', train '%s', " % (subfield, simname, trainname)
	
		fig = plt.figure(figsize=(22, 13))
		fig.subplots_adjust(bottom=0.07, top=0.92, left=0.05, right=0.95, wspace=0.4)

		fig.text(0.05, 0.95, txt, {"fontsize":15})
		
		ax = fig.add_subplot(3, 4, 1)	
		megalut.plot.scatter.scatter(ax, cat, tru_g1, pre_g1, showidline=True, idlinekwargs={"color":"red", "lw":2}, sidehists=True, ms=3)
		
		ax = fig.add_subplot(3, 4, 2)	
		megalut.plot.scatter.scatter(ax, cat, tru_g2, pre_g2, showidline=True, idlinekwargs={"color":"red", "lw":2}, sidehists=True, ms=3)
		
		ax = fig.add_subplot(3, 4, 3)	
		megalut.plot.scatter.scatter(ax, cat, tru_rad, pre_rad, showidline=True, idlinekwargs={"color":"red", "lw":2}, sidehists=True, ms=3)

		ax = fig.add_subplot(3, 4, 4)	
		megalut.plot.scatter.scatter(ax, cat, tru_sersicn, pre_sersicn, showidline=True, idlinekwargs={"color":"red", "lw":2}, sidehists=True, ms=3)

		ax = fig.add_subplot(3, 4, 5)	
		megalut.plot.scatter.scatter(ax, cat, tru_g1, pre_g1, snr_narrow, s=5, metrics=True)
		
		ax = fig.add_subplot(3, 4, 6)	
		megalut.plot.scatter.scatter(ax, cat, tru_g2, pre_g2, snr_narrow, s=5, metrics=True)
		
		ax = fig.add_subplot(3, 4, 7)	
		megalut.plot.scatter.scatter(ax, cat, tru_rad, pre_rad, snr_narrow, s=5, metrics=True)

		ax = fig.add_subplot(3, 4, 8)	
		megalut.plot.scatter.scatter(ax, cat, tru_sersicn, pre_sersicn, snr_narrow, s=5, metrics=True)


		if not outdir is None:
			fig.savefig(os.path.join(outdir,'selfpredict_%03i.pdf' % subfield),transparent=True)

		if show:
			plt.show()	
		plt.close(fig) # Helps releasing memory when calling in large loops.



def show_selfpredict_shear(great3, trainname, simname, outdir=None, show=True):
	"""
	Visualize predictions obtained on simulations
	"""

	for subfield in great3.subfields:
	
		traindir = great3.get_path("ml", "%03i" % subfield, trainname, simname)
		cat = megalut.tools.io.readpickle(os.path.join(traindir, "predtraincat.pkl"))
		
		
		cat["snr"] = cat["sewpy_FLUX_AUTO"] / cat["sewpy_FLUXERR_AUTO"]
		snr = megalut.tools.feature.Feature("snr", 0.1, 150, "SExtractor SNR")
		snr_narrow = megalut.tools.feature.Feature("snr", 10, 60, "SExtractor SNR", rea='all')
		
		
		tru_s1 = megalut.tools.feature.Feature("tru_s1", -0.05, 0.05, rea='all')
		tru_s2 = megalut.tools.feature.Feature("tru_s2", -0.05, 0.05, rea='all')
	
		pre_s1 = megalut.tools.feature.Feature("pre_s1", -0.05, 0.05, rea='all')
		pre_s2 = megalut.tools.feature.Feature("pre_s2", -0.05, 0.05, rea='all')
		
		txt = "Subfield %i, sim '%s', train '%s', " % (subfield, simname, trainname)
	
		fig = plt.figure(figsize=(11, 11))
		fig.subplots_adjust(bottom=0.07, top=0.92, left=0.05, right=0.95, wspace=0.4)

		fig.text(0.05, 0.95, txt, {"fontsize":15})
		
		ax = fig.add_subplot(2, 2, 1)	
		megalut.plot.scatter.scatter(ax, cat, tru_s1, pre_s1, showidline=True, idlinekwargs={"color":"red", "lw":2}, sidehists=True, ms=3)
		
		ax = fig.add_subplot(2, 2, 2)	
		megalut.plot.scatter.scatter(ax, cat, tru_s2, pre_s2, showidline=True, idlinekwargs={"color":"red", "lw":2}, sidehists=True, ms=3)

		ax = fig.add_subplot(2, 2, 3)	
		megalut.plot.scatter.scatter(ax, cat, tru_s1, pre_s1, snr_narrow, s=5, metrics=True)
		
		ax = fig.add_subplot(2, 2, 4)	
		megalut.plot.scatter.scatter(ax, cat, tru_s2, pre_s2, snr_narrow, s=5, metrics=True)

		if not outdir is None:
			fig.savefig(os.path.join(outdir,'selfpredict_shear_%03i.pdf' % subfield),transparent=True)

		if show:
			plt.show()	
		plt.close(fig) # Helps releasing memory when calling in large loops.

def show_selfpredict(subfields, mldir, trainname, simname, xfeat, yfeat, outdir=None, show=True):
	"""
	Visualize predictions obtained on simulations
	"""
	nplt = len(xfeat)
	if nplt != len(yfeat):
		raise ValueError("xfeat and yfeat do not have the same dimension!")
	for subfield in subfields:
	
		traindir = os.path.join(mldir, "%03i" % subfield, trainname, simname)
		cat = megalut.tools.io.readpickle(os.path.join(traindir, "predtraincat.pkl"))
		
		cat["snr"] = cat["sewpy_FLUX_AUTO"] / cat["sewpy_FLUXERR_AUTO"]
		snr = megalut.tools.feature.Feature("snr", 0.1, 150, "SExtractor SNR")
		snr_narrow = megalut.tools.feature.Feature("snr", 10, 60, "SExtractor SNR", rea='all')
		
		txt = "Subfield %i, sim '%s', train '%s', " % (subfield, simname, trainname)
	
		fig = plt.figure(figsize=(11/2.*nplt, 11))
		fig.subplots_adjust(bottom=0.07, top=0.92, left=0.05, right=0.95, wspace=0.4)

		fig.text(0.05, 0.95, txt, {"fontsize":15})
		
		for jj in range(nplt):
			ax = fig.add_subplot(2, nplt, jj+1)	
			megalut.plot.scatter.scatter(ax, cat, xfeat[jj], yfeat[jj], showidline=True, idlinekwargs={"color":"red", "lw":2}, sidehists=True, ms=3)

			ax = fig.add_subplot(2, nplt, nplt+jj+1)	
			megalut.plot.scatter.scatter(ax, cat, xfeat[jj], yfeat[jj], snr_narrow, s=5, metrics=True)
		
		if not outdir is None:
			fig.savefig(os.path.join(outdir,'selfpredict_shear_%03i.pdf' % subfield),transparent=True)

		if show:
			plt.show()	
		plt.close(fig) # Helps releasing memory when calling in large loops.





