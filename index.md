# Advanced Heuristics for Ordering Compiler Optimization Passes

## Problem Statement

_How to improve the existing heuristics or replace the heuristics with machine learning-based models so that the LLVM compiler can provide a superior order of the passes customized per application?_

Developers generally use standard optimizations pipelines like -O2 and -O3 to optimize their code. Usually, manually crafted heuristics are used to determine which optimization passes to select and how to order the execution of those passes. However, this process is not tailored for a particular application, or kind of application, as it is designed to perform “reasonably well” for any input.

## Proposed Solution

We track application code features and how they transform during the execution of the optimization pipeline in order to categorize applications with regards to the impact passes have on them. Once the dependencies between the existing passes and code features are identified for the different “kinds” of programs, e.g., pointer heavy, call heavy, etc., the findings can be used to improve the existing heuristics or design new heuristics and models to optimize the LLVM pass pipeline. This will allow the compiler to order the transform passes in a superior manner, tailored to different code structures and features. 

We identify these features after every pass in the pass pipeline to determine how the pass affects them, and then using those features to identify different function “kinds”. A function kind is determined by the initial code features and is updated by the effect passes have on the function. If we can categorize functions into different kinds with high enough accuracy, we can predict if a particular pass may change (optimize) the code or if it can be skipped to reduce the compilation time, or determine what pass order to apply for maximizing the resulting optimization.

## Implementation Details

### Extracting Function Properties

First, we needed a pass to extract function properties. We modified and extended an already existing pass within LLVM called InlineFeaturesAnalysis for this. 
The first patch was to rename the pass to be able to extend it to function properties other than inliner features. We refactored the pass to separate analyze logic from Function Properties, and the tests were modified accordingly.

We added a printer pass to enable printing the extracted function properties to the standard output along with an LLVM lit test case. We added the ability to extract new function properties in addition to the properties already available. As of now, we look at the following code features on a per-function basis.

1. total number of basic blocks in the function
2. total number of basic blocks reached from conditional instructions in the function
3. total number of uses of the function 
4. total number of direct calls to other defined functions from the function
5. total number of load instructions in the function 
6. total number of store instructions in the function 
7. maximum loop depth of the function
8. total number of top-level loops in the function

Here is the list of patches that were upstreamed to the LLVM Github Monorepo. 

- [FunctionPropertiesAnalysis] [Rename InlineFeaturesAnalysis to  FunctionPropertiesAnalysis](https://reviews.llvm.org/D82044)
- [FunctionPropertiesAnalysis] [Refactor FunctionPropertiesAnalysis](https://reviews.llvm.org/D82044)
- [FunctionPropertiesAnalysis] [Add a Printer to the FunctionPropertiesAnalysis](https://reviews.llvm.org/D82523)
- [FunctionPropertiesAnalysis] [Add new function properties to FunctionPropertiesAnalysis](https://reviews.llvm.org/D82283)

We wrote a new [loadable ‘instrumentation’ pass](https://github.com/tarinduj/GSoC2020/blob/master/FunctionPropertiesAnalysisPassInstrument.cpp), which runs after each pass in the pass pipeline. It takes the IR unit (module, function, etc.) the pass was run on, and extracts the functions from the IR unit to analyze function properties after the pass. The pass can be found [here](https://github.com/tarinduj/GSoC2020/blob/master/FunctionPropertiesAnalysisPassInstrument.cpp).  

### Markdown

Markdown is a lightweight and easy-to-use syntax for styling your writing. It includes conventions for

```markdown
Syntax highlighted code block

# Header 1
## Header 2
### Header 3

- Bulleted
- List

1. Numbered
2. List

**Bold** and _Italic_ and `Code` text

[Link](url) and ![Image](src)
```

For more details see [GitHub Flavored Markdown](https://guides.github.com/features/mastering-markdown/).

### Jekyll Themes

Your Pages site will use the layout and styles from the Jekyll theme you have selected in your [repository settings](https://github.com/tarinduj/GSoC2020/settings). The name of this theme is saved in the Jekyll `_config.yml` configuration file.

### Support or Contact

Having trouble with Pages? Check out our [documentation](https://docs.github.com/categories/github-pages-basics/) or [contact support](https://github.com/contact) and we’ll help you sort it out.
