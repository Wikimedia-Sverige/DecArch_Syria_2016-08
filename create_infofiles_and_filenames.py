
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


# In[10]:

merged = pd.concat([metadata_it,metadata_en], axis=1) 
merged.tail(2)


# # Create filenames

# In[5]:

def create_filename(row_object):
    """Takes a DataFrame row from the 'merged' dataframe and returns a string filename."""
    # remove all underscores
    no_underscores = regex.sub(r"_", " ", row["Filename"])
    
    # <Filename0>, dummy, <Filename1> = <Filename>.partition(" ") 
    filename0, dummy, filename1 = no_underscores.partition(" ")
    
    # Grab the extension for later use
    ext = regex.findall(r"\.\w+",filename1)[-1]
    #print(ext)
    
    # <Filename_1_clean> = <Filename1> with "20 marzo..." removed, any dubble spaces replaced by single ones 
    # and finally the spaces substituted by underscores (_). Also remove the file type extension.
    yeardate_patt = regex.compile(r" \d+[o']? m? ?arz[o0p] ?'?\d+[\. ]?",flags=regex.I)
    year_patt = regex.compile(r" '\d\d[\.,]? ",flags=regex.I)
    
    yeardate_match = yeardate_patt.search(filename1)
    year_match = year_patt.search(filename1)
        
    if yeardate_match:
        filename_1_clean = regex.sub(yeardate_patt, " ",filename1)
        
    elif year_match and not yeardate_match:
        filename_1_clean = regex.sub(year_patt, " ",filename1)
    
    else:
        filename_1_clean = row["Filename"]
    
    # Remove the extension from filename_1_clean
    ext_patt = regex.compile(ext, flags=regex.I)
    filename_1_clean = regex.sub(ext_patt, "", filename_1_clean)
    #print(filename_1_clean)
    
    # Remove all 'Bis' from end of filename_1_clean
    filename_1_clean = regex.sub(r"Bis", "", filename_1_clean, flags=regex.I)
    #print(filename_1_clean)
    
    # Remove all leading and trailing whitespace from end of filename_1_clean
    filename_1_clean = filename_1_clean.strip(" ")
    #print(filename_1_clean)
    
    # <Filename_0_clean> = <Filename0> with any trailing brackets ()) removed.
    filename_0_clean = regex.sub(r"\).?","",filename0)
    #print(filename_0_clean)
        
    # <Folder_#>, dummy, dummy = <Folder>.partition("_")
    folder_no, dummy, dummy  = row["Folder"].partition("_")
    #print(folder_no)
    
    #Filename: <Filename_1_clean>_-_DecArch_-_<Folder_no>-<Filename_0_clean>.<ext>
    #Filename example:
    #So for 49) Palmira. Via colonnata presso il teatro. 20 marzo '93. Bis.jpg end result is
    #Palmira._Via_colonnata_presso_il_teatro._-_DecArch_-1-49.jpg
    #Palmira._Via_colonnata_presso_il_teatro._-_DecArch_-1-49.jpg
    filename = filename_1_clean + "_-_DecArch_" + folder_no + "-" + filename_0_clean + ext
    
    # Ensure no multiple spaces left
    filename = regex.sub(r" +"," ", filename)
    
    # Repalce all spaces with underscores
    filename = regex.sub(r" ", "_", filename)
    
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

# In[6]:

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


# In[7]:

place_mappings_general.head(3)


# In[8]:

place_mappings_specific.head(3)


# # Population of the Photograph template
# 
# ## Template mapping

#  The master template mapping lives as [task T143212 on Phabricator](https://phabricator.wikimedia.org/T143212)

# ## Create wikitext for image pages
# Available as .py script on [my github](https://github.com/mattiasostmar/GAR_Syria_2016-06/blob/master/create_metatdata_textfiles.py)

# In[12]:

# remove possible diuplicate files with other extension names
get_ipython().system('rm -rf ./photograph_template_texts/*')

total_images = 0
OK_images = 0
uncategorized_images = 0
faulty_images = 0

filenames_file = open("./filenames_mapping.csv","w")
filenames_file.write("Folder|Original|Commons\n")

for row_no, row in merged.iterrows():
    
    # Filename: <Filename_1_clean>_-_DecArch_-_<Folder_#>-<Filename_0_clean>.<ext>
    filename = create_filename(row)

    #print("filename: {}".format(filename))
    filenames_file.write("{}|{}|{}\n".format(row["Folder"],row["Nome foto"],filename))
    
    outpath = "./photograph_template_texts/"
    nome_foto = row["Nome foto"].replace(" ", "_")
    nome_foto_0, dummy, nome_foto_1 = nome_foto.rpartition("_")
    #print("nome_foto_0: {}\ndummy: {}\nnome_foto_1: {}".format(nome_foto_0,dummy,nome_foto_1))
    
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
    
    title_it = "{{it|'''" + regex.sub("_"," ",nome_foto) + "'''}}"
    #title_en = "{{en|" + regex.sub("_"," ",row["Title"][:-3]) + "}}"
    
    title = "|title = " + title_it #+ "\n" + title_en
    template_parts.append(title)
    
    if pd.notnull(row["Descrizione"]) and len(row["Descrizione"].split()) >3:
        description_it = "{{it|" + row["Descrizione"] + "}}"
    else:
        if pd.notnull(row["Nome monumento"]) and pd.notnull(row["Luogo"]) and row["Nome monumento"] != row["Luogo"]: 
            description_it = "{{it|" + str(row["Nome monumento"]) + ", " + str(row["Luogo"]) + ", " + str(row["Anno"]) + "}}"
        else:
            pass # Fill in correct code here!
            description_it = "{{it|" + str(str(row["Luogo"])) + ", " + str(row["Anno"]) + "}}"
        
    if pd.notnull(row["Description"]) and not (row["Description"] == row["Descrizione"]):
        description_en = "{{en|" + row["Description"] + "}}" # <Description> is empty though, not translated
        description = "|description = " + description_it + "\n" + description_en
    else:
        #description_en = "{{en|" + str(row["Description"]) + ", " + str(row["Place"]) + " in " + str(row["Anno"]) + "}}"
        description = "|description = " + description_it
    
    
    template_parts.append(description)
    
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
    print("Filename: {}\nMatch: {}".format(row["Filename"], common_date_match))
    
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
    
    source = "|source = " + str(row["Folder"]) + "/" + str(row["Filename"]) + "\n{{Associazione DecArch cooperation project|COH}}"
    template_parts.append(source)
    
    if pd.notnull(row["Nome autore"]):
        permission = "|permission = {{CC-BY-SA-4.0|" + row["Nome autore"][8:] + " / GAR}}\n{{PermissionOTRS|id=2016042410005958}}"
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
    maintanence_category = None
    batchupload_category = "[[Category:Images_from_DecArch_2016-08]]"
    translation_needed_category = "[[Category:Images_from_DecArch_needing_English_description]]"
    
    if place_mappings_specific.loc[spec_place]["category"] != "-" and pd.notnull(place_mappings_specific.loc[spec_place]["category"]): 
        
        specific_place_category = "[[" + place_mappings_specific.loc[spec_place]["category"] + "]]"
        #print("specific_place_category{}".format(specific_place_category)) 
     
    elif place_mappings_general.loc[row["Luogo"]]["category"] != "-" and pd.notnull(place_mappings_general.loc[row["Luogo"]]["category"]):
        general_place_category = "[[" + place_mappings_general.loc[row["Luogo"]]["category"] + "]]"
        #print("general_place_category: {}".format(general_place_category))
    
    # [[Category:Images_from_GAR_Syria_2016-06]]
    else:
        maintanence_category = "[[Category:Images_from_DecArch_without_categories]]"
        #print("maintanence_category: {}".format(maintanence_category))
    
    # manage content categories
    if specific_place_category :
        categories_list.append(specific_place_category)
        
    elif general_place_category and not specific_place_category:
        categories_list.append(general_place_category) 
    
    Commons_category = "[[Category:" + str(row["Commons_category"]) + "]]"
    if regex.search(r" \+ ",Commons_category):
        cats = regex.split(r" \+ ",Commons_category)
        print("{} is really {}".format(row.Commons_category, cats))
        
        for cat_no, cat in enumerate(cats):
            if cat_no == 0:
                Commons_category = cat + "]]" 
            else:
                Commons_category = "[[Category:" + cat
            
            if Commons_category != specific_place_category and Commons_category != general_place_category:
                categories_list.append(Commons_category)
                print("Commons_category: {}".format(Commons_category))
            else:
                pass
    else:
        pass
    
    if Commons_category != specific_place_category     and Commons_category != general_place_category     and pd.notnull(row["Commons_category"]):
            categories_list.append(Commons_category)
            #print("Commons_category: {}".format(Commons_category))
                
    if categories_list == None:
        print("categories_list is None")
        categories_list.append(maintanence_category)
        faulty_images += 1

    categories_list.append(batchupload_category)
    categories_list.append(translation_needed_category)
    
    if len(categories_list) >0:
        OK_images += 1
    #print(categories_list)
    print()
    
    if not os.path.exists(outpath):
        os.mkdir(outpath)
    outfile = open(outpath + filename + ".info", "w")
    outfile.write("\n".join(template_parts) + "\n" + "\n".join(categories_list))

filename_file.close()    
print("Stats: \nTotal images {}\nOK images {}\nUncategorized images {}\nImages missing author {}".format(total_images, OK_images - faulty_images, uncategorized_images, faulty_images ))


# In[21]:

get_ipython().system('ls -la ./photograph_template_texts/ | head -n10')


# ## Tests

# In[ ]:

depicted_place = "|depicted place = {{city|" + place_mappings_specific.loc[row["Luogo"]]["wikidata"] + "}}"


# In[15]:

place_mappings_specific


# In[ ]:



