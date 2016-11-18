import megalut
import config
import measfcts
import glob
import os
import numpy as np
import astropy

import megalut.plot
from megalut.tools.feature import Feature
import matplotlib.pyplot as plt

import logging
logger = logging.getLogger(__name__)





cat = megalut.tools.io.readpickle("/vol/fohlen11/fohlen11_1/mtewes/backgals-megalut/sim/Nico2/precat.pkl")


s = megalut.tools.table.Selector("LowShear", [("in", "tru_s1", -0.05, 0.05), ("in", "tru_s2", -0.05, 0.05)])
cat = s.select(cat)

print megalut.tools.table.info(cat)

megalut.tools.table.addstats(cat, "pre_s1_adamom")
megalut.tools.table.addstats(cat, "pre_s2_adamom")
megalut.tools.table.addstats(cat, "pre_s1_fourier")
megalut.tools.table.addstats(cat, "pre_s2_fourier")

megalut.tools.table.addstats(cat, "snr")

print megalut.tools.table.info(cat)


rea = "All"

adamom_flux = Feature("adamom_flux", rea=rea)
adamom_sigma = Feature("adamom_sigma", rea=rea)
adamom_rho4 = Feature("adamom_rho4", 1.3, 3.0, rea=rea)
adamom_g1 = Feature("adamom_g1", -0.7, 0.7, rea=rea)
adamom_g2 = Feature("adamom_g2", -0.7, 0.7, rea=rea)
snr = Feature("snr", rea=rea)
adamom_x = Feature("adamom_x", rea=rea)
adamom_y = Feature("adamom_y", rea=rea)

tru_s1 = Feature("tru_s1", rea=rea)
tru_s2 = Feature("tru_s2", rea=rea)

tru_g1 = Feature("tru_g1", rea=rea)
tru_g2 = Feature("tru_g2", rea=rea)
tru_rad = Feature("tru_rad", rea=rea)
tru_sersicn = Feature("tru_sersicn", rea=rea)
tru_flux = Feature("tru_flux", rea=rea)

skymad = Feature("skymad", rea=rea)
skystd = Feature("skystd", rea=rea)
skymed = Feature("skymed", rea=rea)
skymean = Feature("skymean", rea=rea)


pre_s1_adamom = Feature("pre_s1_adamom", rea=rea)
pre_s2_adamom = Feature("pre_s2_adamom", rea=rea)
pre_s1_fourier = Feature("pre_s1_fourier", rea=rea)
pre_s2_fourier = Feature("pre_s2_fourier", rea=rea)

pre_s1_mean = Feature("pre_s1_adamom_mean")
pre_s2_mean = Feature("pre_s2_adamom_mean")
snr_mean = Feature("snr_mean")


#simcat["aperphot_sbr1"] = simcat["aperphot_sb2"] / simcat["aperphot_sb5"]
#obscat["aperphot_sbr1"] = obscat["aperphot_sb2"] / obscat["aperphot_sb5"]
#simcat["aperphot_sbr2"] = simcat["aperphot_sb3"] / simcat["aperphot_sb8"]
#obscat["aperphot_sbr2"] = obscat["aperphot_sb3"] / obscat["aperphot_sb8"]
#aperphot_sbr1 = Feature("aperphot_sbr1", rea=rea)
#aperphot_sbr2 = Feature("aperphot_sbr2", rea=rea)

cat["adamom_log_flux"] = np.log10(cat["adamom_flux"])
adamom_log_flux = Feature("adamom_log_flux", rea=rea)


fig = plt.figure(figsize=(16, 10))
#fig = plt.figure(figsize=(8, 8))

"""
ax = fig.add_subplot(2, 3, 1)
megalut.plot.bin.res(ax, cat, tru_s1, pre_s1_adamom, featc=adamom_sigma, nbins=10, ncbins=3, ebarmode="bias", showidline=True, metrics=True, equalcount=True)

ax = fig.add_subplot(2, 3, 4)
megalut.plot.bin.res(ax, cat, tru_s2, pre_s2_adamom, featc=adamom_sigma, nbins=10, ncbins=3, ebarmode="bias", showidline=True, metrics=True, equalcount=True)

ax = fig.add_subplot(2, 3, 2)
megalut.plot.bin.res(ax, cat, tru_s1, pre_s1_adamom, featc=snr, nbins=10, ncbins=3, ebarmode="bias", showidline=True, metrics=True, equalcount=True)

ax = fig.add_subplot(2, 3, 5)
megalut.plot.bin.res(ax, cat, tru_s2, pre_s2_adamom, featc=snr, nbins=10, ncbins=3, ebarmode="bias", showidline=True, metrics=True, equalcount=True)
"""

ax = fig.add_subplot(2, 3, 1)
megalut.plot.scatter.scatter(ax, cat, tru_s1, pre_s1_mean, featc=snr_mean, showidline=True, metrics=True)

ax = fig.add_subplot(2, 3, 4)
megalut.plot.scatter.scatter(ax, cat, tru_s2, pre_s2_mean, featc=snr_mean, showidline=True, metrics=True)

ax = fig.add_subplot(2, 3, 2)
megalut.plot.scatter.scatter(ax, cat, tru_s1, pre_s1_mean, featc=tru_sersicn, showidline=True)

ax = fig.add_subplot(2, 3, 5)
megalut.plot.scatter.scatter(ax, cat, tru_s2, pre_s2_mean, featc=tru_sersicn, showidline=True)


ax = fig.add_subplot(2, 3, 3)
megalut.plot.scatter.scatter(ax, cat, tru_s1, pre_s1_mean, featc=tru_rad, showidline=True)

ax = fig.add_subplot(2, 3, 6)
megalut.plot.scatter.scatter(ax, cat, tru_s2, pre_s2_mean, featc=tru_rad, showidline=True)


"""
ax = fig.add_subplot(2, 3, 2)
megalut.plot.scatter.scatter(ax, obscat, adamom_g1, mom_e13, showidline=True)

ax = fig.add_subplot(2, 3, 3)
megalut.plot.scatter.scatter(ax, obscat, adamom_sigma, fourier_adamom_sigma, adamom_rho4)


ax = fig.add_subplot(2, 3, 4)
megalut.plot.scatter.scatter(ax, obscat, adamom_g1, mom_e15, showidline=True)

ax = fig.add_subplot(2, 3, 5)
megalut.plot.scatter.scatter(ax, obscat, adamom_g1, mom_e18, showidline=True)

ax = fig.add_subplot(2, 3, 6)
megalut.plot.scatter.scatter(ax, obscat, adamom_g1, mom_e110, showidline=True)
"""

plt.tight_layout()

#if filepath:
#	plt.savefig(filepath)
#else:

plt.show()
#plt.close(fig) # Helps releasing memory when calling in large loops.
