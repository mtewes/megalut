"""
Configuration for the GREAT3 scripts.
"""

import megalutgreat3 as mg3

loggerformat='\033[1;31m%(levelname)s\033[1;0m: %(name)s(%(funcName)s): \033[1;21m%(message)s\033[1;0m'


great3 = mg3.great3.GREAT3Run(
	experiment = "control",
	obstype = "ground",
	sheartype = "constant",
	datadir = "/vol/fohlen11/fohlen11_1/mtewes/GREAT3",
	truthdir = "/vol/fohlen11/fohlen11_1/mtewes/GREAT3/truth", # Only needed for final analysis plots
	workdir = "/vol/fohlen11/fohlen11_1/mtewes/2017_MegaLUT_GREAT3/cgc_v1",
	
	#subfields = [0,1,2],
	subfields = [99],	# CGC best PSF subfields: [99, 156, 42],  worst : [2, 191, 166]

	#subfields = range(0, 200),

	#subfields = range(0, 50),
	#subfields = range(50, 100),
	#subfields = range(100, 150),
	#subfields = range(150, 200),

	ncpu = 1,
	skipdone = False
	)

