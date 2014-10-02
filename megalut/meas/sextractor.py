"""
Yet another attempt to build a reusable and transparent SExtractor wrapper, this time

- using only astropy (no astroasciidata or pyfits)
- using logging
- using tempfile
- with support for easy use of ASSOC
- not only with MegaLUT in mind


Here is the minimal example::

 from sextractor import SExtractor
 se = SExtractor(params=["X_IMAGE", "Y_IMAGE"], config={"DETECT_MINAREA":10})
 cat = se.run("myimage.fits")
 print cat

As for every "wrapper", this module should allow us to use SExtractor as if it would all be 
native python. But at the same time we also want this wrapper to allow a more sophisticated use,
with existing SExtractor input files, or revealing the output files.

The philosophy is the following:

- If you do not specify a workdir, I'll write all my required internal files somewhere in /tmp,
  and you don't have to bother about this.
- "params" (a list) refers to the features that you want SExtractor to measure
  (e.g., settings you find in "default.param").
- "config" (a dict) refers to the settings (e.g., stuff you find in "default.sex").
- A SExtractor instance ("se" in the example above) can well be reused for different images
  that you want to analyse with the same params but a different config.
  Indeed you usually don't want to change params from image to image, but you might have to change
  the config (e.g., gain, seeing, ...).
- When repeatedly calling run(), we avoid writing the SExtractor input files over and over again.
  Instead, param is written only once, and config settings are passed as command line arguments to
  the SExtractor executable, superseding the default config, which we take (if not told otherwise)
  as the output of "sextractor -d".
  So to change config from image to image, simply edit se.config between calls of run().


Latest improvements:

- a log file is written for every run()
- filenames change according to FITS image file name where required
- but you can also pass an "imgname" argument to run, and this will be used instead.
- params and config files are written only once, as discussed
- appropriate warnings and behaviour when a workdir already exists, or when you rerun on the same file
- possibility to use existing param / config / conv / nnw files
- possibility to "nice" SExtractor
- run() returns either the catalog, or the filepath to the catalog


To do:

- finish ASSOC
- add a public way to get the filepaths to the output files
- implement _check_config()
- better detection of SExtractor failures
- implement raising Exceptions when SExtractor fails
- implement CHECK IMAGE
- give access to several conv and nnw settings (if needed)


Note that several SExtractor wrappers for python can be found online.
The code for this module mixes elements inspired by:

- previous MegaLUT, alipy, and cosmouline implementations
- pysex from Nicolas Cantale
- sextractor.py by Laurent Le Guillou (from the "forgotten" COSMOGRAIL pipeline)
- pysextractor by Nicolas Gruel


"""


import os
import shutil
import astropy
import subprocess
import tempfile
import re
from datetime import datetime

import logging
logger = logging.getLogger(__name__)


defaultparams = ["XWIN_IMAGE", "YWIN_IMAGE", "AWIN_IMAGE", "BWIN_IMAGE", "THETAWIN_IMAGE", "BACKGROUND", "FLUX_AUTO"]
defaultconfig = {}


class SExtractorError(Exception):
    pass


class SExtractor():
	"""
	Holds together all the settings to run SExtractor executable on one or several images.
	"""
	
	def __init__(self, workdir=None, sexpath="sex", params=None, config=None, configfilepath=None, nice=None):
		"""
		All arguments have default values and are optional.
		
		:param workdir: where I'll write my files. Specify this (e.g., "test") if you care about the output files.
			If None, I create a unique temporary directory myself, usually in /tmp.
			
		:param sexpath: path to the sextractor executable (e.g., "sex" or "sextractor", if in your PATH)
		:param params: the parameters you want SExtractor to measure (i.e., what you would write in the "default.param" file)
		:type params: list of strings
		:param config: config settings that will supersede the default config (e.g., what you would change in the "default.sex" file)
		:type config: dict
		:param configfilepath: specify this if you want me to use an existing SExtractor config file as "default" (instead of the sextractor -d one)
		:param nice: niceness with which I should run SExtractor
		
		To use an existing SExtractor param-, conv-, or nnw-file, simply specify these in the config dict, using the appropriate
		SExtractor keys (PARAMETERS_NAME, FILTER_NAME, ...)
		
		"""

		
		# We set up the trivial things:
		
		self.sexpath = sexpath
		self.configfilepath = configfilepath
		self.nice = nice
		
		# ... and the workdir
		
		if workdir is not None:
			self.workdir = workdir
			self.tmp = False
			if os.path.isdir(workdir):
				logger.warning("SExtractor workdir '%s' exists, be careful! I will (maybe silently) delete or overwrite stuff." % (workdir))	
			else:
				logger.info("Making new SExtractor workdir '%s'..." % (workdir))
				os.makedirs(workdir)
		else:
			self.workdir = tempfile.mkdtemp(prefix='sextractor_dot_py_workdir_')
			self.tmp = True
		
		self._clean_workdir()

		
		# ... and the params:
		
		if params == None:
			self.params = defaultparams
		else:
			self.params = params
		self._check_params()
			
		
		# ... and the config:
		
		if config == None:
			self.config = defaultconfig
		else:
			self.config = config
		
		self._set_instance_config() # Adds some fixed stuff to self.config
		self._check_config()
	
		
	
	def get_version(self):
		"""
		To find the SExtractor version, we call it without arguments and parse the stdout.
		
		:returns: a string (e.g. '2.4.4')
		"""
		p = subprocess.Popen([self.sexpath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = p.communicate()
		version_match = re.search("[Vv]ersion ([0-9\.])+", err)
		assert version_match is not False
		version = str(version_match.group()[8:])
		assert len(version) != 0
		return version
	
	
	def __str__(self):
		"""
		Trivial
		"""
		return "SExtractor in %s" % (self.workdir)
	
	
	def _check_params(self):
		"""
		Compares the params to a list of known params, and spits out a useful warning if
		something seems fishy.
		"""
		strange_param_helper = False
		for param in self.params:
			if param not in self.fullparamlist:
				logger.warning("Parameter '%s' seems strange and might be unknown to SExtractor" % (param))
				strange_param_helper = True
				
		if strange_param_helper:
			logger.warning("Known parameters are: %s" % (self.fullparamtxt))
			
	
	def _check_config(self):
		"""
		Not yet implemented
		"""
		pass

		
	def _set_instance_config(self):
		"""
		Sets config parameters that remain fixed for this instance.
		Called by __init__(). If needed, you could still mess with this config after __init__() has run.
		"""
		
		if "PARAMETERS_NAME" in self.config.keys():
			logger.info("OK, you specified your own PARAMETERS_NAME, I will use it.")
		else:
			self.config["PARAMETERS_NAME"] = self._get_params_filepath()
		
		if "FILTER_NAME" in self.config.keys():
			logger.info("You specified your own FILTER_NAME, I will use it.")
		else:
			self.config["FILTER_NAME"] = self._get_conv_filepath()
		
		
		if "CATALOG_NAME" in self.config.keys():
			logger.critical("You specified your own CATALOG_NAME, but I will *NOT* use it !")
			del self.config["CATALOG_NAME"]
		

	def _get_params_filepath(self):
		"""
		Stays the same for a given instance.
		"""
		return os.path.join(self.workdir, "params.txt")
		
	def _get_config_filepath(self):
		"""
		Idem, stays the same for a given instance.
		Might return the non-default configfilepath, if set.
		"""
		if self.configfilepath is None:
			return os.path.join(self.workdir, "config.txt")
		else:
			return self.configfilepath

	def _get_conv_filepath(self):
		"""
		Stays the same for a given instance.
		"""
		return os.path.join(self.workdir, "conv.txt")
	
	def _get_cat_filepath(self, imgname):
		"""
		This changes from image to image
		"""
		return os.path.join(self.workdir, imgname + ".cat.txt")
	
	def _get_assoc_filepath(self, imgname):
		"""
		Changes from image to image
		"""
		return os.path.join(self.workdir, imgname + ".assoc.txt")
	
	def _get_log_filepath(self, imgname):
		"""
		Changes from image to image
		"""
		return os.path.join(self.workdir, imgname + ".log.txt")
	
	
	def _write_params(self, force=False):
		"""
		Writes the parameters to the file, if needed.
		
		:param force: if True, I overwrite any existing file.
		"""
		if force or not os.path.exists(self._get_params_filepath()):
			f = open(self._get_params_filepath(), 'w')
			f.write("\n".join(self.params))
			f.write("\n")
			f.close()
			logger.debug("Wrote %s" % (self._get_params_filepath()))
		else:
			logger.debug("The params file already exists, I don't overwrite it.")


	def _write_default_config(self, force=False):
		
		"""
		Writes the *default* config file, if needed.
		I don't write this file if a specifig config file is set.
		
		:param force: if True, I overwrite any existing file.
		"""
		
		if self.configfilepath is not None:
			logger.debug("You use the existing config file %s, I don't have to write one." % (self._get_config_filepath()))
			return
		
		if force or not os.path.exists(self._get_config_filepath()):	
			p = subprocess.Popen([self.sexpath, "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out, err = p.communicate()
			if err != "":
				logger.warning("Ouch, SExtractor complains :")
				logger.warning(err)
			f = open(self._get_config_filepath(), 'w')
			f.write(out)
			f.close()
			logger.debug("Wrote %s" % (self._get_config_filepath()))
		else:
			logger.debug("Default config file already exists, I don't overwrite it.")



	def _write_default_conv(self):
		"""
		Writes the default convolution matrix, if needed.
		"""
		
		if not os.path.exists(self._get_conv_filepath()):	
			f = open(self._get_conv_filepath(), 'w')
			f.write("""CONV NORM
# 3x3 ``all-ground'' convolution mask with FWHM = 2 pixels.
1 2 1
2 4 2
1 2 1""")
			f.close()
			logger.debug("Wrote %s" % (self._get_conv_filepath()))
		else:
			logger.debug("Default conv file already exists, I don't overwrite it.")



	def _clean_workdir(self):
		"""
		Removes the config/param files related to this instance, to allow for a fresh restart.
		Files related to specific images are not removed.
		"""
		toremove = [self._get_config_filepath(), self._get_params_filepath(), self._get_conv_filepath()]
		for filepath in toremove:
			if os.path.exists(filepath):	
				logger.debug("Removing existing file %s..." % (filepath))
				os.remove(filepath)


	def write_assoc(cat, xname, yname):
		"""
		Writes a plain text file which can be used as sextractor input for the ASSOC identification.
		And "index" for each source is generated, it gets used to identify galaxies.
		"""
		pass
		
		

	def run(self, imgfilepath, imgname=None, assoccat=None, returncat=True, writelog=True):
		"""
		Runs SExtractor on a given image.
		
		:param imgfilepath: Path to the input FITS image I should run on
		:param assoccat:  input catalog (astropy table) which I should use for ASSOC
		:param returncat: by default I read the SExtractor output catalog and return it as an astropy table.
			If set to False, I return the path to the SExtractor catalog file instead.
		:param writelog: if True I save the sextractor command line input and output into a dedicated log file in the workdir.
		
		:returns: the astropy table of the output catalog, or, if returncat is False, the path to the output catalog file.
		
		Everything related to this particular image stays within this method, the SExtractor instance is not modified.
		"""

		starttime = datetime.now()
		
		logger.info("Preparing to run SExtractor on %s..." % imgfilepath)

		if imgname == None:
			imgname = os.path.splitext(os.path.basename(imgfilepath))[0]
		logger.debug("Using imgname %s..." % (imgname))		
		
		# We write the input files (if needed)
		self._write_default_config()
		self._write_params()
		self._write_default_conv()
		
		# We build the command line arguments
		popencmd = [self.sexpath, imgfilepath, "-c", self._get_config_filepath()]
		if self.nice != None: # We prepend the nice command
			popencmd[:0] = ["nice", "-n", str(self.nice)]
		
		
		# We add the current state of config
		for (key, value) in self.config.items():
			popencmd.append("-"+str(key))
			popencmd.append(str(value))
		
		# We specify the output catalog name (*** without modifying config ***)
		popencmd.extend(["-CATALOG_NAME", self._get_cat_filepath(imgname)])
		if os.path.exists(self._get_cat_filepath(imgname)):
			logger.warning("Output catalog %s already exists, I will overwrite it" % (self._get_cat_filepath(imgname)))
			
		
		# And we run
		logger.debug("Running with command %s..." % (popencmd))
		p = subprocess.Popen(popencmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = p.communicate()
		
		if writelog:
			logfile = open(self._get_log_filepath(imgname), "w")
			logfile.write("SExtractor was called with :\n")
			logfile.write(" ".join(popencmd))
			logfile.write("\n\n####### stdout #######\n")
			logfile.write(out)
			logfile.write("\n####### stderr #######\n")
			logfile.write(err)
			logfile.write("\n")
			logfile.close()
			
		logger.info("SExtractor stderr:")
		logger.info(err)
		
		if not "All done" in err:
			logger.critical("Ouch, check SExtractor log")
		
		endtime = datetime.now()
		logger.info("Done, it took %.2f seconds." % ((endtime - starttime).total_seconds()))

		if returncat:
			cat = astropy.table.Table.read(self._get_cat_filepath(imgname), format="ascii.sextractor")
			return cat
		else:
			return self._get_cat_filepath(imgname)
		
		
#	def destroy(self):
#		"""
#		Removes the complete working dir, careful with this.
#		"""
#		# No, this is way to dangerous, workdir could be "."
#		#shutil.rmtree(self.workdir)


	# Some class attributes:

	fullparamtxt = """
#NUMBER                 Running object number                                     
#EXT_NUMBER             FITS extension number                                     
#FLUX_ISO               Isophotal flux                                             [count]
#FLUXERR_ISO            RMS error for isophotal flux                               [count]
#MAG_ISO                Isophotal magnitude                                        [mag]
#MAGERR_ISO             RMS error for isophotal magnitude                          [mag]
#FLUX_ISOCOR            Corrected isophotal flux                                   [count]
#FLUXERR_ISOCOR         RMS error for corrected isophotal flux                     [count]
#MAG_ISOCOR             Corrected isophotal magnitude                              [mag]
#MAGERR_ISOCOR          RMS error for corrected isophotal magnitude                [mag]
#FLUX_APER              Flux vector within fixed circular aperture(s)              [count]
#FLUXERR_APER           RMS error vector for aperture flux(es)                     [count]
#MAG_APER               Fixed aperture magnitude vector                            [mag]
#MAGERR_APER            RMS error vector for fixed aperture mag.                   [mag]
#FLUX_AUTO              Flux within a Kron-like elliptical aperture                [count]
#FLUXERR_AUTO           RMS error for AUTO flux                                    [count]
#MAG_AUTO               Kron-like elliptical aperture magnitude                    [mag]
#MAGERR_AUTO            RMS error for AUTO magnitude                               [mag]
#FLUX_PETRO             Flux within a Petrosian-like elliptical aperture           [count]
#FLUXERR_PETRO          RMS error for PETROsian flux                               [count]
#MAG_PETRO              Petrosian-like elliptical aperture magnitude               [mag]
#MAGERR_PETRO           RMS error for PETROsian magnitude                          [mag]
#FLUX_BEST              Best of FLUX_AUTO and FLUX_ISOCOR                          [count]
#FLUXERR_BEST           RMS error for BEST flux                                    [count]
#MAG_BEST               Best of MAG_AUTO and MAG_ISOCOR                            [mag]
#MAGERR_BEST            RMS error for MAG_BEST                                     [mag]
#FLUX_WIN               Gaussian-weighted flux                                     [count]
#FLUXERR_WIN            RMS error for WIN flux                                     [count]
#MAG_WIN                Gaussian-weighted magnitude                                [mag]
#MAGERR_WIN             RMS error for MAG_WIN                                      [mag]
#FLUX_SOMFIT            Flux derived from SOM fit                                  [count]
#FLUXERR_SOMFIT         RMS error for SOMFIT flux                                  [count]
#MAG_SOMFIT             Magnitude derived from SOM fit                             [mag]
#MAGERR_SOMFIT          Magnitude error derived from SOM fit                       [mag]
#ERROR_SOMFIT           Reduced Chi-square error of the SOM fit                   
#VECTOR_SOMFIT          Position vector of the winning SOM node                   
#KRON_RADIUS            Kron apertures in units of A or B                         
#PETRO_RADIUS           Petrosian apertures in units of A or B                    
#BACKGROUND             Background at centroid position                            [count]
#THRESHOLD              Detection threshold above background                       [count]
#FLUX_MAX               Peak flux above background                                 [count]
#ISOAREA_IMAGE          Isophotal area above Analysis threshold                    [pixel**2]
#ISOAREAF_IMAGE         Isophotal area (filtered) above Detection threshold        [pixel**2]
#XMIN_IMAGE             Minimum x-coordinate among detected pixels                 [pixel]
#YMIN_IMAGE             Minimum y-coordinate among detected pixels                 [pixel]
#XMAX_IMAGE             Maximum x-coordinate among detected pixels                 [pixel]
#YMAX_IMAGE             Maximum y-coordinate among detected pixels                 [pixel]
#XPEAK_IMAGE            x-coordinate of the brightest pixel                        [pixel]
#YPEAK_IMAGE            y-coordinate of the brightest pixel                        [pixel]
#XPEAK_WORLD            World-x coordinate of the brightest pixel                  [deg]
#YPEAK_WORLD            World-y coordinate of the brightest pixel                  [deg]
#ALPHAPEAK_SKY          Right ascension of brightest pix (native)                  [deg]
#DELTAPEAK_SKY          Declination of brightest pix (native)                      [deg]
#ALPHAPEAK_J2000        Right ascension of brightest pix (J2000)                   [deg]
#DELTAPEAK_J2000        Declination of brightest pix (J2000)                       [deg]
#ALPHAPEAK_B1950        Right ascension of brightest pix (B1950)                   [deg]
#DELTAPEAK_B1950        Declination of brightest pix (B1950)                       [deg]
#X_IMAGE                Object position along x                                    [pixel]
#Y_IMAGE                Object position along y                                    [pixel]
#X_IMAGE_DBL            Object position along x (double precision)                 [pixel]
#Y_IMAGE_DBL            Object position along y (double precision)                 [pixel]
#X_WORLD                Barycenter position along world x axis                     [deg]
#Y_WORLD                Barycenter position along world y axis                     [deg]
#X_MAMA                 Barycenter position along MAMA x axis                      [m**(-6)]
#Y_MAMA                 Barycenter position along MAMA y axis                      [m**(-6)]
#ALPHA_SKY              Right ascension of barycenter (native)                     [deg]
#DELTA_SKY              Declination of barycenter (native)                         [deg]
#ALPHA_J2000            Right ascension of barycenter (J2000)                      [deg]
#DELTA_J2000            Declination of barycenter (J2000)                          [deg]
#ALPHA_B1950            Right ascension of barycenter (B1950)                      [deg]
#DELTA_B1950            Declination of barycenter (B1950)                          [deg]
#X2_IMAGE               Variance along x                                           [pixel**2]
#Y2_IMAGE               Variance along y                                           [pixel**2]
#XY_IMAGE               Covariance between x and y                                 [pixel**2]
#X2_WORLD               Variance along X-WORLD (alpha)                             [deg**2]
#Y2_WORLD               Variance along Y-WORLD (delta)                             [deg**2]
#XY_WORLD               Covariance between X-WORLD and Y-WORLD                     [deg**2]
#CXX_IMAGE              Cxx object ellipse parameter                               [pixel**(-2)]
#CYY_IMAGE              Cyy object ellipse parameter                               [pixel**(-2)]
#CXY_IMAGE              Cxy object ellipse parameter                               [pixel**(-2)]
#CXX_WORLD              Cxx object ellipse parameter (WORLD units)                 [deg**(-2)]
#CYY_WORLD              Cyy object ellipse parameter (WORLD units)                 [deg**(-2)]
#CXY_WORLD              Cxy object ellipse parameter (WORLD units)                 [deg**(-2)]
#A_IMAGE                Profile RMS along major axis                               [pixel]
#B_IMAGE                Profile RMS along minor axis                               [pixel]
#THETA_IMAGE            Position angle (CCW/x)                                     [deg]
#A_WORLD                Profile RMS along major axis (world units)                 [deg]
#B_WORLD                Profile RMS along minor axis (world units)                 [deg]
#THETA_WORLD            Position angle (CCW/world-x)                               [deg]
#THETA_SKY              Position angle (east of north) (native)                    [deg]
#THETA_J2000            Position angle (east of north) (J2000)                     [deg]
#THETA_B1950            Position angle (east of north) (B1950)                     [deg]
#ERRX2_IMAGE            Variance of position along x                               [pixel**2]
#ERRY2_IMAGE            Variance of position along y                               [pixel**2]
#ERRXY_IMAGE            Covariance of position between x and y                     [pixel**2]
#ERRX2_WORLD            Variance of position along X-WORLD (alpha)                 [deg**2]
#ERRY2_WORLD            Variance of position along Y-WORLD (delta)                 [deg**2]
#ERRXY_WORLD            Covariance of position X-WORLD/Y-WORLD                     [deg**2]
#ERRCXX_IMAGE           Cxx error ellipse parameter                                [pixel**(-2)]
#ERRCYY_IMAGE           Cyy error ellipse parameter                                [pixel**(-2)]
#ERRCXY_IMAGE           Cxy error ellipse parameter                                [pixel**(-2)]
#ERRCXX_WORLD           Cxx error ellipse parameter (WORLD units)                  [deg**(-2)]
#ERRCYY_WORLD           Cyy error ellipse parameter (WORLD units)                  [deg**(-2)]
#ERRCXY_WORLD           Cxy error ellipse parameter (WORLD units)                  [deg**(-2)]
#ERRA_IMAGE             RMS position error along major axis                        [pixel]
#ERRB_IMAGE             RMS position error along minor axis                        [pixel]
#ERRTHETA_IMAGE         Error ellipse position angle (CCW/x)                       [deg]
#ERRA_WORLD             World RMS position error along major axis                  [deg]
#ERRB_WORLD             World RMS position error along minor axis                  [deg]
#ERRTHETA_WORLD         Error ellipse pos. angle (CCW/world-x)                     [deg]
#ERRTHETA_SKY           Native error ellipse pos. angle (east of north)            [deg]
#ERRTHETA_J2000         J2000 error ellipse pos. angle (east of north)             [deg]
#ERRTHETA_B1950         B1950 error ellipse pos. angle (east of north)             [deg]
#XWIN_IMAGE             Windowed position estimate along x                         [pixel]
#YWIN_IMAGE             Windowed position estimate along y                         [pixel]
#XWIN_WORLD             Windowed position along world x axis                       [deg]
#YWIN_WORLD             Windowed position along world y axis                       [deg]
#ALPHAWIN_SKY           Windowed right ascension  (native)                         [deg]
#DELTAWIN_SKY           Windowed declination (native)                              [deg]
#ALPHAWIN_J2000         Windowed right ascension (J2000)                           [deg]
#DELTAWIN_J2000         windowed declination (J2000)                               [deg]
#ALPHAWIN_B1950         Windowed right ascension (B1950)                           [deg]
#DELTAWIN_B1950         Windowed declination (B1950)                               [deg]
#X2WIN_IMAGE            Windowed variance along x                                  [pixel**2]
#Y2WIN_IMAGE            Windowed variance along y                                  [pixel**2]
#XYWIN_IMAGE            Windowed covariance between x and y                        [pixel**2]
#X2WIN_WORLD            Windowed variance along X-WORLD (alpha)                    [deg**2]
#Y2WIN_WORLD            Windowed variance along Y-WORLD (delta)                    [deg**2]
#XYWIN_WORLD            Windowed covariance between X-WORLD and Y-WORLD            [deg**2]
#CXXWIN_IMAGE           Windowed Cxx object ellipse parameter                      [pixel**(-2)]
#CYYWIN_IMAGE           Windowed Cyy object ellipse parameter                      [pixel**(-2)]
#CXYWIN_IMAGE           Windowed Cxy object ellipse parameter                      [pixel**(-2)]
#CXXWIN_WORLD           Windowed Cxx object ellipse parameter (WORLD units)        [deg**(-2)]
#CYYWIN_WORLD           Windowed Cyy object ellipse parameter (WORLD units)        [deg**(-2)]
#CXYWIN_WORLD           Windowed Cxy object ellipse parameter (WORLD units)        [deg**(-2)]
#AWIN_IMAGE             Windowed profile RMS along major axis                      [pixel]
#BWIN_IMAGE             Windowed profile RMS along minor axis                      [pixel]
#THETAWIN_IMAGE         Windowed position angle (CCW/x)                            [deg]
#AWIN_WORLD             Windowed profile RMS along major axis (world units)        [deg]
#BWIN_WORLD             Windowed profile RMS along minor axis (world units)        [deg]
#THETAWIN_WORLD         Windowed position angle (CCW/world-x)                      [deg]
#THETAWIN_SKY           Windowed position angle (east of north) (native)           [deg]
#THETAWIN_J2000         Windowed position angle (east of north) (J2000)            [deg]
#THETAWIN_B1950         Windowed position angle (east of north) (B1950)            [deg]
#ERRX2WIN_IMAGE         Variance of windowed pos along x                           [pixel**2]
#ERRY2WIN_IMAGE         Variance of windowed pos along y                           [pixel**2]
#ERRXYWIN_IMAGE         Covariance of windowed pos between x and y                 [pixel**2]
#ERRX2WIN_WORLD         Variance of windowed pos along X-WORLD (alpha)             [deg**2]
#ERRY2WIN_WORLD         Variance of windowed pos along Y-WORLD (delta)             [deg**2]
#ERRXYWIN_WORLD         Covariance of windowed pos X-WORLD/Y-WORLD                 [deg**2]
#ERRCXXWIN_IMAGE        Cxx windowed error ellipse parameter                       [pixel**(-2)]
#ERRCYYWIN_IMAGE        Cyy windowed error ellipse parameter                       [pixel**(-2)]
#ERRCXYWIN_IMAGE        Cxy windowed error ellipse parameter                       [pixel**(-2)]
#ERRCXXWIN_WORLD        Cxx windowed error ellipse parameter (WORLD units)         [deg**(-2)]
#ERRCYYWIN_WORLD        Cyy windowed error ellipse parameter (WORLD units)         [deg**(-2)]
#ERRCXYWIN_WORLD        Cxy windowed error ellipse parameter (WORLD units)         [deg**(-2)]
#ERRAWIN_IMAGE          RMS windowed pos error along major axis                    [pixel]
#ERRBWIN_IMAGE          RMS windowed pos error along minor axis                    [pixel]
#ERRTHETAWIN_IMAGE      Windowed error ellipse pos angle (CCW/x)                   [deg]
#ERRAWIN_WORLD          World RMS windowed pos error along major axis              [deg]
#ERRBWIN_WORLD          World RMS windowed pos error along minor axis              [deg]
#ERRTHETAWIN_WORLD      Windowed error ellipse pos. angle (CCW/world-x)            [deg]
#ERRTHETAWIN_SKY        Native windowed error ellipse pos. angle (east of north)   [deg]
#ERRTHETAWIN_J2000      J2000 windowed error ellipse pos. angle (east of north)    [deg]
#ERRTHETAWIN_B1950      B1950 windowed error ellipse pos. angle (east of north)    [deg]
#NITER_WIN              Number of iterations for WIN centering                    
#MU_THRESHOLD           Detection threshold above background                       [mag * arcsec**(-2)]
#MU_MAX                 Peak surface brightness above background                   [mag * arcsec**(-2)]
#ISOAREA_WORLD          Isophotal area above Analysis threshold                    [deg**2]
#ISOAREAF_WORLD         Isophotal area (filtered) above Detection threshold        [deg**2]
#ISO0                   Isophotal area at level 0                                  [pixel**2]
#ISO1                   Isophotal area at level 1                                  [pixel**2]
#ISO2                   Isophotal area at level 2                                  [pixel**2]
#ISO3                   Isophotal area at level 3                                  [pixel**2]
#ISO4                   Isophotal area at level 4                                  [pixel**2]
#ISO5                   Isophotal area at level 5                                  [pixel**2]
#ISO6                   Isophotal area at level 6                                  [pixel**2]
#ISO7                   Isophotal area at level 7                                  [pixel**2]
#FLAGS                  Extraction flags                                          
#FLAGS_WEIGHT           Weighted extraction flags                                 
#FLAGS_WIN              Flags for WINdowed parameters                             
#IMAFLAGS_ISO           FLAG-image flags OR'ed over the iso. profile              
#NIMAFLAGS_ISO          Number of flagged pixels entering IMAFLAGS_ISO            
#FWHM_IMAGE             FWHM assuming a gaussian core                              [pixel]
#FWHM_WORLD             FWHM assuming a gaussian core                              [deg]
#ELONGATION             A_IMAGE/B_IMAGE                                           
#ELLIPTICITY            1 - B_IMAGE/A_IMAGE                                       
#POLAR_IMAGE            (A_IMAGE^2 - B_IMAGE^2)/(A_IMAGE^2 + B_IMAGE^2)           
#POLAR_WORLD            (A_WORLD^2 - B_WORLD^2)/(A_WORLD^2 + B_WORLD^2)           
#POLARWIN_IMAGE         (AWIN^2 - BWIN^2)/(AWIN^2 + BWIN^2)                       
#POLARWIN_WORLD         (AWIN^2 - BWIN^2)/(AWIN^2 + BWIN^2)                       
#CLASS_STAR             S/G classifier output                                     
#VIGNET                 Pixel data around detection                                [count]
#VIGNET_SHIFT           Pixel data around detection, corrected for shift           [count]
#VECTOR_ASSOC           ASSOCiated parameter vector                               
#NUMBER_ASSOC           Number of ASSOCiated IDs                                  
#THRESHOLDMAX           Maximum threshold possible for detection                   [count]
#FLUX_GROWTH            Cumulated growth-curve                                     [count]
#FLUX_GROWTHSTEP        Step for growth-curves                                     [pixel]
#MAG_GROWTH             Cumulated magnitude growth-curve                           [mag]
#MAG_GROWTHSTEP         Step for growth-curves                                     [pixel]
#FLUX_RADIUS            Fraction-of-light radii                                    [pixel]
#XPSF_IMAGE             X coordinate from PSF-fitting                              [pixel]
#YPSF_IMAGE             Y coordinate from PSF-fitting                              [pixel]
#XPSF_WORLD             PSF position along world x axis                            [deg]
#YPSF_WORLD             PSF position along world y axis                            [deg]
#ALPHAPSF_SKY           Right ascension of the fitted PSF (native)                 [deg]
#DELTAPSF_SKY           Declination of the fitted PSF (native)                     [deg]
#ALPHAPSF_J2000         Right ascension of the fitted PSF (J2000)                  [deg]
#DELTAPSF_J2000         Declination of the fitted PSF (J2000)                      [deg]
#ALPHAPSF_B1950         Right ascension of the fitted PSF (B1950)                  [deg]
#DELTAPSF_B1950         Declination of the fitted PSF (B1950)                      [deg]
#FLUX_PSF               Flux from PSF-fitting                                      [count]
#FLUXERR_PSF            RMS flux error for PSF-fitting                             [count]
#MAG_PSF                Magnitude from PSF-fitting                                 [mag]
#MAGERR_PSF             RMS magnitude error from PSF-fitting                       [mag]
#NITER_PSF              Number of iterations for PSF-fitting                      
#CHI2_PSF               Reduced chi2 from PSF-fitting                             
#ERRX2PSF_IMAGE         Variance of PSF position along x                           [pixel**2]
#ERRY2PSF_IMAGE         Variance of PSF position along y                           [pixel**2]
#ERRXYPSF_IMAGE         Covariance of PSF position between x and y                 [pixel**2]
#ERRX2PSF_WORLD         Variance of PSF position along X-WORLD (alpha)             [deg**2]
#ERRY2PSF_WORLD         Variance of PSF position along Y-WORLD (delta)             [deg**2]
#ERRXYPSF_WORLD         Covariance of PSF position X-WORLD/Y-WORLD                 [deg**2]
#ERRCXXPSF_IMAGE        Cxx PSF error ellipse parameter                            [pixel**(-2)]
#ERRCYYPSF_IMAGE        Cyy PSF error ellipse parameter                            [pixel**(-2)]
#ERRCXYPSF_IMAGE        Cxy PSF error ellipse parameter                            [pixel**(-2)]
#ERRCXXPSF_WORLD        Cxx PSF error ellipse parameter (WORLD units)              [deg**(-2)]
#ERRCYYPSF_WORLD        Cyy PSF error ellipse parameter (WORLD units)              [deg**(-2)]
#ERRCXYPSF_WORLD        Cxy PSF error ellipse parameter (WORLD units)              [deg**(-2)]
#ERRAPSF_IMAGE          PSF RMS position error along major axis                    [pixel]
#ERRBPSF_IMAGE          PSF RMS position error along minor axis                    [pixel]
#ERRTHTPSF_IMAGE        PSF error ellipse position angle (CCW/x)                   [deg]
#ERRAPSF_WORLD          World PSF RMS position error along major axis              [pixel]
#ERRBPSF_WORLD          World PSF RMS position error along minor axis              [pixel]
#ERRTHTPSF_WORLD        PSF error ellipse pos. angle (CCW/world-x)                 [deg]
#ERRTHTPSF_SKY          Native PSF error ellipse pos. angle (east of north)        [deg]
#ERRTHTPSF_J2000        J2000 PSF error ellipse pos. angle (east of north)         [deg]
#ERRTHTPSF_B1950        B1950 PSF error ellipse pos. angle (east of north)         [deg]
#VECTOR_MODEL           Model-fitting coefficients                                
#VECTOR_MODELERR        Model-fitting coefficient uncertainties                   
#CHI2_MODEL             Reduced Chi2 of the fit                                   
#FLAGS_MODEL            Model-fitting flags                                       
#NITER_MODEL            Number of iterations for model-fitting                    
#FLUX_MODEL             Flux from model-fitting                                    [count]
#FLUXERR_MODEL          RMS error on model-fitting flux                            [count]
#MAG_MODEL              Magnitude from model-fitting                               [mag]
#MAGERR_MODEL           RMS error on model-fitting magnitude                       [mag]
#XMODEL_IMAGE           X coordinate from model-fitting                            [pixel]
#YMODEL_IMAGE           Y coordinate from model-fitting                            [pixel]
#XMODEL_WORLD           Fitted position along world x axis                         [deg]
#YMODEL_WORLD           Fitted position along world y axis                         [deg]
#ALPHAMODEL_SKY         Fitted position along right ascension  (native)            [deg]
#DELTAMODEL_SKY         Fitted position along declination (native)                 [deg]
#ALPHAMODEL_J2000       Fitted position along right ascension (J2000)              [deg]
#DELTAMODEL_J2000       Fitted position along declination (J2000)                  [deg]
#ALPHAMODEL_B1950       Fitted position along right ascension (B1950)              [deg]
#DELTAMODEL_B1950       Fitted position along declination (B1950)                  [deg]
#ERRX2MODEL_IMAGE       Variance of fitted position along x                        [pixel**2]
#ERRY2MODEL_IMAGE       Variance of fitted position along y                        [pixel**2]
#ERRXYMODEL_IMAGE       Covariance of fitted position between x and y              [pixel**2]
#ERRX2MODEL_WORLD       Variance of fitted position along X-WORLD (alpha)          [deg**2]
#ERRY2MODEL_WORLD       Variance of fitted position along Y-WORLD (delta)          [deg**2]
#ERRXYMODEL_WORLD       Covariance of fitted position X-WORLD/Y-WORLD              [deg**2]
#ERRCXXMODEL_IMAGE      Cxx error ellipse parameter of fitted position             [pixel**(-2)]
#ERRCYYMODEL_IMAGE      Cyy error ellipse parameter of fitted position             [pixel**(-2)]
#ERRCXYMODEL_IMAGE      Cxy error ellipse parameter of fitted position             [pixel**(-2)]
#ERRCXXMODEL_WORLD      Cxx fitted error ellipse parameter (WORLD units)           [deg**(-2)]
#ERRCYYMODEL_WORLD      Cyy fitted error ellipse parameter (WORLD units)           [deg**(-2)]
#ERRCXYMODEL_WORLD      Cxy fitted error ellipse parameter (WORLD units)           [deg**(-2)]
#ERRAMODEL_IMAGE        RMS error of fitted position along major axis              [pixel]
#ERRBMODEL_IMAGE        RMS error of fitted position along minor axis              [pixel]
#ERRTHETAMODEL_IMAGE    Error ellipse pos.angle of fitted position (CCW/x)         [deg]
#ERRAMODEL_WORLD        World RMS error of fitted position along major axis        [deg]
#ERRBMODEL_WORLD        World RMS error of fitted position along minor axis        [deg]
#ERRTHETAMODEL_WORLD    Error ellipse pos.angle of fitted position (CCW/world-x)   [deg]
#ERRTHETAMODEL_SKY      Native fitted error ellipse pos. angle (east of north)     [deg]
#ERRTHETAMODEL_J2000    J2000 fitted error ellipse pos. angle (east of north)      [deg]
#ERRTHETAMODEL_B1950    B1950 fitted error ellipse pos. angle (east of north)      [deg]
#X2MODEL_IMAGE          Variance along x from model-fitting                        [pixel**2]
#Y2MODEL_IMAGE          Variance along y from model-fitting                        [pixel**2]
#XYMODEL_IMAGE          Covariance between x and y from model-fitting              [pixel**2]
#E1MODEL_IMAGE          Ellipticity component from model-fitting                  
#E2MODEL_IMAGE          Ellipticity component from model-fitting                  
#EPS1MODEL_IMAGE        Ellipticity component (quadratic) from model-fitting      
#EPS2MODEL_IMAGE        Ellipticity component (quadratic) from model-fitting      
#CONCENTRATION_MODEL    Concentration parameter from model-fitting                
#CLASS_STAR_MODEL       S/G classifier from model-fitting                         
#FLUX_BACKOFFSET        Background offset from fitting                             [count]
#FLUXERR_BACKOFFSET     RMS error on fitted background offset                      [count]
#FLUX_SPHEROID          Spheroid total flux from fitting                           [count]
#FLUXERR_SPHEROID       RMS error on fitted spheroid total flux                    [count]
#MAG_SPHEROID           Spheroid total magnitude from fitting                      [mag]
#MAGERR_SPHEROID        RMS error on fitted spheroid total magnitude               [mag]
#SPHEROID_REFF_IMAGE    Spheroid effective radius from fitting                     [pixel]
#SPHEROID_REFFERR_IMAGE RMS error on fitted spheroid effective radius              [pixel]
#SPHEROID_REFF_WORLD    Spheroid effective radius from fitting                     [deg]
#SPHEROID_REFFERR_WORLD RMS error on fitted spheroid effective radius              [deg]
#SPHEROID_ASPECT_IMAGE  Spheroid aspect ratio from fitting                        
#SPHEROID_ASPECTERR_IMA RMS error on fitted spheroid aspect ratio                 
#SPHEROID_ASPECT_WORLD  Spheroid aspect ratio from fitting                        
#SPHEROID_ASPECTERR_WOR RMS error on fitted spheroid aspect ratio                 
#SPHEROID_THETA_IMAGE   Spheroid position angle (CCW/x) from fitting               [deg]
#SPHEROID_THETAERR_IMAG RMS error on spheroid position angle                       [deg]
#SPHEROID_THETA_WORLD   Spheroid position angle (CCW/world-x)                      [deg]
#SPHEROID_THETAERR_WORL RMS error on spheroid position angle                       [deg]
#SPHEROID_THETA_SKY     Spheroid position angle (east of north, native)            [deg]
#SPHEROID_THETA_J2000   Spheroid position angle (east of north, J2000)             [deg]
#SPHEROID_THETA_B1950   Spheroid position angle (east of north, B1950)             [deg]
#SPHEROID_SERSICN       Spheroid Sersic index from fitting                        
#SPHEROID_SERSICNERR    RMS error on fitted spheroid Sersic index                 
#FLUX_DISK              Disk total flux from fitting                               [count]
#FLUXERR_DISK           RMS error on fitted disk total flux                        [count]
#MAG_DISK               Disk total magnitude from fitting                          [mag]
#MAGERR_DISK            RMS error on fitted disk total magnitude                   [mag]
#DISK_SCALE_IMAGE       Disk scalelength from fitting                              [pixel]
#DISK_SCALEERR_IMAGE    RMS error on fitted disk scalelength                       [pixel]
#DISK_SCALE_WORLD       Disk scalelength from fitting (world coords)               [deg]
#DISK_SCALEERR_WORLD    RMS error on fitted disk scalelength (world coords)        [deg]
#DISK_ASPECT_IMAGE      Disk aspect ratio from fitting                            
#DISK_ASPECTERR_IMAGE   RMS error on fitted disk aspect ratio                     
#DISK_ASPECT_WORLD      Disk aspect ratio from fitting                            
#DISK_ASPECTERR_WORLD   RMS error on disk aspect ratio                            
#DISK_INCLINATION       Disk inclination from fitting                              [deg]
#DISK_INCLINATIONERR    RMS error on disk inclination from fitting                 [deg]
#DISK_THETA_IMAGE       Disk position angle (CCW/x) from fitting                   [deg]
#DISK_THETAERR_IMAGE    RMS error on fitted disk position angle                    [deg]
#DISK_THETA_WORLD       Disk position angle (CCW/world-x)                          [deg]
#DISK_THETAERR_WORLD    RMS error on disk position angle                           [deg]
#DISK_THETA_SKY         Disk position angle (east of north, native)                [deg]
#DISK_THETA_J2000       Disk position angle (east of north, J2000)                 [deg]
#DISK_THETA_B1950       Disk position angle (east of north, B1950)                 [deg]
#DISK_PATTERN_VECTOR    Disk pattern fitted coefficients                          
#DISK_PATTERNMOD_VECTOR Disk pattern fitted moduli                                
#DISK_PATTERNARG_VECTOR Disk pattern fitted arguments                              [deg]
#DISK_PATTERN_SPIRAL    Disk pattern spiral index  
"""

	# We turn this text block into a list of the parameter names:
	fullparamlist = map(lambda s: s[1:-1], re.compile("#\w*\s").findall(fullparamtxt))

