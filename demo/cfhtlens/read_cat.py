import megalut
import megalut.cfhtlens
import megalut.meas

import logging
logging.basicConfig(level=logging.INFO)

import numpy as np


catfile = "/vol/fohlen11/fohlen11_1/hendrik/data/CFHTLenS/release_cats/W1m0m0_izrgu_release_mask.cat"
incat = megalut.cfhtlens.utils.readcat(catfile)

megalut.cfhtlens.utils.removejunk(incat)

megalut.utils.writepickle(incat, "incat.pkl")
incat.write("incat.fits")

exit()


"""
incat = megalut.utils.readpickle("incat.pkl")
incat = incat[:10000]

imgfilepath = "/vol/braid1/vol1/thomas/SHEARCOLLAB/Bonn/W1m0m0/i/coadd_V2.2A/W1m0m0_i.V2.2A.swarp.cut.fits"

img = megalut.meas.galsim_adamom.loadimg(imgfilepath)
meascat = megalut.meas.galsim_adamom.measure(img, incat, stampsize=50, xname="Xpos", yname="Ypos")


megalut.utils.writepickle(meascat, "meascat.pkl")
"""

# Select stars
incat = megalut.utils.readpickle("incat.pkl")
print len(incat)

selector = np.logical_and(incat['weight'] < 0.1, incat['fitclass'] == 1, incat['CLASS_STAR'] == 1)
incat = incat[selector]

print len(incat)


incat = incat[:100]

imgfilepath = "/vol/braid1/vol1/thomas/SHEARCOLLAB/Bonn/W1m0m0/i/coadd_V2.2A/W1m0m0_i.V2.2A.swarp.cut.fits"
img = megalut.meas.galsim_adamom.loadimg(imgfilepath)

megalut.meas.galsim_adamom.pngstampgrid("test.png", img, incat, stampsize=50, xname="Xpos", yname="Ypos")

"""


meascat = megalut.utils.readpickle("meascat.pkl")

meascat.meta = {}
meascat.write("meascat.fits")

"""

"""
import matplotlib.pyplot as plt

#plt.hist(meascat["mes_adamom_flag"])
#plt.show()

resi_x = meascat["mes_adamom_x"] - meascat["Xpos"]
resi_y = meascat["mes_adamom_y"] - meascat["Ypos"]
flag = meascat["mes_adamom_flag"]
plt.scatter(resi_x, resi_y, c=flag, lw=0, s=30)
plt.xlabel("mes_adamom_x residual")
plt.ylabel("mes_adamom_y residual")
plt.show()
"""


