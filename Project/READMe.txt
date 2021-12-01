Install the necessary libararies on cims server using pip3 install

Steps to execute:
1. Run the file coherence_protocols.py using the command python3 coherence_protocols.py
2. Follow the prompts and input valid parameters such as
    - Number of processors
    - Cache size 
        1. 32KB 
        2. 64KB
    - Type of mapping
        1. Direct mapping
        2. Set-Associative
            - Input the associativity (2, 4, 8, 16) if 2 is chosen. 
    - Choose the write method
        1. Write back
        2. Write through
3. Select option no. specified in the prompt. 
    Eg. for prompt 'Choose the type of mapping:1. Direct Mapping2. Associative Mapping
    Press 1 for Direct mapping and 2 for Associative mapping
4. Based on these parameters, the program will generate a summary that is analysed in the project report.


The file inst_gen has been used to generate the csv files and does not need to be run again. 
The 4 csv files contain randomized instructions for 2, 4, 8 and 16 core systems separately.