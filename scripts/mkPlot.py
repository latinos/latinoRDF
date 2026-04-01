#!/usr/bin/env python3

import sys
argv = sys.argv
sys.argv = argv[:1]

import argparse

import os

import ROOT


#
# default parser
#

def defaultParser():
    sys.argv = argv

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--pycfg",
        dest="pycfg",
        help="input configuration file",
        default="configuration.py",
    )

    return parser


#
# load configurations into the parser, according to configuration.py
#

def loadDefaultOptions(parser, pycfg=None, quiet=False):

    if pycfg != None and os.path.exists(pycfg):
        # print ("loadDefaultOptions: pycfg = ", pycfg)
        handle = open(pycfg,'r')
        local_variables = {}
        exec(handle.read(),local_variables)
        handle.close()
        # clean the dictionary to remove globals due to "exec" funcionality
        local_variables = {k: v for k, v in local_variables.items() if not (k.startswith('__') and k.endswith('__'))}
        for opt_name, opt_value in local_variables.items():
          parser.add_argument('--' + opt_name, default=opt_value)
        return
    else:
        return



# ----------------------------------------------------- PlotFactory --------------------------------------

import logging
import subprocess


class PlotFactory:
    _logger = logging.getLogger('PlotFactory')

    # _____________________________________________________________________________
    def __init__(self):

        variables = {}
        self._variables = variables

        cuts = {}
        self._cuts = cuts

        samples = {}
        self._samples = samples

        aliases = {}
        self._aliases = aliases

        self._lumi = 1

        # self._outputDir = './test/'
        #
        # self._outputRootFile = 'myhistos.root'
        #
        # self._script_batch_location = './scripts_batch/'
        #
        # self._scripts_run_folder = "scripts_run"

        # conditions
        self._silentMode = False



    # _____________________________________________________________________________
    def __del__(self):
        pass




    # _____________________________________________________________________________
    def setValues(self, outputDir, variables, cuts, samples, nuisances, aliases, lumi):

        self._variables = variables
        self._samples   = samples
        self._cuts      = cuts
        self._nuisances = nuisances
        self._aliases   = aliases
        self._outputDir = outputDir
        self._lumi      = lumi

    # _____________________________________________________________________________
    def setConditions(self, silentMode):

        self._silentMode = silentMode









if __name__ == '__main__':
    sys.argv = argv

    header = """
         --------------------------------------------------------------------------------
         '                                                                              '
         '            _ \   |         |         \  |         |                          '
         '           |   |  |   _ \   __|      |\/ |   _` |  |  /   _ \   __|           '
         '           ___/   |  (   |  |        |   |  (   |    <    __/  |              '
         '          _|     _| \___/  \__|     _|  _| \__,_| _|\_\ \___| _|              '
         '                                                                              '
         '                                                                              '
         --------------------------------------------------------------------------------
         """

    print(header)

    parser = defaultParser()

    parser.add_argument("--submitBatch", action='store_true', dest="submitBatch",   help="Trigger the submission to lxbatch")
    parser.add_argument("--hadd",        action='store_true', dest="haddRootFiles", help="Trigger the merging of the root files")
    parser.add_argument("--silentMode",  action='store_true', dest="silentMode",    help="Remove as much as possible the print and the log/err files production")
    # parser.add_argument('--scaleToPlot'    , dest='scaleToPlot'    , help='scale of maxY to maxHistoY'                 , default=3.0  ,    type=float   )
    # parser.add_argument('--minLogC'        , dest='minLogC'        , help='min Y in log plots'                         , default=0.01  ,    type=float   )
    # parser.add_argument('--maxLogC'        , dest='maxLogC'        , help='max Y in log plots'                         , default=100   ,    type=float   )
    # parser.add_argument('--minLogCratio'   , dest='minLogCratio'   , help='min Y in log ratio plots'                   , default=0.001 ,    type=float   )
    # parser.add_argument('--maxLogCratio'   , dest='maxLogCratio'   , help='max Y in log ratio plots'                   , default=10    ,    type=float   )
    # parser.add_argument('--maxLinearScale' , dest='maxLinearScale' , help='scale factor for max Y in linear plots (1.45 magic number as default)'     , default=1.45   ,    type=float   )
    # parser.add_argument('--outputDirPlots' , dest='outputDirPlots' , help='output directory'                           , default='./')
    # parser.add_argument('--inputFile'      , dest='inputFile'      , help='input file with histograms'                 , default='input.root')
    # parser.add_argument('--tag'            , dest='tag'            , help='Tag used for the shape file name. Used if inputFile is a directory', default=None)
    # parser.add_argument('--nuisancesFile'  , dest='nuisancesFile'  , help='file with nuisances configurations'         , default=None )
    #
    # parser.add_argument('--onlyVariable'   , dest='onlyVariable'   , help='draw only one variable (may be needed in post-fit plots)'          , default=None)
    # parser.add_argument('--onlyCut'        , dest='onlyCut'        , help='draw only one cut phase space (may be needed in post-fit plots)'   , default=None)
    # parser.add_argument('--onlyPlot'       , dest='onlyPlot'       , help='draw only specified plot type (comma-separated c, cratio, and/or cdifference)', default=None)
    #
    # parser.add_argument('--linearOnly'     , dest='linearOnly'     , help='Make linear plot only.', action='store_true', default=False)
    # parser.add_argument('--logOnly'        , dest='logOnly'        , help='Make log plot only.', action='store_true', default=False)
    #
    # parser.add_argument('--fileFormats'    , dest='fileFormats'    , help='Output plot file formats (comma-separated png, pdf, root, C, and/or eps). Default "png,root"', default='png,root')
    #
    # parser.add_argument('--plotNormalizedIncludeData'    , dest='plotNormalizedIncludeData'    , help='plot also normalized distributions for data, for shape comparison purposes', default=None )
    # parser.add_argument('--plotNormalizedDistributions'         , dest='plotNormalizedDistributions'         , help='plot also normalized distributions for optimization purposes'    ,    action='store_true'     , default=None )
    # parser.add_argument('--plotNormalizedDistributionsTHstack'  , dest='plotNormalizedDistributionsTHstack'  , help='plot also normalized distributions for optimization purposes, with stacked sig and bkg'  ,    action='store_true'       , default=None )
    #
    # parser.add_argument('--showIntegralLegend'           , dest='showIntegralLegend'           , help='show the integral, the yields, in the legend'                         , default=0,    type=float )
    #
    # parser.add_argument('--showRelativeRatio'   , dest='showRelativeRatio'   , help='draw instead of data-expected, (data-expected) / expected' ,    action='store_true', default=False)
    # parser.add_argument('--showDataMinusBkgOnly', dest='showDataMinusBkgOnly', help='draw instead of data-expected, data-expected background only' , action='store_true', default=False)
    #
    # parser.add_argument('--removeWeight', dest='removeWeight', help='Remove weight S/B for PR plots, just do the sum' , action='store_true', default=False)
    #
    # parser.add_argument('--invertXY', dest='invertXY', help='Invert the weighting for X <-> Y. Instead of slices along Y, do slices along X' , action='store_true', default=False)
    #
    # parser.add_argument('--postFit', dest='postFit', help='Plot sum of post-fit backgrounds, and the data/post-fit ratio.' , default='n')
    #
    # parser.add_argument('--skipMissingNuisance', dest='skipMissingNuisance', help='Do not trigger errors if a nuisance is missing. To be used with absolute care!!!' , action='store_true', default=False)
    #
    # parser.add_argument('--removeMCStat', dest='removeMCStat', help='Do not plot the MC statistics contribution in the uncertainty band', action='store_true', default=False)
    # parser.add_argument('--extraLegend'   , dest='extraLegend'   , help='User-specified additional legend'          , default=None)
    #
    # parser.add_argument('--customize', dest='customizeKey', help="Optional parameters for the customizations script", default=None)
    # parser.add_argument('--plotFancy', dest='plotFancy', help='Plot fancy data - bkg plot' , action='store_true', default=False)
    #
    # parser.add_argument('--NoPreliminary', dest='NoPreliminary', help='Remove preliminary status in plots' , action='store_true', default=False)
    # parser.add_argument('--RemoveAllMC', dest='RemoveAllMC', help='Remove all MC in legend' , action='store_true', default=False)
    #
    # parser.add_argument('--parallelPlotting', dest='parallelPlotting', help='Plot each cut in parallel' , action='store_true', default=False)



    opt = parser.parse_args()
    print ("opt.pycfg            = ", opt.pycfg)
    loadDefaultOptions(parser, opt.pycfg)
    opt = parser.parse_args()


    print ("opt.tag              = ", opt.tag)
    print ("opt.variablesFile    = ", opt.variablesFile)
    print ("opt.cutsFile         = ", opt.cutsFile)
    print ("opt.samplesFile      = ", opt.samplesFile)
    print ("opt.nuisancesFile    = ", opt.nuisancesFile)
    print ("opt.lumi             = ", opt.lumi)
    print ("opt.outputDir        = ", opt.outputDir)

    print ("opt.submitBatch      = ", opt.submitBatch)
    print ("opt.hadd             = ", opt.haddRootFiles)
    print ("opt.silentMode       = ", opt.silentMode)




    # not used by mkShapes
    # print ("opt.structureFile    = ", opt.structureFile)

    #
    # logic of dependencies:
    #
    #    samples.py
    #      --> nuisances.py   since some nuisances are defined only for some samples
    #      --> aliases.py     since the aliases/defines will be "Defined" only for selected samples
    #    cuts.py
    #      --> nuisances.py   since some nuisances are defined only for some cuts (e.g. lnN of migration)
    #    nuisances.py
    #    variables.py
    #


    #
    # read list of samples
    #
    samples = {}
    if os.path.exists(opt.samplesFile) :
      handle = open(opt.samplesFile,'r')
      exec(handle.read())
      handle.close()
      # clean the dictionary to remove globals due to "exec" funcionality
      samples = {k: v for k, v in samples.items() if not (k.startswith('__') and k.endswith('__'))}

    # print ("samples = ", samples)

    #
    # read list of variables
    #
    variables = {}
    if os.path.exists(opt.variablesFile) :
      handle = open(opt.variablesFile,'r')
      exec(handle.read())
      handle.close()
      # clean the dictionary to remove globals due to "exec" funcionality
      variables = {k: v for k, v in variables.items() if not (k.startswith('__') and k.endswith('__'))}

    print ("variables = ", variables)


    #
    # read list of cuts
    #
    cuts = {}
    if os.path.exists(opt.cutsFile) :
      handle = open(opt.cutsFile,'r')
      exec(handle.read())
      handle.close()
      # clean the dictionary to remove globals due to "exec" funcionality
      cuts = {k: v for k, v in cuts.items() if not (k.startswith('__') and k.endswith('__'))}

    print ("cuts = ", cuts)


    #
    # read list of nuisances
    #
    nuisances = {}
    if os.path.exists(opt.nuisancesFile) :
      handle = open(opt.nuisancesFile,'r')
      exec(handle.read())
      handle.close()
      # clean the dictionary to remove globals due to "exec" funcionality
      nuisances = {k: v for k, v in nuisances.items() if not (k.startswith('__') and k.endswith('__'))}

    print ("nuisances = ", nuisances)


    #
    # read list of aliases
    #
    aliases = {}
    if os.path.exists(opt.aliasesFile) :
      handle = open(opt.aliasesFile,'r')
      exec(handle.read())
      handle.close()
      # clean the dictionary to remove globals due to "exec" funcionality
      aliases = {k: v for k, v in aliases.items() if not (k.startswith('__') and k.endswith('__'))}

    print ("aliases = ", aliases)






    factory = PlotFactory()
    factory.setValues( opt.outputDir, variables, cuts, samples, nuisances , aliases, opt.lumi)
    factory.setConditions (opt.silentMode)

    # factory._treeName  = opt.treeName
    # factory._energy    = opt.energy
    # factory._lumi      = opt.lumi
    # factory._tag       = opt.tag

    # if not opt.submitBatch and not opt.haddRootFiles:
      # factory.makeNominals()

    # if opt.submitBatch :
      # factory.submitBatch()

    # if opt.haddRootFiles :
      # print ("Hadd the different root files ...")
#
      # hadd_cmd = f"hadd -j 8 -f {opt.outputDir}/root_file_joined.root    {opt.outputDir}/root_file___*.root"
#
      # print(f"hadd: {hadd_cmd}")
      # result = os.system(hadd_cmd)
#
      # print ("I have hadded all the root files but I have not removed the original ones")





    print ("\n\n")
    print (" I'm done ... \n\n")


