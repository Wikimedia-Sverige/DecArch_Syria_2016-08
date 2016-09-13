
# coding: utf-8

# In[4]:

import regex, os


# In[104]:

f1 = "37) Alfa 31. Bis.jpg" #folder 1
f2 = "38) Palmira. T. di Bel, temenos. 20 marzo '93. Bis.jpg" #folder 1
f3 = "149 Apamea. Alfa 31. Bis.jpg" # folder 2
f4 = "138 Apamea. 20 marzo '93 Bis.jpg"# folder 2
f5 = "148 Santuario San Simeone. Chiesa esterna. 20 marzo '93. Bis.jpg" # folder 2
f6 = "183 Apamea. Antiquarium. 20 marzo '93. Bis..jpg"
f7 = "170 San Simeone. Nartece della facciata.20 marzo '93. Bis.jpg"

fold1 = "1_SIRIA - Palmira"
fold2 = "2_SIRIA - Damasco e Bosra e Apamea e S. Simeone e Sergiopolis e Aleppo"
fold3 = "3_SIRIA - Zenobia e Dura Europos e Mari"
foldernames = [fold1, fold2, fold3]

foldfnames = [(fold1, f1),(fold1,f2),(fold2, f3),(fold2, f4), (fold2, f5), (fold2, f6), (fold2, f7)]


# In[144]:

def create_filename(fold, fobj):
    import os
    """Takes a DataFrame row from the 'merged' dataframe and returns a string filename."""
    # remove all underscores
    no_underscores = regex.sub(r"_", " ", fobj)
    
    # <Filename0>, dummy, <Filename1> = <Filename>.partition(" ") 
    filename0, dummy, filename1 = no_underscores.partition(" ")
    #print("filename0: {}\n dummy: {}\n filename1: {}\n".format(filename0, dummy, filename1))
    
    # Grab the extension for later use
    ext = regex.findall(r"\.\w+",filename1)[-1]
    #print(ext)
    
    # <Filename_1_clean> = <Filename1> with "20 marzo..." removed, any dubble spaces replaced by single ones 
    # and finally the spaces substituted by underscores (_). 
    yeardate_patt = regex.compile(r"[\. ]?\d+[o']? m? ?arz[o0p] ?'?\d+[\. ]?",flags=regex.I)
    year_patt = regex.compile(r" '\d\d[\.,]? ",flags=regex.I)
    date_patt = regex.compile(r"20 marzo", flags=regex.I)
    
    yeardate_match = yeardate_patt.search(filename1)
    year_match = year_patt.search(filename1)
    date_match = date_patt.search(filename1)
    
    print("filename1: {}".format(filename1))
        
    if yeardate_match:
        filename_1_clean = regex.sub(yeardate_patt, " ",filename1)
        print("yeardate_match. filename_1_clean is:\n {:<30}".format(filename_1_clean))
        
    elif year_match and not yeardate_match:
        filename_1_clean = regex.sub(year_patt, " ",filename1)
        print("year_match and not yeardate_match. filename_1_clean is:\n {:<30}".format(filename_1_clean))
        
    #elif date_match and not yeardate_match:
    #    print("date_match: {} in filename1: {}".format(date_match,filename1))
    
    else:
        filename_1_clean = filename1
        print("no year_match or yeardate_match. filename_1_clean is:\n {:<30}".format(filename_1_clean))
    
    # Remove the extension from filename_1_clean
    fname, extension = os.path.splitext(filename_1_clean)
    
    filename_1_clean = fname
    #print(filename_1_clean)
    
    
    # Remove all 'Bis' from end of filename_1_clean
    filename_1_clean = regex.sub(r"Bis", "", filename_1_clean, flags=regex.I)
    print("filename_1_clean: {}".format(filename_1_clean))
    
    # Remove all leading and trailing whitespace from end of filename_1_clean
    # Ensure no double spaces left
    filename_1_clean = filename_1_clean.strip(". ").replace(" ", "_").replace("__", "_")
    #print(repr(filename_1_clean))
    
    # <Filename_0_clean> = <Filename0> with any trailing brackets ()) removed.
    filename_0_clean = regex.sub(r"\).?","",filename0)
    #print(filename_0_clean)
        
    # <Folder_#>, dummy, dummy = <Folder>.partition("_")
    folder_no, dummy, dummy  = fold.partition("_")
    #print("Folder number is: {}".format(folder_no))
    
    ################## Final piecing together of filename ####################################
    #Filename: <Filename_1_clean>_-_DecArch_-_<Folder_no>-<Filename_0_clean>.<ext>
    #Filename example:
    #So for 49) Palmira. Via colonnata presso il teatro. 20 marzo '93. Bis.jpg end result is
    #Palmira._Via_colonnata_presso_il_teatro._-_DecArch_-1-49.jpg
    #Palmira._Via_colonnata_presso_il_teatro._-_DecArch_-1-49.jpg
    filename = filename_1_clean + "_-_DecArch_-_" + folder_no + "-" + filename_0_clean
    print("filename: {}\n".format(filename))
    
    # Ensure no multiple spaces left
    #filename = regex.sub(r" +"," ", filename)
    #print("filename is: {}".format(filename))
    
    return filename


# In[145]:

for fold, fobj in foldfnames:
    create_filename(fold, fobj)


# In[139]:

f7 = "170 San Simeone. Nartece della facciata.20 marzo '93. Bis.jpg"
date_patt = regex.compile(r"20 marzo", flags=regex.I)

date_match = date_patt.search(f7)
date_match is True


# In[ ]:



