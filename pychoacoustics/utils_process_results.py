# -*- coding: utf-8 -*-

#   Copyright (C) 2008-2014 Samuele Carcagno <sam.carcagno@gmail.com>
#   This file is part of pychoacoustics

#    pychoacoustics is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    pychoacoustics is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with pychoacoustics.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals
from numpy import mean, std, zeros
import numpy, warnings
from .stats_utils import*
from scipy.stats.distributions import norm
from .pysdt import*

class InvalidBlockRange(Exception):
    pass
class DifferentProceduresError(Exception):
    pass

def getBlockRangeToProcess(last, block_range, conditionsList):
    nBlocks = len(conditionsList)

    if last is None and block_range is None: #process all blocks
        start = 0; stop = nBlocks
    elif last is not None:
        if block_range is not None:
            warnings.warn("'last' was given ignoring 'block_range'")
        if last > nBlocks:
            raise InvalidBlockRange("Block range specified is greater than number of blocks in file")

        start = nBlocks - last; stop = nBlocks
    else:
        if isinstance(block_range, tuple) == False:
            raise TypeError("'block_range' must be a tuple")
        if len(block_range) != 2:
            raise InvalidBlockRange("'block_range' must be a tuple with beginning and end blocks, e.g. block_range=(1,3)")
        beginning = block_range[0]; end = block_range[1]
        if beginning < 0:
            raise InvalidBlockRange("'beginning' must be greater than zero")
        if beginning > end:
            raise InvalidBlockRange("'beginning' must be smaller than 'end'")
        if end > nBlocks:
            raise InvalidBlockRange("'end' must be smaller than the number of blocks in file")
        start = beginning-1
        stop = end

    return start, stop

def checkMixedProceduresInTableFile(allLines, separator):
    """
    Function to check that a given table file does not contain more than one header.
    """
    for line in allLines[1:len(allLines)]:
        try:
            float(line.split(separator)[0])
        except:
            return True
    return False
  
    
def processResultsAdaptive(fName, fout=None, last=None, block_range=None):
    if fout == None:
        foutPath = fName[0].split('.txt')[0] + '_res.txt'
    else:
        foutPath = fout
        
    allLines = []
    for fItem in fName:
        f = open(fItem, 'r')
        thisAllLines = f.readlines()
        f.close()
        allLines.extend(thisAllLines)

    startOfBlock = True
    readParameters = False
    conditions = []
    conditionMeans = []
    averageType = []

    for i in range(len(allLines)):
        if allLines[i] == '+++++++++++++++++++++++++++++++++++++++++++++++++++++++\n':
            if startOfBlock == True:
                startOfBlock = False
                readParameters = True
                parameters = []
            elif startOfBlock == False:
                startOfBlock = True
                readParameters = False
                statsLine = allLines[i+4]
                statsLine = statsLine.split(',')[0]
                thisMean = statsLine.split('=')[1]

                if statsLine[0:9] == 'geometric' or statsLine[0:9] == 'Geometric':
                    avType = 'geometric'
                else:
                    avType = 'arithmetic'

                if len(conditions) == 0:
                    conditions.append(parameters)
                    conditionMeans.append([])
                    conditionMeans[0].append(float(thisMean))
                    averageType.append(avType)
                else:
                    if parameters in conditions:
                        j = conditions.index(parameters)
                        conditionMeans[j].append(float(thisMean))
                    else:
                        conditions.append(parameters)
                        conditionMeans.append([])
                        conditionMeans[(len(conditionMeans)-1)].append(float(thisMean))
                        averageType.append(avType)
                            
                        
                    
        if readParameters == True:
            parameters.append(allLines[i])

    
    fout = open(foutPath, 'w')
    cndM = []
    cndSe = []
    for i in range(len(conditions)):
        start, stop = getBlockRangeToProcess(last, block_range, conditionMeans[i])
        if averageType[i] == 'geometric':
            cndM.append(geoMean(conditionMeans[i][start:stop]))
            cndSe.append(geoSe(conditionMeans[i][start:stop]))
        elif averageType[i] == 'arithmetic':
            cndM.append(mean(conditionMeans[i][start:stop]))
            cndSe.append(se(conditionMeans[i][start:stop]))

        fout.write('************************************\n')
        fout.writelines(conditions[i][2:len(conditions[i])])
        fout.write('\n\n')
        for j in range(start,stop):
            #blk = j + start
            fout.write('%5.2f\n'%conditionMeans[i][j])
        fout.write('\n')
        if averageType[i] == 'geometric':
            fout.write('Geometric Mean = %5.2f \n'%cndM[i])
        elif averageType[i] == 'arithmetic':
            fout.write('Mean = %5.2f \n'%cndM[i])
        fout.write('SE = %5.2f \n\n'%cndSe[i])
        fout.write('\n')
    fout.close()


def processResultsAdaptiveInterleaved(fName, fout=None, last=None, block_range=None):

    if fout == None:
        foutPath = fName[0].split('.txt')[0] + '_res.txt'
    else:
        foutPath = fout
        
    allLines = []
    for fItem in fName:
        f = open(fItem, 'r')
        thisAllLines = f.readlines()
        f.close()
        allLines.extend(thisAllLines)
    ## f = open(fName, 'r')
    ## allLines = f.readlines() 
    ## f.close()
    startOfBlock = True
    readParameters = False
    conditions = []
    conditionMeans = []
    averageType = []

    for i in range(len(allLines)):
        if allLines[i] == '+++++++++++++++++++++++++++++++++++++++++++++++++++++++\n':
            if startOfBlock == True:
                startOfBlock = False
                readParameters = True
                parameters = []
            elif startOfBlock == False:
                startOfBlock = True
                readParameters = False
                trackMeans = []
                endOfBlock = False
                k = 1
                while endOfBlock == False:
                    if allLines[i+k].split(':')[0].split(' ')[0] == 'TRACK':
                    
                        trackNumber = int(allLines[i+k].split(':')[0].split(' ')[1])
                        statsLine = allLines[i+k+3]
                        statsLine = statsLine.split(',')[0]
                        thisMean = float(statsLine.split('=')[1])

                        if statsLine[0:9] == 'geometric':
                            avType = 'geometric'
                        else:
                            avType = 'arithmetic'
                    
                        trackMeans.append(thisMean)
                    if allLines[i+k] == '.\n':
                        endOfBlock = True
                    k = k+1
                if len(conditions) == 0:
                    conditions.append(parameters)
                    conditionMeans.append([])
                    for t in range(trackNumber):
                        conditionMeans[0].append([trackMeans[t]])
                    averageType.append(avType)
                else:
                    if parameters in conditions:
                        j = conditions.index(parameters)
                        for t in range(trackNumber):
                            conditionMeans[j][t].append(trackMeans[t])
                    else:
                        conditions.append(parameters)
                        conditionMeans.append([])
                        for t in range(trackNumber):
                            conditionMeans[(len(conditionMeans)-1)].append([trackMeans[t]])
                        averageType.append(avType)
                            
                        
                    
        if readParameters == True:
            parameters.append(allLines[i])
    
    cndM = []
    cndSe = []
    #foutPath = fName.split('.txt')[0] + '_res.txt'
    fout = open(foutPath, 'w')
    for i in range(len(conditions)):
        start, stop = getBlockRangeToProcess(last, block_range, conditionMeans[i][0])
        cndM.append([])
        cndSe.append([])
        currNTracks = len(conditionMeans[i])
        for t in range(currNTracks):
            if averageType[i] == 'geometric':
                cndM.append(geoMean(conditionMeans[i][t][start:stop]))
                cndSe.append(geoSe(conditionMeans[i][t][start:stop]))
            elif averageType[i] == 'arithmetic':
                cndM[i].append(mean(conditionMeans[i][t][start:stop]))
                cndSe[i].append(se(conditionMeans[i][t][start:stop]))
    
   
        fout.write('************************************\n')
        fout.writelines(conditions[i][2:len(conditions[i])]) 
        fout.write('\n\n')
        currNTracks = len(conditionMeans[i])
        for t in range(currNTracks):
            fout.write('----------\n')
            fout.write('TRACK {0}: \n'.format(t+1))
            for j in range(start, stop):
                fout.write('%5.2f\n'%conditionMeans[i][t][j])
            fout.write('\n')
            if averageType[i] == 'geometric':
                fout.write('Geometric Mean = %5.2f \n'%cndM[i][t])
            elif averageType[i] == 'arithmetic':
                fout.write('Mean = %5.2f \n'%cndM[i][t])
            fout.write('SE = %5.2f \n\n'%cndSe[i][t])
            fout.write('\n')
    fout.close()


def processResultsConstantMIntervalsNAlternatives(fName, fout=None, last=None, block_range=None):

    if fout == None:
        foutPath = fName[0].split('.txt')[0] + '_res.txt'
    else:
        foutPath = fout
        
    allLines = []
    for fItem in fName:
        f = open(fItem, 'r')
        thisAllLines = f.readlines()
        f.close()
        allLines.extend(thisAllLines)
    ## f = open(fName, 'r')
    ## allLines = f.readlines()
    ## f.close()
    startOfBlock = True
    readParameters = False
    conditions = []
    nAltList = []
    correctList = []
    totalList = []
  
    for i in range(len(allLines)):
        
        if allLines[i] == '+++++++++++++++++++++++++++++++++++++++++++++++++++++++\n' or allLines[i] == '+++++++++++++++++++++++++++++++++++++++++++++++++++++++\r\n':
            if startOfBlock == True:
                startOfBlock = False
                readParameters = True
                parameters = []
            elif startOfBlock == False:
                startOfBlock = True
                readParameters = False
                #endOfBlock = False

                statsLine_n_corr = allLines[i+2]
                statsLine_n_tot = allLines[i+3]
                thisNCorr = int(statsLine_n_corr.split('=')[1])
                thisNTot = int(statsLine_n_tot.split('=')[1])
                if len(conditions) == 0:
                    conditions.append(parameters)
                    for prLine in parameters:
                        if prLine.strip().split(":")[0].strip() == "Alternatives":
                            nAltList.append(int(prLine.strip().split(":")[1].strip()))
                    correctList.append([])
                    totalList.append([])

                    correctList[0].append(thisNCorr)
                    totalList[0].append(thisNTot)
                else:
                    if parameters in conditions:
                        j = conditions.index(parameters)
                        correctList[j].append(thisNCorr)
                        totalList[j].append(thisNTot)
                    else:
                        conditions.append(parameters)
                        for prLine in parameters:
                            if prLine.strip().split(":")[0].strip() == "Alternatives":
                                nAltList.append(int(prLine.strip().split(":")[1].strip()))
                        correctList.append([])
                        totalList.append([])
                       
                        correctList[(len(correctList)-1)].append(thisNCorr)
                        totalList[(len(totalList)-1)].append(thisNTot)
            
         
        if readParameters == True:
            parameters.append(allLines[i])


    cndCorrect = []
    cndTotal = []
    cndPropCorrect = []
    #foutPath = fName.split('.txt')[0] + '_res.txt'
    fout = open(foutPath, 'w')
    for i in range(len(conditions)):
        start, stop = getBlockRangeToProcess(last, block_range, correctList[i])
        cndCorrect.append(sum(correctList[i][start:stop]))
        cndTotal.append(sum(totalList[i][start:stop]))
        cndPropCorrect.append(sum(correctList[i][start:stop]) / sum(totalList[i][start:stop]))
     
        fout.write('************************************\n')
        fout.writelines(conditions[i][2:len(conditions[i])]) 
        fout.write('\n\n')
        for j in range(start, stop):
            thisPropCorr = correctList[i][j] / totalList[i][j]
            this_dp = dprime_mAFC(thisPropCorr, nAltList[i])
            fout.write('d-prime Block %d = %5.3f \n' %(j+1, this_dp))
           
        fout.write('\n')
        dp = dprime_mAFC(cndPropCorrect[i], nAltList[i])
        fout.write('No. Correct = %d \n'%cndCorrect[i])
        fout.write('No. Total = %d \n'%cndTotal[i])
        fout.write('Percent Correct = %5.2f \n'%(cndPropCorrect[i]*100))
        fout.write('d-prime = %5.3f \n\n'%(dp))

    fout.close()
    

def processResultsMultipleConstantsMIntervalsNAlternatives(fName, fout=None, last=None, block_range=None):

    if fout == None:
        foutPath = fName[0].split('.txt')[0] + '_res.txt'
    else:
        foutPath = fout
        
    allLines = []
    for fItem in fName:
        f = open(fItem, 'r')
        thisAllLines = f.readlines()
        f.close()
        allLines.extend(thisAllLines)
    ## f = open(fName, 'r')
    ## allLines = f.readlines()
    ## f.close()
    startOfBlock = True
    readParameters = False
    conditions = []
    conditionNames = []
    conditionCorrect = []
    conditionTotal = []
    nAltList = []
    blockSummaryType = 'pc'#'dprime' #calculating dprime for each block takes too long, give percent correct instead
  
    for i in range(len(allLines)):
        
        if allLines[i] == '+++++++++++++++++++++++++++++++++++++++++++++++++++++++\n' or allLines[i] == '+++++++++++++++++++++++++++++++++++++++++++++++++++++++\r\n':
            if startOfBlock == True:
                startOfBlock = False
                readParameters = True
                parameters = []
            elif startOfBlock == False:
                startOfBlock = True
                readParameters = False
                endOfBlock = False
                k = 1
                thisConditionName = []
                thisCorrect = []
                thisTotal = []
                while endOfBlock == False:
                    if allLines[i+k].split(',')[0] == 'CONDITION':
                        thisConditionName.append(allLines[i+k].split(',')[1].strip())
                        thisCorrect.append(int(float(allLines[i+k+1].split('=')[1].strip())))
                        thisTotal.append(int(float(allLines[i+k+2].split('=')[1].strip())))
                    
                    if allLines[i+k] == '.\n':
                        endOfBlock = True
                    k = k+1
                    conditionNumber = len(thisConditionName)
                if len(conditions) == 0:
                    conditions.append(parameters)
                    for prLine in parameters:
                        if prLine.strip().split(":")[0].strip() == "Alternatives":
                            nAltList.append(int(prLine.strip().split(":")[1].strip()))
                    conditionNames.append([])
                    conditionCorrect.append([])
                    conditionTotal.append([])
                    for t in range(conditionNumber):
                        conditionNames[0].append([thisConditionName[t]])
                        conditionCorrect[0].append([thisCorrect[t]])
                        conditionTotal[0].append([thisTotal[t]])
                else:
                    if parameters in conditions:
                        j = conditions.index(parameters)
                        for t in range(conditionNumber):
                            conditionNames[j][t].append(thisConditionName[t])
                            conditionCorrect[j][t].append(thisCorrect[t])
                            conditionTotal[j][t].append(thisTotal[t])
                    else:
                        conditions.append(parameters)
                        for prLine in parameters:
                            if prLine.strip().split(":")[0].strip() == "Alternatives":
                                nAltList.append(int(prLine.strip().split(":")[1].strip()))
                        conditionNames.append([])
                        conditionCorrect.append([])
                        conditionTotal.append([])
                        for t in range(conditionNumber):
                            conditionNames[(len(conditionNames)-1)].append([thisConditionName[t]])
                            conditionCorrect[(len(conditionCorrect)-1)].append([thisCorrect[t]])
                            conditionTotal[(len(conditionTotal)-1)].append([thisTotal[t]])


                        
         
        if readParameters == True:
            parameters.append(allLines[i])

    #foutPath = fName.split('.txt')[0] + '_res.txt'
    fout = open(foutPath, 'w')
    cndCorrect = []
    cndTotal = []
    cndPropCorrect = []
    for i in range(len(conditions)):
        start, stop = getBlockRangeToProcess(last, block_range, conditionNames[i][0])
        cndCorrect.append([])
        cndTotal.append([])
        cndPropCorrect.append([])
        thisNDifferences = len(conditionNames[i])
        for t in range(thisNDifferences):
            cndCorrect[i].append(sum(conditionCorrect[i][t][start:stop]))
            cndTotal[i].append(sum(conditionTotal[i][t][start:stop]))
            cndPropCorrect[i].append(cndCorrect[i][t]/cndTotal[i][t])
     
        fout.write('************************************\n')
        fout.writelines(conditions[i][2:len(conditions[i])]) 
        fout.write('\n\n')
           
        
        for t in range(thisNDifferences):
            fout.write('CONDITION %s\n' %(conditionNames[i][t][0]))
            for j in range(start, stop):
                print(start, stop, conditionNames[i], j)
                thisPropCorr = conditionCorrect[i][t][j] / conditionTotal[i][t][j]
                if blockSummaryType =='dprime':
                    this_dp = dprime_mAFC(thisPropCorr, nAltList[i])
                    fout.write('d-prime Block %d = %5.3f \n' %(j+1, this_dp))
                elif blockSummaryType == 'pc':
                    fout.write('Percent Correct Block %d = %5.2f \n' %(j+1, thisPropCorr*100))
            fout.write('\n')
           
            dp = dprime_mAFC(cndPropCorrect[i][t], nAltList[i])
            
            fout.write('No. Correct = %d \n'%cndCorrect[i][t])
            fout.write('No. Total = %d \n'%cndTotal[i][t])
            fout.write('Percent Correct = %5.2f \n'%(cndPropCorrect[i][t]*100))
            fout.write('d-prime = %5.3f \n' %(dp))
            fout.write('\n')

    fout.close()

def processResultsConstant1Interval2Alternatives(fName, fout=None, last=None, block_range=None, dprimeCorrection=True):

    if fout == None:
        foutPath = fName[0].split('.txt')[0] + '_res.txt'
    else:
        foutPath = fout
        
    allLines = []
    for fItem in fName:
        f = open(fItem, 'r')
        thisAllLines = f.readlines()
        f.close()
        allLines.extend(thisAllLines)
    #f = open(fName, 'r')
    #allLines = f.readlines()
    #f.close()
    startOfBlock = True
    readParameters = False
    conditions = []
    A_C = [] # condition A correct
    A_T = [] # condition A total
    B_C = []
    B_T = []

    for i in range(len(allLines)):
        
        if allLines[i] == '+++++++++++++++++++++++++++++++++++++++++++++++++++++++\n' or allLines[i] == '+++++++++++++++++++++++++++++++++++++++++++++++++++++++\r\n':
            if startOfBlock == True:
                startOfBlock = False
                readParameters = True
                parameters = []
            elif startOfBlock == False:
                startOfBlock = True
                readParameters = False
                statsLine_a_C = allLines[i+7]
                statsLine_a_T = allLines[i+8]
                statsLine_b_C = allLines[i+10]
                statsLine_b_T = allLines[i+11]
                n_a_C = float(statsLine_a_C.split('=')[1])
                n_b_C = float(statsLine_b_C.split('=')[1])
                n_a_T = float(statsLine_a_T.split('=')[1])
                n_b_T = float(statsLine_b_T.split('=')[1])
               
                if len(conditions) == 0:
                    conditions.append(parameters)
                    A_C.append([])
                    A_T.append([])
                    B_C.append([])
                    B_T.append([])
                    A_C[0].append(n_a_C)
                    A_T[0].append(n_a_T)
                    B_C[0].append(n_b_C)
                    B_T[0].append(n_b_T)
                  
                else:
                    if parameters in conditions:
                        j = conditions.index(parameters)
                        A_C[j].append(n_a_C)
                        A_T[j].append(n_a_T)
                        B_C[j].append(n_b_C)
                        B_T[j].append(n_b_T)
                    else:
                        conditions.append(parameters)
                        A_C.append([])
                        A_T.append([])
                        B_C.append([])
                        B_T.append([])
                        A_C[(len(A_C)-1)].append(n_a_C)
                        A_T[(len(A_C)-1)].append(n_a_T)
                        B_C[(len(A_C)-1)].append(n_b_C)
                        B_T[(len(A_C)-1)].append(n_b_T)
                    
        if readParameters == True:
            parameters.append(allLines[i])

    A_correct = []
    A_total = []
    B_correct = []
    B_total = []
    start = []
    stop = []

    #foutPath = fName.split('.txt')[0] + '_res.txt'
    fout = open(foutPath, 'w')

    for i in range(len(conditions)):
        start, stop = getBlockRangeToProcess(last, block_range, A_C[i])
        A_correct.append(sum(A_C[i][start:stop]))
        A_total.append(sum(A_T[i][start:stop]))
        B_correct.append(sum(B_C[i][start:stop]))
        B_total.append(sum(B_T[i][start:stop]))
   
        fout.write('************************************\n')
        fout.writelines(conditions[i][2:len(conditions[i])]) 
        fout.write('\n\n')
        for j in range(start, stop):
            this_dprime = dprime_yes_no_from_counts(nCA=A_C[i][j], nTA=A_T[i][j], nCB=B_C[i][j], nTB=B_T[i][j], corr=dprimeCorrection)
            fout.write('d-prime Block %d = %5.3f\n' %(j+1, this_dprime))
        fout.write('\n')
        
        dp = dprime_yes_no_from_counts(nCA=A_correct[i], nTA=A_total[i], nCB=B_correct[i], nTB=B_total[i], corr=dprimeCorrection)
        
        fout.write('No. Correct = %d \n'%(A_correct[i]+B_correct[i]))
        fout.write('No. Total = %d \n'%(A_total[i]+B_total[i]))
        fout.write('Percent Correct = %5.2f \n'%((A_correct[i]+B_correct[i])/(A_total[i]+B_total[i])*100))
        fout.write('d-prime = %5.3f \n'%dp)
        fout.write('\n')
        
        fout.write('No. Correct A = %d \n'%A_correct[i])
        fout.write('No. Total A = %d \n'%A_total[i])
        fout.write('Percent Correct A = %5.2f \n'%(A_correct[i]/A_total[i]*100))
        fout.write('No. Correct B = %d \n'%B_correct[i])
        fout.write('No. Total B = %d \n'%B_total[i])
        fout.write('Percent Correct B = %5.2f \n'%(B_correct[i]/B_total[i]*100))

        fout.write('\n')

      

       
    fout.close()
    

def processResultsMultipleConstants1Interval2Alternatives(fName, fout=None, last=None, block_range=None, dprimeCorrection=True):

    if fout == None:
        foutPath = fName[0].split('.txt')[0] + '_res.txt'
    else:
        foutPath = fout
        
    allLines = []
    for fItem in fName:
        f = open(fItem, 'r')
        thisAllLines = f.readlines()
        f.close()
        allLines.extend(thisAllLines)
    #f = open(fName, 'r')
    #allLines = f.readlines()
    #f.close()
    startOfBlock = True
    readParameters = False
    conditions = []
  
    A_C = [] # condition A correct
    A_T = [] # condition A total
    B_C = []
    B_T = []
    cLabels = []

    for i in range(len(allLines)):
        
        if allLines[i] == '+++++++++++++++++++++++++++++++++++++++++++++++++++++++\n' or allLines[i] == '+++++++++++++++++++++++++++++++++++++++++++++++++++++++\r\n':
            if startOfBlock == True:
                startOfBlock = False
                readParameters = True
                parameters = []
            elif startOfBlock == False:
                startOfBlock = True
                readParameters = False
                endOfBlock = False
                nCorrectA = []
                nTotalA = []
                nCorrectB = []
                nTotalB = []
                conditionLabel = []
                k = 1
                while endOfBlock == False:
                    if allLines[i+k].split(':')[0].split(' ')[0] == 'CONDITION':
                    
                        conditionLabel.append(allLines[i+k].split(':')[1])
                        ACorrectLine = allLines[i+k+6]
                        ATotalLine = allLines[i+k+7]
                        BCorrectLine = allLines[i+k+9]
                        BTotalLine = allLines[i+k+10]
                        nCorrectA.append([float(ACorrectLine.split('=')[1])])
                        nTotalA.append([float(ATotalLine.split('=')[1])])
                        nCorrectB.append([float(BCorrectLine.split('=')[1])])
                        nTotalB.append([float(BTotalLine.split('=')[1])])

                    if allLines[i+k] == '.\n':
                        endOfBlock = True
                    k = k+1
               
                if len(conditions) == 0:
                    conditions.append(parameters)
                    cLabels.append(conditionLabel)
                    A_C.append([])
                    A_T.append([])
                    B_C.append([])
                    B_T.append([])
                    A_C[0].extend(nCorrectA)
                    A_T[0].extend(nTotalA)
                    B_C[0].extend(nCorrectB)
                    B_T[0].extend(nTotalB)
                else:
                    if parameters in conditions:
                        j = conditions.index(parameters)
                        for l in range(len(A_C[j])):
                            A_C[j][l].extend(nCorrectA[l])
                            A_T[j][l].extend(nTotalA[l])
                            B_C[j][l].extend(nCorrectB[l])
                            B_T[j][l].extend(nTotalB[l])
                    else:
                        conditions.append(parameters)
                        A_C.append([])
                        A_T.append([])
                        B_C.append([])
                        B_T.append([])
                        cLabels.append(conditionLabel)
                        A_C[(len(A_C)-1)].extend(nCorrectA)
                        A_T[(len(A_C)-1)].extend(nTotalA)
                        B_C[(len(A_C)-1)].extend(nCorrectB)
                        B_T[(len(A_C)-1)].extend(nTotalB)
                    
        if readParameters == True:
            parameters.append(allLines[i])

    A_correct = []
    A_total = []
    B_correct = []
    B_total = []
    start = []
    stop = []

    #foutPath = fName.split('.txt')[0] + '_res.txt'
    fout = open(foutPath, 'w')

    for i in range(len(conditions)):
        start, stop = getBlockRangeToProcess(last, block_range, A_C[i][0])

        thisACorrect = []
        thisATotal = []
        thisBCorrect = []
        thisBTotal = []
        for k in range(len(cLabels[i])):
            thisACorrect.append(sum(A_C[i][k][start:stop]))
            thisATotal.append(sum(A_T[i][k][start:stop]))
            thisBCorrect.append(sum(B_C[i][k][start:stop]))
            thisBTotal.append(sum(B_T[i][k][start:stop]))
        A_correct.append(thisACorrect)
        A_total.append(thisATotal)
        B_correct.append(thisBCorrect)
        B_total.append(thisBTotal)
  
        fout.write('************************************\n')
        fout.writelines(conditions[i][2:len(conditions[i])]) 
        fout.write('\n\n')
        for k in range(len(cLabels[i])):
            fout.write('----------\n')
            fout.write('CONDITION:' + cLabels[i][k])# + '\n')
            for j in range(start, stop):
                this_dprime = dprime_yes_no_from_counts(nCA=A_C[i][k][j], nTA=A_T[i][k][j], nCB=B_C[i][k][j], nTB=B_T[i][k][j], corr=dprimeCorrection)
                fout.write('d-prime Block %d = %5.3f\n' %(j+1, this_dprime))
            fout.write('\n')

            dp = dprime_yes_no_from_counts(nCA=A_correct[i][k], nTA=A_total[i][k], nCB=B_correct[i][k], nTB=B_total[i][k], corr=dprimeCorrection)
            fout.write('No. Correct = %d \n'%(A_correct[i][k]+B_correct[i][k]))
            fout.write('No. Total = %d \n'%(A_total[i][k]+B_total[i][k]))
            fout.write('Percent Correct = %5.2f \n'%((A_correct[i][k]+B_correct[i][k])/(A_total[i][k]+B_total[i][k])*100))
            fout.write('d-prime = %5.3f \n'%dp)
            fout.write('\n')
            
            fout.write('No. Correct A = %d \n'%A_correct[i][k])
            fout.write('No. Total A = %d \n'%A_total[i][k])
            fout.write('Percent Correct A = %5.2f \n'%(A_correct[i][k]/A_total[i][k]*100))
            fout.write('No. Correct B = %d \n'%B_correct[i][k])
            fout.write('No. Total B = %d \n'%B_total[i][k])
            fout.write('Percent Correct B = %5.2f \n'%(B_correct[i][k]/B_total[i][k]*100))
         
            fout.write('\n')
    fout.close()



def processResultsConstant1PairSameDifferent(fName, fout=None, last=None, block_range=None, dprimeCorrection=True):

    if fout == None:
        foutPath = fName[0].split('.txt')[0] + '_res.txt'
    else:
        foutPath = fout
        
    allLines = []
    for fItem in fName:
        f = open(fItem, 'r')
        thisAllLines = f.readlines()
        f.close()
        allLines.extend(thisAllLines)
    #f = open(fName, 'r')
    #allLines = f.readlines()
    #f.close()
    startOfBlock = True
    readParameters = False
    conditions = []
    A_C = [] # condition A correct
    A_T = [] # condition A total
    B_C = []
    B_T = []

    for i in range(len(allLines)):
        
        if allLines[i] == '+++++++++++++++++++++++++++++++++++++++++++++++++++++++\n' or allLines[i] == '+++++++++++++++++++++++++++++++++++++++++++++++++++++++\r\n':
            if startOfBlock == True:
                startOfBlock = False
                readParameters = True
                parameters = []
            elif startOfBlock == False:
                startOfBlock = True
                readParameters = False
                statsLine_a_C = allLines[i+8]
                statsLine_a_T = allLines[i+9]
                statsLine_b_C = allLines[i+11]
                statsLine_b_T = allLines[i+12]
                n_a_C = float(statsLine_a_C.split('=')[1])
                n_b_C = float(statsLine_b_C.split('=')[1])
                n_a_T = float(statsLine_a_T.split('=')[1])
                n_b_T = float(statsLine_b_T.split('=')[1])
               
                if len(conditions) == 0:
                    conditions.append(parameters)
                    A_C.append([])
                    A_T.append([])
                    B_C.append([])
                    B_T.append([])
                    A_C[0].append(n_a_C)
                    A_T[0].append(n_a_T)
                    B_C[0].append(n_b_C)
                    B_T[0].append(n_b_T)
                  
                else:
                    if parameters in conditions:
                        j = conditions.index(parameters)
                        A_C[j].append(n_a_C)
                        A_T[j].append(n_a_T)
                        B_C[j].append(n_b_C)
                        B_T[j].append(n_b_T)
                    else:
                        conditions.append(parameters)
                        A_C.append([])
                        A_T.append([])
                        B_C.append([])
                        B_T.append([])
                        A_C[(len(A_C)-1)].append(n_a_C)
                        A_T[(len(A_C)-1)].append(n_a_T)
                        B_C[(len(A_C)-1)].append(n_b_C)
                        B_T[(len(A_C)-1)].append(n_b_T)
                    
        if readParameters == True:
            parameters.append(allLines[i])

    A_correct = []
    A_total = []
    B_correct = []
    B_total = []
    start = []
    stop = []

    #foutPath = fName.split('.txt')[0] + '_res.txt'
    fout = open(foutPath, 'w')

    for i in range(len(conditions)):
        start, stop = getBlockRangeToProcess(last, block_range, A_C[i])
     
        A_correct.append(sum(A_C[i][start:stop]))
        A_total.append(sum(A_T[i][start:stop]))
        B_correct.append(sum(B_C[i][start:stop]))
        B_total.append(sum(B_T[i][start:stop]))

        fout.write('************************************\n')
        fout.writelines(conditions[i][2:len(conditions[i])]) 
        fout.write('\n\n')
        for j in range(start, stop):
            thisdp_IO = dprime_SD_from_counts(nCA=A_C[i][j], nTA=A_T[i][j], nCB=B_C[i][j], nTB=B_T[i][j], meth='IO', corr=dprimeCorrection)
            thisdp_diff = dprime_SD_from_counts(nCA=A_C[i][j], nTA=A_T[i][j], nCB=B_C[i][j], nTB=B_T[i][j], meth='diff', corr=dprimeCorrection)
            fout.write('d-prime IO Block %d = %5.3f \n'%(j+1, thisdp_IO))
            fout.write('d-prime diff Block %d = %5.3f \n'%(j+1, thisdp_diff))
        fout.write('\n')

        dp_IO = dprime_SD_from_counts(nCA=A_correct[i], nTA=A_total[i], nCB=B_correct[i], nTB=B_total[i], meth='IO', corr=dprimeCorrection)
        dp_diff = dprime_SD_from_counts(nCA=A_correct[i], nTA=A_total[i], nCB=B_correct[i], nTB=B_total[i], meth='diff', corr=dprimeCorrection)

        fout.write('No. Correct = %d \n'%(A_correct[i]+B_correct[i]))
        fout.write('No. Total = %d \n'%(A_total[i]+B_total[i]))
        fout.write('Percent Correct = %5.2f \n'%((A_correct[i]+B_correct[i])/(A_total[i]+B_total[i])*100))
        fout.write('d-prime IO = %5.3f \n'%dp_IO)
        fout.write('d-prime diff = %5.3f \n'%dp_diff)
        fout.write('\n')
        
        fout.write('No. Correct A = %d \n'%A_correct[i])
        fout.write('No. Total A = %d \n'%A_total[i])
        fout.write('Percent Correct A = %5.2f \n'%(A_correct[i]/A_total[i]*100))
        fout.write('No. Correct B = %d \n'%B_correct[i])
        fout.write('No. Total B = %d \n'%B_total[i])
        fout.write('Percent Correct B = %5.2f \n'%(B_correct[i]/B_total[i]*100))
      
        fout.write('\n')
    fout.close()



    
#================================================    
#TABLE ADAPTIVE
def processResultsTableAdaptive(fName, fout=None, separator=';', last=None, block_range=None):
    """ Function to get summary statistics from the .csv result files in tabular format.
    Results files with data from different experiments can be processes as long as all
    the data have been collected with an adaptive procedure.

    fName: list of files to be processed
    fout : output file name
    separator: csv separator used in the files to be processed
    last : process only the last N blocks
    block-range : process only blocks in the given range
    """


    if fout == None:
        fNameOut = fName[0].split('.csv')[0] + '_processed.csv'
    else:
        fNameOut = fout
        
    allLines = []
    headline = ''
    for i in range(len(fName)):
        f = open(fName[i], 'r')
        thisAllLines = f.readlines()
        f.close()
        if i == 0:
            headline = thisAllLines[0]
            allLines.extend(thisAllLines)
        else:
            if thisAllLines[0] == headline:
                allLines.extend(thisAllLines[1:len(thisAllLines)])
            else:
                raise DifferentProceduresError("The files appear to contain data from different procedures. Cannot process.")

    fout = open(fNameOut, 'w')
    if checkMixedProceduresInTableFile(allLines, separator):
        fout.write("The table files appear to contain multiple headers.\n Usually this happens because they contain results from different experiments/procedures or \n different check box selections. These table processing functions cannot process these type of \n files, and automatic plots are not supported."+separator)
        fout.close()
        return
        
    
    dats = {}
    nHeaders = 0
    firstHeaderWord = ['threshold_geometric', 'threshold_arithmetic']
    
    for i in range(len(allLines)):
        if allLines[i].split(separator)[0].strip() in firstHeaderWord:
            procedure = allLines[i].split(separator)[0].strip().split('_')[1]
            nHeaders = nHeaders + 1
            dats['dats'+str(nHeaders)] = {}
            headerList = []
            for j in range(len(allLines[i].split(separator))):
                thisKey = allLines[i].split(separator)[j].strip()
                dats['dats'+str(nHeaders)][thisKey] = []
                headerList.append(thisKey)

            dats['dats'+str(nHeaders)]['procedure'] = procedure


        if nHeaders > 0 and allLines[i].split(separator)[0].strip() not in firstHeaderWord:
            threshFields = ['threshold_' + procedure]
            for j in range(len(headerList)):
                if headerList[j] in threshFields:
                    dats['dats'+str(nHeaders)][headerList[j]].append(float(allLines[i].split(separator)[j].strip()))
                else:
                    dats['dats'+str(nHeaders)][headerList[j]].append(allLines[i].split(separator)[j].strip())


    for i in range(len(dats)):
        procedure = dats['dats'+str(i+1)]['procedure']
        keysToRemove = ['SD']
        keysToRemove.extend(['session', 'date', 'time', 'duration', 'block', ''])
        datsLength = len(dats['dats'+str(i+1)]['listener'])
        #recursively for all different headers found
        dats['datspro'+str(i+1)] = {}

        #remove ephemeral keys 
        for j in range(len(keysToRemove)):
            if keysToRemove[j] in dats['dats'+str(i+1)]:
                del dats['dats'+str(i+1)][keysToRemove[j]]

        
        keysNotToCheck = ['threshold_' + procedure]
        keysNotToCheck.extend(['conditionAgglomerate', 'procedure'])
        
        standardKeys = ['condition', 'listener', 'experimentLabel', 'experiment']
        dats['dats'+str(i+1)]['conditionAgglomerate'] = ['' for i in range(len(dats['dats'+str(i+1)]['condition']))]
        for j in range(len(dats['dats'+str(i+1)]['condition'])):
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck:
                    dats['dats'+str(i+1)]['conditionAgglomerate'][j] = dats['dats'+str(i+1)]['conditionAgglomerate'][j] + dats['dats'+str(i+1)][key][j]

        for key in dats['dats'+str(i+1)]:
            if key not in keysNotToCheck:
                dats['datspro'+str(i+1)][key] = []
        fout.write('threshold_' + procedure + separator +\
                   'SE' + separator)
      
                       
                       
        #sort on the basis of condition-agglomerate
        cnds = list(set(dats['dats'+str(i+1)]['conditionAgglomerate']))
        dats['datspro'+str(i+1)]['threshold'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['SE'] = zeros(len(cnds))
      
        thresh = [[] for j in range(len(cnds))]
  
        for j in range(datsLength):
            cndIdx = cnds.index(dats['dats'+str(i+1)]['conditionAgglomerate'][j])
            thresh[cndIdx].append(dats['dats'+str(i+1)]['threshold_'+procedure][j])

        for item in standardKeys:
            fout.write(item + separator)
        for key in dats['dats'+str(i+1)]:
            if key not in keysNotToCheck and key not in standardKeys:
                fout.write(key + separator)
        fout.write('\n')  

        for j in range(len(cnds)):
            start, stop = getBlockRangeToProcess(last, block_range, thresh[j])
                
            if procedure == 'arithmetic':
                dats['datspro'+str(i+1)]['threshold'][j] =  mean(thresh[j][start:stop])
                dats['datspro'+str(i+1)]['SE'][j] =  se(thresh[j][start:stop])
            elif procedure == 'geometric':
                dats['datspro'+str(i+1)]['threshold'][j] =  geoMean(thresh[j][start:stop])
                dats['datspro'+str(i+1)]['SE'][j] =  geoSe(thresh[j][start:stop])
   
            cndIdx = dats['dats'+str(i+1)]['conditionAgglomerate'].index(cnds[j])
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck:
                    dats['datspro'+str(i+1)][key].append(dats['dats'+str(i+1)][key][cndIdx])


        for j in range(len(cnds)):
            fout.write(str(dats['datspro'+str(i+1)]['threshold'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['SE'][j]) + separator)
  
            for item in standardKeys:
                fout.write(dats['datspro'+str(i+1)][item][j] + separator)
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck and key not in standardKeys:
                    fout.write(dats['datspro'+str(i+1)][key][j] + separator)
            fout.write('\n')

    fout.close()


#================================================    
#TABLE ADAPTIVE INTERLEAVED
def processResultsTableAdaptiveInterleaved(fName, fout=None, separator=';', last=None, block_range=None):


    if fout == None:
        fNameOut = fName[0].split('.csv')[0] + '_processed.csv'
    else:
        fNameOut = fout
        
    allLines = []
    headline = ''
    for i in range(len(fName)):
        f = open(fName[i], 'r')
        thisAllLines = f.readlines()
        f.close()
        if i == 0:
            headline = thisAllLines[0]
            allLines.extend(thisAllLines)
        else:
            if thisAllLines[0] == headline:
                allLines.extend(thisAllLines[1:len(thisAllLines)])
            else:
                raise DifferentProceduresError("The files appear to contain data from different procedures. Cannot process.")

   
    fout = open(fNameOut, 'w')
    if checkMixedProceduresInTableFile(allLines, separator):
        fout.write("The table files appear to contain multiple headers.\n Usually this happens because they contain results from different experiments/procedures or \n different check box selections. These table processing functions cannot process these type of \n files, and automatic plots are not supported."+separator)
        fout.close()
        return

    dats = {}
    nHeaders = 0
    firstHeaderWord = ['threshold_geometric_track1', 'threshold_arithmetic_track1']
    
    for i in range(len(allLines)):

        if allLines[i].split(separator)[0].strip() in firstHeaderWord:

            procedure = allLines[i].split(separator)[0].strip().split('_')[1]
            nHeaders = nHeaders + 1
            dats['dats'+str(nHeaders)] = {}
            headerList = []
            nTracks = 0
            for j in range(len(allLines[i].split(separator))):
                thisKey = allLines[i].split(separator)[j].strip()
                if thisKey[0:9] == 'threshold':
                    nTracks = nTracks +1
                dats['dats'+str(nHeaders)][thisKey] = []
                headerList.append(thisKey)
            dats['dats'+str(nHeaders)]['nTracks'] = nTracks
            dats['dats'+str(nHeaders)]['procedure'] = procedure


        if nHeaders > 0 and allLines[i].split(separator)[0].strip() not in firstHeaderWord:
            threshFields = ['threshold_' + procedure + '_track' + str(t+1) for t in range(nTracks)]
            for j in range(len(headerList)):
                if headerList[j] in threshFields:
                    dats['dats'+str(nHeaders)][headerList[j]].append(float(allLines[i].split(separator)[j].strip()))
                else:
                    dats['dats'+str(nHeaders)][headerList[j]].append(allLines[i].split(separator)[j].strip())


    for i in range(len(dats)):
        procedure = dats['dats'+str(i+1)]['procedure']

        nTracks = dats['dats'+str(i+1)]['nTracks']

        keysToRemove = ['SD_track' + str(t+1) for t in range(dats['dats'+str(i+1)]['nTracks'])]
        keysToRemove.extend(['session', 'date', 'time', 'duration', 'block', ''])
        datsLength = len(dats['dats'+str(i+1)]['listener'])
        #recursively for all different headers found
        dats['datspro'+str(i+1)] = {}

        #remove ephemeral keys 
        for j in range(len(keysToRemove)):
            if keysToRemove[j] in dats['dats'+str(i+1)]:
                del dats['dats'+str(i+1)][keysToRemove[j]]

        
        keysNotToCheck = ['threshold_' + procedure + '_track' + str(t+1) for t in range(dats['dats'+str(i+1)]['nTracks'])]
        keysNotToCheck.extend(['conditionAgglomerate', 'nTracks', 'procedure'])
        
        standardKeys = ['condition', 'listener', 'experimentLabel', 'experiment']
        dats['dats'+str(i+1)]['conditionAgglomerate'] = ['' for i in range(len(dats['dats'+str(i+1)]['condition']))]
        for j in range(len(dats['dats'+str(i+1)]['condition'])):
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck:
                    dats['dats'+str(i+1)]['conditionAgglomerate'][j] = dats['dats'+str(i+1)]['conditionAgglomerate'][j] + dats['dats'+str(i+1)][key][j]

        for key in dats['dats'+str(i+1)]:
            if key not in keysNotToCheck:
                dats['datspro'+str(i+1)][key] = []
        for t in range(dats['dats'+str(i+1)]['nTracks']):
            fout.write('threshold track' + str(t+1) + separator +\
                       'SE track' + str(t+1) + separator)
      
                       
        #sort on the basis of condition-agglomerate
        cnds = list(set(dats['dats'+str(i+1)]['conditionAgglomerate']))
        for t in range(dats['dats'+str(i+1)]['nTracks']):
            dats['datspro'+str(i+1)]['threshold_track'+str(t+1)] = zeros(len(cnds))
            dats['datspro'+str(i+1)]['SE_track'+str(t+1)] = zeros(len(cnds))
      
        thresh = [[[] for t in range(dats['dats'+str(i+1)]['nTracks'])] for j in range(len(cnds))]
  
        for j in range(datsLength):
            cndIdx = cnds.index(dats['dats'+str(i+1)]['conditionAgglomerate'][j])
            for t in range(dats['dats'+str(i+1)]['nTracks']):
                thresh[cndIdx][t].append(dats['dats'+str(i+1)]['threshold_' + procedure + '_track'+str(t+1)][j])

        for item in standardKeys:
            fout.write(item + separator)
        for key in dats['dats'+str(i+1)]:
            if key not in keysNotToCheck and key not in standardKeys:
                fout.write(key + separator)
        fout.write('\n')

        for j in range(len(cnds)):
            start, stop = getBlockRangeToProcess(last, block_range, thresh[j][0])
            
            for t in range(dats['dats'+str(i+1)]['nTracks']):
                if procedure == 'arithmetic':
                    dats['datspro'+str(i+1)]['threshold_track'+str(t+1)][j] =  mean(thresh[j][t][start:stop])
                    dats['datspro'+str(i+1)]['SE_track'+str(t+1)][j] =  se(thresh[j][t][start:stop])
                elif procedure == 'geometric':
                    dats['datspro'+str(i+1)]['threshold_track'+str(t+1)][j] =  geoMean(thresh[j][t][start:stop])
                    dats['datspro'+str(i+1)]['SE_track'+str(t+1)][j] =  geoSe(thresh[j][t][start:stop])
   
            
            cndIdx = dats['dats'+str(i+1)]['conditionAgglomerate'].index(cnds[j])
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck:
                    dats['datspro'+str(i+1)][key].append(dats['dats'+str(i+1)][key][cndIdx])

            for t in range(dats['dats'+str(i+1)]['nTracks']):
                fout.write(str(dats['datspro'+str(i+1)]['threshold_track'+str(t+1)][j]) + separator +\
                           str(dats['datspro'+str(i+1)]['SE_track'+str(t+1)][j]) + separator)
  
            for item in standardKeys:
                fout.write(dats['datspro'+str(i+1)][item][j] + separator)
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck and key not in standardKeys:
                    fout.write(dats['datspro'+str(i+1)][key][j] + separator)
            fout.write('\n')

    fout.close()

#================================================    
#TABLE CONSTANT M-INT N-ALT
def processResultsTableConstantMIntNAlt(fName, fout=None, separator=';', last=None, block_range=None):    
    
    if fout == None:
        fNameOut = fName[0].split('.csv')[0] + '_processed.csv'
    else:
        fNameOut = fout
        
    allLines = []
    headline = ''
    for i in range(len(fName)):
        f = open(fName[i], 'r')
        thisAllLines = f.readlines()
        f.close()
        if i == 0:
            headline = thisAllLines[0]
            allLines.extend(thisAllLines)
        else:
            if thisAllLines[0] == headline:
                allLines.extend(thisAllLines[1:len(thisAllLines)])
            else:
                raise DifferentProceduresError("The files appear to contain data from different procedures. Cannot process.")


    fout = open(fNameOut, 'w')
    if checkMixedProceduresInTableFile(allLines, separator):
        fout.write("The table files appear to contain multiple headers.\n Usually this happens because they contain results from different experiments/procedures or \n different check box selections. These table processing functions cannot process these type of \n files, and automatic plots are not supported."+separator)
        fout.close()
        return
    
    dats = {}
    nHeaders = 0
    firstHeaderWord = 'dprime'
    
    for i in range(len(allLines)):
         if allLines[i].split(separator)[0].strip() == firstHeaderWord:
              nHeaders = nHeaders + 1
              dats['dats'+str(nHeaders)] = {}
              headerList = []

              for j in range(len(allLines[i].split(separator))):
                   thisKey = allLines[i].split(separator)[j].strip()
                   dats['dats'+str(nHeaders)][thisKey] = []
                   headerList.append(thisKey)


         if nHeaders > 0 and allLines[i].split(separator)[0].strip() != firstHeaderWord:
              for j in range(len(headerList)):
                   numFields = ['n_corr', 'n_trials', 'nAlternatives', 'nIntervals']
                   if headerList[j] in numFields:
                        dats['dats'+str(nHeaders)][headerList[j]].append(int(allLines[i].split(separator)[j].strip()))
                   else:
                        dats['dats'+str(nHeaders)][headerList[j]].append(allLines[i].split(separator)[j].strip())

    for i in range(len(dats)):

        keysToRemove = ['dprime', 'perc_corr', 'session', 'date', 'time', 'duration', 'block', '']
        datsLength = len(dats['dats'+str(i+1)]['listener'])
        #recursively for all different headers found
        dats['datspro'+str(i+1)] = {}

        #remove ephemeral keys 
        for j in range(len(keysToRemove)):
            if keysToRemove[j] in dats['dats'+str(i+1)]:
                del dats['dats'+str(i+1)][keysToRemove[j]]

        
        keysNotToCheck = ['n_corr', 'n_trials', 'conditionAgglomerate']
        
        standardKeys = ['condition', 'listener', 'experimentLabel', 'experiment', 'nIntervals', 'nAlternatives']
        dats['dats'+str(i+1)]['conditionAgglomerate'] = ['' for i in range(len(dats['dats'+str(i+1)]['condition']))]
        for j in range(len(dats['dats'+str(i+1)]['condition'])):
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck:
                    if key in numFields:
                        dats['dats'+str(i+1)]['conditionAgglomerate'][j] = dats['dats'+str(i+1)]['conditionAgglomerate'][j] + str(dats['dats'+str(i+1)][key][j])
                    else:
                        dats['dats'+str(i+1)]['conditionAgglomerate'][j] = dats['dats'+str(i+1)]['conditionAgglomerate'][j] + dats['dats'+str(i+1)][key][j]

        for key in dats['dats'+str(i+1)]:
            if key not in keysNotToCheck:
                dats['datspro'+str(i+1)][key] = []
      
        fout.write('dprime' + separator +\
                    'perc_corr' + separator +\
                   'n_corr' + separator +\
                   'n_trials' + separator)
      
                       
                       
        #sort on the basis of condition-agglomerate
        cnds = list(set(dats['dats'+str(i+1)]['conditionAgglomerate']))
        dats['datspro'+str(i+1)]['dprime'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['perc_corr'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['n_corr'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['n_trials'] = zeros(len(cnds))
      
        nCorr = [[] for j in range(len(cnds))]
        nTrials = [[] for j in range(len(cnds))]
        nAlt = [[] for j in range(len(cnds))]
        for j in range(datsLength):
            cndIdx = cnds.index(dats['dats'+str(i+1)]['conditionAgglomerate'][j])
            nCorr[cndIdx].append(dats['dats'+str(i+1)]['n_corr'][j])
            nTrials[cndIdx].append(dats['dats'+str(i+1)]['n_trials'][j])
            nAlt[cndIdx].append(dats['dats'+str(i+1)]['nAlternatives'][j])

  
        for item in standardKeys:
            fout.write(item + separator)
            #print('Item: ', item)
        for key in dats['dats'+str(i+1)]:
            if key not in keysNotToCheck and key not in standardKeys:
                fout.write(key + separator)
                #print('Key: ', key)
        fout.write('\n')
        
        for j in range(len(cnds)):
            start, stop = getBlockRangeToProcess(last, block_range, nCorr[j])
            
            dats['datspro'+str(i+1)]['n_corr'][j] =  sum(nCorr[j][start:stop])
            dats['datspro'+str(i+1)]['n_trials'][j] =  sum(nTrials[j][start:stop])
            dats['datspro'+str(i+1)]['perc_corr'][j] =  dats['datspro'+str(i+1)]['n_corr'][j] / dats['datspro'+str(i+1)]['n_trials'][j] * 100
            
            dats['datspro'+str(i+1)]['dprime'][j] = dprime_mAFC(dats['datspro'+str(i+1)]['n_corr'][j] / dats['datspro'+str(i+1)]['n_trials'][j], nAlt[j][0])
            cndIdx = dats['dats'+str(i+1)]['conditionAgglomerate'].index(cnds[j])
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck:
                    dats['datspro'+str(i+1)][key].append(dats['dats'+str(i+1)][key][cndIdx])


            fout.write(str(dats['datspro'+str(i+1)]['dprime'][j]) + separator +\
                        str(dats['datspro'+str(i+1)]['perc_corr'][j]) + separator +\
                        str(dats['datspro'+str(i+1)]['n_corr'][j]) + separator +\
                        str(dats['datspro'+str(i+1)]['n_trials'][j]) + separator)
  
            for item in standardKeys:
                fout.write(str(dats['datspro'+str(i+1)][item][j]) + separator)
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck and key not in standardKeys:
                    fout.write(str(dats['datspro'+str(i+1)][key][j]) + separator)
            fout.write('\n')

    fout.close()
                  


def processResultsTableMultipleConstantsMIntNAlt(fName, fout=None, separator=';', last=None, block_range=None):

    if fout == None:
        fNameOut = fName[0].split('.csv')[0] + '_processed.csv'
    else:
        fNameOut = fout
        
    allLines = []
    headline = ''
    for i in range(len(fName)):
        f = open(fName[i], 'r')
        thisAllLines = f.readlines()
        f.close()
        if i == 0:
            headline = thisAllLines[0]
            allLines.extend(thisAllLines)
        else:
            if thisAllLines[0] == headline:
                allLines.extend(thisAllLines[1:len(thisAllLines)])
            else:
                raise DifferentProceduresError("The files appear to contain data from different procedures. Cannot process.")
            
    fout = open(fNameOut, 'w')
    if checkMixedProceduresInTableFile(allLines, separator):
        fout.write("The table files appear to contain multiple headers.\n Usually this happens because they contain results from different experiments/procedures or \n different check box selections. These table processing functions cannot process these type of \n files, and automatic plots are not supported."+separator)
        fout.close()
        return
    
    dats = {}
    nHeaders = 0
    firstHeaderWord = 'dprime_subc1'
    
    for i in range(len(allLines)):
         if allLines[i].split(separator)[0].strip() == firstHeaderWord:
              nHeaders = nHeaders + 1
              dats['dats'+str(nHeaders)] = {}
              headerList = []
              nSubcond = 0
              for j in range(len(allLines[i].split(separator))):
                   thisKey = allLines[i].split(separator)[j].strip()
                   dats['dats'+str(nHeaders)][thisKey] = []
                   headerList.append(thisKey)
                   if thisKey[0:11] == 'dprime_subc':
                        nSubcond = nSubcond +1
              dats['dats'+str(nHeaders)]['nSubcond'] = nSubcond


         if nHeaders > 0 and allLines[i].split(separator)[0].strip() != firstHeaderWord:
              for j in range(len(headerList)):
                   numFields = ['n_corr_subc' + str(t+1) for t in range(nSubcond)]
                   numFields.extend(['n_trials_subc' + str(t+1) for t in range(nSubcond)])
                   numFields.extend(['tot_n_corr', 'tot_n_trials', 'nAlternatives', 'nIntervals'])
                   if headerList[j] in numFields:
                        dats['dats'+str(nHeaders)][headerList[j]].append(int(allLines[i].split(separator)[j].strip()))
                   else:
                        dats['dats'+str(nHeaders)][headerList[j]].append(allLines[i].split(separator)[j].strip())

     
    for i in range(len(dats)):
        nSubcond = dats['dats'+str(i+1)]['nSubcond']

        keysToRemove = ['perc_corr_subc' + str(t+1) for t in range(nSubcond)]
        keysToRemove.extend(['dprime_subc' + str(t+1) for t in range(nSubcond)])
        keysToRemove.extend(['tot_dprime', 'tot_perc_corr', 'session', 'date', 'time', 'duration', 'block', ''])
        datsLength = len(dats['dats'+str(i+1)]['listener'])
        #recursively for all different headers found
        dats['datspro'+str(i+1)] = {}

        #remove ephemeral keys 
        for j in range(len(keysToRemove)):
            if keysToRemove[j] in dats['dats'+str(i+1)]:
                del dats['dats'+str(i+1)][keysToRemove[j]]

        
        keysNotToCheck = ['n_corr_subc' + str(t+1) for t in range(nSubcond)]
        keysNotToCheck.extend(['n_trials_subc' + str(t+1) for t in range(nSubcond)])
        keysNotToCheck.extend(['tot_n_corr', 'tot_n_trials', 'conditionAgglomerate', 'nSubcond'])
        
        standardKeys = ['condition', 'listener', 'experimentLabel', 'experiment', 'nAlternatives', 'nIntervals']
        dats['dats'+str(i+1)]['conditionAgglomerate'] = ['' for i in range(len(dats['dats'+str(i+1)]['condition']))]
        for j in range(len(dats['dats'+str(i+1)]['condition'])):
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck:
                    if key in numFields:
                        dats['dats'+str(i+1)]['conditionAgglomerate'][j] = dats['dats'+str(i+1)]['conditionAgglomerate'][j] + str(dats['dats'+str(i+1)][key][j])
                    else:
                        dats['dats'+str(i+1)]['conditionAgglomerate'][j] = dats['dats'+str(i+1)]['conditionAgglomerate'][j] + dats['dats'+str(i+1)][key][j]

        for key in dats['dats'+str(i+1)]:
            if key not in keysNotToCheck:
                dats['datspro'+str(i+1)][key] = []
        for t in range(nSubcond):
            fout.write('dprime_subc' + str(t+1) + separator +\
                       'perc_corr_subc' + str(t+1) + separator +\
                       'n_corr_subc' + str(t+1) + separator +\
                       'n_trials_subc' + str(t+1) + separator)
        fout.write('tot_dprime' + separator +\
                   'tot_perc_corr' + separator +\
                   'tot_n_corr' + separator +\
                   'tot_n_trials' + separator)
      
                       
                       
        #sort on the basis of condition-agglomerate
        cnds = list(set(dats['dats'+str(i+1)]['conditionAgglomerate']))
        for t in range(nSubcond):
            dats['datspro'+str(i+1)]['perc_corr_subc'+str(t+1)] = zeros(len(cnds))
            dats['datspro'+str(i+1)]['n_corr_subc'+str(t+1)] = zeros(len(cnds))
            dats['datspro'+str(i+1)]['n_trials_subc'+str(t+1)] = zeros(len(cnds))
            dats['datspro'+str(i+1)]['dprime_subc'+str(t+1)] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['tot_perc_corr'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['tot_n_corr'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['tot_n_trials'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['tot_dprime'] = zeros(len(cnds))
        
        nCorr = [[[] for t in range(nSubcond)] for j in range(len(cnds))]
        nTrials = [[[] for t in range(nSubcond)] for j in range(len(cnds))]

        nCorrTot = [[] for j in range(len(cnds))]
        nTrialsTot = [[]for j in range(len(cnds))]
        nAlt = [[]for j in range(len(cnds))]
  
        for j in range(datsLength):
            cndIdx = cnds.index(dats['dats'+str(i+1)]['conditionAgglomerate'][j])
            for t in range(nSubcond):
                nCorr[cndIdx][t].append(dats['dats'+str(i+1)]['n_corr_subc' + str(t+1)][j])
                nTrials[cndIdx][t].append(dats['dats'+str(i+1)]['n_trials_subc' + str(t+1)][j])

            nCorrTot[cndIdx].append(dats['dats'+str(i+1)]['tot_n_corr'][j])
            nTrialsTot[cndIdx].append(dats['dats'+str(i+1)]['tot_n_trials'][j])
            nAlt[cndIdx].append(dats['dats'+str(i+1)]['nAlternatives'][j])


        for item in standardKeys:
                fout.write(item + separator)
        for key in dats['dats'+str(i+1)]:
            if key not in keysNotToCheck and key not in standardKeys:
                fout.write(key + separator)
        fout.write('\n')
      
        for j in range(len(cnds)):
            start, stop = getBlockRangeToProcess(last, block_range, nCorr[j][0])
            
            for t in range(nSubcond):
                
                dats['datspro'+str(i+1)]['n_corr_subc'+str(t+1)][j] =  sum(nCorr[j][t][start:stop])
                dats['datspro'+str(i+1)]['n_trials_subc'+str(t+1)][j] =  sum(nTrials[j][t][start:stop])
                thisPropCorr = dats['datspro'+str(i+1)]['n_corr_subc'+str(t+1)][j] / dats['datspro'+str(i+1)]['n_trials_subc'+str(t+1)][j]
                dats['datspro'+str(i+1)]['perc_corr_subc'+str(t+1)][j] =   thisPropCorr * 100
                dats['datspro'+str(i+1)]['dprime_subc'+str(t+1)][j] = dprime_mAFC(thisPropCorr, nAlt[j][0])
            dats['datspro'+str(i+1)]['tot_n_corr'][j] =  sum(nCorrTot[j][start:stop])
            dats['datspro'+str(i+1)]['tot_n_trials'][j] =  sum(nTrialsTot[j][start:stop])
            totPropCorr = dats['datspro'+str(i+1)]['tot_n_corr'][j] / dats['datspro'+str(i+1)]['tot_n_trials'][j]
            dats['datspro'+str(i+1)]['tot_perc_corr'][j] =   totPropCorr * 100
            dats['datspro'+str(i+1)]['tot_dprime'][j] =   dprime_mAFC(totPropCorr, nAlt[j][0])
               
            
            cndIdx = dats['dats'+str(i+1)]['conditionAgglomerate'].index(cnds[j])
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck:
                    dats['datspro'+str(i+1)][key].append(dats['dats'+str(i+1)][key][cndIdx])

       
            for t in range(nSubcond):
                fout.write(str(dats['datspro'+str(i+1)]['dprime_subc'+str(t+1)][j]) + separator +\
                           str(dats['datspro'+str(i+1)]['perc_corr_subc'+str(t+1)][j]) + separator +\
                           str(dats['datspro'+str(i+1)]['n_corr_subc'+str(t+1)][j]) + separator +\
                           str(dats['datspro'+str(i+1)]['n_trials_subc'+str(t+1)][j]) + separator)
            fout.write(str(dats['datspro'+str(i+1)]['tot_dprime'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['tot_perc_corr'][j]) + separator +\
                           str(dats['datspro'+str(i+1)]['tot_n_corr'][j]) + separator +\
                           str(dats['datspro'+str(i+1)]['tot_n_trials'][j]) + separator)
  
            for item in standardKeys:
                if item in numFields:
                    fout.write(str(dats['datspro'+str(i+1)][item][j]) + separator)
                else:
                    fout.write(dats['datspro'+str(i+1)][item][j] + separator)
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck and key not in standardKeys:
                    fout.write(dats['datspro'+str(i+1)][key][j] + separator)
            fout.write('\n')

    fout.close()
                  


#================================================    
#TABLE CONSTANT 1INT2ALT
def processResultsTableConstant1Int2Alt(fName, fout=None, separator=';', last=None, block_range=None, dprimeCorrection=True):

    if fout == None:
        fNameOut = fName[0].split('.csv')[0] + '_processed.csv'
    else:
        fNameOut = fout
        
    allLines = []
    headline = ''
    for i in range(len(fName)):
        f = open(fName[i], 'r')
        thisAllLines = f.readlines()
        f.close()
        if i == 0:
            headline = thisAllLines[0]
            allLines.extend(thisAllLines)
        else:
            if thisAllLines[0] == headline:
                allLines.extend(thisAllLines[1:len(thisAllLines)])
            else:
                raise DifferentProceduresError("The files appear to contain data from different procedures. Cannot process.")
    
    
    fout = open(fNameOut, 'w')
    if checkMixedProceduresInTableFile(allLines, separator):
        fout.write("The table files appear to contain multiple headers.\n Usually this happens because they contain results from different experiments/procedures or \n different check box selections. These table processing functions cannot process these type of \n files, and automatic plots are not supported."+separator)
        fout.close()
        return
    dats = {}
    nHeaders = 0
    firstHeaderWord = 'dprime'
    
    for i in range(len(allLines)):
        if allLines[i].split(separator)[0].strip() == firstHeaderWord:
            nHeaders = nHeaders + 1
            dats['dats'+str(nHeaders)] = {}
            headerList = []
            for j in range(len(allLines[i].split(separator))):
                thisKey = allLines[i].split(separator)[j].strip()
                dats['dats'+str(nHeaders)][thisKey] = []
                headerList.append(thisKey)


        if nHeaders > 0 and allLines[i].split(separator)[0].strip() != firstHeaderWord:
            for j in range(len(headerList)):
                if headerList[j] in ['nCorrectA', 'nCorrectB', 'nTotalA', 'nTotalB', 'nCorrect', 'nTotal']:
                    dats['dats'+str(nHeaders)][headerList[j]].append(int(allLines[i].split(separator)[j].strip()))
                else:
                    dats['dats'+str(nHeaders)][headerList[j]].append(allLines[i].split(separator)[j].strip())

    
    keysToRemove = ['dprime', 'session', 'date', 'time', 'duration', 'block', '']
    for i in range(len(dats)):
        datsLength = len(dats['dats'+str(i+1)]['listener'])
        #recursively for all different headers found
        dats['datspro'+str(i+1)] = {}

        #remove ephemeral keys 
        for j in range(len(keysToRemove)):
            if keysToRemove[j] in dats['dats'+str(i+1)]:
                del dats['dats'+str(i+1)][keysToRemove[j]]
    
         
        keysNotToCheck = ['nCorrectA', 'nTotalA', 'nCorrectB', 'nTotalB', 'nCorrect', 'nTotal', 'conditionAgglomerate']
        standardKeys = ['condition', 'listener', 'experimentLabel', 'experiment']
        dats['dats'+str(i+1)]['conditionAgglomerate'] = ['' for i in range(len(dats['dats'+str(i+1)]['condition']))]
        for j in range(len(dats['dats'+str(i+1)]['condition'])):
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck:
                    dats['dats'+str(i+1)]['conditionAgglomerate'][j] = dats['dats'+str(i+1)]['conditionAgglomerate'][j] + dats['dats'+str(i+1)][key][j]

        for key in dats['dats'+str(i+1)]:
            if key not in keysNotToCheck:
                dats['datspro'+str(i+1)][key] = []
        fout.write('dprime' + separator +\
                   'nTotal' + separator +\
                   'nCorrectA' + separator +\
                   'nTotalA' + separator +\
                   'nCorrectB' + separator +\
                   'nTotalB' + separator )
                       
                       
        #sort on the basis of condition-agglomerate
        cnds = list(set(dats['dats'+str(i+1)]['conditionAgglomerate']))
        dats['datspro'+str(i+1)]['dprime'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['nCorrectA'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['nCorrectB'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['nTotalA'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['nTotalB'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['nTotal'] = zeros(len(cnds))
        nCorrectA = [[] for j in range(len(cnds))]
        nTotalA = [[] for j in range(len(cnds))]
        nCorrectB = [[] for j in range(len(cnds))]
        nTotalB = [[] for j in range(len(cnds))]
        nTotal = [[] for j in range(len(cnds))]
        for j in range(datsLength):
            cndIdx = cnds.index(dats['dats'+str(i+1)]['conditionAgglomerate'][j])
            nCorrectA[cndIdx].append(dats['dats'+str(i+1)]['nCorrectA'][j])
            nTotalA[cndIdx].append(dats['dats'+str(i+1)]['nTotalA'][j])
            nCorrectB[cndIdx].append(dats['dats'+str(i+1)]['nCorrectB'][j])
            nTotalB[cndIdx].append(dats['dats'+str(i+1)]['nTotalB'][j])
            nTotal[cndIdx].append(dats['dats'+str(i+1)]['nTotal'][j])


        for item in standardKeys:
            fout.write(item + separator)
        for key in dats['dats'+str(i+1)]:
            if key not in keysNotToCheck and key not in standardKeys:
                fout.write(key + separator)
        fout.write('\n')

        for j in range(len(cnds)):
            start, stop = getBlockRangeToProcess(last, block_range, nCorrectA[j])
            
            dats['datspro'+str(i+1)]['nCorrectA'][j] = sum(nCorrectA[j][start:stop])
            dats['datspro'+str(i+1)]['nTotalA'][j] =  sum(nTotalA[j][start:stop])
            dats['datspro'+str(i+1)]['nCorrectB'][j] =  sum(nCorrectB[j][start:stop])
            dats['datspro'+str(i+1)]['nTotalB'][j] =  sum(nTotalB[j][start:stop])
            dats['datspro'+str(i+1)]['nTotal'][j] =  sum(nTotal[j][start:stop])
            dats['datspro'+str(i+1)]['dprime'][j] = dp = dprime_yes_no_from_counts(nCA=dats['datspro'+str(i+1)]['nCorrectA'][j], nTA=dats['datspro'+str(i+1)]['nTotalA'][j], nCB=dats['datspro'+str(i+1)]['nCorrectB'][j], nTB=dats['datspro'+str(i+1)]['nTotalB'][j], corr=dprimeCorrection)
            
            
            cndIdx = dats['dats'+str(i+1)]['conditionAgglomerate'].index(cnds[j])
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck:
                    dats['datspro'+str(i+1)][key].append(dats['dats'+str(i+1)][key][cndIdx])

    
            fout.write(str(dats['datspro'+str(i+1)]['dprime'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['nTotal'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['nCorrectA'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['nTotalA'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['nCorrectB'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['nTotalB'][j]) + separator)
            for item in standardKeys:
                fout.write(dats['datspro'+str(i+1)][item][j] + separator)
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck and key not in standardKeys:
                    fout.write(dats['datspro'+str(i+1)][key][j] + separator)
            fout.write('\n')

    fout.close()


#================================================    
#TABLE MULTIPLE CONSTANTs 1INT2ALT
def processResultsTableMultipleConstants1Int2Alt(fName, fout=None, separator=';', last=None, block_range=None, dprimeCorrection=True):

    if fout == None:
        fNameOut = fName[0].split('.csv')[0] + '_processed.csv'
    else:
        fNameOut = fout
        
    allLines = []
    headline = ''
    for i in range(len(fName)):
        f = open(fName[i], 'r')
        thisAllLines = f.readlines()
        f.close()
        if i == 0:
            headline = thisAllLines[0]
            allLines.extend(thisAllLines)
        else:
            if thisAllLines[0] == headline:
                allLines.extend(thisAllLines[1:len(thisAllLines)])
            else:
                raise DifferentProceduresError("The files appear to contain data from different procedures. Cannot process.")
    
    
    fout = open(fNameOut, 'w')
    if checkMixedProceduresInTableFile(allLines, separator):
        fout.write("The table files appear to contain multiple headers.\n Usually this happens because they contain results from different experiments/procedures or \n different check box selections. These table processing functions cannot process these type of \n files, and automatic plots are not supported."+separator)
        fout.close()
        return
    dats = {}
    nHeaders = 0
    firstHeaderWord = 'dprime_ALL'
    for i in range(len(allLines)):
        if allLines[i].split(separator)[0].strip() == firstHeaderWord:
            nHeaders = nHeaders + 1
            dats['dats'+str(nHeaders)] = {}
            headerList = []
            nSubcond = -1 #we'll count them with dprime_ but that counts also the dprime for all conditions
            for j in range(len(allLines[i].split(separator))):
                thisKey = allLines[i].split(separator)[j].strip()
                if thisKey[0:7] == 'dprime_':
                    nSubcond = nSubcond +1
                dats['dats'+str(nHeaders)][thisKey] = []
                headerList.append(thisKey)
            dats['dats'+str(nHeaders)]['nSubcond'] = nSubcond


        if nHeaders > 0 and allLines[i].split(separator)[0].strip() != firstHeaderWord:
            numericFields = ['nCorrectA_ALL', 'nCorrectB_ALL', 'nTotalA_ALL', 'nTotalB_ALL', 'nCorrect_ALL', 'nTotal_ALL']
            numericFields.extend(['nCorrectA_subc' + str(t+1) for t in range(nSubcond)])
            numericFields.extend(['nCorrectB_subc' + str(t+1) for t in range(nSubcond)])
            numericFields.extend(['nTotalA_subc' + str(t+1) for t in range(nSubcond)])
            numericFields.extend(['nTotalB_subc' + str(t+1) for t in range(nSubcond)])
            numericFields.extend(['nCorrect_subc' + str(t+1) for t in range(nSubcond)])
            numericFields.extend(['nTotal_subc' + str(t+1) for t in range(nSubcond)])
            for j in range(len(headerList)):
                if headerList[j] in numericFields:
                    dats['dats'+str(nHeaders)][headerList[j]].append(int(allLines[i].split(separator)[j].strip()))
                else:
                    dats['dats'+str(nHeaders)][headerList[j]].append(allLines[i].split(separator)[j].strip())

    
   
    for i in range(len(dats)):
        keysToRemove = ['dprime_ALL', 'session', 'date', 'time', 'duration', 'block', '']
        for t in range(dats['dats'+str(i+1)]['nSubcond']):
            keysToRemove.append('dprime_subc'+ str(t+1))
            
        datsLength = len(dats['dats'+str(i+1)]['listener'])
        #recursively for all different headers found
        dats['datspro'+str(i+1)] = {}

        #remove ephemeral keys 
        for j in range(len(keysToRemove)):
            if keysToRemove[j] in dats['dats'+str(i+1)]:
                del dats['dats'+str(i+1)][keysToRemove[j]]


        numericFields = ['nCorrectA_ALL', 'nCorrectB_ALL', 'nTotalA_ALL', 'nTotalB_ALL', 'nCorrect_ALL', 'nTotal_ALL', 'nSubcond']
        numericFields.extend(['nCorrectA_subc' + str(t+1) for t in range(dats['dats'+str(i+1)]['nSubcond'])])
        numericFields.extend(['nCorrectB_subc' + str(t+1) for t in range(dats['dats'+str(i+1)]['nSubcond'])])
        numericFields.extend(['nTotalA_subc' + str(t+1) for t in range(dats['dats'+str(i+1)]['nSubcond'])])
        numericFields.extend(['nTotalB_subc' + str(t+1) for t in range(dats['dats'+str(i+1)]['nSubcond'])])
        numericFields.extend(['nCorrect_subc' + str(t+1) for t in range(dats['dats'+str(i+1)]['nSubcond'])])
        numericFields.extend(['nTotal_subc' + str(t+1) for t in range(dats['dats'+str(i+1)]['nSubcond'])])
        keysNotToCheck = numericFields
        keysNotToCheck.extend(['conditionAgglomerate'])

        standardKeys = ['condition', 'listener', 'experimentLabel', 'experiment']
        dats['dats'+str(i+1)]['conditionAgglomerate'] = ['' for i in range(len(dats['dats'+str(i+1)]['condition']))]
        for j in range(len(dats['dats'+str(i+1)]['condition'])):
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck:
                    dats['dats'+str(i+1)]['conditionAgglomerate'][j] = dats['dats'+str(i+1)]['conditionAgglomerate'][j] + dats['dats'+str(i+1)][key][j]

        for key in dats['dats'+str(i+1)]:
            if key not in keysNotToCheck:
                dats['datspro'+str(i+1)][key] = []
        fout.write('dprime_ALL' + separator +\
                   'nTotal_ALL' + separator +\
                   'nCorrectA_ALL' + separator +\
                   'nTotalA_ALL' + separator +\
                   'nCorrectB_ALL' + separator +\
                   'nTotalB_ALL' + separator )
        for t in range(dats['dats'+str(i+1)]['nSubcond']):
            fout.write('dprime_subc' + str(t+1) + separator +\
                       'nTotal_subc' + str(t+1) + separator +\
                       'nCorrectA_subc' + str(t+1) + separator +\
                       'nTotalA_subc' + str(t+1) + separator +\
                       'nCorrectB_subc' + str(t+1) + separator +\
                       'nTotalB_subc' + str(t+1) + separator )
                       
                       
        #sort on the basis of condition-agglomerate
        cnds = list(set(dats['dats'+str(i+1)]['conditionAgglomerate']))
        dats['datspro'+str(i+1)]['dprime_ALL'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['nCorrectA_ALL'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['nCorrectB_ALL'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['nTotalA_ALL'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['nTotalB_ALL'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['nTotal_ALL'] = zeros(len(cnds))
        nCorrectA_ALL = [[] for j in range(len(cnds))]
        nTotalA_ALL = [[] for j in range(len(cnds))]
        nCorrectB_ALL = [[] for j in range(len(cnds))]
        nTotalB_ALL = [[] for j in range(len(cnds))]
        nTotal_ALL = [[] for j in range(len(cnds))]
        for t in range(dats['dats'+str(i+1)]['nSubcond']):
              dats['datspro'+str(i+1)]['dprime_subc'+str(t+1)] = zeros(len(cnds))
              dats['datspro'+str(i+1)]['nCorrectA_subc'+str(t+1)] = zeros(len(cnds))
              dats['datspro'+str(i+1)]['nCorrectB_subc'+str(t+1)] = zeros(len(cnds))
              dats['datspro'+str(i+1)]['nTotalA_subc'+str(t+1)] = zeros(len(cnds))
              dats['datspro'+str(i+1)]['nTotalB_subc'+str(t+1)] = zeros(len(cnds))
              dats['datspro'+str(i+1)]['nTotal_subc'+str(t+1)] = zeros(len(cnds))
        nCorrectA_subc = [[[] for j in range(len(cnds))] for t in range(dats['dats'+str(i+1)]['nSubcond'])]
        nTotalA_subc = [[[] for j in range(len(cnds))] for t in range(dats['dats'+str(i+1)]['nSubcond'])]
        nCorrectB_subc = [[[] for j in range(len(cnds))] for t in range(dats['dats'+str(i+1)]['nSubcond'])]
        nTotalB_subc = [[[] for j in range(len(cnds))] for t in range(dats['dats'+str(i+1)]['nSubcond'])]
        nTotal_subc = [[[] for j in range(len(cnds))] for t in range(dats['dats'+str(i+1)]['nSubcond'])]
        for j in range(datsLength):
            cndIdx = cnds.index(dats['dats'+str(i+1)]['conditionAgglomerate'][j])
            nCorrectA_ALL[cndIdx].append(dats['dats'+str(i+1)]['nCorrectA_ALL'][j])
            nTotalA_ALL[cndIdx].append(dats['dats'+str(i+1)]['nTotalA_ALL'][j])
            nCorrectB_ALL[cndIdx].append(dats['dats'+str(i+1)]['nCorrectB_ALL'][j])
            nTotalB_ALL[cndIdx].append(dats['dats'+str(i+1)]['nTotalB_ALL'][j])
            nTotal_ALL[cndIdx].append(dats['dats'+str(i+1)]['nTotal_ALL'][j])
            for t in range(dats['dats'+str(i+1)]['nSubcond']):
                nCorrectA_subc[t][cndIdx].append(dats['dats'+str(i+1)]['nCorrectA_subc'+str(t+1)][j])
                nTotalA_subc[t][cndIdx].append(dats['dats'+str(i+1)]['nTotalA_subc'+str(t+1)][j])
                nCorrectB_subc[t][cndIdx].append(dats['dats'+str(i+1)]['nCorrectB_subc'+str(t+1)][j])
                nTotalB_subc[t][cndIdx].append(dats['dats'+str(i+1)]['nTotalB_subc'+str(t+1)][j])
                nTotal_subc[t][cndIdx].append(dats['dats'+str(i+1)]['nTotal_subc'+str(t+1)][j])


        for item in standardKeys:
            fout.write(item + separator)
        for key in dats['dats'+str(i+1)]:
            if key not in keysNotToCheck and key not in standardKeys:
                fout.write(key + separator)
        fout.write('\n')

        for j in range(len(cnds)):
            start, stop = getBlockRangeToProcess(last, block_range, nCorrectA_ALL[j])
            
            dats['datspro'+str(i+1)]['nCorrectA_ALL'][j] = sum(nCorrectA_ALL[j][start:stop])
            dats['datspro'+str(i+1)]['nTotalA_ALL'][j] =  sum(nTotalA_ALL[j][start:stop])
            dats['datspro'+str(i+1)]['nCorrectB_ALL'][j] =  sum(nCorrectB_ALL[j][start:stop])
            dats['datspro'+str(i+1)]['nTotalB_ALL'][j] =  sum(nTotalB_ALL[j][start:stop])
            dats['datspro'+str(i+1)]['nTotal_ALL'][j] =  sum(nTotal_ALL[j][start:stop])
            dats['datspro'+str(i+1)]['dprime_ALL'][j] = dprime_yes_no_from_counts(nCA=dats['datspro'+str(i+1)]['nCorrectA_ALL'][j], nTA=dats['datspro'+str(i+1)]['nTotalA_ALL'][j], nCB=dats['datspro'+str(i+1)]['nCorrectB_ALL'][j], nTB=dats['datspro'+str(i+1)]['nTotalB_ALL'][j], corr=dprimeCorrection)

            for t in range(dats['dats'+str(i+1)]['nSubcond']):
                  dats['datspro'+str(i+1)]['nCorrectA_subc'+str(t+1)][j] = sum(nCorrectA_subc[t][j][start:stop])
                  dats['datspro'+str(i+1)]['nTotalA_subc'+str(t+1)][j] =  sum(nTotalA_subc[t][j][start:stop])
                  dats['datspro'+str(i+1)]['nCorrectB_subc'+str(t+1)][j] =  sum(nCorrectB_subc[t][j][start:stop])
                  dats['datspro'+str(i+1)]['nTotalB_subc'+str(t+1)][j] =  sum(nTotalB_subc[t][j][start:stop])
                  dats['datspro'+str(i+1)]['nTotal_subc'+str(t+1)][j] =  sum(nTotal_subc[t][j][start:stop])
                  dats['datspro'+str(i+1)]['dprime_subc'+str(t+1)][j] = dprime_yes_no_from_counts(nCA=dats['datspro'+str(i+1)]['nCorrectA_subc'+ str(t+1)][j], nTA=dats['datspro'+str(i+1)]['nTotalA_subc'+ str(t+1)][j], nCB=dats['datspro'+str(i+1)]['nCorrectB_subc'+ str(t+1)][j], nTB=dats['datspro'+str(i+1)]['nTotalB_subc'+ str(t+1)][j], corr=dprimeCorrection)
            
            cndIdx = dats['dats'+str(i+1)]['conditionAgglomerate'].index(cnds[j])
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck:
                    dats['datspro'+str(i+1)][key].append(dats['dats'+str(i+1)][key][cndIdx])


            fout.write(str(dats['datspro'+str(i+1)]['dprime_ALL'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['nTotal_ALL'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['nCorrectA_ALL'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['nTotalA_ALL'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['nCorrectB_ALL'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['nTotalB_ALL'][j]) + separator)
            for t in range(dats['dats'+str(i+1)]['nSubcond']):
                fout.write(str(dats['datspro'+str(i+1)]['dprime_subc'+str(t+1)][j]) + separator +\
                           str(dats['datspro'+str(i+1)]['nTotal_subc'+str(t+1)][j]) + separator +\
                           str(dats['datspro'+str(i+1)]['nCorrectA_subc'+str(t+1)][j]) + separator +\
                           str(dats['datspro'+str(i+1)]['nTotalA_subc'+str(t+1)][j]) + separator +\
                           str(dats['datspro'+str(i+1)]['nCorrectB_subc'+str(t+1)][j]) + separator +\
                           str(dats['datspro'+str(i+1)]['nTotalB_subc'+str(t+1)][j]) + separator)
            for item in standardKeys:
                fout.write(dats['datspro'+str(i+1)][item][j] + separator)
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck and key not in standardKeys:
                    fout.write(dats['datspro'+str(i+1)][key][j] + separator)
            fout.write('\n')

    fout.close()
                
                
#================================================    
#TABLE CONSTANT 1PAIRSAMEDIFFERENT
def processResultsTableConstant1PairSameDifferent(fName, fout=None, separator=';', last=None, block_range=None, dprimeCorrection=True):
    

    if fout == None:
        fNameOut = fName[0].split('.csv')[0] + '_processed.csv'
    else:
        fNameOut = fout
        
    allLines = []
    headline = ''
    for i in range(len(fName)):
        f = open(fName[i], 'r')
        thisAllLines = f.readlines()
        f.close()
        if i == 0:
            headline = thisAllLines[0]
            allLines.extend(thisAllLines)
        else:
            if thisAllLines[0] == headline:
                allLines.extend(thisAllLines[1:len(thisAllLines)])
            else:
                raise DifferentProceduresError("The files appear to contain data from different procedures. Cannot process.")

    fout = open(fNameOut, 'w')
    if checkMixedProceduresInTableFile(allLines, separator):
        fout.write("The table files appear to contain multiple headers.\n Usually this happens because they contain results from different experiments/procedures or \n different check box selections. These table processing functions cannot process these type of \n files, and automatic plots are not supported."+separator)
        fout.close()
        return
    
    dats = {}
    nHeaders = 0
    firstHeaderWord = 'dprime_IO'
    
    for i in range(len(allLines)):
        if allLines[i].split(separator)[0].strip() == firstHeaderWord:
            nHeaders = nHeaders + 1
            dats['dats'+str(nHeaders)] = {}
            headerList = []
            for j in range(len(allLines[i].split(separator))):
                thisKey = allLines[i].split(separator)[j].strip()
                dats['dats'+str(nHeaders)][thisKey] = []
                headerList.append(thisKey)


        if nHeaders > 0 and allLines[i].split(separator)[0].strip() != firstHeaderWord:
            for j in range(len(headerList)):
                if headerList[j] in ['nCorrectA', 'nCorrectB', 'nTotalA', 'nTotalB', 'nCorrect', 'nTotal']:
                    dats['dats'+str(nHeaders)][headerList[j]].append(int(allLines[i].split(separator)[j].strip()))
                else:
                    dats['dats'+str(nHeaders)][headerList[j]].append(allLines[i].split(separator)[j].strip())

    
    keysToRemove = ['dprime_IO', 'dprime_diff', 'session', 'date', 'time', 'duration', 'block', '']
    for i in range(len(dats)):
        datsLength = len(dats['dats'+str(i+1)]['listener'])
        #recyrsively for all different headers found
        dats['datspro'+str(i+1)] = {}

        #remove ephemeral keys 
        for j in range(len(keysToRemove)):
            if keysToRemove[j] in dats['dats'+str(i+1)]:
                del dats['dats'+str(i+1)][keysToRemove[j]]
    
         
        keysNotToCheck = ['nCorrectA', 'nTotalA', 'nCorrectB', 'nTotalB', 'nCorrect', 'nTotal', 'conditionAgglomerate']
        standardKeys = ['condition', 'listener', 'experimentLabel', 'experiment']
        dats['dats'+str(i+1)]['conditionAgglomerate'] = ['' for i in range(len(dats['dats'+str(i+1)]['condition']))]
        for j in range(len(dats['dats'+str(i+1)]['condition'])):
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck:
                    dats['dats'+str(i+1)]['conditionAgglomerate'][j] = dats['dats'+str(i+1)]['conditionAgglomerate'][j] + dats['dats'+str(i+1)][key][j]

        for key in dats['dats'+str(i+1)]:
            if key not in keysNotToCheck:
                dats['datspro'+str(i+1)][key] = []
        fout.write('dprime_IO' + separator +\
                   'dprime_diff' + separator +\
                   'nTotal' + separator +\
                   'nCorrectA' + separator +\
                   'nTotalA' + separator +\
                   'nCorrectB' + separator +\
                   'nTotalB' + separator )
                       
                       
        #sort on the basis of condition-agglomerate
        cnds = list(set(dats['dats'+str(i+1)]['conditionAgglomerate']))
        dats['datspro'+str(i+1)]['dprime_IO'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['dprime_diff'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['nCorrectA'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['nCorrectB'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['nTotalA'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['nTotalB'] = zeros(len(cnds))
        dats['datspro'+str(i+1)]['nTotal'] = zeros(len(cnds))
        nCorrectA = [[] for j in range(len(cnds))]
        nTotalA = [[] for j in range(len(cnds))]
        nCorrectB = [[] for j in range(len(cnds))]
        nTotalB = [[] for j in range(len(cnds))]
        nTotal = [[] for j in range(len(cnds))]
        for j in range(datsLength):
            cndIdx = cnds.index(dats['dats'+str(i+1)]['conditionAgglomerate'][j])
            nCorrectA[cndIdx].append(dats['dats'+str(i+1)]['nCorrectA'][j])
            nTotalA[cndIdx].append(dats['dats'+str(i+1)]['nTotalA'][j])
            nCorrectB[cndIdx].append(dats['dats'+str(i+1)]['nCorrectB'][j])
            nTotalB[cndIdx].append(dats['dats'+str(i+1)]['nTotalB'][j])
            nTotal[cndIdx].append(dats['dats'+str(i+1)]['nTotal'][j])


        for item in standardKeys:
            fout.write(item + separator)
        for key in dats['dats'+str(i+1)]:
            if key not in keysNotToCheck and key not in standardKeys:
                fout.write(key + separator)
        fout.write('\n')
        
        for j in range(len(cnds)):
            start, stop = getBlockRangeToProcess(last, block_range, nCorrectA[j])
            
            dats['datspro'+str(i+1)]['nCorrectA'][j] = sum(nCorrectA[j][start:stop])
            dats['datspro'+str(i+1)]['nTotalA'][j] =  sum(nTotalA[j][start:stop])
            dats['datspro'+str(i+1)]['nCorrectB'][j] =  sum(nCorrectB[j][start:stop])
            dats['datspro'+str(i+1)]['nTotalB'][j] =  sum(nTotalB[j][start:stop])
            dats['datspro'+str(i+1)]['nTotal'][j] =  sum(nTotal[j][start:stop])
            dats['datspro'+str(i+1)]['dprime_IO'][j] = dprime_SD_from_counts(nCA=dats['datspro'+str(i+1)]['nCorrectA'][j], nTA=dats['datspro'+str(i+1)]['nTotalA'][j], nCB=dats['datspro'+str(i+1)]['nCorrectB'][j], nTB=dats['datspro'+str(i+1)]['nTotalB'][j], meth='IO', corr=dprimeCorrection)
            dats['datspro'+str(i+1)]['dprime_diff'][j] = dprime_SD_from_counts(nCA=dats['datspro'+str(i+1)]['nCorrectA'][j], nTA=dats['datspro'+str(i+1)]['nTotalA'][j], nCB=dats['datspro'+str(i+1)]['nCorrectB'][j], nTB=dats['datspro'+str(i+1)]['nTotalB'][j], meth='diff', corr=dprimeCorrection)
            
            cndIdx = dats['dats'+str(i+1)]['conditionAgglomerate'].index(cnds[j])
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck:
                    dats['datspro'+str(i+1)][key].append(dats['dats'+str(i+1)][key][cndIdx])

 
            fout.write(str(dats['datspro'+str(i+1)]['dprime_IO'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['dprime_diff'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['nTotal'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['nCorrectA'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['nTotalA'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['nCorrectB'][j]) + separator +\
                       str(dats['datspro'+str(i+1)]['nTotalB'][j]) + separator)
            for item in standardKeys:
                fout.write(dats['datspro'+str(i+1)][item][j] + separator)
            for key in dats['dats'+str(i+1)]:
                if key not in keysNotToCheck and key not in standardKeys:
                    fout.write(dats['datspro'+str(i+1)][key][j] + separator)
            fout.write('\n')

    fout.close()





                
