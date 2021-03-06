"""
Read in the PSF measurements, to find out what subfields have the best PSFs
"""


import momentsml
import momentsml.plot
import config
import numpy as np
import matplotlib.pyplot as plt
from momentsml.tools.feature import Feature

import logging
logging.basicConfig(format=config.loggerformat, level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Loading the run
great3 = config.load_run()


"""
# Read in the star measurements
cat = momentsml.tools.io.readpickle(great3.path("obs", "allstars_meascat.pkl"))

# Compute stats per subfield, by first restructuring the catalog
cat = momentsml.tools.table.groupreshape(cat, groupcolnames=["subfield"])

cat["psf_adamom_g"] = np.hypot(cat["psf_adamom_g1"], cat["psf_adamom_g2"])
momentsml.tools.table.addstats(cat, "psf_adamom_sigma")
momentsml.tools.table.addstats(cat, "psf_adamom_g")
#print cat
#print momentsml.tools.table.info(cat)

cat = momentsml.tools.io.writepickle(cat, great3.path("obs", "allstars_meascat_restruct.pkl"))
"""

cat = momentsml.tools.io.readpickle(great3.path("obs", "allstars_meascat_restruct.pkl"))


"""
psf_adamom_sigma_mean = Feature("psf_adamom_sigma_mean")
psf_adamom_g_mean = Feature("psf_adamom_g_mean")
subfield = Feature("subfield")

fig = plt.figure(figsize=(8, 8))

ax = fig.add_subplot(2, 2, 1)
momentsml.plot.scatter.scatter(ax, cat, psf_adamom_sigma_mean, psf_adamom_g_mean, alpha = 1)

plt.tight_layout()
plt.show()

"""

cat.sort('psf_adamom_sigma_mean')

print cat["subfield", "psf_adamom_sigma_mean"]






