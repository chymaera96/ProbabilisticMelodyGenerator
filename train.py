import os
import numpy as np
import random
import pickle
import argparse


parser = argparse.ArgumentParser(description='Train melody generation automata')
parser.add_argument('--data_path', default='', type=str, metavar='PATH',
                    help='path containing the data file for training')


root = os.path.abspath(os.getcwd())

def translate_notation(swaras):
    '''
    This translates the notes in the data file to western scales.
    '''
    hindi = ['S',r'r','R','g','G','M','m','P','d','D','n','N']
    english = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    trans =  dict(zip(hindi, english))
    note = []
    for s in swaras:
        if s!=',':
            octave = s[1]
            note.append(trans[s[0]]+octave)
        else:
            note.append(s)
    return note

def create_noteset():
    '''
    This creates the set of notes to chose from. "," indicates 
    that the previous note is to be sustained for one beat.
    '''
    noteset = []
    hindi = ['S',r'r','R','g','G','M','m','P','d','D','n','N']
    for ix in range(3,6):
        for n in hindi:
            nt = n + str(ix)
            noteset.append(nt)
    noteset.append(',')
    return noteset

def train_from_dat_file(fpath):
    unotes = translate_notation(create_noteset())
    piecewise_transition_probs = []
    p_transition_probs = np.zeros((len(unotes),len(unotes)))

    for line in open(fpath):
        if len(line) > 0:
            line = line.strip()
            # Counting note transitions
            prev_note = ',' # start with a blank note
            print(line)
            notes = translate_notation(line.split(' '))
            for p_note in notes:
                if len(p_note) > 0:
                    try:
                        toInd = unotes.index(p_note)
                        fromInd = unotes.index(prev_note)
                        p_transition_probs[fromInd,toInd] += 1
                    except:
                        print('\nNote incompatible with raga found:'+p_note+", ignoring note")
                    if p_note == ',': 
                        pass # retain previous note on sustain
                    else: 
                        # update previous note to current note if not sustained
                        prev_note = p_note 

    # convert frequencies to probabilities
    ps = np.sum(p_transition_probs,1)
    ps[np.where(ps==0)] = .1
    p_transition_probs = np.transpose(np.transpose(p_transition_probs)/ps) 
    piecewise_transition_probs.append(p_transition_probs)

    # transition probabilities matrix between the unique notes in the piece
    transition_probs = np.zeros((len(unotes),len(unotes)))
    # computing generic transition_probs from piecewise_transition_probs
    for transition_prob in piecewise_transition_probs:
        transition_probs += transition_prob
        
    return transition_probs

def main():
    args = parser.parse_args()
    data_path = args.data_path
    abs_datapath = os.path.join(root,data_path)
    t_probs = train_from_dat_file(abs_datapath)

    model_fname = data_path.split('/')[-1].split('.')[0]+".aut"
    with open(os.path.join('models',model_fname), "wb") as fp:  
        pickle.dump(t_probs, fp)

if __name__ == '__main__':
    main()