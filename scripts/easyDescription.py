#!/usr/bin/env python3

import argparse
import os

import sys
argv = sys.argv
sys.argv = argv[:1]



if __name__ == '__main__':

    header = """
        '-------------------------------------------------------------------------------------------------------------------------------'
        '                                                                                                                               '
        '       _ \                                                                 |                          |                        '
        '      |   |  _` |  __ \   |   |   __|  |   |  __ `__ \      \ \   /  _ \   | \ \   /  _ \  __ \    _` |  |   |  __ `__ \       '
        '      ___/  (   |  |   |  |   |  |     |   |  |   |   |      \ \ /  (   |  |  \ \ /   __/  |   |  (   |  |   |  |   |   |      '
        '     _|    \__,_|  .__/  \__, | _|    \__,_| _|  _|  _|       \_/  \___/  _|   \_/  \___| _|  _| \__,_| \__,_| _|  _|  _|      '
        '                  _|     ____/                                                                                                 '
        '                                                                                                                               '
        '-------------------------------------------------------------------------------------------------------------------------------'
         """

    print(header)

    sys.argv = argv
    parser = argparse.ArgumentParser( formatter_class=argparse.ArgumentDefaultsHelpFormatter )

    parser.add_argument('--inputFileSamples'      , dest='inputFileSamples'      , help='input file with samples'                 , default=None)
    parser.add_argument('--outputFileSamples'     , dest='outputFileSamples'     , help='output file with samples expanded'       , default=None)
    parser.add_argument('--inputFileNuisances'    , dest='inputFileNuisances'    , help='input file with nuisances'               , default=None)
    parser.add_argument('--outputFileNuisances'   , dest='outputFileNuisances'   , help='output file with nuisances expanded'     , default=None)
    parser.add_argument('--inputFileCuts'         , dest='inputFileCuts'         , help='input file with cuts'                    , default=None)
    parser.add_argument('--outputFileCuts'        , dest='outputFileCuts'        , help='output file with cuts expanded'          , default=None)

    opt = parser.parse_args()

    print ("#   inputFileSamples  =               ", opt.inputFileSamples      )
    print ("#   outputFileSamples =               ", opt.outputFileSamples     )
    print ("#   inputFileNuisances  =             ", opt.inputFileNuisances    )
    print ("#   outputFileNuisances =             ", opt.outputFileNuisances   )
    print ("#   inputFileCuts  =                  ", opt.inputFileCuts         )
    print ("#   outputFileCuts =                  ", opt.outputFileCuts        )

    #
    # unfold Samples
    #

    if opt.inputFileSamples != None :
      samples = {}
      if os.path.exists(opt.inputFileSamples) :
        handle = open(opt.inputFileSamples,'r')
        exec(handle.read())
        handle.close()
        # clean the dictionary to remove globals due to "exec" funcionality
        samples = {k: v for k, v in samples.items() if not (k.startswith('__') and k.endswith('__'))}

      #for sampleName, sample in samples.iteritems():
        #print '        '
        #print '     -> ', sampleName, ' :: '
        #if 'name' in sample :
          #for fileName in sample['name'] :
            #print '         ', fileName
        #if 'weight' in sample :
          #print '    weight =     ', sample['weight']

      #
      # samples
      #

      #printSampleDic (samples)


      if opt.outputFileSamples != None :

        fileOutSamples = open(opt.outputFileSamples,"w")

        fileOutSamples.write("# \n")
        fileOutSamples.write("# Expanded version of samples.py \n")
        fileOutSamples.write("# \n")


        for sampleName, sample in samples.items():

          fileOutSamples.write("samples[\'" + sampleName + "\'] = { \n")
          # print ("sampleName = ", sampleName, " --> sample = ", sample)

          if 'name' in sample :
            fileOutSamples.write("     \'name\'  : {  \n")
            for fileName, list_files in sample['name'].items() :
              fileOutSamples.write("     \'" + fileName + "\'  :  [ \n")
              for name_file in list_files :
                fileOutSamples.write("            '" + name_file + "' ,\n")
              fileOutSamples.write("        ],  \n")
            fileOutSamples.write("        },  \n")


          if 'weights' in sample :
            fileOutSamples.write("     \'weights\'  : {  \n")
            for fileName, specific_weight in sample['weights'].items() :
              fileOutSamples.write("          \'" + fileName + "\'  :  ' " + specific_weight + " ' \n")
            fileOutSamples.write("        },  \n")

          if 'isData' in sample :
            fileOutSamples.write("     \'isData\'  :  [ \n")
            for isData in sample['isData'] :
              fileOutSamples.write("            '" + str(isData) + "',\n")
            fileOutSamples.write("     ],  \n")


          if 'weight' in sample :
            fileOutSamples.write("     \'weight\'  :   '" + sample['weight'] + "' ,\n")

          if 'FilesPerJob' in sample :
            fileOutSamples.write("     \'FilesPerJob\'  :   " + str(sample['FilesPerJob']) + " ,\n")

          if 'subsamples' in sample :
            fileOutSamples.write("     \'subsamples\'  :   " + str(sample['subsamples']) + " ,\n")


          fileOutSamples.write("}  \n")
          fileOutSamples.write("   \n ")


        fileOutSamples.close()






    #
    # unfold Nuisances
    #

    if opt.inputFileNuisances != None :

      nuisances = {}
      if os.path.exists(opt.inputFileNuisances) :
        handle = open(opt.inputFileNuisances,'r')
        exec(handle.read())
        handle.close()
        # clean the dictionary to remove globals due to "exec" funcionality
        nuisances = {k: v for k, v in nuisances.items() if not (k.startswith('__') and k.endswith('__'))}


      if opt.outputFileNuisances != None :

        fileOutNuisances = open(opt.outputFileNuisances,"w")

        fileOutNuisances.write("# \n")
        fileOutNuisances.write("# Expanded version of samples.py \n")
        fileOutNuisances.write("# \n")

        #print " nuisances = ", nuisances

        for nuisanceName, nuisance in nuisances.items():

          fileOutNuisances.write("nuisances[\'" + nuisanceName + "\'] = { \n")

          if 'name' in nuisance :
            fileOutNuisances.write("     \'name\'  :   '" + nuisance['name'] + "' ,\n")

          if 'kind' in nuisance :
            fileOutNuisances.write("     \'kind\'  :   '" + nuisance['kind'] + "' ,\n")

          if 'type' in nuisance :
            fileOutNuisances.write("     \'type\'  :   '" + nuisance['type'] + "' ,\n")

          if 'samples' in nuisance :
            fileOutNuisances.write("     \'samples\'  :  { \n")
            for samples in nuisance['samples'] :
              fileOutNuisances.write("            '" + str(samples) + "',\n")
            fileOutNuisances.write("     },  \n")

          if 'cuts' in nuisance :
            fileOutNuisances.write("     \'cuts\'  :  [ \n")
            for cuts in nuisance['cuts'] :
              fileOutNuisances.write("            '" + str(cuts) + "',\n")
            fileOutNuisances.write("     ],  \n")


          if 'folderUp' in nuisance :
            fileOutNuisances.write("     \'folderUp\'    :   '" + nuisance['folderUp'] + "' ,\n")

          if 'folderDown' in nuisance :
            fileOutNuisances.write("     \'folderDown\'  :   '" + nuisance['folderDown'] + "' ,\n")


          fileOutNuisances.write("}  \n")
          fileOutNuisances.write("   \n ")


        fileOutNuisances.close()



    #
    # unfold Cuts
    #



    if opt.inputFileCuts != None :
      cuts = {}
      if os.path.exists(opt.inputFileCuts) :
        handle = open(opt.inputFileCuts,'r')
        exec(handle.read())
        handle.close()
        # clean the dictionary to remove globals due to "exec" funcionality
        cuts = {k: v for k, v in cuts.items() if not (k.startswith('__') and k.endswith('__'))}

      if opt.outputFileCuts != None :

        fileOutCuts = open(opt.outputFileCuts,"w")

        fileOutCuts.write("# \n")
        fileOutCuts.write("# Expanded version of cuts.py \n")
        fileOutCuts.write("# \n")

        # if supercut
        if 'supercut' in locals():
          fileOutCuts.write("supercut = \' " + str(supercut) + " \' \n\n\n")

        # now the cuts

        for cutName, cut in cuts.items():

          fileOutCuts.write("cuts[\'" + cutName + "\'] = ' \\\n")

          fileOutCuts.write("      " + cut + " \\\n")

          fileOutCuts.write("   ' \n")
          fileOutCuts.write("   \n ")


        fileOutCuts.close()







#
# How to use it:
#
# easyDescription.py   --inputFileSamples=../../PlotsConfigurations/Configurations/ggH/Full2016/samples.py   --outputFileSamples=test.py
# easyDescription.py   --inputFileSamples=../../PlotsConfigurations/Configurations/ggH/Full2016/samples.py  --inputFileNuisances=../../PlotsConfigurations/Configurations/ggH/Full2016/nuisances.py   --outputFileNuisances=testNuisances.py
# easyDescription.py   --inputFileCuts=cuts.py   --outputFileCuts=cuts_expanded.py
#
#  NB: the "samples" file has to be defined, because some global variables are defined there (e.g. NLep)
#



