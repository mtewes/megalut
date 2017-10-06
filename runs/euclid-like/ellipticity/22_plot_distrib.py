import megalut.plot
import megalut.tools
import astropy
import config
import glob
import os
import matplotlib.pyplot as plt

import logging
logger = logging.getLogger(__name__)

from megalut.tools.feature import Feature

name_distrib = "euclid_train"
magfeat = "surface_brigthness"

cat = astropy.table.Table.read(os.path.join(config.dbdir, "{}.fits".format(name_distrib)))
print megalut.tools.table.info(cat)

s = megalut.tools.table.Selector("ok", [
    ("min", "surface_brigthness", 0.255),
    ]
    )

#cat = s.select(cat)



fig = plt.figure(figsize=(16, 10))

ax = fig.add_subplot(2, 3, 1)
megalut.plot.scatter.scatter(ax, cat, Feature(magfeat), Feature("flux"), sidehists=True)

ax = fig.add_subplot(2, 3, 2)
megalut.plot.scatter.scatter(ax, cat, Feature("g1"), Feature("g2"), sidehists=True)

ax = fig.add_subplot(2, 3, 3)
megalut.plot.scatter.scatter(ax, cat, Feature(magfeat), Feature("sersicn"), sidehists=True)

ax = fig.add_subplot(2, 3, 4)
megalut.plot.scatter.scatter(ax, cat, Feature(magfeat), Feature("rad"), sidehists=True)

ax = fig.add_subplot(2, 3, 5)
megalut.plot.scatter.scatter(ax, cat, Feature("snr_calc"), Feature("rad"), sidehists=True)

ax = fig.add_subplot(2, 3, 6)
megalut.plot.scatter.scatter(ax, cat, Feature("snr_calc"), Feature("mag"), Feature("surface_brigthness"), sidehists=False)

plt.tight_layout()

#if filepath:
#    plt.savefig(filepath)
#else:

plt.show()