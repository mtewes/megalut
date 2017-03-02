import matplotlib
matplotlib.use("AGG")

import megalut.tools
import megalut.learn
import megalut

import config
import numpy as np
import os


import logging
logging.basicConfig(format=config.loggerformat, level=logging.DEBUG)
logger = logging.getLogger(__name__)


spname = "G3CGCSersics_statshear"


for subfield in config.great3.subfields:

	logger.info("Working on subfield {}".format(subfield))

	catpath = config.great3.path("simmeas", "%03i" % subfield, spname, "groupmeascat_cases.pkl")
	cat = megalut.tools.io.readpickle(catpath)
	#print megalut.tools.table.info(cat)
	
	conflist = [
		("mlconfig/ada4g1.cfg", config.great3.path("ml", "%03i" % subfield, "ada4g1_sum55")),
		("mlconfig/ada4g2.cfg", config.great3.path("ml", "%03i" % subfield, "ada4g2_sum55"))
	]
	
	
	predcat = megalut.learn.tenbilacrun.predict(cat, conflist)

	predcatpath = config.great3.path("simmeas", "%03i" % subfield, spname, "groupmeascat_cases_pred.pkl")
	megalut.tools.io.writepickle(predcat, predcatpath)
	
	
