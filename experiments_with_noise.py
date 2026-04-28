from xml.dom.minidom import parse, parseString
import random, subprocess, platform, os, re, pdb, time
import sys, platform

def get_data_from_file(filename):
    ''' read data from file into a list'''
    f = open(filename)
    filecontents = f.readlines()
    table = [line.replace('\n', '').replace('\r', '').replace(' ', '\t').split('\t') for line in filecontents]
    f.close()
    return table

class ProcessXML:

    def __init__(self, argos_xml = None):
        self.argos_xml = argos_xml
    
    def run(self):
        run_count = 15
        count =1
        startTime =time.time()
        for _ in range(run_count):
            print "Run "+str(count)
            singleRun_StartTime =  time.time()
            count = count+1
            output = subprocess.check_output(['argos3 -n -c ' + self.argos_xml], shell=True, stderr=subprocess.STDOUT)
            singleRun_EndTime = time.time()
        print 'This run takes '+str((singleRun_EndTime-singleRun_StartTime)/60.0)+' minutes...' 
        endTime = time.time()
        print 'The total running time is '+str((endTime-startTime)/60.0)+' minutes...'   
    


    def update_XML_parameters(self, parameters, value):
        xml = parse(self.argos_xml)
        
        if parameters.has_key("XMLBlock"):
            targetBlock =  xml.getElementsByTagName(parameters["XMLBlock"][0])
        else: 
            print "The target block is not specified in the input data file!!!!!!!!!!!!!!!!"
            return
            
        attrs = None
        count = 0
        #pdb.set_trace()
        for block in targetBlock:
            for idx in range(len(parameters.keys())):
                if  parameters.keys()[idx] != "XMLBlock":
                    if block.getAttribute(parameters.keys()[idx]) == '':
                        break
                    else:
                        attrs = block
                        count +=1
        if count > 1:
            print "More than one blocks have the same attribute!!!!!!!!!!!!!!!!!!!"            
            return
        if attrs == None:
            print "the target block does not exist !!!!!!!!!!!!!!!!"
            return
        for p in parameters:
            if p != "XMLBlock": 
                attrs.setAttribute(p,value)
        
        xml.writexml(open(self.argos_xml, 'w'))
        for p in parameters:
            if p != "XMLBlock":
                print p, "=", attrs.getAttribute(p), attrs.getAttribute(p) == value

        print 'Updated setting parameters ...'


def processData(data):
    result={}
    #system = 'linux' if platform.system() == 'Linux' else 'mac'

    for line in data:
        result[line[0]] = line[1:]
    return result

   
    
if __name__ == "__main__":
    folder = './experiments'
    dataFile = raw_input('Please select the input file: ')
    
    dataFileLocation = os.path.join('.', dataFile)
    if not os.path.isfile(dataFileLocation):
        print "The file ", dataFileLocation, " does not exist!!!!!!!!!!!!!!!!!"
        
    parameterData = get_data_from_file(dataFileLocation)
    
    parameterDict = processData(parameterData)
    print 'parameterDict=', parameterDict
    
    if parameterDict.has_key('Files'):
        targetFiles = parameterDict['Files']
        del parameterDict['Files']
    
    for file in targetFiles:
        fileLocation = os.path.join(folder,file)+'.xml'
        if os.path.isfile(fileLocation):
            print "File: ", fileLocation
            this_run = ProcessXML(fileLocation)
            for value in parameterDict['DestinationNoiseStdev']:
              this_run.update_XML_parameters(parameterDict, value)
              this_run.run()
        else:
            print fileLocation, ' does not exist!!!!!!!!!!!!!!!!!!!!'






