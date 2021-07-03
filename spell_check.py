# -*- coding: utf-8 -*-
"""
@author: MikeShuser
Spell-check program built on top of barrust's pyspellchecker package:
    https://github.com/barrust/pyspellchecker

Designed for survey responses in particular, where spelling errors are common
and can interfere with downstream applications like topic modelling, vector 
space embedding and visualisations 
"""

from spellchecker import SpellChecker
import pandas as pd

def manual_check(text_ser: pd.Series, 
        lang='en', 
        speller=None, 
        perma_fix=None,
        start_ndx=0):
    """
    Spell checking command-line style interface.
    Function input should be a pandas Series with all punctuation removed.
    Run on pre-lemmatized text to produce better lemmas.
    
    Usage
    This function will loop through a Series and, when applicable, 
    will output a word pair of (misspelled word, suggested correction)
    For every such pair, provide input to tell the spell checker what to do:
        y     --> replace misspelled word with suggestion
        ya    --> replace all occurrences of misspelled word with suggestion
        n     --> do not replace word
        na    --> do not replace word and add current spelling to dictionary
                    so future instances do not count as mispelled
        o     --> replace misspelled word, but not with suggested correction
                  -this option will ask you enter a custom spelling, 
                  followed by a 'y' or 'ya' to specify replacement type
        del   --> delete this response from the output Series
        ex    --> exit the function loop
        
    Arguments:
        text_ser    --> Series that contains the text responses to spell-check
        lang        --> Language, only English(en) and French(fr) tested
        speller     --> SpellChecker() object, can pass one instead of starting
                            a new one from scratch
        perma_fix   --> dict recording all permanent spelling corrections, can 
                            pass one instead of starting a new one from scratch
        start_ndx   --> where to begin the Series loop, by default starts at
                            the beginning

    Returns 4 objects:
        -a Series with corrected spellings 
        -a spell checker object which can be saved for future use
        -a list of any new words added to the dictionary through option 'na'
        -a dictionary of {misspelled : corrected} words
    """

    if speller == None:
        spell = SpellChecker(language=lang)
    else:
        assert isinstance(speller, SpellChecker), "Wrong object type passed \
            for 'speller'. Needs to be an instance of SpellChecker"
        spell = speller
    
    if perma_fix == None:
        perma_fix = {}
    else:
        assert isinstance(perma_fix, dict), "Wrong object type passed for \
            'perma_fix'. Needs to be a dictionary object"
        perma_fix = perma_fix
    
    assert isinstance(text_ser, pd.Series), "Wrong object type passed for \
        'text_ser'. Needs to be a pandas Series object"
    unchecked = text_ser.copy()
    unchecked.index = pd.RangeIndex(len(unchecked))
    checked = pd.Series(index=unchecked.index)
    
    new_additions = [] #all words I want to add to dictionary
    del_ndx = [] #responses to delete afterwards
    
    for i, txt in enumerate(unchecked):
        if i < start_ndx:
            checked[i] = txt
            continue
        
        txt_list = txt.split()
        misspelled = spell.unknown(txt_list)
        if len(misspelled) == 0:
            checked[i] = txt
        else:
            print()
            print("Index: " + str(i))
            print("Response: " + txt)
            flag_skip = False
            for word in misspelled:
                if flag_skip:
                    break
                
                if word in perma_fix.keys():
                    txt_list = replace_word(txt_list, word, perma_fix[word])
                    
                else:
                    flag_main = True
                    while flag_main:
                        correct = spell.correction(word)
                        arg = input("{0} {1} > ".format(word, correct))
                        if arg == 'y':
                            #replace only this correction
                            txt_list = replace_word(txt_list, word, correct)
                            flag_main = False
                            
                        elif arg == 'ya':
                            #replace all such words with correction
                            txt_list = replace_word(txt_list, word, correct)                    
                            perma_fix[word] = correct
                            flag_main = False
                        
                        elif arg == 'n':
                            #skip this correction
                            flag_main = False
                        
                        elif arg == 'na':
                            #add word to dict so all future instances will skip
                            spell.word_frequency.add(word)
                            new_additions.append(word)
                            flag_main = False
                            
                        elif arg == 'o':
                            #enter a different spelling
                            flag_other = True
                            while flag_other:
                                custom = input("Enter spelling: ").split()
                                if len(custom) != 2:
                                    print('You must enter 2 arguments. ' +
                                          'Please refer to manualCheck__doc__')
                                else:
                                    if custom[1] == 'y':
                                        txt_list = replace_word(txt_list, 
                                                               word, 
                                                               custom[0])
                                        flag_other = False
                                        flag_main = False
                                    
                                    elif custom[1] == 'ya':
                                        txt_list = replace_word(txt_list, 
                                                               word, 
                                                               custom[0])                    
                                        perma_fix[word] = custom[0]
                                        flag_other = False
                                        flag_main = False
                                    
                                    else:
                                        print('Unknown argument provided')
                        
                        elif arg == 'del':
                            #add index to deletion list
                            del_ndx.append(i)
                            flag_main = False
                            flag_skip = True
                        
                        elif arg == 'ex':
                            #exit function prematurely
                            return (checked[~checked.index.isin(del_ndx)], 
                                    spell, new_additions, perma_fix)
                            
                        else:
                            print('Unknown argument provided')

            checked[i] = ' '.join(txt_list)
    return (checked[~checked.index.isin(del_ndx)], 
            spell, new_additions, perma_fix)

def get_ndx(src_list, word):
    #return all indexes where a value is present
    return [i for i, j in enumerate(src_list) if j == word]

def replace_ndx(src_list, ix_list, new_word):
    #replace all indexes with corrected word
    for ix in ix_list:
        src_list[ix] = new_word
    return src_list
    
def replace_word(src_list, word, new_word):
    ix_list = get_ndx(src_list, word)
    txt_list = replace_ndx(src_list, ix_list, new_word)
    return txt_list

def replace_from_dict(unchecked, perma_fix):
    unchecked.index = pd.RangeIndex(len(unchecked))
    checked = pd.Series(index=unchecked.index)
    
    for i, row in enumerate(unchecked): 
        txt = row.split()
        for word in txt:
            if word in perma_fix.keys():
                txt = replace_word(txt, word, perma_fix[word])
        checked[i] = ' '.join(txt)
        
    return checked

def split_words(text):
    split = text.map(lambda x: x.replace("_", " "))
    return split

if __name__ == '__main__':
    pass

    '''DEBUGGING
    import pickle
    import os

    os.chdir("C:\\spellchecker")
    df = pd.read_pickle("data_sources\\corpus_unlemmatized.pkl")
    text = df.map(lambda x: ' '.join(x))
    clean, spell, new, fixed = manualCheck(df, 
                                           speller=spell,
                                           perma_fix=perma_fix)
    
    res = res[res.notnull()]
    res.index = pd.RangeIndex(len(res))

    res = replace_from_dict(clean, perma_fix)       
    res = split_words(res2)
    
    cleaned = res.map(lambda x: ' '.join([word.lemma_ for word in nlp(x)])) 
    cleaned.to_pickle("data_sources\\ecom_corpus_lemmatized.pkl")
    
    res.to_pickle("data_sources\\ecom_corpus_noLemmas.pkl")
    res = pd.read_pickle("data_sources\\ecom_partial_check_nofrench.pkl")
    ix = pd.read_excel("data_sources\\french_ix.xlsx")
    res = res[~res.index.isin(ix.iloc[:,0].tolist())]

    with open('data_sources\\ecom_spell.pkl', 'wb') as handle:
        pickle.dump(spell, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('data_sources\\perma_fix.pkl', 'wb') as handle:
        pickle.dump(fixed, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('data_sources\\new_words.pkl', 'wb') as handle:
        pickle.dump(new, handle, protocol=pickle.HIGHEST_PROTOCOL)
    '''