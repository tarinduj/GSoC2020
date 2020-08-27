from tqdm import tqdm
from guppy import hpy
import objgraph
import tracemalloc

def zeros(shape):
    retval = []
    for x in range(shape[0]):
        retval.append([])
        for y in range(shape[1]):
            retval[-1].append(0)
    return retval

match_award      = 20
mismatch_penalty = -1000000
gap_penalty      = -5 # both for opening and extanding

def match_score(alpha, beta):
    if alpha == beta:
        return match_award
    elif alpha == '-' or beta == '-':
        return gap_penalty
    else:
        return mismatch_penalty

def align(pipeline, subhyperpipeline):
    seq1, meta1 = pipeline
    seq2, meta2 = subhyperpipeline
    "seq2 is the longer one with multiple keys in the dictionary"
    seq1.reverse()    #reverse sequence 1
    seq2.reverse()    #reverse sequence 2
    meta1.reverse()
    meta2.reverse()
 
    m, n = len(seq1), len(seq2)  # length of two sequences
    
    # Generate DP table and traceback path pointer matrix
    score = zeros((m+1, n+1))      # the DP table
   
    # Calculate DP table
    for i in range(0, m + 1):
        score[i][0] = gap_penalty * i
    for j in range(0, n + 1):
        score[0][j] = gap_penalty * j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            match = score[i - 1][j - 1] + match_score(seq1[i-1], seq2[j-1])
            delete = score[i - 1][j] + gap_penalty
            insert = score[i][j - 1] + gap_penalty
            score[i][j] = max(match, delete, insert)

    # Traceback and compute the alignment
    join = []
    joined_meta = []
    
    i,j = m,n # start from the bottom right cell
    while i > 0 and j > 0: # end toching the top or the left edge
        score_current = score[i][j]
        score_diagonal = score[i-1][j-1]
        score_up = score[i][j-1]
        score_left = score[i-1][j]

        if score_current == score_diagonal + match_score(seq1[i-1], seq2[j-1]):
            join.append(seq1[i-1])
            
            temp_dict = meta2[j-1]
            meta1_key = list(meta1[i-1].keys())[0]
            temp_dict[meta1_key] = meta1[i-1][meta1_key]
            joined_meta.append(temp_dict)
            
            i -= 1
            j -= 1
        elif score_current == score_left + gap_penalty:
            join.append(seq1[i-1])
            
            temp_dict = dict.fromkeys(list(meta2[0].keys()), getFPI(""))
            #keys are the same for all the dictionaries in meta2, so get keys from the 0th one
            meta1_key = list(meta1[i-1].keys())[0]
            temp_dict[meta1_key] = meta1[i-1][meta1_key]
            joined_meta.append(temp_dict)
            
            i -= 1
        elif score_current == score_up + gap_penalty:
            join.append(seq2[j-1])
            
            temp_dict = meta2[j-1]
            meta1_key = list(meta1[i-1].keys())[0]
            temp_dict[meta1_key] = getFPI("")
            joined_meta.append(temp_dict)
        
            j -= 1


    # Finish tracing up to the top left cell
    while i > 0:
        join.append(seq1[i-1])
        
        temp_dict = dict.fromkeys(list(meta2[0].keys()), getFPI(""))
        #keys are the same for all the dictionaries in meta2, so get keys from the 0th one
        meta1_key = list(meta1[i-1].keys())[0]
        temp_dict[meta1_key] = meta1[i-1][meta1_key]
        joined_meta.append(temp_dict)
        
        i -= 1
    while j > 0:
        join.append(seq2[j-1])
        
        temp_dict = meta2[j-1]
        meta1_key = list(meta1[i-1].keys())[0]
        temp_dict[meta1_key] = getFPI("")
        joined_meta.append(temp_dict)
        
        j -= 1
    
    return [join, joined_meta]

def getFPI(fpi):
    if fpi == "":
        functionPropertiesNames = ['BasicBlockCount', 'BlocksReachedFromConditionalInstruction',
                               'Uses', 'DirectCallsToDefinedFunctions', 'LoadInstCount',
                               'StoreInstCount', 'MaxLoopDepth', 'TopLevelLoopCount']
        #return dict.fromkeys(functionPropertiesNames, np.nan)
        return np.nan

    fpiList = fpi.strip().split('\n')
    fpiDict = {}
    for fp in fpiList:
        fp = fp.strip().split(':')
        fpiDict[fp[0].strip()] = fp[1].strip()

    return fpiDict

def alignHyperPipeline(buffer):
    """
    buffer = {
                fnA : [ [passA1, passA2, ...., passAN],
                        [{A: fpiA1},  {A: fpiA2},  ...., {A: fpiAN} ] ],
                fnB : [ [passB1, passB2, ...., passBM],
                        [{B: fpiB1},  {B: fpiB2},  ...., {B: fpiBN} ] ]
             }

    subHyperPipeline = [
                            [pass1, pass2, ...., passN],
                            [   {fnA: fpiA1, fnB: fpiB1},
                                {fnA: fpiA2, fnB: fpiB2},
                                ....
                                {fnA: fpiAN, fnB: fpiBN}
                            ]
                       ]
    """
    """print("*"*10," buffer ", "*"*10)
    print(buffer)"""
    _, maxKey= max((len(v), k) for k,v in buffer.items())
    subHyperPipeline = buffer.pop(maxKey)
    i = 0

    tracemalloc.start()
    
    for key in tqdm(buffer):
        """h = hpy()
        print(h.heap())"""
        #s = tracemalloc.take_snapshot()

        subHyperPipeline = align(buffer[key], subHyperPipeline)

        """top_stats = tracemalloc.take_snapshot().compare_to(s, 'lineno')
        for stats in top_stats[:5]:
            print(stats)
       
        #objgraph.show_refs([subHyperPipeline], filename=f"sample{i}.jpg")
        print("Size: ", len(subHyperPipeline[1]))
        #i += 1
        print(h.heap())
        print("* "*20)
       """
    """
    print("*"*10," subHyperPipeline ", "*"*10)
    print(subHyperPipeline)
    print()"""

    if len(subHyperPipeline[0]) == len(subHyperPipeline[1]):
        return subHyperPipeline
    else:
        sys.exit("ERROR!!!! FPI MISSING. FIX IT")
        
def getHyperPassPipeline(rawDataList):
    buffer = {}
    #buffer = { function1: [[pass1, pass2, ..][FP1, FP2, ..]], .. }

    for i in tqdm(range(len(rawDataList))):
        passName = rawDataList[i][1]
        functionName = rawDataList[i][2]
        functionProperties = {functionName: getFPI(rawDataList[i][3])}

        """
        Ignore llvm.lifetim~ functions.
        """
        if functionName.startswith('llvm.lifetime.'):
            continue

        if functionName not in buffer:
            buffer[functionName] = [[],[]]
        buffer[functionName][0].append(passName)
        buffer[functionName][1].append(functionProperties)

    hyperPassPipeline = alignHyperPipeline(buffer)
        
    return hyperPassPipeline

def getDataFrame(hyperPassPipelineDict):
    functionPropertiesNames = ['BasicBlockCount', 'BlocksReachedFromConditionalInstruction',
                               'Uses', 'DirectCallsToDefinedFunctions', 'LoadInstCount',
                               'StoreInstCount', 'MaxLoopDepth', 'TopLevelLoopCount']

    cols = []
    data = []
    fnNameIndexPointer = {}

    cols.append(('Pass Number','Function Name'))

    for passNo, fpiSet in hyperPassPipelineDict.items():
        for fp in functionPropertiesNames:
            cols.append((passNo, fp))
        for fnName, fpi in fpiSet.items():
            if passNo == 0:
                data.append([fnName])
                fnNameIndexPointer[fnName] = len(data)-1
            if not isinstance(fpi, dict):
                fpi = dict.fromkeys(functionPropertiesNames, np.nan)
            for _, value in fpi.items():
                data[fnNameIndexPointer[fnName]].append(value)

    return pd.DataFrame(data, columns=pd.MultiIndex.from_tuples(cols))
    
import sys
import numpy as np
import pandas as pd

fileName = 'SPASS_clause.c.txt'
functionPropertiesNames = ['BasicBlockCount', 'BlocksReachedFromConditionalInstruction',
                           'Uses', 'DirectCallsToDefinedFunctions', 'LoadInstCount',
                           'StoreInstCount', 'MaxLoopDepth', 'TopLevelLoopCount']
numFunctionProperties = len(functionPropertiesNames)

with open(fileName) as inFile:
    rawData = inFile.read()

rawDataList = list(map(str.strip, rawData.strip().split('***')))[1:]

for i in range(len(rawDataList)):
    rawDataList[i] = list(map(str.strip, rawDataList[i].strip().split('#')))

del rawData

hyperPassPipeline = getHyperPassPipeline(rawDataList)
print("hyperPassPipeline")

del rawDataList

with open("passList.txt", 'w') as f:
    f.write(str(hyperPassPipeline[0]))

hyperPassPipelineDict = dict(zip(list(range(len(hyperPassPipeline[0]))), hyperPassPipeline[1]))
print("hyperPassPipelineDict")

del hyperPassPipeline

passPipelineDF = getDataFrame(hyperPassPipelineDict)
print("passPipelineDF")

passPipelineDF.to_csv('passPipelineDF.csv')
