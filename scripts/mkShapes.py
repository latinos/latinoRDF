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



# ----------------------------------------------------- ShapeFactory --------------------------------------

import logging
import subprocess


class ShapeFactory:
    _logger = logging.getLogger('ShapeFactory')

    # _____________________________________________________________________________
    def __init__(self):

        variables = {}
        self._variables = variables

        cuts = {}
        self._cuts = cuts

        samples = {}
        self._samples = samples


        self._treeName = 'latino'

        self._outputDir = './test/'

        self._outputRootFile = 'myhistos.root'

        self._script_batch_location = './scripts_batch/'

        self._scripts_run_folder = "scripts_run"

    # _____________________________________________________________________________
    def __del__(self):
        pass


    # _____________________________________________________________________________
    def create_cpp_source_single_file(self, output_name, tree_name, file_path, output_root_file_name, sampleName):
        # This is your C++ template as a Python string

        booking_logic = ""


        #
        # In RDataFrame, all variables must be defined before being plotted
        # The pro of this is that they can be used also in cuts
        #
        #
        # In case of already defined variables, for example "mll", and "mll" is already defined in the TTree,
        # the code "SafeDefine" should handle this, and "Define" a variable only when needed
        #
        # booking_logic += f'auto df = base_df'
        # for variableName, variable in self._variables.items():
        #     name = variable['name']
        #     booking_logic += f'        .Define("{variableName}", "{name}")\n'
        # booking_logic += f'        ;\n'

        booking_logic += f"//  I need to define the RNode, otherwise SafeDefine will not work\n"
        booking_logic += f'    auto current_node = ROOT::RDF::RNode(base_df);\n'

        booking_logic += f"    // Define variables \n"
        for variableName, variable in self._variables.items():
            name = variable['name']
            booking_logic += f'    current_node = SafeDefine(current_node, "{variableName}", "{name}");\n'


        #
        # once all variables are defined, they can be used and plotted with "variableName"
        #
        # In root file:    <cut>/<variable>/histo_<sample>
        #
        for cutName, cut in self._cuts.items():
          booking_logic += f'    auto node_{cutName} = current_node.Filter("{cut}", "{cutName}");\n'

          for variableName, variable in self._variables.items():
              (bins, v_min, v_max) = variable['range']
              # FIXME: folding needed

              # We add each RResultPtr to a vector called 'histograms'
              booking_logic += f'    hist_map["{cutName}"].push_back(node_{cutName}.Histo1D({{"h_{variableName}", "{variableName}", {bins}, {v_min}, {v_max}}}, "{variableName}"));\n'




        booking_logic += f'    std::vector<std::string> list_of_variables;\n'
        for variableName, variable in self._variables.items():
          booking_logic += f'    list_of_variables.push_back("{variableName}");\n'



        cpp_code = f"""
#include "ROOT/RDataFrame.hxx"
#include "TFile.h"
#include "TH1D.h"
#include "TDirectory.h"
#include <map>
#include <vector>
#include <iostream>


ROOT::RDF::RNode SafeDefine(ROOT::RDF::RNode df, std::string name, std::string expr) {{
    auto colNames = df.GetColumnNames();
    if (std::find(colNames.begin(), colNames.end(), name) == colNames.end()) {{
        return df.Define(name, expr);
    }}
    return df;
}}


int main() {{
    ROOT::EnableImplicitMT();
    ROOT::RDataFrame base_df("{tree_name}", "{file_path}");

    // auto count = base_df.Count();
    // std::cout << "Successfully processed {tree_name}. Event count: " << *count << std::endl;

    std::map<std::string, std::vector<ROOT::RDF::RResultPtr<TH1D>>> hist_map;

    // --- Automatically generated bookings ---

    {booking_logic}

    // ----------------------------------------

    //
    // In root file:    <cut>/<variable>/histo_<sample>
    //

    TFile out_file("{self._outputDir}/{output_root_file_name}", "RECREATE");
    for (auto& [cut_label, h_list] : hist_map) {{
        // Create a folder for this cut
        TDirectory *dir = out_file.mkdir(cut_label.c_str());
        int ivar = 0;
        for (auto& h : h_list) {{
            dir->cd();
            TDirectory *subdir = out_file.mkdir( (cut_label+"/"+list_of_variables.at(ivar)).c_str() );
            subdir->cd();
            ivar++;
            h->SetName("histo_{sampleName}");
            h->Write();
        }}
        out_file.cd(); // Go back to root for the next directory
    }}
    out_file.Close();

    return 0;
}}

        """


        with open(f"{output_name}.cpp", "w") as f:
            f.write(cpp_code)
        # print(f"Created {output_name}.cpp")


    # _____________________________________________________________________________
    def compile_cpp(self, source_name):
        # Get ROOT flags automatically using 'root-config'
        root_flags = subprocess.check_output(["root-config", "--cflags", "--libs"]).decode().strip()

        # Construct the compilation command
        compile_cmd = f"g++ -O2 {source_name}.cpp -o {source_name} {root_flags}"
        # compile_cmd = f"g++ -O3 {source_name}.cpp -o {source_name} {root_flags}"

        print(f"Compiling...")
        result = os.system(compile_cmd)

        if result == 0:
            print(f"Compilation successful: ./{source_name}")
        else:
            print("Compilation failed!")


    # _____________________________________________________________________________
    def generate_makefile(self,file_paths, makefile_name="Makefile"):
        # Get ROOT configuration via shell calls
        cpp_flags = "$(shell root-config --cflags)"
        ld_flags = "$(shell root-config --libs)"
        type_of_compilation = "-O2"
        # from "blabla.cpp" to "blabla"
        targets = [os.path.splitext(f)[0] for f in file_paths]

        with open(makefile_name, "w") as f:
            f.write("# Generated Makefile\n")
            f.write("CXX = g++\n")
            f.write(f"CXXFLAGS = {type_of_compilation} -Wall {cpp_flags}\n")
            f.write(f"LDFLAGS = {ld_flags}\n\n")

            # 'all' target: the list of all executables to be created
            all_targets = " ".join(targets)
            f.write(f"all: {all_targets}\n\n")

            # The Pattern Rule
            # This says: To create ANY executable 'X', look for 'X.cpp'
            # It works across subdirectories automatically.
            f.write("%: %.cpp\n")
            f.write("\t$(CXX) $(CXXFLAGS) $< -o $@ $(LDFLAGS)\n\n")

            # Clean target
            f.write("clean:\n")
            f.write(f"\trm -f {all_targets}\n")


    # _____________________________________________________________________________
    def setValues(self, outputDir, variables, cuts, samples, nuisances):

        self._variables = variables
        self._samples   = samples
        self._cuts      = cuts
        self._nuisances = nuisances
        self._outputDir = outputDir


    # _____________________________________________________________________________
    def makeNominals(self):

        print ("======================")
        print ("==== makeNominals ====")
        print ("======================")

        os.system ("mkdir " + self._outputDir + "/")

        ROOT.TH1.SetDefaultSumw2(True)

        os.system ("mkdir " + self._scripts_run_folder + "/")

        list_of_files_to_compile = []

        # print ("length of samples = ", len(self._samples))
        #
        # Loop over samples
        #
        for sampleName, sample in self._samples.items():
          os.system ("mkdir " + self._scripts_run_folder + "/" + sampleName + "/")
          #
          # create an executable for each file in each sample
          #
          # samples is a dictionary: {'subname' : [list of root files] }
          #
          # print ("length of sample['name'] = ", len(sample['name']))

          for subname, list_root_files in sample['name'].items():
            print ("length of list_root_files = ", len(list_root_files))
            os.system ("mkdir " + self._scripts_run_folder + "/" + sampleName + "/" + subname + "/")
            for i, root_file in enumerate(list_root_files):
              # name_code = self._scripts_run_folder + "/" + sampleName + "/" + subname + "/" + "my_run_analysis_" + str(i)
              name_code = self._scripts_run_folder + "/" + sampleName + "/" + subname + "/" + "my_run_analysis_" + sampleName + "_" + subname + "_" + str(i)
              tree = "Events"

              output_root_file_name = "root_file_" + sampleName + "_" + subname + "_" + str(i) + ".root"
              self.create_cpp_source_single_file(name_code, tree, root_file, output_root_file_name, sampleName)

              list_of_files_to_compile.append(name_code)
              # self.compile_cpp(name_code)

        self.generate_makefile(list_of_files_to_compile)

        # Run the compilation in parallel
        print("Start parallel compilation...")
        # subprocess.run(["make", "-j8"])
        #
        # subprocess.run() is a blocking call -> it will make the compilation to end before the next step
        #

        # Now you can run it:
        # subprocess.run([f"./{name_code}"])


    # _____________________________________________________________________________
    def submitBatch(self):

        print ("======================")
        print ("==== submit Batch ====")
        print ("======================")

        os.system ("mkdir " + self._script_batch_location + "/")
        os.system ("mkdir " + self._script_batch_location + "/")

        submission_dir = os.getcwd()

        #
        # Loop over samples
        #
        for sampleName, sample in self._samples.items():
          os.system ("mkdir " + self._script_batch_location + "/" + sampleName + "/")

          for subname, list_root_files in sample['name'].items():
            os.system ("mkdir " + self._script_batch_location + "/" + sampleName + "/" + subname + "/")
            for i, root_file in enumerate(list_root_files):
              name_code = self._scripts_run_folder + "/" + sampleName + "/" + subname + "/" + "my_run_analysis_" + sampleName + "_" + subname + "_" + str(i)
              name_code_no_folder = "my_run_analysis_" + sampleName + "_" + subname + "_" + str(i)
              name_bash = self._script_batch_location + "/" + sampleName + "/" + subname + "/" + "my_script_" + str(i) + ".sh"
              output_root_file_name = "root_file_" + sampleName + "_" + subname + "_" + str(i) + ".root"

              bash_code = f"""#!/bin/bash
set -e  # Exit on error
echo "Job started at $(date)"
echo "Running on node $(hostname)"
mkdir {self._outputDir}
./{name_code_no_folder}
cp {self._outputDir}/{output_root_file_name}  {submission_dir}/{self._outputDir}/

echo "Current directory content after running:"
ls -lh
echo "Current full path: $(pwd)"

"""

              with open(f"{name_bash}", "w") as f:
                f.write(bash_code)
                os.system ("chmod +x " + name_bash)
                # print ("name_bash = ", name_bash)

              name_submit = submission_dir + "/" + self._script_batch_location + "/" + sampleName + "/" + subname + "/" + "my_script_" + str(i) + ".sub"
              # name_folder = submission_dir + "/" + self._script_batch_location + "/" + sampleName + "/" + subname + "/"
              name_folder = self._script_batch_location + "/" + sampleName + "/" + subname + "/"
              name_folder_code = self._scripts_run_folder + "/" + sampleName + "/" + subname + "/"
              name_bash_no_folder = "my_script_" + str(i) + ".sh"

              submit_code = f"""
initialdir            = {name_folder}
executable            = {name_bash}
transfer_input_files  = {submission_dir}/{name_folder_code}{name_code_no_folder}
should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
output                = log/{name_bash_no_folder}.out
error                 = log/{name_bash_no_folder}.err
log                   = log/{name_bash_no_folder}.log
getenv                = True
+JobFlavour           = "longlunch"
queue
"""

              with open(f"{name_submit}", "w") as f:
                f.write(submit_code)

              print("Submitting job to HTCondor: condor_submit " + name_submit)
              subprocess.run(["condor_submit", f"{name_submit}"])

#
#
#  Main
#
#

if __name__ == '__main__':
    sys.argv = argv

    header = """
         --------------------------------------------------------------------------------------------------
         '                                                                                                '
         '                ___|   |                               \  |         |                           '
         '              \___ \   __ \    _` |  __ \    _ \      |\/ |   _` |  |  /   _ \   __|            '
         '                    |  | | |  (   |  |   |   __/      |   |  (   |    <    __/  |               '
         '              _____/  _| |_| \__,_|  .__/  \___|     _|  _| \__,_| _|\_\ \___| _|               '
         '                                    _|                                                          '
         '                                                                                                '
         --------------------------------------------------------------------------------------------------
         """

    print(header)

    parser = defaultParser()

    parser.add_argument("--submitBatch", action='store_true', dest="submitBatch",   help="Trigger the submission to lxbatch")
    parser.add_argument("--hadd",        action='store_true', dest="haddRootFiles", help="Trigger the merging of the root files")

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


    # not used by mkShapes
    # print ("opt.structureFile    = ", opt.structureFile)

    #
    # logic of dependencies:
    #
    #    samples.py
    #      --> nuisances.py   since some nuisances are defined only for some samples
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




    factory = ShapeFactory()
    factory.setValues( opt.outputDir, variables, cuts, samples, nuisances )

    # factory._treeName  = opt.treeName
    # factory._energy    = opt.energy
    # factory._lumi      = opt.lumi
    # factory._tag       = opt.tag

    if not opt.submitBatch and not opt.haddRootFiles:
      factory.makeNominals()

    if opt.submitBatch :
      factory.submitBatch()


    if opt.haddRootFiles :
      print ("Hadd the different root files ...")

# hadd -j 8 -O -f target.root source1.root source2.root ...

      print ("I have hadded all the root files but I have not removed the original ones")





    print ("\n\n")
    print (" I'm done ... \n\n")













