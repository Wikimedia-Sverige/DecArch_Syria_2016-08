
# coding: utf-8

# In[ ]:

get_ipython().system('pip install regex # A sligthly better version of RE')
get_ipython().system('pip install html5lib # For Pandas read_html used to parse mapping wikitables ')
get_ipython().system('pip install pandas # A great library for data wrangling (and analysis)')


# In[1]:

import pandas as pd 
import numpy as np
import regex
import os 


# # Metadata and mappings
# The template mapping can be found here:
# 
# Phabricator task [T143212](https://phabricator.wikimedia.org/T143212)
# 
# The original metadata is a Google Spreadsheet located here:
# 
# https://docs.google.com/spreadsheets/d/1F43jhv_ekLfnjnvRxZjl5VmibFbRUQ2affrIkSck4WU/edit?usp=sharing
# 
# The doc below is downloaded locally 2016-08-17 17:00

# In[2]:

def strip(text):
    try:
        return text.strip()
    except AttributeError:
        return text
    
it_converters = {"Folder":strip,"Filename":strip,"Nome foto":strip,"Anno":strip,"Luogo":strip,"Nome monumento":strip,"Descrizione":strip,"Nome autore":strip}
metadata_it = pd.read_excel("./data/COH DechArch Metadata.xlsx",sheetname="Italian", converters=it_converters) # empty first row
metadata_it.columns = ["Folder","Filename","Nome foto","Anno","Luogo","Nome monumento","Descrizione","Nome autore"]

en_converters = {"Place":strip,"Monument name":strip,"Description":strip} # Skip column "Filename" we don't parse
metadata_en = pd.read_excel("./data/COH DechArch Metadata.xlsx",sheetname="English",                             converters=en_converters, parse_cols=[1,2,3,4],) # Skip column "Filename" --> 0


# In[3]:

metadata_it.tail(2)


# In[4]:

metadata_en.tail(10)


# In[5]:

merged = pd.concat([metadata_it,metadata_en], axis=1) 
merged.head(5)


# # Create filenames

# In[6]:

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
    
    #print("filename1: {}".format(filename1))
        
    if yeardate_match:
        filename_1_clean = regex.sub(yeardate_patt, " ",filename1)
        #print("yeardate_match. filename_1_clean is:\n {:<30}".format(filename_1_clean))
        
    elif year_match and not yeardate_match:
        filename_1_clean = regex.sub(year_patt, " ",filename1)
        #print("year_match and not yeardate_match. filename_1_clean is:\n {:<30}".format(filename_1_clean))
        
    #elif date_match and not yeardate_match:
    #    print("date_match: {} in filename1: {}".format(date_match,filename1))
    
    else:
        filename_1_clean = filename1
        #print("no year_match or yeardate_match. filename_1_clean is:\n {:<30}".format(filename_1_clean))
    
    # Remove the extension from filename_1_clean
    fname, extension = os.path.splitext(filename_1_clean)
    
    filename_1_clean = fname
    #print(filename_1_clean)
    
    
    # Remove all 'Bis' from end of filename_1_clean
    filename_1_clean = regex.sub(r"Bis", "", filename_1_clean, flags=regex.I)
    #print("filename_1_clean: {}".format(filename_1_clean))
    
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
    #print("filename: {}\n".format(filename))
    
    # Ensure no multiple spaces left
    #filename = regex.sub(r" +"," ", filename)
    #print("filename is: {}".format(filename))
    
    return filename


# # Keyword mappings
# 
# Mappings of places published as wikitables can be found here:
# 
# https://commons.wikimedia.org/w/index.php?title=Special%3APrefixIndex&prefix=Associazione+DecArch%2FBatch+upload%2F&namespace=4

# ## Places (Luogo)
# 
# We have two different mappings of places, one general based on the column "Place (Luogo)" in the original metadata file and one more specific which is a combination of the columns "Place (Luogo)" and "Subject (Nome_monumento)". 
# 
# The mapping can be found here:
# 
# https://commons.wikimedia.org/wiki/Commons:Associazione_DecArch/Batch_upload/places

# In[7]:

place_mappings_url = "https://commons.wikimedia.org/wiki/Commons:Associazione_DecArch/Batch_upload/places"
place_mappings = pd.read_html(place_mappings_url, attrs = {"class":"wikitable"}, header=0)
place_mappings_general = place_mappings[0]
# Strip away potential surrounding whitespace
place_mappings_general["Luogo"] = place_mappings_general.Luogo.str.strip() 
place_mappings_general["wikidata"] = place_mappings_general.wikidata.str.strip()
place_mappings_general["category"] = place_mappings_general.category.str.strip() 
place_mappings_general["category"] = place_mappings_general.category.str.replace("_", " ") 

place_mappings_general = place_mappings_general.set_index("Luogo")

place_mappings_specific = place_mappings[1]
# Strip away potential surrounding whitespace
place_mappings_specific["Luogo"] = place_mappings_specific.Luogo.str.strip()
place_mappings_specific["Nome_monumento"] = place_mappings_specific.Nome_monumento.str.strip()

place_mappings_specific["category"] = place_mappings_specific.category.str.strip()
place_mappings_specific["category"] = place_mappings_specific.category.str.replace("_", " ")
place_mappings_specific["wikidata"] = place_mappings_specific.wikidata.str.strip()


place_mappings_specific["Specific_place"] = place_mappings_specific.Luogo + " " + place_mappings_specific.Nome_monumento
place_mappings_specific = place_mappings_specific[["Specific_place" ,"Luogo","Nome_monumento","category","wikidata"]]
place_mappings_specific = place_mappings_specific.set_index("Specific_place")


# In[8]:

place_mappings_general.head(3)


# In[9]:

place_mappings_specific.head(3)


# # Population of the Photograph template
# 
# ## Template mapping

#  The master template mapping lives as [task T143212 on Phabricator](https://phabricator.wikimedia.org/T143212)

# ## Create wikitext for image pages
# Available as .py script on [my github](https://github.com/mattiasostmar/GAR_Syria_2016-06/blob/master/create_metatdata_textfiles.py)

# In[10]:

def save_filename_to_filename_file(filname_file, filename):
    """Create a file mapping original filenames and their folders with new
    Commons filenames according to <Task X on Phabricator>"""
    folder = row["Folder"]
    file = row["Filename"]
    # Filename: <Filename_1_clean>_-_DecArch_-_<Folder_#>-<Filename_0_clean>.<ext>
    
    #print("filename: {}".format(filename))
    filenames_file.write("{}|{}|{}\n".format(row["Folder"],row["Filename"],filename))


# In[15]:

def create_infofile(row, filename):
    """Create wikitext for each file and store them in a folder with the extension .info"""
    
    outpath = "./photograph_template_texts/"
    nome_foto = row["Nome foto"].replace(" ", "_")
    nome_foto_0, dummy, nome_foto_1 = nome_foto.rpartition("_")
    #print("nome_foto_0: {}\ndummy: {}\nnome_foto_1: {}".format(nome_foto_0,dummy,nome_foto_1))
    global total_images
    global OK_images
    global faulty_images
    global uncategorized_images
    
    total_images += 1
    
    template_parts = []
    
    header = "{{Photograph"
    template_parts.append(header)
    
    if not pd.isnull(row["Nome autore"]): 
        photographer = "|photographer = " + row["Nome autore"][8:]
    else:
        print("Warning! Empty Author column in row no {} photo {}".format(row_no, row["Nome foto"]))
        photographer = "|photographer = "
        faulty_images += 1
    template_parts.append(photographer)
    
    if pd.notnull(row["Nome foto"]):
        title_it = "{{it|'''" + row["Nome foto"] + "'''}}"
    else:
        print("Warning! Column 'Nome foto' in file {} is empty!".format())
    if pd.notnull(row["Monument name"]) and row["Monument name"] != row["Nome foto"]:
        title_en = "{{en|" + row["Monument name"] + "}}"
    else:
        pass
    title = "|title = "
    if 'title_en' in locals():
        full_title = title + title_it + "\n" + title_en
        template_parts.append(full_title)
    else:
        full_title = title + title_it
        template_parts.append(full_title)
    
    # {{it|<Descrizione> OR <Nome monumento>, <Luogo>, <Anno>}}  IF <Nome monumento> is the same as <Luogo> then leave out <Nome Monumento>
    if pd.notnull(row["Descrizione"]) and len(row["Descrizione"].split()) >3: 
        description_it = "{{it|" + row["Descrizione"] + "}}"
    else:
        if pd.notnull(row["Nome monumento"]) and pd.notnull(row["Luogo"]) and row["Nome monumento"] != row["Luogo"]: 
            description_it = "{{it|" + str(row["Nome monumento"]) + ", " + str(row["Luogo"]) + ", " + str(row["Anno"]) + "}}"
        else:
            pass # Fill in correct code here!
            description_it = "{{it|" + str(str(row["Luogo"])) + ", " + str(row["Anno"]) + "}}"
    
    eng_description_maintanence_category = None
    # {{en|<Description> OR <Subject>, <Place> in <Anno>}} IF <Description> is the same as <Descrizione> THEN treat as empty
    if pd.notnull(row["Description"]) and not (row["Description"] == row["Descrizione"]): #77 av 535 helt tomma
        #print("Case 1")
        description_en = "{{en|" + row["Monument name"] + "}}" # <Description> is empty though, not translated
        #description = "|description = " + description_it + "\n" + description_en
        
    elif pd.notnull(row["Monument name"]) and pd.notnull(row["Description"]) and not row["Monument name"] == row["Nome monumento"]:
        #print("Case  2")
        #description_en = "{{en|" + str(row["Description"]) + ", " + str(row["Place"]) + " in " + str(row["Anno"]) + "}}"
        description_en = "{{en|" + row["Monument name"] + ", " + row["Place"] + ", in " + str(row["Anno"]) + "}}"
        
    else:
        #print("Case 3") # add maintanence category further down in categories appending section
        eng_description_maintanence_category = "[[Category:Images_from_DecArch_without_English_description]]" # Nothing here at the moment
    
    
    if 'description_en' in locals():
        full_description = "|description = " + description_it + "\n" + description_en
        template_parts.append(full_description)
    else: 
        full_description = "|description = " + description_it
        template_parts.append(full_description)
    
    depicted_people = "|depicted people ="
    template_parts.append(depicted_people)
    # Workoaround that we don't have actual specific places in mapping table
    if not row["Luogo"] == row["Nome monumento"] and pd.notnull(row["Luogo"]) and pd.notnull(row["Nome monumento"]):
        
        spec_place = row["Luogo"] + " " + row["Nome monumento"]
    
        if not place_mappings_specific.loc[spec_place]["wikidata"] == "-"         and pd.notnull(place_mappings_specific.loc[spec_place]["wikidata"]):
            depicted_place = "|depicted place = {{city|" +             place_mappings_specific.loc[spec_place]["wikidata"][2:] + "}}" #[2:] since "d:" begins wikidata string
            #print(depicted_place)
        elif not place_mappings_general.loc[row["Luogo"]]["wikidata"] == "-" or pd.isnull(place_mappings_general.loc[row["Luogo"]]["wikidata"]):
            depicted_place = "|depicted place = {{city|" +             place_mappings_general.loc[row["Luogo"]]["wikidata"][2:] + "}}" #[2:] since "d:" begins wikidata string
            #print(depicted_place)
        else:
            depicted_place = "|depicted place = " + row["Nome monumento"] + ", " + row["Luogo"]
            #print(depicted_place)
            
    else:
        depicted_place = "|depicted place = " + row["Luogo"]
    template_parts.append(depicted_place)
    
    # ex "...20 marzo '93..."
    common_date_patt = regex.compile(r" 20?[o']? m? ?arz[o0p] ?'?\d+[\. ]?",flags=regex.I) # matches one occasion of 2 marzo '93
    common_date_match = common_date_patt.search(row["Filename"])
    #print("Filename: {}\nMatch: {}".format(row["Filename"], common_date_match))
    
    if pd.notnull(row["Anno"]):
        if common_date_match:
            date = "|date = 1993-03-20" # or better {{date|1993|3|20}}?
        else:
            date = "|date = " + str(row["Anno"])
    else:
        date = "|date = "
    template_parts.append(date)
        
    medium = "|medium =" 
    template_parts.append(medium)
    
    dimensions = "|dimensions ="
    template_parts.append(dimensions)
    
    institution = "|institution = {{Institution:Associazione DecArch}}"
    template_parts.append(institution)
    
    department = "|department ="
    template_parts.append(department)
    
    references = "|references ="
    template_parts.append(references)
    
    object_history = "|object history ="
    template_parts.append(object_history)
    
    exhibition_history = "|exhibition history ="
    template_parts.append(exhibition_history)
    
    credit_line = "|credit line ="
    template_parts.append(credit_line)
    
    inscriptions = "|inscriptions ="
    template_parts.append(inscriptions)
    
    notes = "|notes ="
    template_parts.append(notes)
    
    accession_number = "|accession number ="
    template_parts.append(accession_number)
    
    source = "|source = " +    "The original image file was recieved from Associazione Decarch with the following <folder> / <filename> structure:<br />\n''" +    str(row["Folder"]) + " / " + str(row["Filename"]) + "''\n{{Associazione DecArch cooperation project|COH}}"
    
    template_parts.append(source)
    
    if pd.notnull(row["Nome autore"]):
        permission = "|permission = {{CC-BY-SA-4.0|" + row["Nome autore"][8:] + " / DecArch}}\n{{PermissionOTRS|id=2016042410005869}}"
    else:
        permission = "|permission = {{CC-BY-SA-4.0|Associazione DecArch}}\n{{PermissionOTRS|id=2016042410005869}}"
    template_parts.append(permission)
    
    other_versions = "|other_versions ="
    template_parts.append(other_versions)
    
    template_parts.append("}}")
    
    
    categories_list = []
    # [[Category:<Category from Specific Place> AND/OR <Category from Luogo (place)>]] 
    specific_place_category = None
    general_place_category = None
    categories_maintanence_category = None
    batchupload_category = "[[Category:Images_from_DecArch_2016-08]]"
    # if requested by DecArch:
    # translation_needed_category = "[[Category:Images_from_DecArch_needing_English_description]]"
    # categories_list.append(translation_needed_category)
    
    if eng_description_maintanence_category:
        categories_list.append(eng_description_maintanence_category)
    
    if 'spec_place' in locals():
        if place_mappings_specific.loc[spec_place]["category"] != "-" and pd.notnull(place_mappings_specific.loc[spec_place]["category"]): 
            specific_place_category = "[[" + place_mappings_specific.loc[spec_place]["category"] + "]]"
            #print("specific_place_category{}".format(specific_place_category)) 

            
    if place_mappings_general.loc[row["Luogo"]]["category"] != "-" and pd.notnull(place_mappings_general.loc[row["Luogo"]]["category"]):
        general_place_category = "[[" + place_mappings_general.loc[row["Luogo"]]["category"] + "]]"
        #print("general_place_category: {}".format(general_place_category))
    
    # manage content categories
    if specific_place_category:
        categories_list.append(specific_place_category)
        
    elif general_place_category and not specific_place_category:
        categories_list.append(general_place_category) 
        
    elif general_place_category and specific_place_category:
        categories_list.extend([general_place_category, specific_place_category])
        
    else:
        print("No categories appended to file: {}".format(filename))
        categories_maintanence_category = "[[Category:Images_from_DecArch_without_categories]]"
        #print("maintanence_category: {}".format(maintanence_category))
        categories_list.append(categories_maintanence_category)
    
    Commons_category = "[[Category:" + str(row["Commons_category"]) + "]]"
    if regex.search(r" \+ ",Commons_category):
        cats = regex.split(r" \+ ",Commons_category)
        #print("{} is really {}".format(row.Commons_category, cats))
        
        for cat_no, cat in enumerate(cats):
            if cat_no == 0:
                Commons_category = cat + "]]" 
            else:
                Commons_category = "[[Category:" + cat
            
            if Commons_category != specific_place_category and Commons_category != general_place_category:
                categories_list.append(Commons_category)
                #print("Commons_category: {}".format(Commons_category))
            else:
                pass
    else:
        pass
    
    if Commons_category != specific_place_category     and Commons_category != general_place_category     and pd.notnull(row["Commons_category"]):
        categories_list.append(Commons_category)
        #print("Commons_category: {}".format(Commons_category))
                
    if categories_list == None:
        print("categories_list is None")
        categories_list.append(categories_maintanence_category)
        #faulty_images += 1
        uncategorized_images += 1

    categories_list.append(batchupload_category)
    
    
    if len(categories_list) >0:
        OK_images += 1
    
    #print(categories_list)
    #print()
    
    if not os.path.exists(outpath):
        os.mkdir(outpath)
    outfile = open(outpath + filename + ".info", "w")
    outfile.write("\n".join(template_parts) + "\n" + "\n".join(categories_list))

    outfile.close()
    #return total_images, faulty_images, OK_images


# # Run the full script

# In[16]:

# remove possible duplicate files with other extension names
get_ipython().system('rm -rf ./photograph_template_texts/*')

total_images = 0
OK_images = 0
uncategorized_images = 0
faulty_images = 0

filenames_file = open("./filenames_mapping.csv","w")
filenames_file.write("Folder|Original|Commons\n")
    
for row_index, row in merged.iterrows():
    filename = create_filename(row["Folder"], row["Filename"])
    save_filename_to_filename_file(filenames_file, filename)
    create_infofile(row, filename)
    #print("Stats: \nTotal images {}\nOK images {}\nUncategorized images {}\nImages missing author {}".format(total_images, OK_images - faulty_images, uncategorized_images, faulty_images ))
#print("Total Stats: \nTotal images {}\nOK images {}\nUncategorized images {}\nImages missing author {}".format(total_images, OK_images - faulty_images, uncategorized_images, faulty_images ))
print("Uncategorized images: {} out of {}".format(uncategorized_images, total_images))


# ## Tests

# In[44]:

not_translated_description = 0
for index, row in merged.iterrows():
    if row["Description"] == row["Descrizione"]:
        not_translated_description += 1
print(not_translated_description)


# In[45]:

not_translated_monument_name = 0
for index, row in merged.iterrows():
    if row["Monument name"] == row["Nome monumento"]:
        not_translated_description += 1
print(not_translated_description)


# In[ ]:

depicted_place = "|depicted place = {{city|" + place_mappings_specific.loc[row["Luogo"]]["wikidata"] + "}}"


# In[15]:

place_mappings_specific


# In[26]:

merged.columns

test ssh no 2
# In[ ]:



